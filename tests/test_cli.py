"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner

from orchestration.cli import main


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestCLIHealth:
    """Tests for health command."""

    def test_health_command(self, runner):
        """Health command should run without error."""
        result = runner.invoke(main, ["health"])
        # May have warnings about config but should run
        assert result.exit_code in [0, 1]
        assert "Health" in result.output or "health" in result.output.lower()

    def test_version_flag(self, runner):
        """--version should show version."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0." in result.output  # Version starts with 0.


class TestCLIConfig:
    """Tests for config commands."""

    def test_config_show_table(self, runner):
        """config show should display table."""
        result = runner.invoke(main, ["config-cmd", "show"])
        assert result.exit_code == 0

    def test_config_show_json(self, runner):
        """config show --format json should output JSON."""
        result = runner.invoke(main, ["config-cmd", "show", "--format", "json"])
        assert result.exit_code == 0
        # Should contain JSON-like content
        assert "{" in result.output

    def test_config_validate(self, runner):
        """config validate should check configuration."""
        result = runner.invoke(main, ["config-cmd", "validate"])
        # May pass or fail depending on env, but should run
        assert result.exit_code in [0, 1]


class TestCLIWorkflow:
    """Tests for workflow commands."""

    def test_workflow_list(self, runner):
        """workflow list should show workflows."""
        result = runner.invoke(main, ["workflow", "list"])
        assert result.exit_code == 0
        assert "content-research" in result.output or "Workflow" in result.output

    def test_workflow_run(self, runner):
        """workflow run should execute workflow."""
        result = runner.invoke(main, ["workflow", "run", "test-workflow", "-i", "test input"])
        assert result.exit_code == 0
        assert "Running" in result.output or "Result" in result.output

    def test_workflow_status(self, runner):
        """workflow status should show status."""
        result = runner.invoke(main, ["workflow", "status", "test-id-123"])
        assert result.exit_code == 0
        assert "test-id-123" in result.output


class TestCLIMetrics:
    """Tests for metrics commands."""

    def test_metrics_show_table(self, runner):
        """metrics show should display metrics."""
        result = runner.invoke(main, ["metrics", "show"])
        assert result.exit_code == 0

    def test_metrics_show_json(self, runner):
        """metrics show --format json should output JSON."""
        result = runner.invoke(main, ["metrics", "show", "--format", "json"])
        assert result.exit_code == 0


class TestCLIApproval:
    """Tests for approval commands."""

    def test_approval_list(self, runner):
        """approval list should show pending approvals."""
        result = runner.invoke(main, ["approval", "list"])
        assert result.exit_code == 0

    def test_approval_approve(self, runner):
        """approval approve should approve request."""
        result = runner.invoke(main, ["approval", "approve", "test-id", "-r", "Looks good"])
        assert result.exit_code == 0
        assert "Approved" in result.output

    def test_approval_reject(self, runner):
        """approval reject should reject request."""
        result = runner.invoke(main, ["approval", "reject", "test-id", "-r", "Not acceptable"])
        assert result.exit_code == 0
        assert "Rejected" in result.output


class TestCLIRecall:
    """Tests for recall command."""

    def test_recall_command(self, runner):
        """recall should search memory."""
        result = runner.invoke(main, ["recall", "test query"])
        assert result.exit_code == 0


class TestCLIHelp:
    """Tests for help output."""

    def test_main_help(self, runner):
        """Main help should show all commands."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "health" in result.output
        assert "workflow" in result.output
        assert "serve" in result.output

    def test_workflow_help(self, runner):
        """Workflow help should show subcommands."""
        result = runner.invoke(main, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "run" in result.output
