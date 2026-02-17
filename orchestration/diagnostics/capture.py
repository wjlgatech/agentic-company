"""Browser automation and diagnostic capture using Playwright."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


class ActionType(Enum):
    """Types of browser actions that can be performed."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    SCREENSHOT = "screenshot"
    EVALUATE = "evaluate"


@dataclass
class BrowserAction:
    """Represents a single browser action to perform.

    Attributes:
        type: Type of action to perform
        selector: CSS selector for element (for click, type, wait_for_selector)
        value: Value for action (URL for navigate, text for type, etc.)
        timeout: Optional timeout override for this action (ms)
    """

    type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrowserAction":
        """Create BrowserAction from dictionary.

        Args:
            data: Dictionary with action data

        Returns:
            BrowserAction instance
        """
        action_type = ActionType(data["type"])
        return cls(
            type=action_type,
            selector=data.get("selector"),
            value=data.get("value"),
            timeout=data.get("timeout"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "selector": self.selector,
            "value": self.value,
            "timeout": self.timeout,
        }


@dataclass
class ConsoleMessage:
    """Browser console message."""

    type: str  # log, warning, error, etc.
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class NetworkRequest:
    """Network request information."""

    url: str
    method: str
    status: Optional[int] = None
    response_time_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DiagnosticCapture:
    """Result of a diagnostic capture session.

    Attributes:
        success: Whether the test passed
        error: Error message if test failed
        console_logs: Captured console messages
        console_errors: Console errors only
        network_requests: Captured network activity
        screenshots: Paths to captured screenshots
        final_url: Final URL after all actions
        execution_time_ms: Total execution time
        metadata: Additional metadata
    """

    success: bool
    error: Optional[str] = None
    console_logs: List[ConsoleMessage] = field(default_factory=list)
    console_errors: List[ConsoleMessage] = field(default_factory=list)
    network_requests: List[NetworkRequest] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    final_url: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "error": self.error,
            "console_logs": [msg.to_dict() for msg in self.console_logs],
            "console_errors": [msg.to_dict() for msg in self.console_errors],
            "network_requests": [req.to_dict() for req in self.network_requests],
            "screenshots": self.screenshots,
            "final_url": self.final_url,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagnosticCapture":
        """Create DiagnosticCapture from dictionary."""
        # Convert console logs
        console_logs = [
            ConsoleMessage(
                type=msg["type"],
                text=msg["text"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
            )
            for msg in data.get("console_logs", [])
        ]

        # Convert console errors
        console_errors = [
            ConsoleMessage(
                type=msg["type"],
                text=msg["text"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
            )
            for msg in data.get("console_errors", [])
        ]

        # Convert network requests
        network_requests = [
            NetworkRequest(
                url=req["url"],
                method=req["method"],
                status=req.get("status"),
                response_time_ms=req.get("response_time_ms"),
                timestamp=datetime.fromisoformat(req["timestamp"]),
            )
            for req in data.get("network_requests", [])
        ]

        return cls(
            success=data["success"],
            error=data.get("error"),
            console_logs=console_logs,
            console_errors=console_errors,
            network_requests=network_requests,
            screenshots=data.get("screenshots", []),
            final_url=data.get("final_url"),
            execution_time_ms=data.get("execution_time_ms"),
            metadata=data.get("metadata", {}),
        )


class PlaywrightCapture:
    """Browser automation and diagnostic capture using Playwright.

    This class provides a high-level interface for automating browser interactions
    and capturing diagnostic information including console logs, network activity,
    and screenshots.

    Example:
        ```python
        from orchestration.diagnostics import DiagnosticsConfig, PlaywrightCapture

        config = DiagnosticsConfig(enabled=True)
        capture = PlaywrightCapture(config)

        async with capture:
            actions = [
                BrowserAction(type=ActionType.NAVIGATE, value="https://example.com"),
                BrowserAction(type=ActionType.WAIT_FOR_SELECTOR, selector="h1"),
                BrowserAction(type=ActionType.SCREENSHOT, value="page.png"),
            ]
            result = await capture.execute_actions(actions)
        ```
    """

    def __init__(self, config: "DiagnosticsConfig"):  # noqa: F821
        """Initialize PlaywrightCapture.

        Args:
            config: Diagnostics configuration
        """
        from .config import DiagnosticsConfig

        self.config: DiagnosticsConfig = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Capture state
        self.console_logs: List[ConsoleMessage] = []
        self.console_errors: List[ConsoleMessage] = []
        self.network_requests: List[NetworkRequest] = []
        self.screenshots: List[str] = []

    async def __aenter__(self) -> "PlaywrightCapture":
        """Start browser automation session."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            from ..diagnostics import require_playwright
            require_playwright()

        logger.info("Starting browser automation session", browser=self.config.browser_type)

        # Launch playwright
        self.playwright = await async_playwright().start()

        # Get browser type
        if self.config.browser_type == "chromium":
            browser_type = self.playwright.chromium
        elif self.config.browser_type == "firefox":
            browser_type = self.playwright.firefox
        elif self.config.browser_type == "webkit":
            browser_type = self.playwright.webkit
        else:
            raise ValueError(f"Invalid browser type: {self.config.browser_type}")

        # Launch browser
        self.browser = await browser_type.launch(
            headless=self.config.playwright_headless
        )

        # Create context with viewport
        self.context = await self.browser.new_context(
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            }
        )

        # Create page
        self.page = await self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(self.config.timeout_ms)

        # Setup event listeners
        if self.config.capture_console:
            self.page.on("console", self._on_console_message)

        if self.config.capture_network:
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)

        logger.info("Browser automation session started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up browser automation session."""
        logger.info("Closing browser automation session")

        # Close page
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                logger.warning("Error closing page", error=str(e))

        # Close context
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.warning("Error closing context", error=str(e))

        # Close browser
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning("Error closing browser", error=str(e))

        # Stop playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning("Error stopping playwright", error=str(e))

        logger.info("Browser automation session closed")

    def _on_console_message(self, msg) -> None:
        """Handle console message event."""
        console_msg = ConsoleMessage(type=msg.type, text=msg.text)
        self.console_logs.append(console_msg)

        # Track errors separately
        if msg.type in ("error", "warning"):
            self.console_errors.append(console_msg)

    def _on_request(self, request) -> None:
        """Handle request event."""
        network_req = NetworkRequest(
            url=request.url,
            method=request.method,
        )
        self.network_requests.append(network_req)

    def _on_response(self, response) -> None:
        """Handle response event."""
        # Update the corresponding request
        for req in self.network_requests:
            if req.url == response.url and req.status is None:
                req.status = response.status
                break

    async def execute_actions(
        self, actions: List[BrowserAction], output_dir: Optional[Path] = None
    ) -> DiagnosticCapture:
        """Execute a series of browser actions and capture diagnostics.

        Args:
            actions: List of actions to execute
            output_dir: Directory for output files (screenshots)

        Returns:
            DiagnosticCapture with results and captured diagnostics
        """
        if not self.page:
            raise RuntimeError("Browser session not started. Use 'async with' context.")

        # Clear previous captures
        self.console_logs.clear()
        self.console_errors.clear()
        self.network_requests.clear()
        self.screenshots.clear()

        # Setup output directory
        if output_dir is None:
            output_dir = self.config.output_dir or Path.cwd()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        start_time = datetime.utcnow()
        error: Optional[str] = None

        try:
            for action in actions:
                await self._execute_action(action, output_dir)

            success = True

        except Exception as e:
            logger.error("Action execution failed", error=str(e), exc_info=True)
            error = str(e)
            success = False

            # Capture error screenshot
            if self.config.screenshot_on_error:
                try:
                    error_screenshot = output_dir / f"error_{datetime.utcnow().timestamp()}.png"
                    await self.page.screenshot(path=str(error_screenshot))
                    self.screenshots.append(str(error_screenshot))
                    logger.info("Error screenshot captured", path=str(error_screenshot))
                except Exception as screenshot_error:
                    logger.warning("Failed to capture error screenshot", error=str(screenshot_error))

        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Get final URL
        final_url = self.page.url if self.page else None

        return DiagnosticCapture(
            success=success,
            error=error,
            console_logs=self.console_logs.copy(),
            console_errors=self.console_errors.copy(),
            network_requests=self.network_requests.copy(),
            screenshots=self.screenshots.copy(),
            final_url=final_url,
            execution_time_ms=execution_time_ms,
        )

    async def _execute_action(self, action: BrowserAction, output_dir: Path) -> None:
        """Execute a single browser action.

        Args:
            action: Action to execute
            output_dir: Directory for output files

        Raises:
            ValueError: If action is invalid
            TimeoutError: If action times out
        """
        if not self.page:
            raise RuntimeError("Browser page not available")

        logger.debug("Executing action", action_type=action.type.value, selector=action.selector)

        # Get timeout for this action
        timeout = action.timeout or self.config.timeout_ms

        if action.type == ActionType.NAVIGATE:
            if not action.value:
                raise ValueError("NAVIGATE action requires value (URL)")
            await self.page.goto(action.value, timeout=timeout)

        elif action.type == ActionType.CLICK:
            if not action.selector:
                raise ValueError("CLICK action requires selector")
            await self.page.click(action.selector, timeout=timeout)

        elif action.type == ActionType.TYPE:
            if not action.selector or not action.value:
                raise ValueError("TYPE action requires selector and value")
            await self.page.fill(action.selector, action.value, timeout=timeout)

        elif action.type == ActionType.WAIT:
            if not action.value:
                raise ValueError("WAIT action requires value (milliseconds)")
            wait_ms = int(action.value)
            await asyncio.sleep(wait_ms / 1000.0)

        elif action.type == ActionType.WAIT_FOR_SELECTOR:
            if not action.selector:
                raise ValueError("WAIT_FOR_SELECTOR action requires selector")
            await self.page.wait_for_selector(action.selector, timeout=timeout)

        elif action.type == ActionType.SCREENSHOT:
            if not action.value:
                raise ValueError("SCREENSHOT action requires value (filename)")
            screenshot_path = output_dir / action.value
            await self.page.screenshot(path=str(screenshot_path))
            self.screenshots.append(str(screenshot_path))
            logger.info("Screenshot captured", path=str(screenshot_path))

        elif action.type == ActionType.EVALUATE:
            if not action.value:
                raise ValueError("EVALUATE action requires value (JavaScript code)")
            await self.page.evaluate(action.value)

        else:
            raise ValueError(f"Unknown action type: {action.type}")
