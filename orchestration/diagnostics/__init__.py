"""
Automated diagnostics capture system for Agenticom.

Provides browser automation, error capture, and meta-analysis to reduce
debugging iteration time from 30 minutes to 30 seconds.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .capture import BrowserAction, DiagnosticCapture, PlaywrightCapture
    from .config import DiagnosticsConfig


def check_playwright_installation() -> bool:
    """Check if Playwright is installed and available.

    Returns:
        True if Playwright is installed, False otherwise
    """
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def require_playwright() -> None:
    """Raise helpful error if Playwright is not installed.

    Raises:
        ImportError: If Playwright is not available with installation instructions
    """
    if not check_playwright_installation():
        raise ImportError(
            "Playwright is required for automated diagnostics.\n"
            "\n"
            "Install with:\n"
            "  pip install 'agentic-company[diagnostics]'\n"
            "\n"
            "Then install browsers:\n"
            "  playwright install\n"
            "\n"
            "Or install just Chromium:\n"
            "  playwright install chromium"
        )


# Lazy imports - only load if Playwright is available
def __getattr__(name: str):
    """Lazy load diagnostics modules to avoid Playwright import errors."""
    if name == "DiagnosticsConfig":
        from .config import DiagnosticsConfig

        return DiagnosticsConfig
    elif name == "PlaywrightCapture":
        require_playwright()
        from .capture import PlaywrightCapture

        return PlaywrightCapture
    elif name == "BrowserAction":
        require_playwright()
        from .capture import BrowserAction

        return BrowserAction
    elif name == "DiagnosticCapture":
        from .capture import DiagnosticCapture

        return DiagnosticCapture
    elif name == "IterationMonitor":
        from .iteration_monitor import IterationMonitor

        return IterationMonitor
    elif name == "CriteriaBuilder":
        from .criteria_builder import CriteriaBuilder

        return CriteriaBuilder
    elif name == "MetaAnalyzer":
        from .meta_analyzer import MetaAnalyzer

        return MetaAnalyzer
    elif name == "DiagnosticsIntegrator":
        require_playwright()
        from .integration import DiagnosticsIntegrator

        return DiagnosticsIntegrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DiagnosticsConfig",
    "PlaywrightCapture",
    "BrowserAction",
    "DiagnosticCapture",
    "IterationMonitor",
    "CriteriaBuilder",
    "MetaAnalyzer",
    "DiagnosticsIntegrator",
    "check_playwright_installation",
    "require_playwright",
]
