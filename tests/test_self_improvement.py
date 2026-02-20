"""
Tests for the self-improvement module.

Covers:
- StepResultAdapter and CapabilityMapper (adapters.py)
- Vendor classes (smoke tests)
- PromptVersionStore CRUD (improvement_loop.py)
- RunRecorder.record_run() (run_recorder.py)
- PromptEvolver.propose_patch() heuristic path (prompt_evolver.py)
- ImprovementLoop orchestration (improvement_loop.py)
- CLI feedback commands (agenticom/cli.py)
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# =========================================================================== #
# Helpers / fixtures                                                            #
# =========================================================================== #


def _make_step_result(
    success=True, retries=0, step_id="plan", agent_role_value="planner"
):
    """Build a minimal StepResult-like object (avoids heavy orchestration imports)."""
    step = MagicMock()
    step.id = step_id
    step.expects = "STATUS: done"
    step.agent_role.value = agent_role_value

    agent_result = MagicMock()
    agent_result.output = "Some output text"
    agent_result.success = success
    agent_result.duration_ms = 500.0
    agent_result.tokens_used = 100
    agent_result.artifacts = []
    agent_result.error = None if success else "failure"

    sr = MagicMock()
    sr.step = step
    sr.agent_result = agent_result
    sr.retries = retries
    sr.status.value = "completed" if success else "failed"
    return sr


def _make_team_result(steps=None, success=True):
    """Build a minimal TeamResult-like object."""
    tr = MagicMock()
    tr.team_id = str(uuid.uuid4())
    tr.workflow_id = "feature-dev"
    tr.task = "Add login button"
    tr.success = success
    tr.steps = steps or [_make_step_result()]
    tr.started_at = datetime.utcnow()
    tr.completed_at = datetime.utcnow()
    tr.metadata = {}
    return tr


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test_si.db"


# =========================================================================== #
# Adapters                                                                     #
# =========================================================================== #


class TestStepResultAdapter:
    def test_to_smarc_input_keys(self):
        from orchestration.self_improvement.adapters import StepResultAdapter

        sr = _make_step_result()
        smarc_input = StepResultAdapter.to_smarc_input(sr)

        assert "output" in smarc_input
        assert "next_step" in smarc_input
        assert "recommendation" in smarc_input
        assert "artifacts" in smarc_input
        assert smarc_input["step_id"] == "plan"

    def test_to_performance_data_ranges(self):
        from orchestration.self_improvement.adapters import StepResultAdapter

        sr = _make_step_result(retries=2)
        perf = StepResultAdapter.to_performance_data(sr, smarc_score=0.6)

        assert 0.0 <= perf["accuracy"] <= 1.0
        assert 0.0 <= perf["efficiency"] <= 1.0
        assert 0.0 <= perf["adaptability"] <= 1.0
        assert perf["accuracy"] == 0.6
        assert perf["efficiency"] == pytest.approx(0.6)  # 1 - 2*0.2

    def test_to_performance_data_failed_step(self):
        from orchestration.self_improvement.adapters import StepResultAdapter

        sr = _make_step_result(success=False)
        perf = StepResultAdapter.to_performance_data(sr, smarc_score=0.0)
        assert perf["adaptability"] == pytest.approx(0.3)


class TestCapabilityMapper:
    def test_smarc_to_capabilities_passed(self):
        from orchestration.self_improvement.adapters import CapabilityMapper

        smarc = {"specific": True, "measurable": True, "actionable": True}
        caps = CapabilityMapper.smarc_to_capabilities("planner", smarc)

        assert "planner_output_specificity" in caps
        assert caps["planner_output_specificity"]["proficiency"] == pytest.approx(0.8)

    def test_smarc_to_capabilities_failed(self):
        from orchestration.self_improvement.adapters import CapabilityMapper

        smarc = {"specific": False, "measurable": False}
        caps = CapabilityMapper.smarc_to_capabilities("developer", smarc)

        assert caps["developer_output_specificity"]["proficiency"] == pytest.approx(0.1)

    def test_smarc_score(self):
        from orchestration.self_improvement.adapters import CapabilityMapper

        assert CapabilityMapper.smarc_score({}) == 0.0
        assert CapabilityMapper.smarc_score({"a": True, "b": False}) == pytest.approx(
            0.5
        )
        assert CapabilityMapper.smarc_score({"a": True, "b": True}) == pytest.approx(
            1.0
        )


# =========================================================================== #
# Vendor smoke tests                                                            #
# =========================================================================== #


class TestVendorSmoke:
    def test_results_verification_framework(self):
        from orchestration.self_improvement.vendor.results_verification import (
            ResultsVerificationFramework,
        )

        verifier = ResultsVerificationFramework()
        result = verifier.verify_results(
            {
                "output": "some text",
                "next_step": "step2",
                "recommendation": "do X",
                "artifacts": [],
                "score": 0.9,
            }
        )
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "specific",
            "measurable",
            "actionable",
            "reusable",
            "compoundable",
        }
        # All values are bool
        assert all(isinstance(v, bool) for v in result.values())

    def test_multi_agent_performance_optimizer(self):
        from orchestration.self_improvement.vendor.multi_agent_performance import (
            MultiAgentPerformanceOptimizer,
        )

        opt = MultiAgentPerformanceOptimizer(quality_threshold=0.85)
        agent_id = opt.register_agent({"role": "planner"})
        opt.update_agent_performance(
            agent_id, {"accuracy": 0.9, "efficiency": 0.8, "adaptability": 0.7}
        )
        assert opt.agents[agent_id]["performance_score"] > 0

    def test_recursive_self_improvement_protocol(self):
        from orchestration.self_improvement.vendor.recursive_self_improvement import (
            RecursiveSelfImprovementProtocol,
        )

        proto = RecursiveSelfImprovementProtocol()
        proto.update_capability_map(
            {"test_cap": {"proficiency": 0.4, "source": "test"}}
        )
        gaps = proto._identify_capability_gaps()
        assert "low_performance_areas" in gaps
        assert "test_cap" in gaps["low_performance_areas"]

    def test_anti_idling_system(self):
        from orchestration.self_improvement.vendor.anti_idling_system import (
            AntiIdlingSystem,
        )

        ais = AntiIdlingSystem(idle_threshold=0.9)
        ais.log_activity({"type": "coding", "is_productive": True, "duration": 3600})
        rate = ais.calculate_idle_rate()
        assert 0.0 <= rate <= 1.0


# =========================================================================== #
# PromptVersionStore                                                            #
# =========================================================================== #


class TestPromptVersionStore:
    def test_create_and_get_initial_version(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import PromptVersionStore

        store = PromptVersionStore(tmp_db)
        v = store.create_initial_version(
            "feature-dev", "planner", "planner", "Be precise."
        )

        assert v.version_number == 1
        assert v.is_active is True
        assert v.persona_text == "Be precise."
        assert v.previous_version_id is None

        got = store.get_active_version("feature-dev", "planner")
        assert got is not None
        assert got.id == v.id

    def test_apply_patch_creates_new_version(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import (
            PromptPatch,
            PromptVersionStore,
        )

        store = PromptVersionStore(tmp_db)
        v1 = store.create_initial_version(
            "feature-dev", "planner", "planner", "Original."
        )

        patch = PromptPatch(
            id=str(uuid.uuid4()),
            workflow_id="feature-dev",
            agent_id="planner",
            agent_role="planner",
            capability_gaps=["output_specificity"],
            base_prompt_version_id=v1.id,
            proposed_persona_text="Original.\n\nCRITICAL: Be specific.",
            justification="Heuristic patch.",
            generated_by="heuristic",
            status="pending",
            confidence=0.6,
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
            created_at=datetime.utcnow().isoformat(),
        )
        store.save_patch(patch)
        v2 = store.apply_patch(patch)

        assert v2.version_number == 2
        assert "CRITICAL" in v2.persona_text
        assert v2.previous_version_id == v1.id

        # v1 should be deactivated
        active = store.get_active_version("feature-dev", "planner")
        assert active.id == v2.id

    def test_rollback(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import (
            PromptPatch,
            PromptVersionStore,
        )

        store = PromptVersionStore(tmp_db)
        v1 = store.create_initial_version("feature-dev", "planner", "planner", "V1.")

        patch = PromptPatch(
            id=str(uuid.uuid4()),
            workflow_id="feature-dev",
            agent_id="planner",
            agent_role="planner",
            capability_gaps=[],
            base_prompt_version_id=v1.id,
            proposed_persona_text="V2.",
            justification="test",
            generated_by="heuristic",
            status="pending",
            confidence=0.7,
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
            created_at=datetime.utcnow().isoformat(),
        )
        store.save_patch(patch)
        store.apply_patch(patch)

        restored = store.rollback("feature-dev", "planner")
        assert restored is not None
        assert restored.persona_text == "V1."
        assert restored.is_active is True

    def test_rollback_at_initial_returns_none(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import PromptVersionStore

        store = PromptVersionStore(tmp_db)
        store.create_initial_version("feature-dev", "planner", "planner", "V1.")
        result = store.rollback("feature-dev", "planner")
        assert result is None

    def test_patch_approve_reject(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import (
            PromptPatch,
            PromptVersionStore,
        )

        store = PromptVersionStore(tmp_db)
        v1 = store.create_initial_version("w", "a", "a", "p")

        patch = PromptPatch(
            id=str(uuid.uuid4()),
            workflow_id="w",
            agent_id="a",
            agent_role="a",
            capability_gaps=[],
            base_prompt_version_id=v1.id,
            proposed_persona_text="new",
            justification="j",
            generated_by="heuristic",
            status="pending",
            confidence=0.5,
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
            created_at=datetime.utcnow().isoformat(),
        )
        store.save_patch(patch)

        assert store.approve_patch(patch.id)
        refetched = store.get_patch(patch.id)
        assert refetched.status == "approved"

        # Can't reject after approval
        rejected = store.reject_patch(patch.id, "reason")
        assert not rejected

    def test_get_persona_for_run_returns_active(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import PromptVersionStore

        store = PromptVersionStore(tmp_db)
        v = store.create_initial_version("wf", "dev", "developer", "Dev persona.")
        persona, vid = store.get_persona_for_run("wf", "dev", run_id="run1")
        assert persona == "Dev persona."
        assert vid == v.id

    def test_list_patches_filter(self, tmp_db):
        from orchestration.self_improvement.improvement_loop import (
            PromptPatch,
            PromptVersionStore,
        )

        store = PromptVersionStore(tmp_db)
        v = store.create_initial_version("wf", "ag", "ag", "p")
        for i in range(3):
            p = PromptPatch(
                id=str(uuid.uuid4()),
                workflow_id="wf",
                agent_id="ag",
                agent_role="ag",
                capability_gaps=[],
                base_prompt_version_id=v.id,
                proposed_persona_text="text",
                justification="j",
                generated_by="heuristic",
                status="pending",
                confidence=0.5,
                approved_by=None,
                approved_at=None,
                rejection_reason=None,
                created_at=datetime.utcnow().isoformat(),
            )
            store.save_patch(p)

        all_patches = store.list_patches("wf")
        assert len(all_patches) == 3
        pending = store.list_patches("wf", status="pending")
        assert len(pending) == 3
        applied = store.list_patches("wf", status="applied")
        assert len(applied) == 0


# =========================================================================== #
# RunRecorder                                                                   #
# =========================================================================== #


class TestRunRecorder:
    def _make_recorder(self, tmp_db, **kwargs):
        from orchestration.self_improvement.run_recorder import RunRecorder
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

        return RunRecorder(
            db_path=tmp_db,
            verifier=ResultsVerificationFramework(),
            performance=MultiAgentPerformanceOptimizer(),
            improvement_protocol=RecursiveSelfImprovementProtocol(),
            anti_idling=AntiIdlingSystem(),
            **kwargs,
        )

    async def test_record_run_persists_record(self, tmp_db):
        recorder = self._make_recorder(tmp_db)
        tr = _make_team_result()
        record = await recorder.record_run(tr, "feature-dev")

        assert record.workflow_id == "feature-dev"
        assert record.task_description == "Add login button"
        assert isinstance(record.step_scores, dict)
        assert isinstance(record.agent_scores, dict)

    async def test_record_run_increments_run_count(self, tmp_db):
        recorder = self._make_recorder(tmp_db)
        assert recorder._run_count == 0

        for _ in range(3):
            await recorder.record_run(_make_team_result(), "wf")

        assert recorder._run_count == 3

    async def test_record_run_triggers_pattern_on_n(self, tmp_db):
        triggered = []

        async def mock_trigger(wf_id):
            triggered.append(wf_id)

        recorder = self._make_recorder(
            tmp_db, pattern_trigger_n=2, on_pattern_trigger=mock_trigger
        )
        await recorder.record_run(_make_team_result(), "wf")
        await recorder.record_run(_make_team_result(), "wf")

        # Allow scheduled tasks to run
        await asyncio.sleep(0)
        assert "wf" in triggered

    async def test_get_recent_records(self, tmp_db):
        recorder = self._make_recorder(tmp_db)
        for _ in range(5):
            await recorder.record_run(_make_team_result(), "wf")

        records = recorder.get_recent_records("wf", limit=3)
        assert len(records) == 3

    async def test_rate_run(self, tmp_db):
        recorder = self._make_recorder(tmp_db)
        tr = _make_team_result()
        record = await recorder.record_run(tr, "wf")

        ok = recorder.rate_run(record.run_id, 0.9, "excellent")
        assert ok

        # Non-existent run returns False
        assert not recorder.rate_run("nonexistent", 0.5)

    async def test_failed_step_agent_score_below_success(self, tmp_db):
        """A failed step (adaptability=0.3) should produce a lower agent composite
        score than a successful step (adaptability=1.0)."""
        # Successful run
        recorder_ok = self._make_recorder(tmp_db)
        ok_tr = _make_team_result(
            steps=[_make_step_result(success=True, retries=0)], success=True
        )
        ok_record = await recorder_ok.record_run(ok_tr, "wf")

        # Failed run — separate recorder so agent IDs are independent
        tmp_db2 = tmp_db.parent / "test_si2.db"
        recorder_fail = self._make_recorder(tmp_db2)
        fail_sr = _make_step_result(success=False, retries=3)
        fail_tr = _make_team_result(steps=[fail_sr], success=False)
        fail_record = await recorder_fail.record_run(fail_tr, "wf")

        ok_score = list(ok_record.agent_scores.values())[0]
        fail_score = list(fail_record.agent_scores.values())[0]
        assert fail_score < ok_score


# =========================================================================== #
# PromptEvolver                                                                 #
# =========================================================================== #


class TestPromptEvolver:
    def _make_evolver(self, llm_executor=None):
        from orchestration.self_improvement.prompt_evolver import PromptEvolver
        from orchestration.self_improvement.vendor.recursive_self_improvement import (
            RecursiveSelfImprovementProtocol,
        )

        return PromptEvolver(
            improvement_protocol=RecursiveSelfImprovementProtocol(),
            llm_executor=llm_executor,
        )

    def _make_version(self, persona="You are a planner."):
        from orchestration.self_improvement.improvement_loop import PromptVersion

        return PromptVersion(
            id=str(uuid.uuid4()),
            workflow_id="feature-dev",
            agent_id="planner",
            agent_role="planner",
            version_number=1,
            persona_text=persona,
            is_active=True,
            applied_patch_id=None,
            previous_version_id=None,
            ab_test_id=None,
            ab_variant=None,
            created_at=datetime.utcnow().isoformat(),
            deactivated_at=None,
        )

    async def test_heuristic_propose_specificity(self):
        evolver = self._make_evolver()
        version = self._make_version()
        gaps = [
            {"capability": "planner_output_specificity", "source": "low_performance"}
        ]

        patch = await evolver.propose_patch(
            workflow_id="feature-dev",
            agent_id="planner",
            agent_role="planner",
            current_version=version,
            capability_gaps=gaps,
        )

        assert patch.generated_by == "heuristic"
        assert "CRITICAL" in patch.proposed_persona_text
        assert patch.status == "pending"
        assert patch.confidence > 0.0

    async def test_heuristic_no_matching_rules(self):
        evolver = self._make_evolver()
        version = self._make_version()
        gaps = [{"capability": "unknown_capability", "source": "test"}]

        patch = await evolver.propose_patch(
            workflow_id="wf",
            agent_id="planner",
            agent_role="planner",
            current_version=version,
            capability_gaps=gaps,
        )

        # Falls through to "no matching rules" path
        assert patch.status == "pending"

    async def test_llm_path_success(self):
        """LLM path: executor returns valid JSON persona."""
        llm_response = json.dumps(
            {
                "proposed_persona": "You are an improved planner.",
                "justification": "Fixed specificity gap.",
                "confidence": 0.85,
            }
        )

        async def mock_llm(prompt, _ctx):
            return llm_response

        evolver = self._make_evolver(llm_executor=mock_llm)
        version = self._make_version()
        gaps = [{"capability": "planner_output_specificity", "source": "low"}]

        patch = await evolver.propose_patch(
            workflow_id="wf",
            agent_id="planner",
            agent_role="planner",
            current_version=version,
            capability_gaps=gaps,
        )

        assert patch.generated_by == "llm"
        assert "improved" in patch.proposed_persona_text
        assert patch.confidence == pytest.approx(0.85)

    async def test_llm_path_falls_back_to_heuristic(self):
        """LLM executor raises; should fall back to heuristic."""

        async def broken_llm(prompt, _ctx):
            raise RuntimeError("API down")

        evolver = self._make_evolver(llm_executor=broken_llm)
        version = self._make_version()
        gaps = [{"capability": "planner_output_specificity", "source": "low"}]

        patch = await evolver.propose_patch(
            workflow_id="wf",
            agent_id="planner",
            agent_role="planner",
            current_version=version,
            capability_gaps=gaps,
        )

        assert patch.generated_by == "heuristic"
        assert patch.status == "pending"

    async def test_empty_gaps_returns_unchanged_persona(self):
        evolver = self._make_evolver()
        original = "You are a planner."
        version = self._make_version(original)

        patch = await evolver.propose_patch(
            workflow_id="wf",
            agent_id="planner",
            agent_role="planner",
            current_version=version,
            capability_gaps=[],
        )

        assert patch.proposed_persona_text == original


# =========================================================================== #
# ImprovementLoop                                                               #
# =========================================================================== #


class TestImprovementLoop:
    def _make_loop(self, tmp_db, **kwargs):
        from orchestration.self_improvement.improvement_loop import ImprovementLoop

        return ImprovementLoop(db_path=tmp_db, **kwargs)

    def _make_mock_team(self, role_value="planner", persona="Test persona."):
        agent = MagicMock()
        agent.role.value = role_value
        agent.persona = persona

        team = MagicMock()
        team.agents = {MagicMock(): agent}
        return team, agent

    def test_attach_to_team_creates_initial_version(self, tmp_db):
        loop = self._make_loop(tmp_db)
        team, agent = self._make_mock_team()
        loop.attach_to_team(team, "feature-dev", self_improve=False)

        version = loop.version_store.get_active_version("feature-dev", "planner")
        assert version is not None
        assert version.persona_text == "Test persona."

    def test_attach_to_team_idempotent(self, tmp_db):
        """Attaching twice should not create duplicate versions."""
        loop = self._make_loop(tmp_db)
        team, _ = self._make_mock_team()
        loop.attach_to_team(team, "feature-dev")
        loop.attach_to_team(team, "feature-dev")

        from orchestration.self_improvement.improvement_loop import PromptVersionStore

        store = PromptVersionStore(tmp_db)
        # Only one active version
        assert store.get_active_version("feature-dev", "planner") is not None

    async def test_record_completed_run(self, tmp_db):
        loop = self._make_loop(tmp_db, pattern_trigger_n=999)
        team, _ = self._make_mock_team()
        loop.attach_to_team(team, "feature-dev")

        tr = _make_team_result()
        await loop.record_completed_run(tr, "feature-dev", self_improve=False)

        records = loop.run_recorder.get_recent_records("feature-dev")
        assert len(records) == 1

    def test_list_patches_empty(self, tmp_db):
        loop = self._make_loop(tmp_db)
        patches = loop.list_patches("feature-dev")
        assert patches == []

    def test_reject_nonexistent_patch(self, tmp_db):
        loop = self._make_loop(tmp_db)
        result = loop.reject_patch("doesnt-exist", "reason")
        assert "error" in result

    def test_approve_nonexistent_patch(self, tmp_db):
        loop = self._make_loop(tmp_db)
        result = loop.approve_patch("doesnt-exist")
        assert "error" in result

    def test_rollback_no_history(self, tmp_db):
        loop = self._make_loop(tmp_db)
        team, _ = self._make_mock_team()
        loop.attach_to_team(team, "wf")
        result = loop.rollback("wf", "planner")
        assert "error" in result

    def test_feedback_status(self, tmp_db):
        loop = self._make_loop(tmp_db)
        status = loop.feedback_status("feature-dev")
        assert "pending_patches" in status
        assert "applied_patches" in status

    async def test_on_pattern_trigger_creates_patches(self, tmp_db):
        loop = self._make_loop(tmp_db)
        team, agent = self._make_mock_team()
        loop.attach_to_team(team, "wf")

        # Populate capability map with a low-proficiency capability
        loop.improvement_protocol.update_capability_map(
            {"planner_output_specificity": {"proficiency": 0.1, "source": "test"}}
        )
        loop.run_recorder._run_count = 5

        await loop._on_pattern_trigger("wf")

        patches = loop.version_store.list_patches("wf")
        assert len(patches) >= 1

    async def test_auto_approve_applies_patch(self, tmp_db):
        loop = self._make_loop(tmp_db, auto_approve_patches=True)
        team, agent = self._make_mock_team()
        agent.update_persona = MagicMock()
        loop.attach_to_team(team, "wf")

        loop.improvement_protocol.update_capability_map(
            {"planner_output_specificity": {"proficiency": 0.1, "source": "test"}}
        )
        loop.run_recorder._run_count = 5

        await loop._on_pattern_trigger("wf")

        # With auto_approve, patch should be applied immediately
        applied = loop.version_store.list_patches("wf", status="applied")
        assert len(applied) >= 1


# =========================================================================== #
# AgentTeam integration (update_persona + attach_improvement_loop)             #
# =========================================================================== #


class TestAgentTeamIntegration:
    def test_update_persona_changes_persona(self):
        from orchestration.agents.base import AgentConfig, AgentRole, LLMAgent

        config = AgentConfig(role=AgentRole.PLANNER, name="P", persona="Old persona.")
        agent = LLMAgent(config)
        agent.update_persona("New persona.", "v2-id")

        assert agent.persona == "New persona."
        assert "active_prompt_version_id" in (agent.metadata or {})

    def test_update_persona_without_version_id(self):
        from orchestration.agents.base import AgentConfig, AgentRole, LLMAgent

        config = AgentConfig(role=AgentRole.PLANNER, name="P", persona="Old.")
        agent = LLMAgent(config)
        agent.update_persona("New.")  # no version_id
        assert agent.persona == "New."

    def test_attach_improvement_loop_stores_refs(self, tmp_db):
        from orchestration.agents.base import AgentConfig, AgentRole, LLMAgent
        from orchestration.agents.team import AgentTeam, TeamConfig
        from orchestration.self_improvement.improvement_loop import ImprovementLoop

        team = AgentTeam(TeamConfig(name="test"))
        agent = LLMAgent(AgentConfig(role=AgentRole.PLANNER, name="P", persona="p"))
        team.add_agent(agent)

        loop = ImprovementLoop(db_path=tmp_db, pattern_trigger_n=99)
        result = team.attach_improvement_loop(loop, "wf", self_improve=False)

        assert result is team  # fluent API
        assert team._improvement_loop is loop
        assert team._improvement_workflow_id == "wf"


# =========================================================================== #
# CLI feedback commands                                                         #
# =========================================================================== #


class TestFeedbackCLI:
    def _invoke(self, args, loop=None):
        from click.testing import CliRunner

        from agenticom.cli import cli

        runner = CliRunner()

        if loop is not None:
            with patch(
                "orchestration.self_improvement.get_improvement_loop",
                return_value=loop,
            ):
                return runner.invoke(cli, args, catch_exceptions=False)
        return runner.invoke(cli, args, catch_exceptions=False)

    def _make_loop_mock(self):
        """Build a MagicMock that satisfies ImprovementLoop's interface."""
        m = MagicMock()
        m.rate_run.return_value = True
        m.list_patches.return_value = []
        m.approve_patch.return_value = {
            "status": "applied",
            "version_number": 2,
            "new_version_id": "v2",
        }
        m.reject_patch.return_value = {"status": "rejected", "patch_id": "p1"}
        m.rollback.return_value = {"status": "rolled_back", "version_number": 1}
        m.feedback_status.return_value = {
            "pending_patches": 0,
            "applied_patches": 0,
            "patches": [],
        }
        return m

    def test_feedback_status(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "status"], loop=loop)
        assert result.exit_code == 0
        assert "Self-Improvement" in result.output

    def test_feedback_list_patches_empty(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "list-patches"], loop=loop)
        assert result.exit_code == 0
        assert "No patches" in result.output

    def test_feedback_approve_patch(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "approve-patch", "abc12345"], loop=loop)
        assert result.exit_code == 0
        assert "applied" in result.output.lower()

    def test_feedback_reject_patch(self):
        loop = self._make_loop_mock()
        result = self._invoke(
            ["feedback", "reject-patch", "abc12345", "Too broad"], loop=loop
        )
        assert result.exit_code == 0
        assert "rejected" in result.output.lower()

    def test_feedback_rollback(self):
        loop = self._make_loop_mock()
        result = self._invoke(
            ["feedback", "rollback", "feature-dev", "planner"], loop=loop
        )
        assert result.exit_code == 0
        assert "Rolled back" in result.output

    def test_feedback_rate_run_valid(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "rate-run", "run123", "0.85"], loop=loop)
        assert result.exit_code == 0
        assert "rated" in result.output

    def test_feedback_rate_run_invalid_score(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "rate-run", "run123", "1.5"], loop=loop)
        assert result.exit_code == 0
        assert "0.0" in result.output or "must be" in result.output.lower()

    def test_feedback_list_patches_json(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "list-patches", "--json"], loop=loop)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "patches" in data

    def test_feedback_status_json(self):
        loop = self._make_loop_mock()
        result = self._invoke(["feedback", "status", "--json"], loop=loop)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "pending_patches" in data


# =========================================================================== #
# feature-dev.yaml self_improve flag                                           #
# =========================================================================== #


class TestFeatureDevYaml:
    def test_yaml_has_self_improve_flag(self):
        import yaml

        yaml_path = (
            Path(__file__).parent.parent
            / "agenticom"
            / "bundled_workflows"
            / "feature-dev.yaml"
        )
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        assert data.get("metadata", {}).get("self_improve") is True


# =========================================================================== #
# SemanticSMARCVerifier                                                        #
# =========================================================================== #


class TestSemanticSMARCVerifier:
    """Tests for the LLM-based SMARC scorer (semantic_smarc.py)."""

    # ── imports / constants ──────────────────────────────────────────────────

    def _import(self):
        from orchestration.self_improvement.semantic_smarc import (
            PASS_THRESHOLD,
            SemanticSMARCVerifier,
            SMARCResult,
        )

        return SemanticSMARCVerifier, SMARCResult, PASS_THRESHOLD

    # ── SMARCResult unit tests ───────────────────────────────────────────────

    def test_smarc_result_passed_threshold(self):
        _, SMARCResult, PASS_THRESHOLD = self._import()
        result = SMARCResult(
            agent_role="planner",
            step_id="plan",
            scores={
                "specific": 0.8,
                "measurable": 0.3,
                "actionable": 0.9,
                "reusable": 0.6,
                "compoundable": 0.5,
            },
            reasoning=dict.fromkeys(
                ("specific", "measurable", "actionable", "reusable", "compoundable"),
                "ok",
            ),
            source="llm",
        )
        passed = result.passed
        assert passed["specific"] is True  # 0.8 >= 0.6
        assert passed["measurable"] is False  # 0.3 < 0.6
        assert passed["actionable"] is True  # 0.9 >= 0.6
        assert passed["reusable"] is True  # 0.6 >= 0.6
        assert passed["compoundable"] is False  # 0.5 < 0.6

    def test_smarc_result_composite(self):
        _, SMARCResult, _ = self._import()
        result = SMARCResult(
            agent_role="dev",
            step_id="develop",
            scores={
                "specific": 1.0,
                "measurable": 0.5,
                "actionable": 0.75,
                "reusable": 0.25,
                "compoundable": 0.5,
            },
            reasoning={},
            source="rule",
        )
        assert result.composite == pytest.approx(0.6, abs=1e-9)

    def test_smarc_result_composite_empty(self):
        _, SMARCResult, _ = self._import()
        result = SMARCResult(
            agent_role="dev", step_id="x", scores={}, reasoning={}, source="rule"
        )
        assert result.composite == 0.0

    def test_smarc_result_to_dict_keys(self):
        _, SMARCResult, _ = self._import()
        result = SMARCResult(
            agent_role="tester",
            step_id="test",
            scores={
                "specific": 0.7,
                "measurable": 0.8,
                "actionable": 0.9,
                "reusable": 0.6,
                "compoundable": 0.5,
            },
            reasoning={"specific": "x" * 300},  # should be truncated to 200
            source="llm",
        )
        d = result.to_dict()
        assert set(d.keys()) >= {
            "agent_role",
            "step_id",
            "scores",
            "reasoning",
            "composite",
            "passed",
            "source",
            "evaluated_at",
        }
        assert len(d["reasoning"]["specific"]) <= 200
        assert d["source"] == "llm"

    def test_pass_threshold_value(self):
        _, _, PASS_THRESHOLD = self._import()
        assert PASS_THRESHOLD == pytest.approx(0.6)

    # ── Rule-based fallback ──────────────────────────────────────────────────

    async def test_rule_fallback_when_no_llm(self):
        SemanticSMARCVerifier, SMARCResult, _ = self._import()
        verifier = SemanticSMARCVerifier(llm_executor=None)
        result = await verifier.verify(
            output="The plan includes 5 concrete steps with numbered sub-tasks " * 10,
            agent_role="planner",
            step_id="plan",
            expects="STATUS: done",
            smarc_input={
                "output": "x" * 250,
                "step_id": "plan",
                "success": True,
                "duration_ms": 300,
                "tokens_used": 80,
                "retries": 0,
                "artifacts": [],
                "next_step": "develop",
                "recommendation": "proceed",
            },
        )
        assert isinstance(result, SMARCResult)
        assert result.source == "rule"
        assert set(result.scores.keys()) == {
            "specific",
            "measurable",
            "actionable",
            "reusable",
            "compoundable",
        }
        for score in result.scores.values():
            assert 0.0 <= score <= 1.0

    async def test_rule_fallback_compoundable_requires_long_output(self):
        SemanticSMARCVerifier, _, _ = self._import()
        verifier = SemanticSMARCVerifier(llm_executor=None)

        # Short output → compoundable should be low
        short_result = await verifier.verify(
            output="short",
            agent_role="planner",
            step_id="plan",
            smarc_input={"output": "short", "artifacts": []},
        )
        # Long output with artifacts → compoundable should be higher
        long_result = await verifier.verify(
            output="x" * 250,
            agent_role="planner",
            step_id="plan",
            smarc_input={"output": "x" * 250, "artifacts": ["file.py"]},
        )
        assert long_result.scores["compoundable"] > short_result.scores["compoundable"]

    # ── LLM path ─────────────────────────────────────────────────────────────

    async def test_llm_path_success(self):
        SemanticSMARCVerifier, SMARCResult, _ = self._import()
        llm_response = json.dumps(
            {
                "specific": 0.85,
                "measurable": 0.70,
                "actionable": 0.90,
                "reusable": 0.65,
                "compoundable": 0.95,
                "reasoning": {
                    "specific": "Concrete steps provided.",
                    "measurable": "Some metrics present.",
                    "actionable": "Clear next step specified.",
                    "reusable": "Template-like structure.",
                    "compoundable": "Creates flywheel across all downstream steps.",
                },
            }
        )

        async def fake_llm(prompt, _ctx=None):
            return llm_response

        verifier = SemanticSMARCVerifier(llm_executor=fake_llm)
        result = await verifier.verify(
            output="Add OAuth2 endpoint: 1) install PyJWT 2) add /token route",
            agent_role="planner",
            step_id="plan",
            expects="STATUS: done",
        )
        assert result.source == "llm"
        assert result.scores["specific"] == pytest.approx(0.85)
        assert result.scores["compoundable"] == pytest.approx(0.95)
        assert result.passed["compoundable"] is True  # 0.95 >= 0.6
        assert "flywheel" in result.reasoning["compoundable"].lower()

    async def test_llm_path_clamps_scores_to_0_1(self):
        SemanticSMARCVerifier, _, _ = self._import()
        # LLM returns out-of-range values — must be clamped
        llm_response = json.dumps(
            {
                "specific": 1.5,
                "measurable": -0.2,
                "actionable": 0.7,
                "reusable": 2.0,
                "compoundable": 0.8,
                "reasoning": dict.fromkeys(
                    (
                        "specific",
                        "measurable",
                        "actionable",
                        "reusable",
                        "compoundable",
                    ),
                    "x",
                ),
            }
        )

        async def fake_llm(prompt, _ctx=None):
            return llm_response

        verifier = SemanticSMARCVerifier(llm_executor=fake_llm)
        result = await verifier.verify(output="test", agent_role="dev", step_id="s")
        assert result.scores["specific"] == pytest.approx(1.0)
        assert result.scores["measurable"] == pytest.approx(0.0)
        assert result.scores["reusable"] == pytest.approx(1.0)

    async def test_llm_path_falls_back_on_bad_json(self):
        SemanticSMARCVerifier, SMARCResult, _ = self._import()

        async def bad_llm(prompt, _ctx=None):
            return "This is not JSON at all!"

        verifier = SemanticSMARCVerifier(llm_executor=bad_llm)
        result = await verifier.verify(
            output="test output",
            agent_role="planner",
            step_id="plan",
            smarc_input={"output": "test", "next_step": "x", "recommendation": "y"},
        )
        # Should fall back to rule-based
        assert result.source == "rule"
        assert set(result.scores.keys()) == {
            "specific",
            "measurable",
            "actionable",
            "reusable",
            "compoundable",
        }

    async def test_llm_path_handles_markdown_fences(self):
        """LLM sometimes wraps JSON in ```json ... ``` fences."""
        SemanticSMARCVerifier, _, _ = self._import()
        inner = json.dumps(
            {
                "specific": 0.7,
                "measurable": 0.6,
                "actionable": 0.8,
                "reusable": 0.5,
                "compoundable": 0.9,
                "reasoning": dict.fromkeys(
                    (
                        "specific",
                        "measurable",
                        "actionable",
                        "reusable",
                        "compoundable",
                    ),
                    "ok",
                ),
            }
        )
        fenced = f"```json\n{inner}\n```"

        async def fence_llm(prompt, _ctx=None):
            return fenced

        verifier = SemanticSMARCVerifier(llm_executor=fence_llm)
        result = await verifier.verify(output="hello", agent_role="dev", step_id="s")
        assert result.source == "llm"
        assert result.scores["compoundable"] == pytest.approx(0.9)

    async def test_llm_path_handles_sync_executor(self):
        """Sync (non-async) LLM executor must also work."""
        SemanticSMARCVerifier, _, _ = self._import()
        llm_response = json.dumps(
            {
                "specific": 0.6,
                "measurable": 0.6,
                "actionable": 0.6,
                "reusable": 0.6,
                "compoundable": 0.6,
                "reasoning": dict.fromkeys(
                    (
                        "specific",
                        "measurable",
                        "actionable",
                        "reusable",
                        "compoundable",
                    ),
                    "ok",
                ),
            }
        )

        def sync_llm(prompt, _ctx=None):  # NOT async
            return llm_response

        verifier = SemanticSMARCVerifier(llm_executor=sync_llm)
        result = await verifier.verify(output="hello", agent_role="dev", step_id="s")
        assert result.source == "llm"
        assert result.composite == pytest.approx(0.6)

    # ── History / aggregation ────────────────────────────────────────────────

    async def test_history_stored_and_queried(self):
        SemanticSMARCVerifier, _, _ = self._import()

        async def fake_llm(prompt, _ctx=None):
            return json.dumps(
                {
                    "specific": 0.8,
                    "measurable": 0.7,
                    "actionable": 0.9,
                    "reusable": 0.6,
                    "compoundable": 0.5,
                    "reasoning": dict.fromkeys(
                        (
                            "specific",
                            "measurable",
                            "actionable",
                            "reusable",
                            "compoundable",
                        ),
                        "ok",
                    ),
                }
            )

        verifier = SemanticSMARCVerifier(llm_executor=fake_llm)
        await verifier.verify(output="a", agent_role="planner", step_id="plan")
        await verifier.verify(output="b", agent_role="planner", step_id="plan2")
        await verifier.verify(output="c", agent_role="developer", step_id="dev")

        planner_history = verifier.history_for_agent("planner")
        assert len(planner_history) == 2
        dev_history = verifier.history_for_agent("developer")
        assert len(dev_history) == 1

    async def test_avg_scores_across_history(self):
        SemanticSMARCVerifier, _, _ = self._import()

        call_count = 0

        async def varying_llm(prompt, _ctx=None):
            nonlocal call_count
            call_count += 1
            score = 0.6 if call_count == 1 else 0.8
            return json.dumps(
                {
                    "specific": score,
                    "measurable": score,
                    "actionable": score,
                    "reusable": score,
                    "compoundable": score,
                    "reasoning": dict.fromkeys(
                        (
                            "specific",
                            "measurable",
                            "actionable",
                            "reusable",
                            "compoundable",
                        ),
                        "ok",
                    ),
                }
            )

        verifier = SemanticSMARCVerifier(llm_executor=varying_llm)
        await verifier.verify(output="a", agent_role="planner", step_id="s1")
        await verifier.verify(output="b", agent_role="planner", step_id="s2")

        avgs = verifier.avg_scores(agent_role="planner")
        assert avgs["specific"] == pytest.approx(0.7)  # (0.6 + 0.8) / 2

    def test_avg_scores_empty_history(self):
        SemanticSMARCVerifier, _, _ = self._import()
        verifier = SemanticSMARCVerifier(llm_executor=None)
        assert verifier.avg_scores() == {}
        assert verifier.avg_scores(agent_role="planner") == {}

    async def test_history_capped_at_100(self):
        """History ring-buffer must not grow beyond 100 entries."""
        SemanticSMARCVerifier, _, _ = self._import()

        async def fast_llm(prompt, _ctx=None):
            return json.dumps(
                {
                    "specific": 0.5,
                    "measurable": 0.5,
                    "actionable": 0.5,
                    "reusable": 0.5,
                    "compoundable": 0.5,
                    "reasoning": dict.fromkeys(
                        (
                            "specific",
                            "measurable",
                            "actionable",
                            "reusable",
                            "compoundable",
                        ),
                        "",
                    ),
                }
            )

        verifier = SemanticSMARCVerifier(llm_executor=fast_llm)
        for _i in range(110):
            await verifier.verify(
                output=f"out{_i}", agent_role="planner", step_id=f"s{_i}"
            )

        assert len(verifier._history) == 100

    # ── RunRecorder integration ───────────────────────────────────────────────

    async def test_run_recorder_uses_semantic_verifier(self, tmp_db):
        """RunRecorder should call semantic verifier and store smarc_detail."""
        import sqlite3

        from orchestration.self_improvement.run_recorder import RunRecorder
        from orchestration.self_improvement.semantic_smarc import SemanticSMARCVerifier
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

        async def fake_llm(prompt, _ctx=None):
            return json.dumps(
                {
                    "specific": 0.75,
                    "measurable": 0.80,
                    "actionable": 0.85,
                    "reusable": 0.70,
                    "compoundable": 0.90,
                    "reasoning": dict.fromkeys(
                        (
                            "specific",
                            "measurable",
                            "actionable",
                            "reusable",
                            "compoundable",
                        ),
                        "semantic",
                    ),
                }
            )

        semantic_verifier = SemanticSMARCVerifier(llm_executor=fake_llm)
        recorder = RunRecorder(
            db_path=tmp_db,
            verifier=ResultsVerificationFramework(),
            performance=MultiAgentPerformanceOptimizer(),
            improvement_protocol=RecursiveSelfImprovementProtocol(
                ethical_constraints={
                    "do_no_harm": True,
                    "human_alignment": True,
                    "transparency": True,
                    "reversibility": True,
                }
            ),
            anti_idling=AntiIdlingSystem(),
            semantic_verifier=semantic_verifier,
        )

        team_result = _make_team_result()
        record = await recorder.record_run(team_result, "feature-dev")

        # smarc_detail should be populated (not empty)
        assert record.smarc_detail  # non-empty dict
        step_id = list(record.smarc_detail.keys())[0]
        detail = record.smarc_detail[step_id]
        assert detail["source"] == "llm"
        assert detail["scores"]["compoundable"] == pytest.approx(0.90)

        # Also verify it was persisted to DB
        with sqlite3.connect(tmp_db) as conn:
            row = conn.execute(
                "SELECT smarc_detail FROM si_run_records WHERE id = ?", (record.id,)
            ).fetchone()
        assert row is not None
        stored = json.loads(row[0])
        assert stored  # non-empty

    # ── CapabilityMapper float score support ──────────────────────────────────

    def test_capability_mapper_float_scores(self):
        from orchestration.self_improvement.adapters import CapabilityMapper

        # Float scores should be stored as direct proficiency
        float_smarc = {"specific": 0.82, "measurable": 0.71}
        caps = CapabilityMapper.smarc_to_capabilities("planner", float_smarc)
        assert caps["planner_output_specificity"]["proficiency"] == pytest.approx(
            0.82, abs=0.001
        )
        assert caps["planner_output_measurability"]["proficiency"] == pytest.approx(
            0.71, abs=0.001
        )
        assert "semantic score" in caps["planner_output_specificity"]["evidence"]

    def test_capability_mapper_smarc_score_with_floats(self):
        from orchestration.self_improvement.adapters import CapabilityMapper

        assert CapabilityMapper.smarc_score({"a": 0.6, "b": 0.8}) == pytest.approx(0.7)
        assert CapabilityMapper.smarc_score({"a": True, "b": False}) == pytest.approx(
            0.5
        )
        assert CapabilityMapper.smarc_score({}) == 0.0
