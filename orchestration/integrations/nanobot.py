"""
Nanobot Integration

Provides seamless integration with Nanobot for LLM execution.
Handles automatic installation if Nanobot is not present.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class NanobotConfig:
    """Configuration for Nanobot"""

    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: str | None = None  # Uses OPENAI_API_KEY env var if not set
    base_url: str | None = None  # For custom endpoints


def is_nanobot_installed() -> bool:
    """Check if Nanobot (OpenAI SDK) is installed"""
    try:
        import openai

        return True
    except ImportError:
        return False


def install_nanobot(quiet: bool = False) -> bool:
    """
    Install Nanobot (OpenAI SDK) automatically.

    Args:
        quiet: If True, suppress output

    Returns:
        True if installation successful
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install", "openai>=1.0.0"]
        if quiet:
            cmd.append("-q")

        result = subprocess.run(cmd, capture_output=quiet, text=True)
        return result.returncode == 0
    except Exception as e:
        if not quiet:
            print(f"Failed to install Nanobot: {e}")
        return False


class NanobotExecutor:
    """
    Execute LLM calls using Nanobot (OpenAI SDK).

    Example:
        executor = NanobotExecutor()
        result = await executor.execute("Write a Python function")
    """

    def __init__(self, config: NanobotConfig | None = None):
        self.config = config or NanobotConfig()
        self._client = None
        self._ensure_installed()

    def _ensure_installed(self):
        """Ensure Nanobot is installed, install if not"""
        if not is_nanobot_installed():
            print("🔧 Nanobot not found. Installing automatically...")
            if install_nanobot():
                print("✅ Nanobot installed successfully!")
            else:
                raise RuntimeError(
                    "Failed to install Nanobot. Please install manually: "
                    "pip install openai"
                )

    def _get_client(self):
        """Get or create OpenAI client"""
        if self._client is None:
            import openai

            api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Please set the environment variable "
                    "or pass api_key in NanobotConfig."
                )

            kwargs = {"api_key": api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url

            self._client = openai.OpenAI(**kwargs)

        return self._client

    async def execute(self, prompt: str, context: Any = None) -> str:
        """
        Execute a prompt using Nanobot.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context (for compatibility with Agent interface)

        Returns:
            The LLM response text
        """
        import asyncio

        # Run in thread pool since openai SDK is sync by default
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_sync, prompt)

    def _execute_sync(self, prompt: str) -> str:
        """Synchronous execution"""
        client = self._get_client()

        response = client.chat.completions.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

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
        return f"NanobotExecutor(model={self.config.model})"


class NanobotAsyncExecutor:
    """
    Async-native Nanobot executor using AsyncOpenAI.

    Example:
        executor = NanobotAsyncExecutor()
        result = await executor.execute("Write a Python function")
    """

    def __init__(self, config: NanobotConfig | None = None):
        self.config = config or NanobotConfig()
        self._client = None
        self._ensure_installed()

    def _ensure_installed(self):
        """Ensure Nanobot is installed"""
        if not is_nanobot_installed():
            print("🔧 Nanobot not found. Installing automatically...")
            if install_nanobot():
                print("✅ Nanobot installed successfully!")
            else:
                raise RuntimeError("Failed to install Nanobot")

    def _get_client(self):
        """Get or create AsyncOpenAI client"""
        if self._client is None:
            import openai

            api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            kwargs = {"api_key": api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url

            self._client = openai.AsyncOpenAI(**kwargs)

        return self._client

    async def execute(self, prompt: str, context: Any = None) -> str:
        """Execute a prompt using async Nanobot"""
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


def create_nanobot_executor(
    model: str = "gpt-4-turbo-preview",
    api_key: str | None = None,
    async_mode: bool = False,
    **kwargs,
) -> NanobotExecutor:
    """
    Factory function to create Nanobot executor.

    Args:
        model: The GPT model to use
        api_key: Optional API key (uses env var if not provided)
        async_mode: If True, return async-native executor
        **kwargs: Additional config options

    Returns:
        Configured NanobotExecutor
    """
    config = NanobotConfig(model=model, api_key=api_key, **kwargs)

    if async_mode:
        return NanobotAsyncExecutor(config)
    return NanobotExecutor(config)
