"""
RunRecorder — records every TeamResult to SQLite and feeds the four vendor systems.

After each run:
1. For every StepResult: SMARC-verify → update performance optimizer → update capability map.
2. Log activity to AntiIdlingSystem.
3. Persist a RunRecord row to si_run_records.
4. Optionally extract lessons (non-blocking background task).
5. Every N runs: call on_pattern_trigger for gap analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from orchestration.self_improvement.adapters import CapabilityMapper, StepResultAdapter

if TYPE_CHECKING:
    from orchestration.agents.team import TeamResult
    from orchestration.self_improvement.vendor.anti_idling_system import (
        AntiIdlingSystem,
    )
    from orchestration.self_improvement.vendor.multi_agent_performance import (
        MultiAgentPerformanceOptimizer,
    )
    from orchestration.self_improvement.vendor.recursive_self_improvement import (
        RecursiveSelfImprovementProtocol,
    )
    from orchestration.self_improvement.vendor.results_verification import (
        ResultsVerificationFramework,
    )

logger = logging.getLogger(__name__)


@dataclass
class RunRecord:
    """One row in si_run_records — immutable summary of a completed run."""

    id: str
    run_id: str  # FK → workflow_runs.id (existing table)
    workflow_id: str
    task_description: str
    overall_success: bool
    total_duration_ms: float
    total_retries: int
    total_tokens: int
    step_scores: dict[str, float]  # {step_id: smarc_score}
    agent_scores: dict[str, float]  # {agent_role: composite_score}
    prompt_version_ids: dict[str, str]  # {agent_id: version_id}
    ab_test_variant: str | None
    created_at: str


class RunRecorder:
    """Wire TeamResult into the four vendor systems and persist to SQLite."""

    def __init__(
        self,
        db_path: Path,
        verifier: ResultsVerificationFramework,
        performance: MultiAgentPerformanceOptimizer,
        improvement_protocol: RecursiveSelfImprovementProtocol,
        anti_idling: AntiIdlingSystem,
        lesson_extractor: Any | None = None,
        lesson_manager: Any | None = None,
        version_store: Any | None = None,
        pattern_trigger_n: int = 5,
        on_pattern_trigger: Callable | None = None,
    ) -> None:
        self.db_path = db_path
        self.verifier = verifier
        self.performance = performance
        self.improvement_protocol = improvement_protocol
        self.anti_idling = anti_idling
        self.lesson_extractor = lesson_extractor
        self.lesson_manager = lesson_manager
        self.version_store = version_store
        self.pattern_trigger_n = pattern_trigger_n
        self.on_pattern_trigger = on_pattern_trigger

        # agent_role → optimizer agent_id (registered lazily)
        self._agent_optimizer_ids: dict[str, str] = {}
        self._run_count: int = 0

        self._init_db()

    # ------------------------------------------------------------------ #
    # DB setup                                                             #
    # ------------------------------------------------------------------ #

    def _init_db(self) -> None:
        """Create si_run_records table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS si_run_records (
                    id TEXT PRIMARY KEY,
                    run_id TEXT,
                    workflow_id TEXT,
                    task_description TEXT,
                    overall_success INTEGER,
                    total_duration_ms REAL,
                    total_retries INTEGER,
                    total_tokens INTEGER,
                    step_scores TEXT DEFAULT '{}',
                    agent_scores TEXT DEFAULT '{}',
                    prompt_version_ids TEXT DEFAULT '{}',
                    ab_test_variant TEXT,
                    created_at TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_si_runs_workflow
                ON si_run_records(workflow_id)
            """)
            conn.commit()

    # ------------------------------------------------------------------ #
    # Agent registration                                                   #
    # ------------------------------------------------------------------ #

    def _ensure_agent_registered(self, agent_role: str) -> str:
        """Return the MultiAgentPerformanceOptimizer ID for an agent role."""
        if agent_role not in self._agent_optimizer_ids:
            optimizer_id = self.performance.register_agent(
                {
                    "role": agent_role,
                    "registered_at": datetime.utcnow().isoformat(),
                }
            )
            self._agent_optimizer_ids[agent_role] = optimizer_id
        return self._agent_optimizer_ids[agent_role]

    # ------------------------------------------------------------------ #
    # Main entry point                                                     #
    # ------------------------------------------------------------------ #

    async def record_run(
        self,
        team_result: TeamResult,
        workflow_id: str,
        self_improve: bool = False,
    ) -> RunRecord:
        """
        Record a completed TeamResult into all vendor systems and SQLite.

        Returns a RunRecord (also persisted to DB).
        """
        step_scores: dict[str, float] = {}
        agent_scores_accumulated: dict[str, list[float]] = {}

        # ── 1. Per-step SMARC + performance + capability update ─────────
        for step_result in team_result.steps:
            agent_role = step_result.step.agent_role.value

            # SMARC verification
            smarc_input = StepResultAdapter.to_smarc_input(step_result)
            try:
                smarc_results = self.verifier.verify_results(smarc_input)
            except Exception:
                smarc_results = {
                    "specific": False,
                    "measurable": False,
                    "actionable": False,
                    "reusable": False,
                    "compoundable": False,
                }

            smarc_score = CapabilityMapper.smarc_score(smarc_results)
            step_scores[step_result.step.id] = smarc_score

            # Performance optimizer
            optimizer_id = self._ensure_agent_registered(agent_role)
            perf_data = StepResultAdapter.to_performance_data(step_result, smarc_score)
            try:
                self.performance.update_agent_performance(optimizer_id, perf_data)
            except Exception as exc:
                logger.warning("Performance update failed for %s: %s", agent_role, exc)

            # Track composite score per agent
            composite = self.performance.agents.get(optimizer_id, {}).get(
                "performance_score", smarc_score
            )
            agent_scores_accumulated.setdefault(agent_role, []).append(composite)

            # Capability map update
            capabilities = CapabilityMapper.smarc_to_capabilities(
                agent_role, smarc_results
            )
            try:
                self.improvement_protocol.update_capability_map(capabilities)
            except Exception as exc:
                logger.warning("Capability map update failed: %s", exc)

        # ── 2. Anti-idling activity log ──────────────────────────────────
        overall_smarc = (
            sum(step_scores.values()) / len(step_scores) if step_scores else 0.0
        )
        try:
            self.anti_idling.log_activity(
                {
                    "type": "workflow_run",
                    "workflow_id": workflow_id,
                    "improvement_delta": overall_smarc,
                    "is_productive": team_result.success,
                    "duration": (
                        (
                            team_result.completed_at - team_result.started_at
                        ).total_seconds()
                        if team_result.completed_at
                        else 0
                    ),
                }
            )
        except Exception as exc:
            logger.warning("Anti-idling log failed: %s", exc)

        # ── 3. Compute summary stats ─────────────────────────────────────
        total_retries = sum(sr.retries for sr in team_result.steps)
        total_tokens = sum(sr.agent_result.tokens_used for sr in team_result.steps)
        total_duration_ms = sum(sr.agent_result.duration_ms for sr in team_result.steps)
        agent_scores: dict[str, float] = {
            role: sum(scores) / len(scores)
            for role, scores in agent_scores_accumulated.items()
        }

        # ── 4. Collect prompt version IDs (if version store is wired) ───
        prompt_version_ids: dict[str, str] = {}
        if self.version_store:
            for step_result in team_result.steps:
                agent_id = step_result.step.agent_role.value
                try:
                    _, version_id = self.version_store.get_persona_for_run(
                        workflow_id, agent_id, team_result.team_id
                    )
                    if version_id:
                        prompt_version_ids[agent_id] = version_id
                except Exception:
                    pass

        # ── 5. Persist RunRecord ─────────────────────────────────────────
        record = RunRecord(
            id=str(uuid.uuid4()),
            run_id=team_result.team_id,
            workflow_id=workflow_id,
            task_description=team_result.task,
            overall_success=team_result.success,
            total_duration_ms=total_duration_ms,
            total_retries=total_retries,
            total_tokens=total_tokens,
            step_scores=step_scores,
            agent_scores=agent_scores,
            prompt_version_ids=prompt_version_ids,
            ab_test_variant=team_result.metadata.get("ab_test_variant"),
            created_at=datetime.utcnow().isoformat(),
        )
        self._persist_record(record)
        self._run_count += 1

        # ── 6. Optional: async lesson extraction ─────────────────────────
        if self_improve and self.lesson_extractor and self.lesson_manager:
            asyncio.create_task(self._extract_lessons_async(team_result, workflow_id))

        # ── 7. Pattern trigger every N runs ──────────────────────────────
        if (
            self.on_pattern_trigger is not None
            and self._run_count % self.pattern_trigger_n == 0
        ):
            asyncio.create_task(self.on_pattern_trigger(workflow_id))

        return record

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _persist_record(self, record: RunRecord) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO si_run_records
                (id, run_id, workflow_id, task_description, overall_success,
                 total_duration_ms, total_retries, total_tokens,
                 step_scores, agent_scores, prompt_version_ids,
                 ab_test_variant, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.run_id,
                    record.workflow_id,
                    record.task_description,
                    int(record.overall_success),
                    record.total_duration_ms,
                    record.total_retries,
                    record.total_tokens,
                    json.dumps(record.step_scores),
                    json.dumps(record.agent_scores),
                    json.dumps(record.prompt_version_ids),
                    record.ab_test_variant,
                    record.created_at,
                ),
            )
            conn.commit()

    async def _extract_lessons_async(
        self, team_result: TeamResult, workflow_id: str
    ) -> None:
        """Background lesson extraction — never blocks the hot path."""
        try:
            steps_data = [
                {
                    "step_id": sr.step.id,
                    "agent": sr.step.agent_role.value,
                    "status": sr.status.value,
                    "error": sr.agent_result.error,
                }
                for sr in team_result.steps
            ]
            duration = (
                (team_result.completed_at - team_result.started_at).total_seconds()
                if team_result.completed_at
                else 0
            )
            lessons = self.lesson_extractor.extract_from_run(
                run_id=team_result.team_id,
                workflow_id=workflow_id,
                task=team_result.task,
                status="completed" if team_result.success else "failed",
                duration=duration,
                stages={},
                steps=steps_data,
            )
            for lesson in lessons:
                self.lesson_manager.add_proposed(lesson)
        except Exception as exc:
            logger.warning("Lesson extraction failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Query helpers                                                        #
    # ------------------------------------------------------------------ #

    def get_recent_records(self, workflow_id: str, limit: int = 20) -> list[RunRecord]:
        """Return the most recent RunRecords for a workflow."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM si_run_records
                   WHERE workflow_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (workflow_id, limit),
            ).fetchall()
        records = []
        for row in rows:
            records.append(
                RunRecord(
                    id=row["id"],
                    run_id=row["run_id"],
                    workflow_id=row["workflow_id"],
                    task_description=row["task_description"],
                    overall_success=bool(row["overall_success"]),
                    total_duration_ms=row["total_duration_ms"],
                    total_retries=row["total_retries"],
                    total_tokens=row["total_tokens"],
                    step_scores=json.loads(row["step_scores"] or "{}"),
                    agent_scores=json.loads(row["agent_scores"] or "{}"),
                    prompt_version_ids=json.loads(row["prompt_version_ids"] or "{}"),
                    ab_test_variant=row["ab_test_variant"],
                    created_at=row["created_at"],
                )
            )
        return records

    def rate_run(self, run_id: str, score: float, notes: str = "") -> bool:
        """Store a human satisfaction rating in metadata for a run record."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT metadata FROM si_run_records WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row:
                return False
            meta = json.loads(row[0] or "{}")
            meta["human_score"] = score
            meta["human_notes"] = notes
            conn.execute(
                "UPDATE si_run_records SET metadata = ? WHERE run_id = ?",
                (json.dumps(meta), run_id),
            )
            conn.commit()
        return True
