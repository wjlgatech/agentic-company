"""Tests for Phase 3: Auto-Test-After-Fix Loop."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from orchestration.diagnostics import (
    DiagnosticsConfig,
    check_playwright_installation,
)
from orchestration.diagnostics.integration import DiagnosticsIntegrator
from orchestration.diagnostics.capture import DiagnosticCapture, BrowserAction, ActionType


# ============== Fixtures ==============


@pytest.fixture
def mock_executor():
    """Create a mock executor."""
    executor = AsyncMock()
    executor.execute = AsyncMock(return_value={
        "content": "Mock analysis",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    })
    return executor


@pytest.fixture
def diagnostics_config():
    """Create diagnostics config for testing."""
    return DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        iteration_threshold=3,
        max_iterations=5,
        capture_screenshots=True,
        capture_console=True,
    )


@pytest.fixture
def mock_step():
    """Create a mock workflow step."""
    step = MagicMock()
    step.id = "test_step"
    step.metadata = {
        "diagnostics_enabled": True,
        "test_url": "https://example.com",
        "test_actions": [
            {"type": "navigate", "value": "https://example.com"},
            {"type": "wait_for_selector", "selector": "h1"},
            {"type": "screenshot", "value": "test.png"},
        ],
    }
    return step


@pytest.fixture
def mock_step_result():
    """Create a mock step result."""
    result = MagicMock()
    result.metadata = {}
    result.agent_result = MagicMock()
    result.agent_result.output = "Test output from agent"
    return result


# ============== Unit Tests ==============


def test_diagnostics_integrator_initialization(diagnostics_config, mock_executor):
    """Test DiagnosticsIntegrator initializes correctly."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    assert integrator.config == diagnostics_config
    assert integrator.executor == mock_executor
    assert integrator.monitor is not None
    assert integrator.analyzer is not None


@pytest.mark.asyncio
async def test_wrap_step_execution_without_diagnostics_enabled(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test wrap_step_execution when diagnostics not enabled for step."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Disable diagnostics for this step
    mock_step.metadata["diagnostics_enabled"] = False

    # Mock original execute function
    async def original_execute(*args, **kwargs):
        return mock_step_result

    # Execute
    result = await integrator.wrap_step_execution(
        mock_step, original_execute
    )

    # Should just call original execute and return
    assert result == mock_step_result


@pytest.mark.asyncio
async def test_wrap_step_execution_no_test_config(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test wrap_step_execution when no test_url/test_actions configured."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Remove test config
    mock_step.metadata["test_url"] = None
    mock_step.metadata["test_actions"] = []

    # Mock original execute function
    async def original_execute(*args, **kwargs):
        return mock_step_result

    # Execute
    result = await integrator.wrap_step_execution(
        mock_step, original_execute
    )

    # Should return result with error
    assert result == mock_step_result
    assert "diagnostics" in result.metadata
    assert result.metadata["diagnostics"]["captured"] is False


@pytest.mark.asyncio
async def test_capture_step_diagnostics_no_config(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test capture_step_diagnostics with no test configuration."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Remove test config
    mock_step.metadata["test_url"] = None
    mock_step.metadata["test_actions"] = []

    result = await integrator.capture_step_diagnostics(mock_step, mock_step_result)

    assert result["captured"] is False
    assert "No test_url or test_actions" in result["error"]


@pytest.mark.asyncio
async def test_run_diagnostics_invalid_action(
    diagnostics_config, mock_executor
):
    """Test _run_diagnostics with invalid action format."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Invalid action (missing required fields)
    invalid_actions = [
        {"type": "navigate"},  # Missing value
    ]

    result = await integrator._run_diagnostics(
        "https://example.com",
        invalid_actions
    )

    assert result.success is False
    # Error message comes from action execution, not format validation
    assert "requires value" in result.error or "Invalid action format" in result.error


# ============== Integration Tests (Require Playwright) ==============


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_diagnostics_real_browser(diagnostics_config, mock_executor):
    """Test _run_diagnostics with real browser automation."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Simple test: navigate to example.com and take screenshot
    actions = [
        {"type": "navigate", "value": "https://example.com"},
        {"type": "wait_for_selector", "selector": "h1", "timeout": 5000},
        {"type": "screenshot", "value": "example.png"},
    ]

    result = await integrator._run_diagnostics("https://example.com", actions)

    # Should succeed
    assert result.success is True
    assert result.error is None
    assert result.final_url == "https://example.com/"
    assert len(result.screenshots) >= 1
    assert result.execution_time_ms > 0


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_diagnostics_navigation_failure(diagnostics_config, mock_executor):
    """Test _run_diagnostics with navigation failure."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Try to navigate to invalid URL
    actions = [
        {"type": "navigate", "value": "https://invalid-url-that-does-not-exist.local"},
    ]

    result = await integrator._run_diagnostics(
        "https://invalid-url-that-does-not-exist.local",
        actions
    )

    # Should fail
    assert result.success is False
    assert result.error is not None


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_diagnostics_timeout(diagnostics_config, mock_executor):
    """Test _run_diagnostics with timeout."""
    # Set very short timeout
    config_with_timeout = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        timeout_ms=100,  # Very short timeout
    )

    integrator = DiagnosticsIntegrator(config_with_timeout, mock_executor)

    # Wait for element that doesn't exist with short timeout
    actions = [
        {"type": "navigate", "value": "https://example.com"},
        {"type": "wait_for_selector", "selector": "#element-that-does-not-exist"},
    ]

    result = await integrator._run_diagnostics("https://example.com", actions)

    # Should fail with timeout
    assert result.success is False
    assert result.error is not None


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_capture_step_diagnostics_real_browser(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test capture_step_diagnostics with real browser."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    result = await integrator.capture_step_diagnostics(mock_step, mock_step_result)

    assert result["captured"] is True
    assert result["success"] is True
    assert "screenshots" in result
    assert len(result["screenshots"]) >= 1


# ============== Auto-Test Loop Tests ==============


@pytest.mark.asyncio
async def test_iteration_monitor_integration(diagnostics_config, mock_executor):
    """Test that IterationMonitor is used correctly."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Start monitoring
    integrator.monitor.start_step("test_step")

    # Record some iterations
    for i in range(3):
        integrator.monitor.record_iteration(
            error=f"Error {i}",
            fix_attempted=f"Fix {i}",
            test_result=False,
        )

    # Should trigger meta-analysis
    assert integrator.monitor.should_trigger_meta_analysis() is True
    assert integrator.monitor.get_iteration_count() == 3


@pytest.mark.asyncio
async def test_monitor_resets_per_step(diagnostics_config, mock_executor):
    """Test that monitor tracks iterations per step separately."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Step 1
    integrator.monitor.start_step("step1")
    integrator.monitor.record_iteration("Error", "Fix", False)
    integrator.monitor.record_iteration("Error", "Fix", False)
    assert integrator.monitor.get_iteration_count() == 2

    # Step 2
    integrator.monitor.start_step("step2")
    integrator.monitor.record_iteration("Error", "Fix", False)
    assert integrator.monitor.get_iteration_count() == 1

    # Step 1 still has 2
    assert integrator.monitor.get_iteration_count("step1") == 2


# ============== Error Handling Tests ==============


@pytest.mark.asyncio
async def test_graceful_handling_of_playwright_errors(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test graceful handling when Playwright operations fail."""
    integrator = DiagnosticsIntegrator(diagnostics_config, mock_executor)

    # Mock _run_diagnostics to raise an exception
    async def failing_execute(*args, **kwargs):
        return mock_step_result

    with patch.object(
        integrator,
        '_run_diagnostics',
        side_effect=Exception("Playwright crashed!")
    ):
        result = await integrator.wrap_step_execution(
            mock_step, failing_execute
        )

        # Should handle error gracefully
        assert result is not None
        assert "diagnostics" in result.metadata
        assert result.metadata["diagnostics"]["success"] is False


# ============== Performance Tests ==============


@pytest.mark.asyncio
async def test_max_iterations_respected(
    diagnostics_config, mock_executor, mock_step, mock_step_result
):
    """Test that max_iterations is respected."""
    # Set max_iterations to 2, threshold to 1 (must be <= max_iterations)
    config = DiagnosticsConfig(
        enabled=True,
        max_iterations=2,
        iteration_threshold=1,
    )

    integrator = DiagnosticsIntegrator(config, mock_executor)

    call_count = 0

    async def original_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_step_result

    # Mock _run_diagnostics to always fail
    async def failing_diagnostics(*args, **kwargs):
        return DiagnosticCapture(
            success=False,
            error="Test always fails",
        )

    with patch.object(integrator, '_run_diagnostics', side_effect=failing_diagnostics):
        result = await integrator.wrap_step_execution(
            mock_step, original_execute
        )

        # Should have tried exactly max_iterations times
        assert call_count == 2
        assert result.metadata["iterations_total"] == 2
        assert "Max iterations" in result.metadata.get("diagnostics_note", "")
