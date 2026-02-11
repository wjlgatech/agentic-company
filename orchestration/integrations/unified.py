"""
Unified LLM Executor

Provides a unified interface for multiple LLM backends.
Automatically detects, installs, and configures the best available option.

Supports:
- OpenClaw (Anthropic Claude) - Cloud API
- Nanobot (OpenAI GPT) - Cloud API
- Ollama (Local LLMs) - 100% FREE, runs on your machine!
"""

import os
from typing import Optional, Any, Literal
from dataclasses import dataclass
from enum import Enum

from orchestration.integrations.openclaw import (
    OpenClawExecutor,
    OpenClawConfig,
    is_openclaw_installed,
    install_openclaw,
)
from orchestration.integrations.nanobot import (
    NanobotExecutor,
    NanobotConfig,
    is_nanobot_installed,
    install_nanobot,
)
from orchestration.integrations.ollama import (
    OllamaExecutor,
    OllamaConfig,
    is_ollama_running,
    is_ollama_installed,
    get_available_models,
)


class Backend(Enum):
    """Available LLM backends"""
    OPENCLAW = "openclaw"  # Anthropic Claude (cloud)
    NANOBOT = "nanobot"    # OpenAI GPT (cloud)
    OLLAMA = "ollama"      # Local LLMs (free!)
    LOCAL = "local"        # Alias for Ollama
    AUTO = "auto"          # Auto-detect best available


@dataclass
class UnifiedConfig:
    """Configuration for unified executor"""
    preferred_backend: Backend = Backend.AUTO
    openclaw_model: str = "claude-3-5-sonnet-20241022"
    nanobot_model: str = "gpt-4-turbo-preview"
    ollama_model: str = "llama3.2"  # Default local model
    ollama_url: str = "http://localhost:11434"
    max_tokens: int = 4096
    temperature: float = 0.7
    auto_install: bool = True  # Auto-install missing backends


def get_available_backends() -> list[Backend]:
    """
    Get list of available (installed/running) backends.

    Returns:
        List of available Backend enums
    """
    available = []

    # Check cloud backends (SDK installed + API key)
    if is_openclaw_installed():
        available.append(Backend.OPENCLAW)

    if is_nanobot_installed():
        available.append(Backend.NANOBOT)

    # Check local backend (Ollama running)
    if is_ollama_running():
        available.append(Backend.OLLAMA)

    return available


def get_ready_backends() -> list[Backend]:
    """
    Get backends that are fully ready to use (with API keys or running).

    Returns:
        List of ready Backend enums
    """
    ready = []

    # Cloud backends need API keys
    if is_openclaw_installed() and os.environ.get("ANTHROPIC_API_KEY"):
        ready.append(Backend.OPENCLAW)

    if is_nanobot_installed() and os.environ.get("OPENAI_API_KEY"):
        ready.append(Backend.NANOBOT)

    # Local backend just needs to be running
    if is_ollama_running():
        ready.append(Backend.OLLAMA)

    return ready


def _has_api_key(backend: Backend) -> bool:
    """Check if API key is available for backend (or no key needed)"""
    if backend == Backend.OPENCLAW:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    elif backend == Backend.NANOBOT:
        return bool(os.environ.get("OPENAI_API_KEY"))
    elif backend in (Backend.OLLAMA, Backend.LOCAL):
        return True  # No API key needed for local!
    return False


class UnifiedExecutor:
    """
    Unified LLM executor that works with multiple backends.

    Features:
    - Auto-detects best available backend
    - Installs missing dependencies automatically
    - Falls back gracefully between backends
    - Consistent interface regardless of backend

    Example:
        # Auto-detect best backend
        executor = UnifiedExecutor()
        result = await executor.execute("Write a function")

        # Force specific backend
        executor = UnifiedExecutor(backend=Backend.OPENCLAW)

        # Connect to agents
        agent = DeveloperAgent()
        agent.set_executor(executor.execute)
    """

    def __init__(
        self,
        config: Optional[UnifiedConfig] = None,
        backend: Optional[Backend] = None,
        eager_init: bool = False
    ):
        self.config = config or UnifiedConfig()

        if backend:
            self.config.preferred_backend = backend

        self._executor = None
        self._active_backend: Optional[Backend] = None

        # Eagerly initialize if requested (useful to verify backend before execution)
        if eager_init:
            self._setup_executor()

    def _setup_executor(self):
        """Setup the appropriate executor based on config"""
        if self._executor is not None:
            return

        backend = self._select_backend()
        self._active_backend = backend

        if backend == Backend.OPENCLAW:
            self._executor = OpenClawExecutor(OpenClawConfig(
                model=self.config.openclaw_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ))
        elif backend == Backend.NANOBOT:
            self._executor = NanobotExecutor(NanobotConfig(
                model=self.config.nanobot_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ))
        elif backend in (Backend.OLLAMA, Backend.LOCAL):
            self._executor = OllamaExecutor(OllamaConfig(
                model=self.config.ollama_model,
                base_url=self.config.ollama_url,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ))
        else:
            raise RuntimeError("No LLM backend available")

    def _select_backend(self) -> Backend:
        """Select the best available backend"""
        preferred = self.config.preferred_backend

        # If specific backend requested
        if preferred != Backend.AUTO:
            if preferred == Backend.OPENCLAW:
                if not is_openclaw_installed() and self.config.auto_install:
                    print("🔧 Installing OpenClaw...")
                    install_openclaw()
                if not _has_api_key(Backend.OPENCLAW):
                    raise ValueError(
                        "ANTHROPIC_API_KEY not set. "
                        "Set it with: export ANTHROPIC_API_KEY=your-key"
                    )
                return Backend.OPENCLAW

            elif preferred == Backend.NANOBOT:
                if not is_nanobot_installed() and self.config.auto_install:
                    print("🔧 Installing Nanobot...")
                    install_nanobot()
                if not _has_api_key(Backend.NANOBOT):
                    raise ValueError(
                        "OPENAI_API_KEY not set. "
                        "Set it with: export OPENAI_API_KEY=your-key"
                    )
                return Backend.NANOBOT

            elif preferred in (Backend.OLLAMA, Backend.LOCAL):
                if not is_ollama_running():
                    raise ValueError(
                        "Ollama not running!\n"
                        "Start it with: ollama serve\n"
                        "Or install from: https://ollama.ai"
                    )
                return Backend.OLLAMA

        # Auto-detect: check what's ready to use
        ready = get_ready_backends()

        # Priority: Local (free!) > OpenClaw > Nanobot
        if Backend.OLLAMA in ready:
            print("🦙 Using Ollama (local, free!)")
            return Backend.OLLAMA
        elif Backend.OPENCLAW in ready:
            return Backend.OPENCLAW
        elif Backend.NANOBOT in ready:
            return Backend.NANOBOT

        # Try to install cloud backend if API key available
        if self.config.auto_install:
            if os.environ.get("ANTHROPIC_API_KEY"):
                print("🔧 Auto-installing OpenClaw (Anthropic API key detected)...")
                install_openclaw()
                return Backend.OPENCLAW
            elif os.environ.get("OPENAI_API_KEY"):
                print("🔧 Auto-installing Nanobot (OpenAI API key detected)...")
                install_nanobot()
                return Backend.NANOBOT

        raise RuntimeError(
            "No LLM backend available. Choose one:\n\n"
            "🦙 OPTION 1: FREE LOCAL (Ollama)\n"
            "   curl -fsSL https://ollama.ai/install.sh | sh\n"
            "   ollama serve\n"
            "   ollama pull llama3.2\n\n"
            "☁️  OPTION 2: Cloud API\n"
            "   export ANTHROPIC_API_KEY=sk-ant-...  # Claude\n"
            "   # or\n"
            "   export OPENAI_API_KEY=sk-...         # GPT\n"
        )

    @property
    def active_backend(self) -> Optional[Backend]:
        """Get the currently active backend"""
        return self._active_backend

    async def execute(self, prompt: str, context: Any = None) -> str:
        """
        Execute a prompt using the selected backend.

        Args:
            prompt: The prompt to send
            context: Optional context (for Agent compatibility)

        Returns:
            The LLM response text
        """
        self._setup_executor()
        return await self._executor.execute(prompt, context)

    def execute_sync(self, prompt: str) -> str:
        """
        Synchronous version of execute.

        Args:
            prompt: The prompt to send

        Returns:
            The LLM response text
        """
        self._setup_executor()
        return self._executor.execute_sync(prompt)

    def __repr__(self) -> str:
        backend = self._active_backend or "not initialized"
        return f"UnifiedExecutor(backend={backend})"


def auto_setup_executor(
    preferred: Literal["openclaw", "nanobot", "ollama", "local", "auto"] = "auto",
    eager_init: bool = True,
    **kwargs
) -> UnifiedExecutor:
    """
    Automatically setup the best available LLM executor.

    Args:
        preferred: Preferred backend ("openclaw", "nanobot", or "auto")
        eager_init: If True, initialize executor immediately (default: True)
        **kwargs: Additional configuration options

    Returns:
        Configured UnifiedExecutor

    Example:
        # Auto-detect (ready to use immediately)
        executor = auto_setup_executor()
        print(f"Using: {executor.active_backend}")  # Works immediately!

        # Prefer Claude
        executor = auto_setup_executor("openclaw")

        # Use with agents
        from orchestration import DeveloperAgent
        agent = DeveloperAgent()
        agent.set_executor(executor.execute)
    """
    backend_map = {
        "openclaw": Backend.OPENCLAW,
        "nanobot": Backend.NANOBOT,
        "ollama": Backend.OLLAMA,
        "local": Backend.LOCAL,
        "auto": Backend.AUTO,
    }

    backend = backend_map.get(preferred, Backend.AUTO)
    config = UnifiedConfig(preferred_backend=backend, **kwargs)

    return UnifiedExecutor(config, eager_init=eager_init)


def quick_start():
    """
    Print quick start guide for setting up LLM backends.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    🚀 AGENTICOM QUICK START                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🦙 OPTION 1: FREE LOCAL (No API key needed!)                    ║
║  ─────────────────────────────────────────────────────────────   ║
║  1. Install Ollama:                                              ║
║     curl -fsSL https://ollama.ai/install.sh | sh                 ║
║  2. Start server:                                                ║
║     ollama serve                                                 ║
║  3. Pull a model:                                                ║
║     ollama pull llama3.2                                         ║
║  4. Run Agenticom - it auto-detects Ollama!                      ║
║                                                                  ║
║  ☁️  OPTION 2: Cloud APIs (Higher quality, requires key)         ║
║  ─────────────────────────────────────────────────────────────   ║
║  For Claude (OpenClaw):                                          ║
║    export ANTHROPIC_API_KEY=sk-ant-your-key-here                 ║
║                                                                  ║
║  For GPT (Nanobot):                                              ║
║    export OPENAI_API_KEY=sk-your-key-here                        ║
║                                                                  ║
║  🎯 RUN AGENTICOM                                                ║
║  ─────────────────────────────────────────────────────────────   ║
║  GUI:      agenticom-launch                                      ║
║  CLI:      agentic create   (Easy workflow builder)              ║
║  Test:     agentic health   (Check your setup)                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    quick_start()
