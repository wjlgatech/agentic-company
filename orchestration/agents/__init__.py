"""
Multi-Agent Team Orchestration

Provides specialized agent roles that work together in coordinated workflows
with cross-verification and fresh context per step.
"""

from orchestration.agents.base import Agent, AgentConfig, AgentRole
from orchestration.agents.specialized import (
    DeveloperAgent,
    PlannerAgent,
    ReviewerAgent,
    TesterAgent,
    VerifierAgent,
)
from orchestration.agents.team import AgentTeam, TeamConfig, TeamResult

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
