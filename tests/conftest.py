"""
Pytest configuration and shared fixtures.

collect_ignore: script-style files moved from the repo root that were never
part of the automated test suite. They require real LLM API keys, Playwright
browsers, or hardcoded machine paths, so they are excluded from CI collection.
Run them manually when needed:

    python tests/test_complete_integration.py
    python tests/test_phase4_meta_analysis_additional.py
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

collect_ignore = [
    "test_complete_integration.py",
    "test_phase3_retry.py",
    "test_phase3_workflow.py",
    "test_phase4_meta_analysis_additional.py",
    "test_real_cases.py",
    "test_stage_tracking.py",
]


@pytest.fixture
def tmp_artifact_dir(tmp_path: Path) -> Path:
    """Temporary directory for artifact storage in tests."""
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    return artifact_dir


@pytest.fixture
def mock_executor() -> AsyncMock:
    """
    AsyncMock LLM executor compatible with agent.set_executor().

    Signature: async (prompt: str, context) -> str
    Returns a standard string response for any prompt.
    """
    return AsyncMock(return_value="Mock LLM response: task completed successfully.")


@pytest.fixture
def api_client():
    """FastAPI TestClient for orchestration.api (function-scoped)."""
    from fastapi.testclient import TestClient

    from orchestration.api import app

    return TestClient(app)


@pytest.fixture
def sample_workflow_yaml() -> str:
    """Minimal inline workflow YAML for tests that need a parseable workflow."""
    return """
id: sample-workflow
name: Sample Workflow
description: Minimal two-step workflow for testing
agents:
  - id: planner
    name: Planner
    role: planner
  - id: developer
    name: Developer
    role: developer
steps:
  - id: plan
    agent: planner
    input: "{{task}}"
    expects: "STATUS: done"
  - id: implement
    agent: developer
    input: "Based on plan: {{step_outputs.plan}}"
    expects: "STATUS: done"
"""
