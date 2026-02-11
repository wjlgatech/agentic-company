"""
Ollama Integration - Run Agenticom 100% Locally

Provides seamless integration with Ollama for local LLM execution.
No API keys needed! No data leaves your machine!

Supports:
- Ollama (ollama.ai)
- LM Studio (lmstudio.ai)
- LocalAI
- Any OpenAI-compatible local server
"""

import subprocess
import sys
import os
import httpx
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Configuration for Ollama/local LLM"""
    model: str = "llama3.2"  # Default model
    base_url: str = "http://localhost:11434"  # Ollama default
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120  # Local models can be slow


# Popular local models
RECOMMENDED_MODELS = {
    "fast": "llama3.2:1b",       # Fast, small, good for simple tasks
    "balanced": "llama3.2",      # Good balance of speed and quality
    "quality": "llama3.1:8b",    # High quality, slower
    "coding": "codellama:7b",    # Specialized for code
    "tiny": "tinyllama",         # Ultra-fast, minimal resources
}


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running"""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_ollama_installed() -> bool:
    """Check if Ollama CLI is installed"""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_available_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Get list of locally available models"""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def pull_model(model: str, quiet: bool = False) -> bool:
    """Pull/download a model using Ollama CLI"""
    try:
        cmd = ["ollama", "pull", model]
        if quiet:
            result = subprocess.run(cmd, capture_output=True, text=True)
        else:
            print(f"📥 Downloading {model}... (this may take a few minutes)")
            result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        if not quiet:
            print(f"❌ Failed to pull model: {e}")
        return False


def install_ollama_instructions() -> str:
    """Return installation instructions for Ollama"""
    return """
╔══════════════════════════════════════════════════════════════════╗
║                 🦙 INSTALL OLLAMA (FREE & LOCAL)                 ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  macOS:    curl -fsSL https://ollama.ai/install.sh | sh          ║
║  Linux:    curl -fsSL https://ollama.ai/install.sh | sh          ║
║  Windows:  Download from https://ollama.ai/download              ║
║                                                                  ║
║  After installing:                                               ║
║    1. Run: ollama serve                                          ║
║    2. Pull a model: ollama pull llama3.2                         ║
║    3. You're ready! No API key needed!                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


class OllamaExecutor:
    """
    Execute LLM calls using Ollama (local models).

    100% FREE. 100% PRIVATE. No API keys!

    Example:
        executor = OllamaExecutor()
        result = await executor.execute("Write a Python function")

    Works with:
        - Ollama (ollama.ai)
        - LM Studio (use base_url="http://localhost:1234/v1")
        - LocalAI (use base_url="http://localhost:8080/v1")
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._client = None

    def _ensure_running(self):
        """Check if Ollama is running, provide helpful message if not"""
        if not is_ollama_running(self.config.base_url):
            # Check if it's LM Studio or similar
            if "1234" in self.config.base_url:
                raise RuntimeError(
                    "LM Studio not running! Start LM Studio and load a model, "
                    "then enable the local server."
                )
            raise RuntimeError(
                "Ollama not running!\n\n"
                "Start it with: ollama serve\n\n"
                f"{install_ollama_instructions()}"
            )

    def _ensure_model(self):
        """Ensure the model is available, pull if not"""
        available = get_available_models(self.config.base_url)
        model_name = self.config.model.split(":")[0]  # Handle tags

        if not any(model_name in m for m in available):
            print(f"⚠️ Model '{self.config.model}' not found locally.")
            print(f"📥 Pulling model... (one-time download)")
            if not pull_model(self.config.model):
                raise RuntimeError(
                    f"Failed to pull model '{self.config.model}'.\n"
                    f"Available models: {available}\n"
                    f"Pull manually with: ollama pull {self.config.model}"
                )

    async def execute(self, prompt: str, context: Any = None) -> str:
        """
        Execute a prompt using Ollama.

        Args:
            prompt: The prompt to send
            context: Optional context (for Agent compatibility)

        Returns:
            The LLM response text
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_sync, prompt)

    def _execute_sync(self, prompt: str) -> str:
        """Synchronous execution"""
        self._ensure_running()
        self._ensure_model()

        # Use Ollama's native API
        response = httpx.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                }
            },
            timeout=self.config.timeout
        )

        if response.status_code != 200:
            raise RuntimeError(f"Ollama error: {response.text}")

        return response.json()["response"]

    def execute_sync(self, prompt: str) -> str:
        """Synchronous version of execute"""
        return self._execute_sync(prompt)

    def __repr__(self) -> str:
        return f"OllamaExecutor(model={self.config.model})"


class LMStudioExecutor(OllamaExecutor):
    """
    Execute LLM calls using LM Studio.

    LM Studio provides an OpenAI-compatible API at localhost:1234.

    Example:
        executor = LMStudioExecutor()
        result = await executor.execute("Write a Python function")
    """

    def __init__(self, model: str = "local-model"):
        config = OllamaConfig(
            model=model,
            base_url="http://localhost:1234/v1"
        )
        super().__init__(config)

    def _execute_sync(self, prompt: str) -> str:
        """Use OpenAI-compatible API for LM Studio"""
        response = httpx.post(
            f"{self.config.base_url}/chat/completions",
            json={
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
            timeout=self.config.timeout
        )

        if response.status_code != 200:
            raise RuntimeError(f"LM Studio error: {response.text}")

        return response.json()["choices"][0]["message"]["content"]


def create_ollama_executor(
    model: str = "llama3.2",
    base_url: str = "http://localhost:11434",
    **kwargs
) -> OllamaExecutor:
    """
    Factory function to create Ollama executor.

    Args:
        model: Model name (default: llama3.2)
        base_url: Ollama server URL
        **kwargs: Additional config options

    Returns:
        Configured OllamaExecutor
    """
    config = OllamaConfig(model=model, base_url=base_url, **kwargs)
    return OllamaExecutor(config)


def quick_setup_local():
    """Interactive setup for local LLM"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              🦙 LOCAL LLM SETUP (100% FREE & PRIVATE)            ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Check Ollama
    if is_ollama_running():
        print("✅ Ollama is running!")
        models = get_available_models()
        if models:
            print(f"   Available models: {', '.join(models[:5])}")
        else:
            print("   No models installed yet.")
            print("   Recommended: ollama pull llama3.2")
        return True

    if is_ollama_installed():
        print("⚠️ Ollama is installed but not running.")
        print("   Start it with: ollama serve")
        return False

    print("❌ Ollama not found.")
    print(install_ollama_instructions())
    return False


if __name__ == "__main__":
    quick_setup_local()
