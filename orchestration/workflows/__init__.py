"""
YAML Workflow Definitions

Parse and execute workflows defined in YAML files.
Inspired by Antfarm's simple, readable workflow format.
"""

from orchestration.workflows.parser import (
    WorkflowDefinition,
    WorkflowParser,
    load_ready_workflow,  # Ready-to-run workflow loading
    load_workflow,
    load_workflows_from_directory,
)
from orchestration.workflows.templates import (
    BUG_FIX_TEMPLATE,
    FEATURE_DEV_TEMPLATE,
    SECURITY_AUDIT_TEMPLATE,
    init_workflow,
)

__all__ = [
    # Parser
    "WorkflowDefinition",
    "WorkflowParser",
    "load_workflow",
    "load_ready_workflow",  # NEW: Recommended for execution
    "load_workflows_from_directory",
    # Templates
    "FEATURE_DEV_TEMPLATE",
    "BUG_FIX_TEMPLATE",
    "SECURITY_AUDIT_TEMPLATE",
    "init_workflow",
]
