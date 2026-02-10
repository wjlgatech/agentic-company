"""
YAML Workflow Definitions

Parse and execute workflows defined in YAML files.
Inspired by Antfarm's simple, readable workflow format.
"""

from orchestration.workflows.parser import (
    WorkflowDefinition,
    WorkflowParser,
    load_workflow,
    load_workflows_from_directory,
)
from orchestration.workflows.templates import (
    FEATURE_DEV_TEMPLATE,
    BUG_FIX_TEMPLATE,
    SECURITY_AUDIT_TEMPLATE,
    init_workflow,
)

__all__ = [
    # Parser
    "WorkflowDefinition",
    "WorkflowParser",
    "load_workflow",
    "load_workflows_from_directory",
    # Templates
    "FEATURE_DEV_TEMPLATE",
    "BUG_FIX_TEMPLATE",
    "SECURITY_AUDIT_TEMPLATE",
    "init_workflow",
]
