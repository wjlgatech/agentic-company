"""
LLM Integrations for Agenticom

Provides unified interface for OpenClaw, Nanobot, Ollama, and other LLM backends.
Automatically handles installation if dependencies are missing.

Three ways to run:
1. OpenClaw (Claude) - Cloud API, requires ANTHROPIC_API_KEY
2. Nanobot (GPT) - Cloud API, requires OPENAI_API_KEY
3. Ollama (Local) - 100% FREE, no API key, runs on your machine!
"""

from orchestration.integrations.nanobot import (
    NanobotConfig,
    NanobotExecutor,
    install_nanobot,
    is_nanobot_installed,
)
from orchestration.integrations.ollama import (
    RECOMMENDED_MODELS,
    LMStudioExecutor,
    OllamaConfig,
    OllamaExecutor,
    get_available_models,
    is_ollama_installed,
    is_ollama_running,
    pull_model,
)
from orchestration.integrations.openclaw import (
    OpenClawConfig,
    OpenClawExecutor,
    install_openclaw,
    is_openclaw_installed,
)
from orchestration.integrations.unified import (
    Backend,
    UnifiedConfig,
    UnifiedExecutor,
    auto_setup_executor,
    get_available_backends,
    get_ready_backends,
    quick_start,
)

__all__ = [
    # OpenClaw (Anthropic)
    "OpenClawExecutor",
    "OpenClawConfig",
    "install_openclaw",
    "is_openclaw_installed",
    # Nanobot (OpenAI)
    "NanobotExecutor",
    "NanobotConfig",
    "install_nanobot",
    "is_nanobot_installed",
    # Ollama (Local - FREE!)
    "OllamaExecutor",
    "OllamaConfig",
    "LMStudioExecutor",
    "is_ollama_running",
    "is_ollama_installed",
    "get_available_models",
    "pull_model",
    "RECOMMENDED_MODELS",
    # Unified
    "UnifiedExecutor",
    "UnifiedConfig",
    "Backend",
    "auto_setup_executor",
    "get_available_backends",
    "get_ready_backends",
    "quick_start",
]
