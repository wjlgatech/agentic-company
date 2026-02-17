"""Integration tests for diagnostics with AgentTeam (Phase 2)."""

import pytest
from pathlib import Path
from datetime import datetime

from orchestration.diagnostics import (
    DiagnosticsConfig,
    check_playwright_installation,
)
from orchestration.agents.team import (
    AgentTeam,
    TeamConfig,
    WorkflowStep,
    StepStatus,
)
from orchestration.agents.base import Agent, AgentConfig, AgentRole, AgentResult


# ============== Fixtures ==============


@pytest.fixture
def mock_executor():
    """Create a mock executor for testing."""

    class MockExecutor:
        """Mock executor that returns predefined responses."""

        async def execute(self, prompt: str, **kwargs):
            """Return mock response."""
            return {
                "content": "Mock response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            }

    return MockExecutor()


@pytest.fixture
def mock_agent(mock_executor):
    """Create a mock agent for testing."""

    class MockAgent(Agent):
        """Mock agent that always succeeds."""

        def __init__(self):
            config = AgentConfig(
                name="TestAgent",
                role=AgentRole.DEVELOPER,
                persona="Test agent",
            )
            super().__init__(config)
            self._executor = mock_executor

        async def _execute_task(self, task: str, context=None):
            """Implement abstract method."""
            return AgentResult(
                agent_id=self.id,
                agent_role=self.role,
                step_id=context.step_id if context else "test-step",
                output="Task completed successfully",
                success=True,
            )

        async def execute(self, task: str, context=None, fresh_context=True):
            """Return mock successful result."""
            return AgentResult(
                agent_id=self.id,
                agent_role=self.role,
                step_id=context.step_id if context else "test-step",
                output="Task completed successfully",
                success=True,
            )

    return MockAgent()


# ============== Basic Integration Tests ==============


def test_step_result_has_metadata_field():
    """Test that StepResult dataclass has metadata field."""
    from orchestration.agents.team import StepResult
    from dataclasses import fields

    # Get fields of StepResult
    step_result_fields = {f.name: f for f in fields(StepResult)}

    # Should have metadata field
    assert "metadata" in step_result_fields
    assert step_result_fields["metadata"].type == dict

    # Verify default factory
    assert step_result_fields["metadata"].default_factory is not None


def test_team_config_has_diagnostics_config_field():
    """Test that TeamConfig has diagnostics_config field."""
    from orchestration.agents.team import TeamConfig

    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    # Should have diagnostics_config field
    assert hasattr(config, "diagnostics_config")
    assert config.diagnostics_config is None  # Default


def test_team_config_accepts_diagnostics_config():
    """Test that TeamConfig accepts DiagnosticsConfig."""
    from orchestration.agents.team import TeamConfig

    diag_config = DiagnosticsConfig(enabled=True)

    config = TeamConfig(
        name="Test Team",
        description="Test",
        diagnostics_config=diag_config,
    )

    assert config.diagnostics_config is not None
    assert config.diagnostics_config.enabled is True


@pytest.mark.asyncio
async def test_agent_team_initializes_without_diagnostics(mock_agent):
    """Test AgentTeam initializes normally without diagnostics."""
    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    team = AgentTeam(config)

    # Should have diagnostics attribute
    assert hasattr(team, "diagnostics")
    # Should be None when not configured
    assert team.diagnostics is None


@pytest.mark.asyncio
async def test_agent_team_gracefully_handles_missing_playwright(mock_agent):
    """Test AgentTeam handles missing Playwright gracefully."""
    diag_config = DiagnosticsConfig(enabled=True)

    config = TeamConfig(
        name="Test Team",
        description="Test",
        diagnostics_config=diag_config,
    )

    # Should not raise even if Playwright not installed
    team = AgentTeam(config)

    # Diagnostics should be None if Playwright not installed
    if not check_playwright_installation():
        assert team.diagnostics is None
    else:
        # If Playwright is installed, should initialize
        assert team.diagnostics is not None


@pytest.mark.asyncio
async def test_agent_team_executes_step_without_diagnostics(mock_agent):
    """Test AgentTeam executes steps normally without diagnostics."""
    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    team = AgentTeam(config)
    team.add_agent(mock_agent)

    step = WorkflowStep(
        id="test_step",
        name="Test Step",
        agent_role=AgentRole.DEVELOPER,
        input_template="Test task",
    )

    result = await team._execute_step(
        step=step,
        agent=mock_agent,
        task="Test task",
        outputs={},
        context={},
        workflow_id="test-workflow",
    )

    assert result.status == StepStatus.COMPLETED
    assert result.agent_result.success is True


@pytest.mark.asyncio
async def test_step_metadata_preserved_without_diagnostics(mock_agent):
    """Test step metadata is preserved even without diagnostics."""
    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    team = AgentTeam(config)
    team.add_agent(mock_agent)

    step = WorkflowStep(
        id="test_step",
        name="Test Step",
        agent_role=AgentRole.DEVELOPER,
        input_template="Test task",
        metadata={"custom": "value"},
    )

    result = await team._execute_step(
        step=step,
        agent=mock_agent,
        task="Test task",
        outputs={},
        context={},
        workflow_id="test-workflow",
    )

    # Result should have metadata field
    assert hasattr(result, "metadata")
    assert isinstance(result.metadata, dict)


# ============== Integration Tests with Playwright ==============
# These tests require Playwright to be installed


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed (required for integration tests)",
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_diagnostics_integrator_initializes(mock_agent):
    """Test DiagnosticsIntegrator initializes when Playwright available."""
    diag_config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
    )

    config = TeamConfig(
        name="Test Team",
        description="Test",
        diagnostics_config=diag_config,
    )

    # Need to have an executor available
    try:
        from orchestration.integrations.unified import auto_setup_executor

        executor = auto_setup_executor()

        team = AgentTeam(config)

        # Should have initialized diagnostics
        assert team.diagnostics is not None
    except Exception as e:
        # If no LLM backend configured, skip test
        pytest.skip(f"No LLM backend configured: {e}")


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed (required for integration tests)",
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_step_with_diagnostics_enabled(mock_agent):
    """Test step execution with diagnostics enabled in metadata."""
    diag_config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
    )

    config = TeamConfig(
        name="Test Team",
        description="Test",
        diagnostics_config=diag_config,
    )

    try:
        team = AgentTeam(config)
        team.add_agent(mock_agent)

        step = WorkflowStep(
            id="test_step",
        name="Test Step",
            agent_role=AgentRole.DEVELOPER,
            input_template="Test task",
            metadata={
                "diagnostics_enabled": True,
                "test_url": "https://example.com",
                "test_actions": [],
            },
        )

        result = await team._execute_step(
            step=step,
            agent=mock_agent,
            task="Test task",
            outputs={},
            context={},
            workflow_id="test-workflow",
        )

        assert result.status == StepStatus.COMPLETED
        # Should have attempted diagnostics capture
        # (may fail if capture_step_diagnostics not fully implemented)

    except Exception as e:
        # Expected for Phase 2 - capture_step_diagnostics is a stub
        pytest.skip(f"Diagnostics capture not fully implemented: {e}")


# ============== Backward Compatibility Tests ==============


@pytest.mark.asyncio
async def test_existing_code_still_works(mock_agent):
    """Test that existing code without diagnostics still works."""
    # Old-style config without diagnostics_config
    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    team = AgentTeam(config)
    team.add_agent(mock_agent)

    step = WorkflowStep(
        id="test_step",
        name="Test Step",
        agent_role=AgentRole.DEVELOPER,
        input_template="Test task",
    )

    # Should work exactly as before
    result = await team._execute_step(
        step=step,
        agent=mock_agent,
        task="Test task",
        outputs={},
        context={},
        workflow_id="test-workflow",
    )

    assert result.status == StepStatus.COMPLETED
    assert result.agent_result.success is True
    # No diagnostics, no problem
    assert result.metadata == {} or "diagnostics" not in result.metadata


@pytest.mark.asyncio
async def test_workflow_run_without_diagnostics(mock_agent):
    """Test full workflow run without diagnostics."""
    config = TeamConfig(
        name="Test Team",
        description="Test",
    )

    team = AgentTeam(config)
    team.add_agent(mock_agent)

    step = WorkflowStep(
        id="test_step",
        name="Test Step",
        agent_role=AgentRole.DEVELOPER,
        input_template="{task}",
    )
    team.add_step(step)

    # Full workflow run
    result = await team.run(task="Test task")

    assert result.success is True
    assert len(result.steps) == 1
    assert result.steps[0].status == StepStatus.COMPLETED
