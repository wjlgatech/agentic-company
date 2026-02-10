"""
Unified LLM Executor

Provides a unified interface for multiple LLM backends.
Automatically detects, installs, and configures the best available option.
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


class Backend(Enum):
    """Available LLM backends"""
    OPENCLAW = "openclaw"  # Anthropic Claude
    NANOBOT = "nanobot"    # OpenAI GPT
    AUTO = "auto"          # Auto-detect best available


@dataclass
class UnifiedConfig:
    """Configuration for unified executor"""
    preferred_backend: Backend = Backend.AUTO
    openclaw_model: str = "claude-3-5-sonnet-20241022"
    nanobot_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    temperature: float = 0.7
    auto_install: bool = True  # Auto-install missing backends


def get_available_backends() -> list[Backend]:
    """
    Get list of available (installed) backends.

    Returns:
        List of available Backend enums
    """
    available = []

    if is_openclaw_installed():
        available.append(Backend.OPENCLAW)

    if is_nanobot_installed():
        available.append(Backend.NANOBOT)

    return available


def _has_api_key(backend: Backend) -> bool:
    """Check if API key is available for backend"""
    if backend == Backend.OPENCLAW:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    elif backend == Backend.NANOBOT:
        return bool(os.environ.get("OPENAI_API_KEY"))
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
        backend: Optional[Backend] = None
    ):
        self.config = config or UnifiedConfig()

        if backend:
            self.config.preferred_backend = backend

        self._executor = None
        self._active_backend: Optional[Backend] = None

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

        # Auto-detect: prefer OpenClaw (Claude) if available
        available = get_available_backends()

        # Check which ones have API keys
        ready_backends = [b for b in available if _has_api_key(b)]

        if Backend.OPENCLAW in ready_backends:
            return Backend.OPENCLAW
        elif Backend.NANOBOT in ready_backends:
            return Backend.NANOBOT

        # Try to install one
        if self.config.auto_install:
            # Prefer OpenClaw
            if os.environ.get("ANTHROPIC_API_KEY"):
                print("🔧 Auto-installing OpenClaw (Anthropic API key detected)...")
                install_openclaw()
                return Backend.OPENCLAW
            elif os.environ.get("OPENAI_API_KEY"):
                print("🔧 Auto-installing Nanobot (OpenAI API key detected)...")
                install_nanobot()
                return Backend.NANOBOT

        raise RuntimeError(
            "No LLM backend available. Please either:\n"
            "1. Set ANTHROPIC_API_KEY for OpenClaw (Claude)\n"
            "2. Set OPENAI_API_KEY for Nanobot (GPT)\n"
            "\nExample:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  # or\n"
            "  export OPENAI_API_KEY=sk-..."
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
    preferred: Literal["openclaw", "nanobot", "auto"] = "auto",
    **kwargs
) -> UnifiedExecutor:
    """
    Automatically setup the best available LLM executor.

    Args:
        preferred: Preferred backend ("openclaw", "nanobot", or "auto")
        **kwargs: Additional configuration options

    Returns:
        Configured UnifiedExecutor

    Example:
        # Auto-detect
        executor = auto_setup_executor()

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
        "auto": Backend.AUTO,
    }

    backend = backend_map.get(preferred, Backend.AUTO)
    config = UnifiedConfig(preferred_backend=backend, **kwargs)

    return UnifiedExecutor(config)


def quick_start():
    """
    Print quick start guide for setting up LLM backends.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    🚀 AGENTICOM QUICK START                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Step 1: Set your API key                                        ║
║  ─────────────────────────────────────────────────────────────   ║
║                                                                  ║
║  For Claude (OpenClaw):                                          ║
║    export ANTHROPIC_API_KEY=sk-ant-your-key-here                 ║
║                                                                  ║
║  For GPT (Nanobot):                                              ║
║    export OPENAI_API_KEY=sk-your-key-here                        ║
║                                                                  ║
║  Step 2: Run Agenticom                                           ║
║  ─────────────────────────────────────────────────────────────   ║
║                                                                  ║
║  Quick test:                                                     ║
║    python -c "from orchestration import auto_setup_executor;     ║
║    e = auto_setup_executor(); print(e.execute_sync('Hello!'))"   ║
║                                                                  ║
║  Start web interface:                                            ║
║    agenticom-launch                                              ║
║                                                                  ║
║  Or use the desktop icon!                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    quick_start()
