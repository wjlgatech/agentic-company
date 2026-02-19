"""Configuration for automated diagnostics capture."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiagnosticsConfig:
    """Configuration for automated diagnostics capture.

    This configuration controls the behavior of the automated diagnostics system,
    including browser automation, capture settings, and iteration control.

    Attributes:
        enabled: Enable/disable the diagnostics system (opt-in by default)
        playwright_headless: Run browser in headless mode
        browser_type: Browser to use (chromium, firefox, webkit)
        viewport_width: Browser viewport width in pixels
        viewport_height: Browser viewport height in pixels
        timeout_ms: Default timeout for browser operations in milliseconds
        capture_screenshots: Capture screenshots during test execution
        capture_console: Capture browser console logs
        capture_network: Capture network requests and responses
        screenshot_on_error: Automatically capture screenshot when error occurs
        iteration_threshold: Number of iterations before triggering meta-analysis
        max_iterations: Maximum number of auto-retry iterations
        output_dir: Directory for diagnostic output files (defaults to workflow run dir)
    """

    # Enable/disable
    enabled: bool = False  # Opt-in by default for safety

    # Browser settings
    playwright_headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout_ms: int = 30000  # 30 seconds

    # Capture options
    capture_screenshots: bool = True
    capture_console: bool = True
    capture_network: bool = True
    screenshot_on_error: bool = True

    # Iteration control
    iteration_threshold: int = 3  # Trigger meta-analysis after N iterations
    max_iterations: int = 10

    # Output
    output_dir: Path | None = None  # Defaults to workflow run dir

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.browser_type not in ("chromium", "firefox", "webkit"):
            raise ValueError(
                f"Invalid browser_type: {self.browser_type}. "
                "Must be one of: chromium, firefox, webkit"
            )

        if self.viewport_width <= 0 or self.viewport_height <= 0:
            raise ValueError("Viewport dimensions must be positive")

        if self.timeout_ms <= 0:
            raise ValueError("Timeout must be positive")

        if self.iteration_threshold < 1:
            raise ValueError("Iteration threshold must be at least 1")

        if self.max_iterations < 1:
            raise ValueError("Max iterations must be at least 1")

        if self.iteration_threshold > self.max_iterations:
            raise ValueError("Iteration threshold cannot exceed max iterations")

        # Convert output_dir string to Path if needed
        if self.output_dir is not None and not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)
