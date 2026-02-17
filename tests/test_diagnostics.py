"""Unit tests for diagnostics module (Phase 1 - mocked Playwright)."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from orchestration.diagnostics import (
    DiagnosticsConfig,
    check_playwright_installation,
    require_playwright,
)
from orchestration.diagnostics.capture import (
    ActionType,
    BrowserAction,
    ConsoleMessage,
    DiagnosticCapture,
    NetworkRequest,
)
from orchestration.diagnostics.iteration_monitor import (
    IterationMonitor,
    IterationRecord,
)


# ============== Config Tests ==============


def test_diagnostics_config_defaults():
    """Test DiagnosticsConfig default values."""
    config = DiagnosticsConfig()

    assert config.enabled is False  # Opt-in by default
    assert config.playwright_headless is True
    assert config.browser_type == "chromium"
    assert config.viewport_width == 1920
    assert config.viewport_height == 1080
    assert config.timeout_ms == 30000
    assert config.capture_screenshots is True
    assert config.capture_console is True
    assert config.capture_network is True
    assert config.screenshot_on_error is True
    assert config.iteration_threshold == 3
    assert config.max_iterations == 10
    assert config.output_dir is None


def test_diagnostics_config_validation():
    """Test DiagnosticsConfig validation."""
    # Invalid browser type
    with pytest.raises(ValueError, match="Invalid browser_type"):
        DiagnosticsConfig(browser_type="safari")

    # Invalid viewport
    with pytest.raises(ValueError, match="Viewport dimensions"):
        DiagnosticsConfig(viewport_width=0)

    # Invalid timeout
    with pytest.raises(ValueError, match="Timeout must be positive"):
        DiagnosticsConfig(timeout_ms=-1)

    # Invalid iteration threshold
    with pytest.raises(ValueError, match="Iteration threshold"):
        DiagnosticsConfig(iteration_threshold=0)

    # Invalid max iterations
    with pytest.raises(ValueError, match="Max iterations"):
        DiagnosticsConfig(max_iterations=0)

    # Threshold exceeds max iterations
    with pytest.raises(ValueError, match="cannot exceed"):
        DiagnosticsConfig(iteration_threshold=10, max_iterations=5)


def test_diagnostics_config_valid():
    """Test valid DiagnosticsConfig."""
    config = DiagnosticsConfig(
        enabled=True,
        browser_type="firefox",
        viewport_width=1280,
        viewport_height=720,
        timeout_ms=10000,
        iteration_threshold=2,
        max_iterations=5,
    )

    assert config.enabled is True
    assert config.browser_type == "firefox"
    assert config.viewport_width == 1280
    assert config.iteration_threshold == 2


# ============== Browser Action Tests ==============


def test_browser_action_creation():
    """Test BrowserAction creation."""
    action = BrowserAction(
        type=ActionType.NAVIGATE,
        value="https://example.com",
        timeout=5000,
    )

    assert action.type == ActionType.NAVIGATE
    assert action.value == "https://example.com"
    assert action.timeout == 5000
    assert action.selector is None


def test_browser_action_from_dict():
    """Test BrowserAction.from_dict()."""
    data = {
        "type": "click",
        "selector": "#button",
        "timeout": 3000,
    }

    action = BrowserAction.from_dict(data)

    assert action.type == ActionType.CLICK
    assert action.selector == "#button"
    assert action.timeout == 3000


def test_browser_action_to_dict():
    """Test BrowserAction.to_dict()."""
    action = BrowserAction(
        type=ActionType.TYPE,
        selector="#input",
        value="test",
    )

    data = action.to_dict()

    assert data["type"] == "type"
    assert data["selector"] == "#input"
    assert data["value"] == "test"


# ============== Console Message Tests ==============


def test_console_message_creation():
    """Test ConsoleMessage creation."""
    msg = ConsoleMessage(type="error", text="Test error")

    assert msg.type == "error"
    assert msg.text == "Test error"
    assert isinstance(msg.timestamp, datetime)


def test_console_message_to_dict():
    """Test ConsoleMessage.to_dict()."""
    msg = ConsoleMessage(type="log", text="Test log")
    data = msg.to_dict()

    assert data["type"] == "log"
    assert data["text"] == "Test log"
    assert "timestamp" in data


# ============== Network Request Tests ==============


def test_network_request_creation():
    """Test NetworkRequest creation."""
    req = NetworkRequest(
        url="https://api.example.com/data",
        method="GET",
        status=200,
    )

    assert req.url == "https://api.example.com/data"
    assert req.method == "GET"
    assert req.status == 200


def test_network_request_to_dict():
    """Test NetworkRequest.to_dict()."""
    req = NetworkRequest(
        url="https://api.example.com/data",
        method="POST",
        status=201,
    )
    data = req.to_dict()

    assert data["url"] == "https://api.example.com/data"
    assert data["method"] == "POST"
    assert data["status"] == 201


# ============== Diagnostic Capture Tests ==============


def test_diagnostic_capture_creation():
    """Test DiagnosticCapture creation."""
    capture = DiagnosticCapture(
        success=True,
        console_logs=[ConsoleMessage(type="log", text="Test")],
        final_url="https://example.com",
    )

    assert capture.success is True
    assert len(capture.console_logs) == 1
    assert capture.final_url == "https://example.com"


def test_diagnostic_capture_to_dict():
    """Test DiagnosticCapture.to_dict()."""
    capture = DiagnosticCapture(
        success=False,
        error="Test error",
        console_errors=[ConsoleMessage(type="error", text="Error")],
    )

    data = capture.to_dict()

    assert data["success"] is False
    assert data["error"] == "Test error"
    assert len(data["console_errors"]) == 1


def test_diagnostic_capture_from_dict():
    """Test DiagnosticCapture.from_dict()."""
    data = {
        "success": True,
        "error": None,
        "console_logs": [
            {"type": "log", "text": "Test", "timestamp": "2024-01-01T00:00:00"}
        ],
        "console_errors": [],
        "network_requests": [
            {
                "url": "https://example.com",
                "method": "GET",
                "status": 200,
                "timestamp": "2024-01-01T00:00:00",
            }
        ],
        "screenshots": ["test.png"],
        "final_url": "https://example.com",
        "execution_time_ms": 1000,
    }

    capture = DiagnosticCapture.from_dict(data)

    assert capture.success is True
    assert len(capture.console_logs) == 1
    assert len(capture.network_requests) == 1
    assert capture.screenshots == ["test.png"]


# ============== Iteration Monitor Tests ==============


def test_iteration_monitor_creation():
    """Test IterationMonitor creation."""
    config = DiagnosticsConfig(iteration_threshold=3)
    monitor = IterationMonitor(config)

    assert monitor.config == config
    assert monitor.current_step_id is None
    assert monitor.iterations_by_step == {}


def test_iteration_monitor_start_step():
    """Test IterationMonitor.start_step()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")

    assert monitor.current_step_id == "test_step"
    assert "test_step" in monitor.iterations_by_step
    assert monitor.iterations_by_step["test_step"] == []


def test_iteration_monitor_record_iteration():
    """Test IterationMonitor.record_iteration()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")

    record = monitor.record_iteration(
        error="Test error",
        fix_attempted="Fixed bug",
        test_result=False,
        diagnostics=None,
    )

    assert record.iteration == 1
    assert record.step_id == "test_step"
    assert record.error == "Test error"
    assert record.test_result is False
    assert len(monitor.iterations_by_step["test_step"]) == 1


def test_iteration_monitor_record_without_start():
    """Test IterationMonitor.record_iteration() without start_step()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    with pytest.raises(RuntimeError, match="No step is currently being monitored"):
        monitor.record_iteration(
            error="Test",
            fix_attempted="Fix",
            test_result=False,
        )


def test_iteration_monitor_should_trigger_meta_analysis():
    """Test IterationMonitor.should_trigger_meta_analysis()."""
    config = DiagnosticsConfig(iteration_threshold=3)
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")

    # Record 2 failures - should not trigger
    monitor.record_iteration(error="Error 1", fix_attempted="Fix 1", test_result=False)
    monitor.record_iteration(error="Error 2", fix_attempted="Fix 2", test_result=False)

    assert monitor.should_trigger_meta_analysis() is False

    # Record 3rd failure - should trigger
    monitor.record_iteration(error="Error 3", fix_attempted="Fix 3", test_result=False)

    assert monitor.should_trigger_meta_analysis() is True


def test_iteration_monitor_no_trigger_on_success():
    """Test meta-analysis not triggered if test passes."""
    config = DiagnosticsConfig(iteration_threshold=2)
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")

    # Record failure then success
    monitor.record_iteration(error="Error", fix_attempted="Fix", test_result=False)
    monitor.record_iteration(error=None, fix_attempted="Fix 2", test_result=True)

    # Should not trigger because not all recent iterations failed
    assert monitor.should_trigger_meta_analysis() is False


def test_iteration_monitor_get_iterations():
    """Test IterationMonitor.get_iterations()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")
    monitor.record_iteration(error="Error", fix_attempted="Fix", test_result=False)

    iterations = monitor.get_iterations("test_step")
    assert len(iterations) == 1
    assert iterations[0].iteration == 1


def test_iteration_monitor_get_iteration_count():
    """Test IterationMonitor.get_iteration_count()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")
    assert monitor.get_iteration_count() == 0

    monitor.record_iteration(error="Error", fix_attempted="Fix", test_result=False)
    assert monitor.get_iteration_count() == 1


def test_iteration_monitor_reset_step():
    """Test IterationMonitor.reset_step()."""
    config = DiagnosticsConfig()
    monitor = IterationMonitor(config)

    monitor.start_step("test_step")
    monitor.record_iteration(error="Error", fix_attempted="Fix", test_result=False)

    assert monitor.get_iteration_count() == 1

    monitor.reset_step()
    assert monitor.get_iteration_count() == 0


# ============== Installation Check Tests ==============


def test_check_playwright_installation():
    """Test check_playwright_installation()."""
    # This will actually check if playwright is installed
    # Result depends on test environment
    result = check_playwright_installation()
    assert isinstance(result, bool)


def test_require_playwright_when_not_installed():
    """Test require_playwright() raises error when not installed."""
    with patch("orchestration.diagnostics.check_playwright_installation", return_value=False):
        with pytest.raises(ImportError, match="Playwright is required"):
            require_playwright()


def test_require_playwright_when_installed():
    """Test require_playwright() succeeds when installed."""
    with patch("orchestration.diagnostics.check_playwright_installation", return_value=True):
        # Should not raise
        require_playwright()


# ============== Mocked Playwright Capture Tests ==============
# These tests use pytest.importorskip to skip if playwright not installed
# (since we're mocking it, we don't actually need it, but the patch requires the module)


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed (optional for unit tests)"
)
@pytest.mark.asyncio
async def test_playwright_capture_context_manager():
    """Test PlaywrightCapture async context manager with mocked Playwright."""
    # Only import and patch if playwright is available
    from unittest.mock import patch, AsyncMock, MagicMock

    with patch("playwright.async_api.async_playwright") as mock_playwright:
        # Mock Playwright API
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = MagicMock()

        # Import after patching
        from orchestration.diagnostics.capture import PlaywrightCapture

        config = DiagnosticsConfig(enabled=True)
        capture = PlaywrightCapture(config)

        async with capture:
            assert capture.playwright is not None
            assert capture.browser is not None
            assert capture.page is not None

        # Verify cleanup was called
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed (optional for unit tests)"
)
@pytest.mark.asyncio
async def test_playwright_capture_execute_navigate():
    """Test PlaywrightCapture execute NAVIGATE action with mocked Playwright."""
    from unittest.mock import patch, AsyncMock, MagicMock

    with patch("playwright.async_api.async_playwright") as mock_playwright:
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.screenshot = AsyncMock()

        from orchestration.diagnostics.capture import PlaywrightCapture

        config = DiagnosticsConfig(enabled=True)
        capture = PlaywrightCapture(config)

        async with capture:
            actions = [
                BrowserAction(type=ActionType.NAVIGATE, value="https://example.com"),
            ]

            result = await capture.execute_actions(actions)

            assert result.success is True
            assert result.error is None
            mock_page.goto.assert_called_once_with("https://example.com", timeout=30000)


@pytest.mark.skipif(
    not check_playwright_installation(),
    reason="Playwright not installed (optional for unit tests)"
)
@pytest.mark.asyncio
async def test_playwright_capture_error_screenshot():
    """Test PlaywrightCapture captures screenshot on error with mocked Playwright."""
    from unittest.mock import patch, AsyncMock, MagicMock

    with patch("playwright.async_api.async_playwright") as mock_playwright:
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = MagicMock()
        mock_page.goto = AsyncMock(side_effect=Exception("Navigation failed"))
        mock_page.screenshot = AsyncMock()

        from orchestration.diagnostics.capture import PlaywrightCapture

        config = DiagnosticsConfig(enabled=True, screenshot_on_error=True)
        capture = PlaywrightCapture(config)

        async with capture:
            actions = [
                BrowserAction(type=ActionType.NAVIGATE, value="https://example.com"),
            ]

            result = await capture.execute_actions(actions)

            assert result.success is False
            assert result.error == "Navigation failed"
            # Should have captured error screenshot
            mock_page.screenshot.assert_called_once()
            assert len(result.screenshots) == 1
