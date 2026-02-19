"""
CLI tests for agenticom/cli.py (the `agenticom` CLI entry point).

Covers:
- Help text discoverability (--help on all levels)
- workflow list: empty state, with workflows, counts displayed
- workflow run: unknown ID error, dry-run plan, invalid JSON context, success output
- workflow status: not-found error, details displayed, --json flag
- workflow inspect: not-found error
- install: reports installed count and errors
- uninstall: requires --force flag
- UX checks: human-readable output, no raw dicts, exit codes, no stack traces
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agenticom.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_core():
    """MagicMock AgenticomCore with sensible defaults."""
    core = MagicMock()
    core.home = "/tmp/test-agenticom"
    return core


# ---------------------------------------------------------------------------
# Top-level --help
# ---------------------------------------------------------------------------


class TestHelpText:
    def test_top_level_help_exit_code_0(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_top_level_help_mentions_workflow(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "workflow" in result.output.lower()

    def test_workflow_subgroup_help_lists_subcommands(self, runner):
        result = runner.invoke(cli, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "run" in result.output
        assert "status" in result.output
        assert "inspect" in result.output

    def test_version_flag_shows_version_number(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert any(c.isdigit() for c in result.output)


# ---------------------------------------------------------------------------
# workflow list
# ---------------------------------------------------------------------------


class TestWorkflowList:
    def test_list_empty_shows_no_workflows_message(self, runner, mock_core):
        mock_core.list_workflows.return_value = []
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "list"])
        assert result.exit_code == 0
        assert "No workflows installed" in result.output

    def test_list_empty_hints_install_command(self, runner, mock_core):
        mock_core.list_workflows.return_value = []
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "list"])
        assert "install" in result.output.lower()

    def test_list_shows_workflow_ids(self, runner, mock_core):
        mock_core.list_workflows.return_value = [
            {
                "id": "feature-dev",
                "name": "Feature Dev Team",
                "description": "Plan and build code",
                "agents": 5,
                "steps": 5,
            },
            {
                "id": "due-diligence",
                "name": "Due Diligence",
                "description": "M&A analysis",
                "agents": 4,
                "steps": 4,
            },
        ]
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "list"])
        assert result.exit_code == 0
        assert "feature-dev" in result.output
        assert "due-diligence" in result.output

    def test_list_shows_agents_and_steps_count(self, runner, mock_core):
        mock_core.list_workflows.return_value = [
            {
                "id": "test-wf",
                "name": "Test WF",
                "description": "desc",
                "agents": 3,
                "steps": 7,
            }
        ]
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "list"])
        assert "3" in result.output  # agents count
        assert "7" in result.output  # steps count

    def test_list_output_is_not_raw_dict_repr(self, runner, mock_core):
        """CLI should format output, not print raw Python dict."""
        mock_core.list_workflows.return_value = [
            {
                "id": "wf1",
                "name": "Workflow One",
                "description": "desc",
                "agents": 1,
                "steps": 2,
            }
        ]
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "list"])
        assert "{'id':" not in result.output
        assert "wf1" in result.output


# ---------------------------------------------------------------------------
# workflow run
# ---------------------------------------------------------------------------


class TestWorkflowRun:
    def test_run_unknown_workflow_shows_human_readable_error(self, runner, mock_core):
        mock_core.get_workflow.return_value = None
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "run", "nonexistent", "some task"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "❌" in result.output
        assert "Traceback" not in result.output

    def test_run_dry_run_shows_plan_without_running(self, runner, mock_core):
        mock_wf = MagicMock()
        mock_wf.name = "Feature Dev Team"
        mock_step = MagicMock()
        mock_step.id = "plan"
        mock_step.agent = "planner"
        mock_step.expects = "STATUS: done"
        mock_wf.agents = [MagicMock()]
        mock_wf.steps = [mock_step]
        mock_core.get_workflow.return_value = mock_wf
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(
                cli,
                ["workflow", "run", "feature-dev", "build a login page", "--dry-run"],
            )
        assert result.exit_code == 0
        # dry-run never calls run_workflow
        mock_core.run_workflow.assert_not_called()

    def test_run_invalid_json_context_shows_error(self, runner, mock_core):
        mock_core.get_workflow.return_value = MagicMock()
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(
                cli,
                [
                    "workflow",
                    "run",
                    "feature-dev",
                    "task",
                    "--context",
                    "not-valid-json",
                ],
            )
        assert result.exit_code == 0
        assert "Invalid JSON" in result.output

    def test_run_successful_workflow_shows_run_id(self, runner, mock_core):
        mock_wf = MagicMock()
        mock_core.get_workflow.return_value = mock_wf
        mock_core.run_workflow.return_value = {
            "run_id": "abc-123",
            "status": "completed",
            "steps_completed": 5,
            "total_steps": 5,
            "results": [],
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(
                cli, ["workflow", "run", "feature-dev", "build login"]
            )
        assert result.exit_code == 0
        assert "abc-123" in result.output

    def test_run_shows_step_count_progress(self, runner, mock_core):
        mock_wf = MagicMock()
        mock_core.get_workflow.return_value = mock_wf
        mock_core.run_workflow.return_value = {
            "run_id": "xyz",
            "status": "completed",
            "steps_completed": 3,
            "total_steps": 5,
            "results": [],
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "run", "feature-dev", "task"])
        assert result.exit_code == 0
        assert "3" in result.output
        assert "5" in result.output


# ---------------------------------------------------------------------------
# workflow status
# ---------------------------------------------------------------------------


class TestWorkflowStatus:
    def test_status_unknown_run_shows_error_not_traceback(self, runner, mock_core):
        mock_core.get_run_status.return_value = {
            "error": "Run 'unknown-run-id' not found"
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "status", "unknown-run-id"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "❌" in result.output
        assert "Traceback" not in result.output

    def test_status_shows_run_details(self, runner, mock_core):
        mock_core.get_run_status.return_value = {
            "run_id": "run-abc",
            "workflow": "feature-dev",
            "task": "build login",
            "status": "completed",
            "progress": "5/5",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:01:00",
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "status", "run-abc"])
        assert result.exit_code == 0
        assert "run-abc" in result.output
        assert "completed" in result.output

    def test_status_json_flag_produces_parseable_json(self, runner, mock_core):
        mock_core.get_run_status.return_value = {
            "run_id": "abc",
            "status": "completed",
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "status", "abc", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# workflow inspect
# ---------------------------------------------------------------------------


class TestWorkflowInspect:
    def test_inspect_unknown_run_shows_error(self, runner, mock_core):
        mock_core.inspect_run.return_value = {"error": "Run not found"}
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "inspect", "unknown-id"])
        assert result.exit_code == 0
        assert "❌" in result.output or "not found" in result.output.lower()
        assert "Traceback" not in result.output

    def test_inspect_completed_run_shows_step_details(self, runner, mock_core):
        mock_core.inspect_run.return_value = {
            "run_id": "run-xyz",
            "workflow": "feature-dev",
            "task": "build something",
            "status": "completed",
            "steps": [
                {
                    "step_id": "plan",
                    "agent": "planner",
                    "status": "completed",
                    "input": "FEATURE REQUEST:\nbuild something",
                    "output": "Here is the plan...",
                    "error": None,
                    "started_at": "2024-01-01T00:00:00",
                    "completed_at": "2024-01-01T00:01:00",
                }
            ],
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "inspect", "run-xyz"])
        assert result.exit_code == 0
        assert "plan" in result.output
        assert "completed" in result.output


# ---------------------------------------------------------------------------
# install / uninstall
# ---------------------------------------------------------------------------


class TestInstallUninstall:
    def test_install_reports_workflow_count(self, runner, mock_core):
        mock_core.install.return_value = {
            "workflows": ["feature-dev.yaml", "due-diligence.yaml"],
            "agents": [],
            "errors": [],
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["install"])
        assert result.exit_code == 0
        assert "2" in result.output
        assert "feature-dev.yaml" in result.output

    def test_install_shows_errors_when_present(self, runner, mock_core):
        mock_core.install.return_value = {
            "workflows": [],
            "agents": [],
            "errors": ["Failed to load bad.yaml: parse error"],
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["install"])
        assert result.exit_code == 0
        # Should mention errors
        assert "Errors" in result.output or "⚠" in result.output

    def test_uninstall_without_force_shows_warning(self, runner, mock_core):
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["uninstall"])
        assert result.exit_code == 0
        assert "--force" in result.output
        # Uninstall should NOT have been called
        mock_core.uninstall.assert_not_called()

    def test_uninstall_with_force_calls_core(self, runner, mock_core):
        mock_core.uninstall.return_value = {
            "status": "uninstalled",
            "path": "/tmp/test-agenticom",
        }
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["uninstall", "--force"])
        assert result.exit_code == 0
        mock_core.uninstall.assert_called_once_with(force=True)


# ---------------------------------------------------------------------------
# UX quality checks
# ---------------------------------------------------------------------------


class TestUXBehavior:
    def test_unknown_subcommand_returns_nonzero_exit_code(self, runner):
        result = runner.invoke(cli, ["nonexistent-subcommand-xyz"])
        assert result.exit_code != 0

    def test_workflow_run_missing_args_returns_error(self, runner):
        """workflow run requires workflow_id and task arguments."""
        result = runner.invoke(cli, ["workflow", "run"])
        assert result.exit_code != 0

    def test_error_messages_are_human_readable(self, runner, mock_core):
        """Error states must use friendly text, not Python exception dumps."""
        mock_core.get_workflow.return_value = None
        with patch("agenticom.cli.AgenticomCore", return_value=mock_core):
            result = runner.invoke(cli, ["workflow", "run", "not-a-workflow", "task"])
        assert result.exit_code == 0
        assert "Exception" not in result.output
        assert "Traceback" not in result.output
