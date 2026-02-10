"""
Agentic Company - AI Agent Orchestration System

A comprehensive framework for building production-ready AI agent workflows
with multi-agent teams, guardrails, memory, observability, and approval gates.

Inspired by Antfarm's elegant simplicity + production-grade safety.
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

# Multi-Agent Teams (inspired by Antfarm)
from orchestration.agents import (
    Agent,
    AgentRole,
    AgentConfig,
    AgentTeam,
    TeamConfig,
    TeamResult,
    PlannerAgent,
    DeveloperAgent,
    VerifierAgent,
    TesterAgent,
    ReviewerAgent,
)
from orchestration.agents.team import (
    TeamBuilder,
    WorkflowStep,
    create_feature_dev_team,
    create_bug_fix_team,
    create_security_audit_team,
)

# YAML Workflow Definitions
from orchestration.workflows import (
    WorkflowDefinition,
    WorkflowParser,
    load_workflow,
    load_workflows_from_directory,
    init_workflow,
)

# LLM Integrations (OpenClaw + Nanobot)
from orchestration.integrations import (
    OpenClawExecutor,
    NanobotExecutor,
    UnifiedExecutor,
    auto_setup_executor,
    get_available_backends,
)

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
    # Multi-Agent Teams
    "Agent",
    "AgentRole",
    "AgentConfig",
    "AgentTeam",
    "TeamConfig",
    "TeamResult",
    "TeamBuilder",
    "WorkflowStep",
    "PlannerAgent",
    "DeveloperAgent",
    "VerifierAgent",
    "TesterAgent",
    "ReviewerAgent",
    "create_feature_dev_team",
    "create_bug_fix_team",
    "create_security_audit_team",
    # YAML Workflows
    "WorkflowDefinition",
    "WorkflowParser",
    "load_workflow",
    "load_workflows_from_directory",
    "init_workflow",
    # LLM Integrations
    "OpenClawExecutor",
    "NanobotExecutor",
    "UnifiedExecutor",
    "auto_setup_executor",
    "get_available_backends",
]
