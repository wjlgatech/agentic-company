"""
Agentic Company - AI Agent Orchestration System

A comprehensive framework for building production-ready AI agent workflows
with multi-agent teams, guardrails, memory, observability, and approval gates.

Inspired by Antfarm's elegant simplicity + production-grade safety.
"""

from orchestration._version import __version__

# Multi-Agent Teams (inspired by Antfarm)
from orchestration.agents import (
    Agent,
    AgentConfig,
    AgentRole,
    AgentTeam,
    DeveloperAgent,
    PlannerAgent,
    ReviewerAgent,
    TeamConfig,
    TeamResult,
    TesterAgent,
    VerifierAgent,
)
from orchestration.agents.team import (
    TeamBuilder,
    WorkflowStep,
    create_bug_fix_team,
    create_feature_dev_team,
    create_security_audit_team,
)
from orchestration.approval import (
    ApprovalGate,
    ApprovalRequest,
    AutoApprovalGate,
    HumanApprovalGate,
)
from orchestration.config import OrchestratorConfig, get_config

# Conversational Workflow Builder (Easy Mode)
from orchestration.conversation import (
    ConversationBuilder,
    Question,
    QuestionType,
    run_conversation,
)
from orchestration.evaluator import (
    EvaluationResult,
    EvaluatorOptimizer,
    LLMEvaluator,
    RuleBasedEvaluator,
)
from orchestration.guardrails import (
    ContentFilter,
    GuardrailPipeline,
    GuardrailResult,
    RateLimiter,
    RelevanceGuardrail,
)

# LLM Integrations (OpenClaw + Nanobot)
from orchestration.integrations import (
    NanobotExecutor,
    OpenClawExecutor,
    UnifiedExecutor,
    auto_setup_executor,
    get_available_backends,
)
from orchestration.memory import (
    LocalMemoryStore,
    MemoryEntry,
    MemoryStore,
)
from orchestration.observability import (
    Logger,
    MetricsCollector,
    ObservabilityStack,
    Tracer,
)
from orchestration.pipeline import Pipeline, PipelineStep

# YAML Workflow Definitions
from orchestration.workflows import (
    WorkflowDefinition,
    WorkflowParser,
    init_workflow,
    load_ready_workflow,  # NEW: Ready-to-run workflow loading
    load_workflow,
    load_workflows_from_directory,
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
    "load_ready_workflow",
    "load_workflows_from_directory",
    "init_workflow",
    # LLM Integrations
    "OpenClawExecutor",
    "NanobotExecutor",
    "UnifiedExecutor",
    "auto_setup_executor",
    "get_available_backends",
    # Conversational Builder (Easy Mode)
    "ConversationBuilder",
    "Question",
    "QuestionType",
    "run_conversation",
]
