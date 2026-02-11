"""
Agenticom - Multi-Agent Team Orchestration for OpenClaw/Claude Code

Following the antfarm pattern:
- YAML workflow definitions
- SQLite state persistence
- Fresh context per agent step
- Cross-agent verification
- Simple CLI: agenticom install, agenticom run, etc.
"""

__version__ = "1.0.0"

from .core import AgenticomCore
from .workflows import WorkflowRunner, WorkflowDefinition
from .state import StateManager

__all__ = ["AgenticomCore", "WorkflowRunner", "WorkflowDefinition", "StateManager", "__version__"]
