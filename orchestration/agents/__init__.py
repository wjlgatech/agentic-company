"""
Multi-Agent Team Orchestration

Provides specialized agent roles that work together in coordinated workflows
with cross-verification and fresh context per step.
"""

from orchestration.agents.base import Agent, AgentRole, AgentConfig
from orchestration.agents.team import AgentTeam, TeamConfig, TeamResult
from orchestration.agents.specialized import (
    PlannerAgent,
    DeveloperAgent,
    VerifierAgent,
    TesterAgent,
    ReviewerAgent,
)

__all__ = [
    # Base
    "Agent",
    "AgentRole",
    "AgentConfig",
    # Team
    "AgentTeam",
    "TeamConfig",
    "TeamResult",
    # Specialized Agents
    "PlannerAgent",
    "DeveloperAgent",
    "VerifierAgent",
    "TesterAgent",
    "ReviewerAgent",
]
