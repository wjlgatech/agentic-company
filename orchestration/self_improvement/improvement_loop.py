"""
ImprovementLoop — the top-level orchestrator that wires together all four
vendor systems and the in-house integration layer.

Public API
----------
    loop = ImprovementLoop()
    loop.attach_to_team(team, workflow_id="feature-dev", self_improve=True)
    # ... team.run(task) happens ...
    # ... loop automatically records the run and may evolve prompts ...

    # CLI helpers
    loop.list_patches(workflow_id)
    loop.approve_patch(patch_id)
    loop.reject_patch(patch_id, reason)
    loop.rollback(workflow_id, agent_id)
    loop.feedback_status(workflow_id)
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from orchestration.self_improvement.vendor.anti_idling_system import AntiIdlingSystem
from orchestration.self_improvement.vendor.multi_agent_performance import (
    MultiAgentPerformanceOptimizer,
)
from orchestration.self_improvement.vendor.recursive_self_improvement import (
    RecursiveSelfImprovementProtocol,
)
from orchestration.self_improvement.vendor.results_verification import (
    ResultsVerificationFramework,
)

logger = structlog.get_logger(__name__)


# =========================================================================== #
# Data models                                                                  #
# =========================================================================== #


@dataclass
class PromptVersion:
    """A versioned snapshot of an agent's persona text."""

    id: str
    workflow_id: str
    agent_id: str
    agent_role: str
    version_number: int
    persona_text: str
    is_active: bool
    applied_patch_id: str | None
    previous_version_id: str | None
    ab_test_id: str | None
    ab_variant: str | None  # "control" | "candidate"
    created_at: str
    deactivated_at: str | None


@dataclass
class PromptPatch:
    """A proposed change to an agent's persona, pending human approval."""

    id: str
    workflow_id: str
    agent_id: str
    agent_role: str
    capability_gaps: list[str]  # stored as JSON
    base_prompt_version_id: str
    proposed_persona_text: str
    justification: str
    generated_by: str  # "llm" | "heuristic"
    status: str  # pending | approved | rejected | applied | rolled_back
    confidence: float
    approved_by: str | None
    approved_at: str | None
    rejection_reason: str | None
    created_at: str


# =========================================================================== #
# PromptVersionStore                                                            #
# =========================================================================== #


class PromptVersionStore:
    """Versioned prompt store backed by SQLite.

    Rollback = follow the previous_version_id chain until we reach the target.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS si_prompt_versions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    agent_id TEXT,
                    agent_role TEXT,
                    version_number INTEGER,
                    persona_text TEXT,
                    is_active INTEGER DEFAULT 1,
                    applied_patch_id TEXT,
                    previous_version_id TEXT,
                    ab_test_id TEXT,
                    ab_variant TEXT,
                    created_at TEXT,
                    deactivated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS si_prompt_patches (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    agent_id TEXT,
                    agent_role TEXT,
                    capability_gaps TEXT,
                    base_prompt_version_id TEXT,
                    proposed_persona_text TEXT,
                    justification TEXT,
                    generated_by TEXT DEFAULT 'heuristic',
                    status TEXT DEFAULT 'pending',
                    confidence REAL,
                    approved_by TEXT,
                    approved_at TEXT,
                    rejection_reason TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS si_ab_tests (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    agent_id TEXT,
                    control_version_id TEXT,
                    candidate_version_id TEXT,
                    status TEXT DEFAULT 'active',
                    winner TEXT,
                    started_at TEXT,
                    concluded_at TEXT
                );

                CREATE TABLE IF NOT EXISTS si_capability_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT,
                    snapshot_json TEXT,
                    created_at TEXT
                );
            """)
            conn.commit()

    # ------------------------------------------------------------------ #
    # Version CRUD                                                         #
    # ------------------------------------------------------------------ #

    def get_active_version(
        self, workflow_id: str, agent_id: str
    ) -> PromptVersion | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT * FROM si_prompt_versions
                   WHERE workflow_id = ? AND agent_id = ? AND is_active = 1
                   ORDER BY version_number DESC LIMIT 1""",
                (workflow_id, agent_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_version(row)

    def create_initial_version(
        self,
        workflow_id: str,
        agent_id: str,
        agent_role: str,
        persona_text: str,
    ) -> PromptVersion:
        version = PromptVersion(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            agent_id=agent_id,
            agent_role=agent_role,
            version_number=1,
            persona_text=persona_text,
            is_active=True,
            applied_patch_id=None,
            previous_version_id=None,
            ab_test_id=None,
            ab_variant=None,
            created_at=datetime.utcnow().isoformat(),
            deactivated_at=None,
        )
        self._insert_version(version)
        return version

    def apply_patch(self, patch: PromptPatch) -> PromptVersion:
        """Deactivate current version and create a new active one from the patch."""
        current = self.get_active_version(patch.workflow_id, patch.agent_id)
        prev_id = current.id if current else None
        next_num = (current.version_number + 1) if current else 1

        # Deactivate current
        if current:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """UPDATE si_prompt_versions
                       SET is_active = 0, deactivated_at = ?
                       WHERE id = ?""",
                    (datetime.utcnow().isoformat(), current.id),
                )
                conn.commit()

        new_version = PromptVersion(
            id=str(uuid.uuid4()),
            workflow_id=patch.workflow_id,
            agent_id=patch.agent_id,
            agent_role=patch.agent_role,
            version_number=next_num,
            persona_text=patch.proposed_persona_text,
            is_active=True,
            applied_patch_id=patch.id,
            previous_version_id=prev_id,
            ab_test_id=None,
            ab_variant=None,
            created_at=datetime.utcnow().isoformat(),
            deactivated_at=None,
        )
        self._insert_version(new_version)

        # Mark patch as applied
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE si_prompt_patches SET status = 'applied' WHERE id = ?",
                (patch.id,),
            )
            conn.commit()

        return new_version

    def rollback(self, workflow_id: str, agent_id: str) -> PromptVersion | None:
        """Roll back to the previous version. Returns the restored version or None."""
        current = self.get_active_version(workflow_id, agent_id)
        if current is None or current.previous_version_id is None:
            return None

        # Deactivate current
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE si_prompt_versions
                   SET is_active = 0, deactivated_at = ?
                   WHERE id = ?""",
                (datetime.utcnow().isoformat(), current.id),
            )
            # Reactivate previous
            conn.execute(
                "UPDATE si_prompt_versions SET is_active = 1, deactivated_at = NULL WHERE id = ?",
                (current.previous_version_id,),
            )
            conn.commit()

        return self.get_active_version(workflow_id, agent_id)

    def get_persona_for_run(
        self, workflow_id: str, agent_id: str, run_id: str
    ) -> tuple[str, str]:
        """Return (persona_text, version_id) for the active version.

        If an A/B test is active for this agent, alternates between control and
        candidate based on run_id hash parity so 50% of runs see each variant.
        """
        active = self.get_active_version(workflow_id, agent_id)
        if active is None:
            return "", ""

        # Check for active A/B test
        ab_test = self._get_active_ab_test(workflow_id, agent_id)
        if ab_test is not None:
            # Route by hash of run_id (deterministic, 50/50 split)
            use_candidate = hash(run_id) % 2 == 1
            if use_candidate:
                candidate = self._get_version_by_id(ab_test["candidate_version_id"])
                if candidate:
                    return candidate.persona_text, candidate.id

        return active.persona_text, active.id

    # ------------------------------------------------------------------ #
    # Patch CRUD                                                           #
    # ------------------------------------------------------------------ #

    def save_patch(self, patch: PromptPatch) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO si_prompt_patches
                   (id, workflow_id, agent_id, agent_role, capability_gaps,
                    base_prompt_version_id, proposed_persona_text, justification,
                    generated_by, status, confidence, approved_by, approved_at,
                    rejection_reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    patch.id,
                    patch.workflow_id,
                    patch.agent_id,
                    patch.agent_role,
                    json.dumps(patch.capability_gaps),
                    patch.base_prompt_version_id,
                    patch.proposed_persona_text,
                    patch.justification,
                    patch.generated_by,
                    patch.status,
                    patch.confidence,
                    patch.approved_by,
                    patch.approved_at,
                    patch.rejection_reason,
                    patch.created_at,
                ),
            )
            conn.commit()

    def get_patch(self, patch_id: str) -> PromptPatch | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM si_prompt_patches WHERE id = ?", (patch_id,)
            ).fetchone()
        return self._row_to_patch(row) if row else None

    def list_patches(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
    ) -> list[PromptPatch]:
        query = "SELECT * FROM si_prompt_patches WHERE 1=1"
        params: list[Any] = []
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_patch(r) for r in rows]

    def approve_patch(
        self, patch_id: str, approved_by: str = "human", notes: str = ""
    ) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """UPDATE si_prompt_patches
                   SET status = 'approved', approved_by = ?, approved_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (approved_by, datetime.utcnow().isoformat(), patch_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    def reject_patch(self, patch_id: str, reason: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """UPDATE si_prompt_patches
                   SET status = 'rejected', rejection_reason = ?
                   WHERE id = ? AND status = 'pending'""",
                (reason, patch_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # A/B test helpers                                                     #
    # ------------------------------------------------------------------ #

    def create_ab_test(
        self, workflow_id: str, agent_id: str, candidate_version_id: str
    ) -> str:
        """Create an A/B test between the current active and a candidate version."""
        active = self.get_active_version(workflow_id, agent_id)
        if active is None:
            raise ValueError(f"No active version for {workflow_id}/{agent_id}")

        test_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO si_ab_tests
                   (id, workflow_id, agent_id, control_version_id,
                    candidate_version_id, status, started_at)
                   VALUES (?, ?, ?, ?, ?, 'active', ?)""",
                (
                    test_id,
                    workflow_id,
                    agent_id,
                    active.id,
                    candidate_version_id,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
        return test_id

    def conclude_ab_test(self, test_id: str, winner: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """UPDATE si_ab_tests
                   SET status = 'concluded', winner = ?, concluded_at = ?
                   WHERE id = ?""",
                (winner, datetime.utcnow().isoformat(), test_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    def _get_active_ab_test(self, workflow_id: str, agent_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT * FROM si_ab_tests
                   WHERE workflow_id = ? AND agent_id = ? AND status = 'active'
                   LIMIT 1""",
                (workflow_id, agent_id),
            ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # Capability snapshot                                                  #
    # ------------------------------------------------------------------ #

    def save_capability_snapshot(self, workflow_id: str, capability_map: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO si_capability_states (workflow_id, snapshot_json, created_at)
                   VALUES (?, ?, ?)""",
                (
                    workflow_id,
                    json.dumps(capability_map),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    # ------------------------------------------------------------------ #
    # Serialization helpers                                                #
    # ------------------------------------------------------------------ #

    def _insert_version(self, version: PromptVersion) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO si_prompt_versions
                   (id, workflow_id, agent_id, agent_role, version_number,
                    persona_text, is_active, applied_patch_id, previous_version_id,
                    ab_test_id, ab_variant, created_at, deactivated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    version.id,
                    version.workflow_id,
                    version.agent_id,
                    version.agent_role,
                    version.version_number,
                    version.persona_text,
                    int(version.is_active),
                    version.applied_patch_id,
                    version.previous_version_id,
                    version.ab_test_id,
                    version.ab_variant,
                    version.created_at,
                    version.deactivated_at,
                ),
            )
            conn.commit()

    @staticmethod
    def _row_to_version(row: sqlite3.Row) -> PromptVersion:
        return PromptVersion(
            id=row["id"],
            workflow_id=row["workflow_id"],
            agent_id=row["agent_id"],
            agent_role=row["agent_role"],
            version_number=row["version_number"],
            persona_text=row["persona_text"],
            is_active=bool(row["is_active"]),
            applied_patch_id=row["applied_patch_id"],
            previous_version_id=row["previous_version_id"],
            ab_test_id=row["ab_test_id"],
            ab_variant=row["ab_variant"],
            created_at=row["created_at"],
            deactivated_at=row["deactivated_at"],
        )

    @staticmethod
    def _row_to_patch(row: sqlite3.Row) -> PromptPatch:
        return PromptPatch(
            id=row["id"],
            workflow_id=row["workflow_id"],
            agent_id=row["agent_id"],
            agent_role=row["agent_role"],
            capability_gaps=json.loads(row["capability_gaps"] or "[]"),
            base_prompt_version_id=row["base_prompt_version_id"],
            proposed_persona_text=row["proposed_persona_text"],
            justification=row["justification"],
            generated_by=row["generated_by"],
            status=row["status"],
            confidence=row["confidence"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            rejection_reason=row["rejection_reason"],
            created_at=row["created_at"],
        )

    def _get_version_by_id(self, version_id: str) -> PromptVersion | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM si_prompt_versions WHERE id = ?", (version_id,)
            ).fetchone()
        return self._row_to_version(row) if row else None


# =========================================================================== #
# ImprovementLoop                                                               #
# =========================================================================== #


class ImprovementLoop:
    """
    Top-level orchestrator for self-improving workflows.

    Wires together:
        • ResultsVerificationFramework (SMARC scoring)
        • MultiAgentPerformanceOptimizer (per-agent composite score)
        • RecursiveSelfImprovementProtocol (capability gap detection)
        • AntiIdlingSystem (stagnation detection)
        • PromptVersionStore (versioned personas + patch lifecycle)
        • RunRecorder (per-run SQLite persistence)
        • PromptEvolver (gap → patch proposals)
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_executor: Callable | None = None,
        auto_approve_patches: bool = False,
        ab_test_enabled: bool = True,
        pattern_trigger_n: int = 5,
        stagnation_threshold: float = 0.05,
    ) -> None:
        if db_path is None:
            db_path = Path.home() / ".agenticom" / "self_improve.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.auto_approve_patches = auto_approve_patches
        self.ab_test_enabled = ab_test_enabled
        self.pattern_trigger_n = pattern_trigger_n

        # ── Vendor systems ───────────────────────────────────────────────
        self.verifier = ResultsVerificationFramework()
        self.performance = MultiAgentPerformanceOptimizer(quality_threshold=0.85)
        self.improvement_protocol = RecursiveSelfImprovementProtocol(
            ethical_constraints={
                "do_no_harm": True,
                "human_alignment": True,
                "transparency": True,
                "reversibility": True,
            }
        )
        self.anti_idling = AntiIdlingSystem(idle_threshold=stagnation_threshold)

        # Register sync callbacks (vendor code calls them synchronously)
        self.anti_idling.register_intervention_callback(self._sync_stagnation_callback)
        self.performance.register_optimization_strategy(
            self._sync_agent_below_threshold_callback
        )

        # ── In-house systems ─────────────────────────────────────────────
        self.version_store = PromptVersionStore(db_path)

        from orchestration.self_improvement.prompt_evolver import PromptEvolver
        from orchestration.self_improvement.run_recorder import RunRecorder

        self.prompt_evolver = PromptEvolver(
            self.improvement_protocol, llm_executor=llm_executor
        )

        self.run_recorder = RunRecorder(
            db_path=db_path,
            verifier=self.verifier,
            performance=self.performance,
            improvement_protocol=self.improvement_protocol,
            anti_idling=self.anti_idling,
            version_store=self.version_store,
            pattern_trigger_n=pattern_trigger_n,
            on_pattern_trigger=self._on_pattern_trigger,
        )

        # Track pending async work triggered by sync vendor callbacks
        self._pending_below_threshold: list[dict] = []
        self._pending_stagnation: bool = False

        # Workflow → agent_id → agent ref (populated by attach_to_team)
        self._teams: dict[str, Any] = {}

        logger.info("ImprovementLoop initialised", db=str(db_path))

    # ------------------------------------------------------------------ #
    # Team attachment                                                      #
    # ------------------------------------------------------------------ #

    def attach_to_team(
        self, team: Any, workflow_id: str, self_improve: bool = False
    ) -> None:
        """Register the team and seed initial PromptVersions for each agent."""
        self._teams[workflow_id] = {"team": team, "self_improve": self_improve}

        for _role, agent in team.agents.items():
            agent_id = agent.role.value
            existing = self.version_store.get_active_version(workflow_id, agent_id)
            if existing is None:
                # Bootstrap from the agent's current persona
                persona = agent.persona or ""
                self.version_store.create_initial_version(
                    workflow_id, agent_id, agent.role.value, persona
                )

            if self_improve:
                # Serve the best known persona for this run
                persona_text, version_id = self.version_store.get_persona_for_run(
                    workflow_id, agent_id, run_id=str(uuid.uuid4())
                )
                if persona_text and hasattr(agent, "update_persona"):
                    agent.update_persona(persona_text, version_id)

    # ------------------------------------------------------------------ #
    # Post-run recording (called via asyncio.create_task from team.run)   #
    # ------------------------------------------------------------------ #

    async def record_completed_run(
        self,
        team_result: Any,
        workflow_id: str,
        self_improve: bool = False,
    ) -> None:
        """Record a completed TeamResult. Called as a background task."""
        try:
            await self.run_recorder.record_run(team_result, workflow_id, self_improve)
        except Exception as exc:
            logger.warning("record_completed_run failed", error=str(exc))

        # Flush any pending async work triggered by sync vendor callbacks
        if self._pending_below_threshold:
            pending = list(self._pending_below_threshold)
            self._pending_below_threshold.clear()
            for agent_details in pending:
                await self._on_agent_below_threshold(agent_details, workflow_id)

        if self._pending_stagnation:
            self._pending_stagnation = False
            await self._on_stagnation_detected(workflow_id)

    # ------------------------------------------------------------------ #
    # Loop callbacks                                                       #
    # ------------------------------------------------------------------ #

    async def _on_pattern_trigger(self, workflow_id: str) -> None:
        """Every N runs: identify capability gaps and propose prompt patches."""
        try:
            gaps_raw = self.improvement_protocol._identify_capability_gaps()
            # Save capability snapshot
            self.version_store.save_capability_snapshot(
                workflow_id, self.improvement_protocol.capability_map
            )

            # Build flat gap list for the evolver
            gap_dicts: list[dict] = []
            for cap in gaps_raw.get("low_performance_areas", []):
                gap_dicts.append({"capability": cap, "source": "low_performance_areas"})
            for cap in gaps_raw.get("missing_capabilities", []):
                gap_dicts.append({"capability": cap, "source": "missing_capabilities"})

            if not gap_dicts:
                logger.info("No capability gaps found", workflow_id=workflow_id)
                return

            logger.info(
                "Capability gaps detected",
                workflow_id=workflow_id,
                gaps=len(gap_dicts),
            )

            # Propose a patch per agent that has gaps
            team_info = self._teams.get(workflow_id, {})
            team = team_info.get("team")
            if team is None:
                return

            for _role, agent in team.agents.items():
                agent_id = agent.role.value
                current_version = self.version_store.get_active_version(
                    workflow_id, agent_id
                )
                if current_version is None:
                    continue

                patch = await self.prompt_evolver.propose_patch(
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    agent_role=agent.role.value,
                    current_version=current_version,
                    capability_gaps=gap_dicts,
                    run_count=self.run_recorder._run_count,
                )
                self.version_store.save_patch(patch)
                logger.info("Prompt patch proposed", patch_id=patch.id, agent=agent_id)

                if self.auto_approve_patches:
                    await self._auto_apply_patch(patch, workflow_id, agent)

        except Exception as exc:
            logger.warning("_on_pattern_trigger failed", error=str(exc))

    async def _on_agent_below_threshold(
        self, agent_details: dict, workflow_id: str = ""
    ) -> None:
        """Propose an immediate patch when an agent's composite score drops below 0.85."""
        agent_role = agent_details.get("role", "")
        if not agent_role or not workflow_id:
            return

        team_info = self._teams.get(workflow_id, {})
        team = team_info.get("team")
        if team is None:
            return

        # Find the agent object
        for _role_enum, agent in team.agents.items():
            if agent.role.value == agent_role:
                current_version = self.version_store.get_active_version(
                    workflow_id, agent_role
                )
                if current_version is None:
                    break

                gap_dicts = [
                    {
                        "capability": f"{agent_role}_output_specificity",
                        "source": "below_threshold",
                    }
                ]
                patch = await self.prompt_evolver.propose_patch(
                    workflow_id=workflow_id,
                    agent_id=agent_role,
                    agent_role=agent_role,
                    current_version=current_version,
                    capability_gaps=gap_dicts,
                    run_count=self.run_recorder._run_count,
                )
                self.version_store.save_patch(patch)
                logger.info(
                    "Emergency patch proposed (below threshold)",
                    patch_id=patch.id,
                    agent=agent_role,
                )

                if self.auto_approve_patches:
                    await self._auto_apply_patch(patch, workflow_id, agent)
                break

    async def _on_stagnation_detected(self, workflow_id: str = "") -> None:
        """When AntiIdlingSystem detects stagnation, trigger full gap analysis."""
        logger.warning("Stagnation detected", workflow_id=workflow_id)
        await self._on_pattern_trigger(workflow_id)

    # ------------------------------------------------------------------ #
    # Sync vendor callback bridges (vendor code calls these synchronously) #
    # ------------------------------------------------------------------ #

    def _sync_agent_below_threshold_callback(self, agent_details: dict) -> None:
        """Sync bridge: stash details for async processing after the recording loop."""
        self._pending_below_threshold.append(dict(agent_details))

    def _sync_stagnation_callback(self) -> None:
        """Sync bridge: flag stagnation for async processing after the recording loop."""
        self._pending_stagnation = True

    # ------------------------------------------------------------------ #
    # Auto-apply helper                                                    #
    # ------------------------------------------------------------------ #

    async def _auto_apply_patch(
        self, patch: PromptPatch, workflow_id: str, agent: Any
    ) -> None:
        """Apply an approved patch immediately and update the live agent persona."""
        self.version_store.approve_patch(patch.id, approved_by="auto")
        approved_patch = self.version_store.get_patch(patch.id)
        if approved_patch is None:
            return
        new_version = self.version_store.apply_patch(approved_patch)
        if hasattr(agent, "update_persona"):
            agent.update_persona(new_version.persona_text, new_version.id)
        logger.info(
            "Patch auto-applied",
            patch_id=patch.id,
            version=new_version.version_number,
        )

    # ================================================================== #
    # Public CLI-facing API                                               #
    # ================================================================== #

    def list_patches(
        self, workflow_id: str | None = None, status: str | None = None
    ) -> list[dict]:
        """Return patch records as plain dicts (for CLI display)."""
        patches = self.version_store.list_patches(workflow_id, status)
        return [
            {
                "id": p.id,
                "workflow_id": p.workflow_id,
                "agent_id": p.agent_id,
                "status": p.status,
                "generated_by": p.generated_by,
                "confidence": p.confidence,
                "gaps": p.capability_gaps,
                "justification": p.justification[:120],
                "created_at": p.created_at,
            }
            for p in patches
        ]

    def approve_patch(self, patch_id: str, notes: str = "") -> dict:
        """Human approves a patch; immediately applies it if team is attached."""
        ok = self.version_store.approve_patch(
            patch_id, approved_by="human", notes=notes
        )
        if not ok:
            return {"error": f"Patch {patch_id} not found or not pending"}

        patch = self.version_store.get_patch(patch_id)
        if patch is None:
            return {"error": "Patch disappeared after approval"}

        new_version = self.version_store.apply_patch(patch)

        # Update live agent if team is still attached
        team_info = self._teams.get(patch.workflow_id, {})
        team = team_info.get("team")
        if team:

            for _role_enum, agent in team.agents.items():
                if agent.role.value == patch.agent_id:
                    if hasattr(agent, "update_persona"):
                        agent.update_persona(new_version.persona_text, new_version.id)
                    break

        return {
            "status": "applied",
            "patch_id": patch_id,
            "new_version_id": new_version.id,
            "version_number": new_version.version_number,
        }

    def reject_patch(self, patch_id: str, reason: str) -> dict:
        ok = self.version_store.reject_patch(patch_id, reason)
        if not ok:
            return {"error": f"Patch {patch_id} not found or not pending"}
        return {"status": "rejected", "patch_id": patch_id}

    def rollback(self, workflow_id: str, agent_id: str) -> dict:
        """Roll back an agent's persona to the previous version."""
        restored = self.version_store.rollback(workflow_id, agent_id)
        if restored is None:
            return {"error": "Nothing to roll back (already at initial version)"}

        # Update live agent if attached
        team_info = self._teams.get(workflow_id, {})
        team = team_info.get("team")
        if team:
            for _role, agent in team.agents.items():
                if agent.role.value == agent_id:
                    if hasattr(agent, "update_persona"):
                        agent.update_persona(restored.persona_text, restored.id)
                    break

        return {
            "status": "rolled_back",
            "version_number": restored.version_number,
            "version_id": restored.id,
        }

    def evaluate_ab_test(self, test_id: str) -> dict:
        """Return A/B test summary (run counts and avg SMARC per variant)."""
        # Placeholder — in production, query si_run_records grouped by ab_test_variant
        return {
            "test_id": test_id,
            "note": "Query si_run_records grouped by ab_test_variant for scores.",
        }

    def promote_ab_winner(self, test_id: str, winner: str) -> bool:
        return self.version_store.conclude_ab_test(test_id, winner)

    def feedback_status(self, workflow_id: str | None = None) -> dict:
        """Summary of pending patches and version history."""
        pending = self.version_store.list_patches(workflow_id, status="pending")
        applied = self.version_store.list_patches(workflow_id, status="applied")
        return {
            "pending_patches": len(pending),
            "applied_patches": len(applied),
            "patches": self.list_patches(workflow_id),
        }

    def rate_run(self, run_id: str, score: float, notes: str = "") -> bool:
        return self.run_recorder.rate_run(run_id, score, notes)
