"""
Tests for orchestration/executor.py — SafeExecutor, execute_command.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestration.executor import (
    ApprovalDenied,
    ApprovalRequired,
    ExecutionPolicy,
    ExecutionTimeout,
    SafeExecutor,
    SecurityError,
    execute_command,
)

# ---------------------------------------------------------------------------
# _get_policy
# ---------------------------------------------------------------------------


class TestGetPolicy:
    def setup_method(self):
        self.executor = SafeExecutor()

    def test_exact_match_auto_approve(self):
        policy = self.executor._get_policy("pytest")
        assert policy == ExecutionPolicy.AUTO_APPROVE

    def test_prefix_match_auto_approve(self):
        policy = self.executor._get_policy("pytest tests/")
        assert policy == ExecutionPolicy.AUTO_APPROVE

    def test_prefix_match_require_approval(self):
        policy = self.executor._get_policy("pip install requests")
        assert policy == ExecutionPolicy.REQUIRE_APPROVAL

    def test_dangerous_rm_rf_deny(self):
        policy = self.executor._get_policy("rm -rf /tmp/data")
        assert policy == ExecutionPolicy.DENY

    def test_unknown_command_require_approval(self):
        policy = self.executor._get_policy("echo hello world")
        assert policy == ExecutionPolicy.REQUIRE_APPROVAL

    def test_exact_ruff_check_auto_approve(self):
        policy = self.executor._get_policy("ruff check .")
        assert policy == ExecutionPolicy.AUTO_APPROVE


# ---------------------------------------------------------------------------
# execute — AUTO_APPROVE
# ---------------------------------------------------------------------------


class TestExecuteAutoApprove:
    async def test_execute_success(self, tmp_path):
        executor = SafeExecutor()
        result = await executor.execute("pytest --version", cwd=tmp_path)
        # pytest is in the env; exit code should be 0
        assert result.exit_code == 0
        assert result.success() is True
        assert result.policy == ExecutionPolicy.AUTO_APPROVE

    async def test_execute_nonzero_captured(self, tmp_path):
        executor = SafeExecutor()
        # Add the command as auto-approved so it runs without needing approval
        executor.add_safe_command("python -c", ExecutionPolicy.AUTO_APPROVE)
        result = await executor.execute(
            "python -c 'import sys; sys.exit(2)'", cwd=tmp_path
        )
        assert result.exit_code == 2
        assert result.success() is False

    async def test_execute_stores_in_history(self, tmp_path):
        executor = SafeExecutor()
        await executor.execute("pytest --version", cwd=tmp_path)
        assert len(executor.get_history()) == 1


# ---------------------------------------------------------------------------
# execute — DENY
# ---------------------------------------------------------------------------


class TestExecuteDeny:
    async def test_deny_raises_security_error(self, tmp_path):
        executor = SafeExecutor()
        with pytest.raises(SecurityError):
            await executor.execute("rm -rf /tmp", cwd=tmp_path)

    async def test_deny_subprocess_never_called(self, tmp_path):
        executor = SafeExecutor()
        with patch("asyncio.create_subprocess_shell") as mock_sub:
            with pytest.raises(SecurityError):
                await executor.execute("rm -rf /tmp", cwd=tmp_path)
            mock_sub.assert_not_called()


# ---------------------------------------------------------------------------
# execute — REQUIRE_APPROVAL
# ---------------------------------------------------------------------------


class TestExecuteRequireApproval:
    async def test_no_callback_raises_approval_required(self, tmp_path):
        executor = SafeExecutor()
        with pytest.raises(ApprovalRequired):
            await executor.execute("make build", cwd=tmp_path)

    async def test_callback_returns_false_raises_approval_denied(self, tmp_path):
        async def deny_callback(cmd, cwd):
            return False

        executor = SafeExecutor(approval_callback=deny_callback)
        with pytest.raises(ApprovalDenied):
            await executor.execute("make build", cwd=tmp_path)

    async def test_callback_returns_true_proceeds(self, tmp_path):
        async def approve_callback(cmd, cwd):
            return True

        executor = SafeExecutor(approval_callback=approve_callback)
        # We'll override "make build" policy to require approval and mock subprocess
        with patch(
            "asyncio.create_subprocess_shell", new_callable=AsyncMock
        ) as mock_sub:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_sub.return_value = mock_proc

            result = await executor.execute("make build", cwd=tmp_path)
            assert result.approved is True


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


class TestExecuteTimeout:
    async def test_timeout_raises_execution_timeout(self, tmp_path):
        executor = SafeExecutor(timeout=1)
        # Add "sleep" as auto-approve for testing
        executor.add_safe_command("sleep", ExecutionPolicy.AUTO_APPROVE)

        with patch(
            "asyncio.create_subprocess_shell", new_callable=AsyncMock
        ) as mock_sub:
            mock_proc = AsyncMock()
            # Make communicate raise TimeoutError
            mock_proc.communicate.side_effect = Exception("timeout")  # will hit except
            mock_sub.return_value = mock_proc

            # Use wait_for mock to simulate timeout
            import asyncio as _asyncio

            original_wait_for = _asyncio.wait_for

            async def timeout_wait(*args, **kwargs):
                raise _asyncio.TimeoutError()

            with patch("asyncio.wait_for", side_effect=_asyncio.TimeoutError()):
                with pytest.raises(ExecutionTimeout):
                    await executor.execute("sleep 100", cwd=tmp_path)


# ---------------------------------------------------------------------------
# Output truncation
# ---------------------------------------------------------------------------


class TestOutputTruncation:
    async def test_output_truncated_to_max(self, tmp_path):
        executor = SafeExecutor(max_output_size=10)
        with patch(
            "asyncio.create_subprocess_shell", new_callable=AsyncMock
        ) as mock_sub:
            mock_proc = AsyncMock()
            big_output = b"x" * 10000
            mock_proc.communicate.return_value = (big_output, b"")
            mock_proc.returncode = 0
            mock_sub.return_value = mock_proc

            executor.add_safe_command("mycommand", ExecutionPolicy.AUTO_APPROVE)
            result = await executor.execute("mycommand", cwd=tmp_path)
            assert len(result.stdout) <= 10


# ---------------------------------------------------------------------------
# add_safe_command, get_history, clear_history, get_stats
# ---------------------------------------------------------------------------


class TestHistoryAndStats:
    def test_add_safe_command(self):
        executor = SafeExecutor()
        executor.add_safe_command("mygrep", ExecutionPolicy.AUTO_APPROVE)
        assert executor._get_policy("mygrep") == ExecutionPolicy.AUTO_APPROVE

    async def test_clear_history(self, tmp_path):
        executor = SafeExecutor()
        await executor.execute("pytest --version", cwd=tmp_path)
        executor.clear_history()
        assert executor.get_history() == []

    async def test_get_stats_empty(self):
        executor = SafeExecutor()
        stats = executor.get_stats()
        assert stats == {"total": 0}

    async def test_get_stats_with_history(self, tmp_path):
        executor = SafeExecutor()
        await executor.execute("pytest --version", cwd=tmp_path)
        stats = executor.get_stats()
        assert stats["total"] == 1
        assert "success_rate" in stats


# ---------------------------------------------------------------------------
# execute_command helper
# ---------------------------------------------------------------------------


class TestExecuteCommandHelper:
    async def test_execute_command_without_approval(self, tmp_path):
        result = await execute_command("pytest --version", cwd=tmp_path)
        assert result.exit_code == 0

    async def test_execute_command_with_require_approval_no_callback(self, tmp_path):
        """When require_approval=True but no callback, should raise ApprovalRequired."""
        with pytest.raises(ApprovalRequired):
            await execute_command(
                "some_unknown_cmd", cwd=tmp_path, require_approval=True
            )
