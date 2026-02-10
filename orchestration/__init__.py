"""
EpiLoop - AI Agent Orchestration System

A comprehensive framework for building production-ready AI agent workflows
with guardrails, memory, observability, and approval gates.
"""

from orchestration._version import __version__
from orchestration.config import OrchestratorConfig, get_config
from orchestration.guardrails import (
    GuardrailResult,
    ContentFilter,
    RelevanceGuardrail,
    RateLimiter,
    GuardrailPipeline,
)
from orchestration.evaluator import (
    EvaluationResult,
    RuleBasedEvaluator,
    LLMEvaluator,
    EvaluatorOptimizer,
)
from orchestration.memory import (
    MemoryEntry,
    MemoryStore,
    LocalMemoryStore,
)
from orchestration.approval import (
    ApprovalRequest,
    ApprovalGate,
    AutoApprovalGate,
    HumanApprovalGate,
)
from orchestration.observability import (
    MetricsCollector,
    Tracer,
    Logger,
    ObservabilityStack,
)
from orchestration.pipeline import Pipeline, PipelineStep

__all__ = [
    # Version
    "__version__",
    # Config
    "OrchestratorConfig",
    "get_config",
    # Guardrails
    "GuardrailResult",
    "ContentFilter",
    "RelevanceGuardrail",
    "RateLimiter",
    "GuardrailPipeline",
    # Evaluator
    "EvaluationResult",
    "RuleBasedEvaluator",
    "LLMEvaluator",
    "EvaluatorOptimizer",
    # Memory
    "MemoryEntry",
    "MemoryStore",
    "LocalMemoryStore",
    # Approval
    "ApprovalRequest",
    "ApprovalGate",
    "AutoApprovalGate",
    "HumanApprovalGate",
    # Observability
    "MetricsCollector",
    "Tracer",
    "Logger",
    "ObservabilityStack",
    # Pipeline
    "Pipeline",
    "PipelineStep",
]
