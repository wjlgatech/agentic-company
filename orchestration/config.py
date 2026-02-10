"""
Configuration management for EpiLoop.

Supports environment variables, .env files, and YAML configuration.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: Optional[str] = None


@dataclass
class GuardrailsConfig:
    """Guardrails configuration."""

    enabled: bool = True
    content_filter_enabled: bool = True
    blocked_topics: list[str] = field(default_factory=lambda: ["harmful", "illegal"])
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    relevance_threshold: float = 0.7


@dataclass
class MemoryConfig:
    """Memory system configuration."""

    backend: str = "local"  # local, supabase, redis, postgres
    max_entries: int = 1000
    ttl_seconds: int = 86400  # 24 hours
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    redis_url: Optional[str] = None
    database_url: Optional[str] = None


@dataclass
class ServerConfig:
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    debug: bool = False
    reload: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class ObservabilityConfig:
    """Observability configuration."""

    tracing_enabled: bool = True
    metrics_enabled: bool = True
    logging_enabled: bool = True
    log_level: str = "INFO"
    otlp_endpoint: Optional[str] = None
    prometheus_port: int = 9090


@dataclass
class CeleryConfig:
    """Celery task queue configuration."""

    enabled: bool = False
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    task_timeout: int = 300


@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    celery: CeleryConfig = field(default_factory=CeleryConfig)

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "anthropic"),
                model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
            ),
            guardrails=GuardrailsConfig(
                enabled=os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true",
                max_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
            ),
            memory=MemoryConfig(
                backend=os.getenv("MEMORY_BACKEND", "local"),
                supabase_url=os.getenv("SUPABASE_URL"),
                supabase_key=os.getenv("SUPABASE_KEY"),
                redis_url=os.getenv("REDIS_URL"),
                database_url=os.getenv("DATABASE_URL"),
            ),
            server=ServerConfig(
                host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "8000")),
                workers=int(os.getenv("WORKERS", "4")),
                debug=os.getenv("DEBUG", "false").lower() == "true",
            ),
            observability=ObservabilityConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            ),
            celery=CeleryConfig(
                enabled=os.getenv("CELERY_ENABLED", "false").lower() == "true",
                broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
            ),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "OrchestratorConfig":
        """Create configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "OrchestratorConfig":
        """Create configuration from dictionary."""
        return cls(
            llm=LLMConfig(**data.get("llm", {})),
            guardrails=GuardrailsConfig(**data.get("guardrails", {})),
            memory=MemoryConfig(**data.get("memory", {})),
            server=ServerConfig(**data.get("server", {})),
            observability=ObservabilityConfig(**data.get("observability", {})),
            celery=CeleryConfig(**data.get("celery", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
            },
            "guardrails": {
                "enabled": self.guardrails.enabled,
                "content_filter_enabled": self.guardrails.content_filter_enabled,
                "rate_limit_enabled": self.guardrails.rate_limit_enabled,
                "max_requests_per_minute": self.guardrails.max_requests_per_minute,
            },
            "memory": {
                "backend": self.memory.backend,
                "max_entries": self.memory.max_entries,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
                "debug": self.server.debug,
            },
            "observability": {
                "log_level": self.observability.log_level,
                "tracing_enabled": self.observability.tracing_enabled,
                "metrics_enabled": self.observability.metrics_enabled,
            },
        }


# Global config instance
_config: Optional[OrchestratorConfig] = None


def get_config() -> OrchestratorConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        # Try to load from config file first, then fall back to env
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            _config = OrchestratorConfig.from_yaml(config_path)
        else:
            _config = OrchestratorConfig.from_env()
    return _config


def set_config(config: OrchestratorConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def validate_config(config: OrchestratorConfig) -> list[str]:
    """Validate configuration and return list of errors."""
    errors = []

    # Check API key
    if not config.llm.api_key:
        if config.llm.provider == "anthropic":
            errors.append("ANTHROPIC_API_KEY is not set")
        elif config.llm.provider == "openai":
            errors.append("OPENAI_API_KEY is not set")

    # Check memory backend requirements
    if config.memory.backend == "supabase":
        if not config.memory.supabase_url:
            errors.append("SUPABASE_URL is required for supabase backend")
        if not config.memory.supabase_key:
            errors.append("SUPABASE_KEY is required for supabase backend")
    elif config.memory.backend == "redis":
        if not config.memory.redis_url:
            errors.append("REDIS_URL is required for redis backend")
    elif config.memory.backend == "postgres":
        if not config.memory.database_url:
            errors.append("DATABASE_URL is required for postgres backend")

    # Check Celery requirements
    if config.celery.enabled:
        if not config.celery.broker_url:
            errors.append("CELERY_BROKER_URL is required when Celery is enabled")

    # Check port validity
    if not (1 <= config.server.port <= 65535):
        errors.append(f"Invalid port number: {config.server.port}")

    return errors
