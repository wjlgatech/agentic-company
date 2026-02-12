"""
OpenClaw Integration

Provides seamless integration with OpenClaw for LLM execution.
Handles automatic installation if OpenClaw is not present.
"""

import subprocess
import sys
import os
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class OpenClawConfig:
    """Configuration for OpenClaw"""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: Optional[str] = None  # Uses ANTHROPIC_API_KEY env var if not set


def is_openclaw_installed() -> bool:
    """Check if OpenClaw is installed"""
    try:
        import anthropic
        return True
    except ImportError:
        return False


def install_openclaw(quiet: bool = False) -> bool:
    """
    Install OpenClaw (anthropic SDK) automatically.

    Args:
        quiet: If True, suppress output

    Returns:
        True if installation successful
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install", "anthropic>=0.30.0"]
        if quiet:
            cmd.append("-q")

        result = subprocess.run(cmd, capture_output=quiet, text=True)
        return result.returncode == 0
    except Exception as e:
        if not quiet:
            print(f"Failed to install OpenClaw: {e}")
        return False


class OpenClawExecutor:
    """
    Execute LLM calls using OpenClaw (Anthropic SDK).

    Example:
        executor = OpenClawExecutor()
        result = await executor.execute("Write a Python function")
    """

    def __init__(self, config: Optional[OpenClawConfig] = None):
        self.config = config or OpenClawConfig()
        self._client = None
        self._ensure_installed()

    def _ensure_installed(self):
        """Ensure OpenClaw is installed, install if not"""
        if not is_openclaw_installed():
            print("🔧 OpenClaw not found. Installing automatically...")
            if install_openclaw():
                print("✅ OpenClaw installed successfully!")
            else:
                raise RuntimeError(
                    "Failed to install OpenClaw. Please install manually: "
                    "pip install anthropic"
                )

    def _get_client(self):
        """Get or create Anthropic client"""
        if self._client is None:
            import anthropic

            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Please set the environment variable "
                    "or pass api_key in OpenClawConfig."
                )

            self._client = anthropic.Anthropic(api_key=api_key)

        return self._client

    async def execute(self, prompt: str, context: Any = None) -> str:
        """
        Execute a prompt using OpenClaw.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context (for compatibility with Agent interface)

        Returns:
            The LLM response text
        """
        import asyncio

        # Run in thread pool since anthropic SDK is sync
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_sync, prompt)

    def _execute_sync(self, prompt: str) -> str:
        """Synchronous execution"""
        client = self._get_client()

        message = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def execute_sync(self, prompt: str) -> str:
        """
        Synchronous version of execute.

        Args:
            prompt: The prompt to send

        Returns:
            The LLM response text
        """
        return self._execute_sync(prompt)

    def __repr__(self) -> str:
        return f"OpenClawExecutor(model={self.config.model})"


def create_openclaw_executor(
    model: str = "claude-sonnet-4-20250514",
    api_key: Optional[str] = None,
    **kwargs
) -> OpenClawExecutor:
    """
    Factory function to create OpenClaw executor.

    Args:
        model: The Claude model to use
        api_key: Optional API key (uses env var if not provided)
        **kwargs: Additional config options

    Returns:
        Configured OpenClawExecutor
    """
    config = OpenClawConfig(
        model=model,
        api_key=api_key,
        **kwargs
    )
    return OpenClawExecutor(config)
