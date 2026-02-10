"""
LLM Integrations for Agenticom

Provides unified interface for OpenClaw, Nanobot, and other LLM backends.
Automatically handles installation if dependencies are missing.
"""

from orchestration.integrations.openclaw import (
    OpenClawExecutor,
    install_openclaw,
    is_openclaw_installed,
)
from orchestration.integrations.nanobot import (
    NanobotExecutor,
    install_nanobot,
    is_nanobot_installed,
)
from orchestration.integrations.unified import (
    UnifiedExecutor,
    auto_setup_executor,
    get_available_backends,
)

__all__ = [
    # OpenClaw
    "OpenClawExecutor",
    "install_openclaw",
    "is_openclaw_installed",
    # Nanobot
    "NanobotExecutor",
    "install_nanobot",
    "is_nanobot_installed",
    # Unified
    "UnifiedExecutor",
    "auto_setup_executor",
    "get_available_backends",
]
