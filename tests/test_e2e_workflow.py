"""
End-to-end workflow execution tests.

Tests the full AgentTeam.run() lifecycle using MockAgent (no LLM API required).
Covers:
- Single-step and multi-step workflow execution
- Template substitution: {{task}}, {{step_outputs.X}}
- Retry on failure (success on Nth attempt)
- on_fail=abort: subsequent steps not executed
- on_fail=skip: subsequent steps continue
- WorkflowParser YAML → AgentTeam conversion (including bundled workflows)
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from orchestration.agents.base import AgentConfig, AgentRole, MockAgent
from orchestration.agents.team import (
    AgentTeam,
    StepStatus,
    TeamConfig,
    WorkflowStep,
)
from orchestration.workflows.parser import WorkflowParser

BUNDLED_WORKFLOWS_DIR = Path(__file__).parent.parent / "agenticom" / "bundled_workflows"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_agent(
    role: AgentRole, output: str, *, should_fail: bool = False
) -> MockAgent:
    config = AgentConfig(role=role, name=f"Mock-{role.value}")
    return MockAgent(config, mock_output=output, should_fail=should_fail)


def make_step(
    step_id: str,
    role: AgentRole,
    template: str,
    *,
    on_fail: str = "retry",
    max_retries: int = 0,
    artifacts_required: bool = False,
) -> WorkflowStep:
    return WorkflowStep(
        id=step_id,
        name=step_id,
        agent_role=role,
        input_template=template,
        on_fail=on_fail,
        max_retries=max_retries,
        artifacts_required=artifacts_required,
    )


def make_team(*agents, steps=None):
    """Build an AgentTeam with given agents and steps. Patches ArtifactManager."""
    config = TeamConfig(name="test-team")
    team = AgentTeam(config)
    for agent in agents:
        team.add_agent(agent)
    for step in steps or []:
        team.add_step(step)
    return team


# ---------------------------------------------------------------------------
# Journey 1: Single-step workflow
# ---------------------------------------------------------------------------


class TestSingleStepWorkflow:
    async def test_single_step_success(self):
        agent = make_mock_agent(AgentRole.PLANNER, "the plan")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("build a login page")

        assert result.success is True
        assert result.final_output == "the plan"
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.COMPLETED

    async def test_single_step_result_has_correct_metadata(self):
        agent = make_mock_agent(AgentRole.PLANNER, "output")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("my task")

        assert result.task == "my task"
        assert result.team_id == team.id
        assert result.workflow_id  # non-empty UUID string
        assert result.completed_at is not None


# ---------------------------------------------------------------------------
# Journey 2: Template substitution chain
# ---------------------------------------------------------------------------


class TestTemplateSubstitution:
    async def test_two_step_chain_passes_output_forward(self):
        planner = make_mock_agent(AgentRole.PLANNER, "plan output")
        developer = make_mock_agent(AgentRole.DEVELOPER, "code output")
        step1 = make_step("plan", AgentRole.PLANNER, "{{task}}")
        step2 = make_step(
            "implement", AgentRole.DEVELOPER, "Implement: {{step_outputs.plan}}"
        )
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(planner, developer, steps=[step1, step2])
            result = await team.run("build something")

        assert result.success is True
        assert result.final_output == "code output"
        assert result.steps[0].status == StepStatus.COMPLETED
        assert result.steps[1].status == StepStatus.COMPLETED

    def test_preprocess_template_converts_step_outputs(self):
        config = TeamConfig(name="t")
        team = AgentTeam(config)
        result = team._preprocess_template("Based on: {{step_outputs.plan}}")
        assert result == "Based on: {plan}"

    def test_preprocess_template_converts_task_var(self):
        config = TeamConfig(name="t")
        team = AgentTeam(config)
        result = team._preprocess_template("Do: {{task}}")
        assert result == "Do: {task}"

    def test_preprocess_template_converts_arbitrary_vars(self):
        config = TeamConfig(name="t")
        team = AgentTeam(config)
        result = team._preprocess_template("{{foo}} and {{bar}}")
        assert result == "{foo} and {bar}"

    def test_preprocess_template_handles_hyphenated_step_ids(self):
        """step_outputs.step-id with hyphen should be preserved."""
        config = TeamConfig(name="t")
        team = AgentTeam(config)
        # The regex converts {{step_outputs.X}} → {X} regardless of X content
        result = team._preprocess_template("{{step_outputs.my-step}}")
        assert result == "{my-step}"

    async def test_three_step_chain(self):
        planner = make_mock_agent(AgentRole.PLANNER, "plan")
        developer = make_mock_agent(AgentRole.DEVELOPER, "code")
        reviewer = make_mock_agent(AgentRole.REVIEWER, "APPROVED")
        step1 = make_step("plan", AgentRole.PLANNER, "{{task}}")
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{step_outputs.plan}}")
        step3 = make_step(
            "review",
            AgentRole.REVIEWER,
            "{{step_outputs.plan}} + {{step_outputs.implement}}",
        )
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(planner, developer, reviewer, steps=[step1, step2, step3])
            result = await team.run("task")

        assert result.success is True
        assert result.final_output == "APPROVED"
        assert len(result.steps) == 3


# ---------------------------------------------------------------------------
# Journey 3: Retry on failure
# ---------------------------------------------------------------------------


class CallCountingAgent(MockAgent):
    """MockAgent that fails the first N calls, succeeds on N+1."""

    def __init__(self, config, fail_n_times=0, success_output="success"):
        super().__init__(config, mock_output=success_output)
        self.fail_n_times = fail_n_times
        self.call_count = 0

    async def _execute_task(self, task, context):
        self.call_count += 1
        if self.call_count <= self.fail_n_times:
            raise Exception(f"Transient failure #{self.call_count}")
        return self.mock_output


class TestRetryBehavior:
    async def test_succeeds_on_second_attempt(self):
        config = AgentConfig(role=AgentRole.PLANNER, name="Retry Agent")
        agent = CallCountingAgent(config, fail_n_times=1, success_output="recovered")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}", max_retries=2)
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("task")

        assert result.success is True
        assert result.final_output == "recovered"
        assert agent.call_count == 2
        assert result.steps[0].retries == 1

    async def test_fails_after_max_retries_exhausted(self):
        config = AgentConfig(role=AgentRole.PLANNER, name="Always Fail")
        agent = CallCountingAgent(config, fail_n_times=99, success_output="never")
        # max_retries=2: up to 3 attempts total (retries 0, 1, 2)
        step = make_step("plan", AgentRole.PLANNER, "{{task}}", max_retries=2)
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("task")

        assert result.success is False
        assert result.steps[0].status == StepStatus.FAILED

    async def test_retries_before_failure_are_counted(self):
        config = AgentConfig(role=AgentRole.PLANNER, name="Counter")
        agent = CallCountingAgent(config, fail_n_times=2, success_output="ok")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}", max_retries=3)
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("task")

        assert result.success is True
        # 2 failures + 1 success = 3 calls total
        assert agent.call_count == 3


# ---------------------------------------------------------------------------
# Journey 4: on_fail=abort stops the pipeline
# ---------------------------------------------------------------------------


class TestOnFailAbort:
    async def test_abort_stops_subsequent_steps(self):
        failing = make_mock_agent(AgentRole.PLANNER, "never", should_fail=True)
        second = make_mock_agent(AgentRole.DEVELOPER, "should not run")
        step1 = make_step(
            "plan", AgentRole.PLANNER, "{{task}}", on_fail="abort", max_retries=0
        )
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(failing, second, steps=[step1, step2])
            result = await team.run("task")

        assert result.success is False
        # Only step1 ran — abort exits immediately
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.FAILED

    async def test_abort_result_has_error_message(self):
        agent = make_mock_agent(AgentRole.PLANNER, "never", should_fail=True)
        step = make_step(
            "plan", AgentRole.PLANNER, "{{task}}", on_fail="abort", max_retries=0
        )
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("task")

        assert result.error is not None
        assert len(result.error) > 0
        # Error message references the failing step
        assert "plan" in result.error


# ---------------------------------------------------------------------------
# Journey 5: on_fail=skip continues to next step
# ---------------------------------------------------------------------------


class TestOnFailSkip:
    async def test_skip_continues_to_next_step(self):
        failing = make_mock_agent(AgentRole.PLANNER, "never", should_fail=True)
        second = make_mock_agent(AgentRole.DEVELOPER, "second ran")
        step1 = make_step(
            "plan", AgentRole.PLANNER, "{{task}}", on_fail="skip", max_retries=0
        )
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(failing, second, steps=[step1, step2])
            result = await team.run("task")

        # Both steps in results, step1=FAILED, step2=COMPLETED
        assert len(result.steps) == 2
        assert result.steps[0].status == StepStatus.FAILED
        assert result.steps[1].status == StepStatus.COMPLETED

    async def test_skip_overall_success_is_false(self):
        failing = make_mock_agent(AgentRole.PLANNER, "never", should_fail=True)
        second = make_mock_agent(AgentRole.DEVELOPER, "ok")
        step1 = make_step(
            "plan", AgentRole.PLANNER, "{{task}}", on_fail="skip", max_retries=0
        )
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(failing, second, steps=[step1, step2])
            result = await team.run("task")

        # Failed step means overall success=False
        assert result.success is False

    async def test_skip_final_output_comes_from_last_completed_step(self):
        failing = make_mock_agent(AgentRole.PLANNER, "never", should_fail=True)
        second = make_mock_agent(AgentRole.DEVELOPER, "final output")
        step1 = make_step(
            "plan", AgentRole.PLANNER, "{{task}}", on_fail="skip", max_retries=0
        )
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(failing, second, steps=[step1, step2])
            result = await team.run("task")

        assert result.final_output == "final output"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    async def test_empty_workflow_returns_success(self):
        config = TeamConfig(name="empty")
        team = AgentTeam(config)
        result = await team.run("task")
        assert result.success is True
        assert result.final_output is None
        assert result.steps == []

    async def test_missing_agent_for_step_returns_failure(self):
        """AgentTeam.run() catches ValueError from missing agent and returns failure."""
        config = TeamConfig(name="bad")
        team = AgentTeam(config)
        step = make_step("plan", AgentRole.PLANNER, "{{task}}")
        team.add_step(step)
        # No agent added — run() should catch exception and return failure
        result = await team.run("task")
        assert result.success is False

    async def test_empty_task_string_works(self):
        agent = make_mock_agent(AgentRole.PLANNER, "output")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("")  # empty task string

        assert result.success is True

    async def test_stop_flag_halts_between_steps(self):
        """stop() mid-execution prevents subsequent steps from running."""
        planner = make_mock_agent(AgentRole.PLANNER, "plan")
        developer = make_mock_agent(AgentRole.DEVELOPER, "code")
        step1 = make_step("plan", AgentRole.PLANNER, "{{task}}")
        step2 = make_step("implement", AgentRole.DEVELOPER, "{{task}}")

        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(planner, developer, steps=[step1, step2])

            # Register an observer that stops after the first step completes
            async def stop_after_first(step_result):
                team.stop()

            team.on_step_complete(stop_after_first)
            result = await team.run("task")

        # Only step1 ran; stop() prevented step2
        assert len(result.steps) == 1
        assert result.steps[0].step.id == "plan"

    async def test_step_result_has_started_and_completed_timestamps(self):
        agent = make_mock_agent(AgentRole.PLANNER, "output")
        step = make_step("plan", AgentRole.PLANNER, "{{task}}")
        with patch("orchestration.agents.team.ArtifactManager") as MockAM:
            MockAM.return_value.extract_artifacts_from_text.return_value = []
            team = make_team(agent, steps=[step])
            result = await team.run("task")

        sr = result.steps[0]
        assert sr.started_at is not None
        assert sr.completed_at is not None


# ---------------------------------------------------------------------------
# WorkflowParser: YAML parsing and team construction
# ---------------------------------------------------------------------------


MINIMAL_YAML = """
id: test-workflow
name: Test Workflow
description: Minimal test
agents:
  - id: planner
    name: Planner
    role: planning
steps:
  - id: plan
    agent: planner
    input: "{{task}}"
    expects: "STATUS: done"
"""

MULTI_AGENT_YAML = """
id: multi-agent
name: Multi Agent
agents:
  - id: planner
    name: Planner
    role: planner
  - id: developer
    name: Developer
    role: developer
steps:
  - id: plan
    agent: planner
    input: "{{task}}"
  - id: implement
    agent: developer
    input: "{{step_outputs.plan}}"
"""


class TestWorkflowParser:
    def test_parse_minimal_yaml_produces_definition(self):
        parser = WorkflowParser()
        definition = parser.parse(MINIMAL_YAML)
        assert definition.id == "test-workflow"
        assert definition.name == "Test Workflow"
        assert len(definition.agents) == 1
        assert len(definition.steps) == 1

    def test_parse_step_fields_preserved(self):
        parser = WorkflowParser()
        definition = parser.parse(MINIMAL_YAML)
        step = definition.steps[0]
        assert step.id == "plan"
        assert step.agent == "planner"
        assert step.expects == "STATUS: done"

    def test_to_team_creates_correct_agent_count(self):
        parser = WorkflowParser()
        definition = parser.parse(MINIMAL_YAML)
        team = parser.to_team(definition)
        assert len(team.steps) == 1
        assert len(team.agents) == 1

    def test_to_team_multi_agent_creates_all_agents(self):
        parser = WorkflowParser()
        definition = parser.parse(MULTI_AGENT_YAML)
        team = parser.to_team(definition)
        assert len(team.steps) == 2
        assert len(team.agents) == 2

    def test_feature_dev_yaml_parses_cleanly(self):
        yaml_path = BUNDLED_WORKFLOWS_DIR / "feature-dev.yaml"
        if not yaml_path.exists():
            pytest.skip("Bundled workflow not found")
        parser = WorkflowParser()
        definition = parser.parse_file(yaml_path)
        assert definition.id == "feature-dev"
        assert len(definition.agents) == 5
        assert len(definition.steps) == 5

    def test_all_bundled_workflows_parse_without_error(self):
        """Every bundled YAML should parse to a valid WorkflowDefinition."""
        if not BUNDLED_WORKFLOWS_DIR.exists():
            pytest.skip("Bundled workflows directory not found")
        parser = WorkflowParser()
        yaml_files = list(BUNDLED_WORKFLOWS_DIR.glob("*.yaml"))
        assert len(yaml_files) >= 1
        for yaml_file in yaml_files:
            definition = parser.parse_file(yaml_file)
            assert definition.id, f"{yaml_file.name}: missing id field"
            assert len(definition.steps) > 0, f"{yaml_file.name}: no steps"

    def test_resolve_role_explicit_mapping(self):
        assert WorkflowParser.resolve_role("planner") == AgentRole.PLANNER
        assert WorkflowParser.resolve_role("developer") == AgentRole.DEVELOPER
        assert WorkflowParser.resolve_role("tester") == AgentRole.TESTER
        assert WorkflowParser.resolve_role("verifier") == AgentRole.VERIFIER
        assert WorkflowParser.resolve_role("reviewer") == AgentRole.REVIEWER

    def test_resolve_role_pattern_matching(self):
        assert WorkflowParser.resolve_role("custom-analyst") == AgentRole.ANALYST
        assert WorkflowParser.resolve_role("lead-engineer") == AgentRole.DEVELOPER

    def test_resolve_role_unknown_falls_back_to_custom(self):
        assert WorkflowParser.resolve_role("completely-unknown-xyz") == AgentRole.CUSTOM

    def test_resolve_role_case_insensitive(self):
        assert WorkflowParser.resolve_role("PLANNER") == AgentRole.PLANNER
        assert WorkflowParser.resolve_role("Developer") == AgentRole.DEVELOPER
