"""
Safe Execution System for Agenticom

Provides controlled command execution with:
- Whitelisting of safe commands
- Approval gates for dangerous operations
- Resource limits (timeout, output size)
- Audit logging
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Awaitable, Dict, List

logger = logging.getLogger(__name__)


class ExecutionPolicy(Enum):
    """Policy for command execution"""
    AUTO_APPROVE = "auto"         # Execute without approval
    REQUIRE_APPROVAL = "approve"  # Require human approval
    DENY = "deny"                 # Always deny


@dataclass
class ExecutionResult:
    """Result from command execution"""
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    cwd: str
    approved: bool = True
    policy: ExecutionPolicy = ExecutionPolicy.AUTO_APPROVE

    def success(self) -> bool:
        """Check if execution was successful"""
        return self.exit_code == 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'command': self.command,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'duration_ms': self.duration_ms,
            'cwd': self.cwd,
            'success': self.success(),
            'approved': self.approved,
            'policy': self.policy.value,
        }


class SecurityError(Exception):
    """Raised when command violates security policy"""
    pass


class ApprovalDenied(Exception):
    """Raised when user denies approval"""
    pass


class ApprovalRequired(Exception):
    """Raised when approval is needed but no callback provided"""
    pass


class ExecutionTimeout(Exception):
    """Raised when command times out"""
    pass


class SafeExecutor:
    """
    Controlled code execution with security policies.

    Provides a whitelist of safe commands that can auto-execute,
    and requires approval for potentially dangerous operations.
    """

    # Default whitelist of safe commands
    DEFAULT_SAFE_COMMANDS = {
        # Testing
        'pytest': ExecutionPolicy.AUTO_APPROVE,
        'python -m pytest': ExecutionPolicy.AUTO_APPROVE,
        'python3 -m pytest': ExecutionPolicy.AUTO_APPROVE,
        'npm test': ExecutionPolicy.AUTO_APPROVE,
        'yarn test': ExecutionPolicy.AUTO_APPROVE,
        'make test': ExecutionPolicy.AUTO_APPROVE,
        'cargo test': ExecutionPolicy.AUTO_APPROVE,
        'go test': ExecutionPolicy.AUTO_APPROVE,
        'python -m unittest': ExecutionPolicy.AUTO_APPROVE,

        # Linting/Formatting
        'ruff check': ExecutionPolicy.AUTO_APPROVE,
        'black': ExecutionPolicy.AUTO_APPROVE,
        'mypy': ExecutionPolicy.AUTO_APPROVE,
        'eslint': ExecutionPolicy.AUTO_APPROVE,
        'prettier': ExecutionPolicy.AUTO_APPROVE,

        # Type checking
        'tsc --noEmit': ExecutionPolicy.AUTO_APPROVE,

        # Require approval for installation
        'pip install': ExecutionPolicy.REQUIRE_APPROVAL,
        'pip3 install': ExecutionPolicy.REQUIRE_APPROVAL,
        'npm install': ExecutionPolicy.REQUIRE_APPROVAL,
        'yarn install': ExecutionPolicy.REQUIRE_APPROVAL,
        'cargo install': ExecutionPolicy.REQUIRE_APPROVAL,

        # Require approval for build operations
        'make': ExecutionPolicy.REQUIRE_APPROVAL,
        'make build': ExecutionPolicy.REQUIRE_APPROVAL,
        'npm run build': ExecutionPolicy.REQUIRE_APPROVAL,
        'cargo build': ExecutionPolicy.REQUIRE_APPROVAL,

        # Deny dangerous operations
        'rm -rf': ExecutionPolicy.DENY,
        'rm -fr': ExecutionPolicy.DENY,
        'dd': ExecutionPolicy.DENY,
        'mkfs': ExecutionPolicy.DENY,
        'format': ExecutionPolicy.DENY,
    }

    def __init__(
        self,
        approval_callback: Optional[Callable[[str, str], Awaitable[bool]]] = None,
        timeout: int = 60,
        max_output_size: int = 1_000_000,
        custom_commands: Optional[Dict[str, ExecutionPolicy]] = None,
    ):
        """
        Initialize safe executor.

        Args:
            approval_callback: Async function to request approval (command, cwd) -> bool
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in bytes
            custom_commands: Additional command policies to merge with defaults
        """
        self.approval_callback = approval_callback
        self.timeout = timeout
        self.max_output_size = max_output_size

        # Merge default and custom commands
        self.safe_commands = self.DEFAULT_SAFE_COMMANDS.copy()
        if custom_commands:
            self.safe_commands.update(custom_commands)

        self.execution_history: List[ExecutionResult] = []

    async def execute(
        self,
        command: str,
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute command with safety checks.

        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Override default timeout

        Returns:
            ExecutionResult

        Raises:
            SecurityError: If command is denied
            ApprovalDenied: If user denies approval
            ApprovalRequired: If approval needed but no callback
            ExecutionTimeout: If command times out
        """
        command = command.strip()
        cwd = Path(cwd).resolve()
        timeout = timeout or self.timeout

        logger.info(f"Executing command: {command} in {cwd}")

        # 1. Check security policy
        policy = self._get_policy(command)

        if policy == ExecutionPolicy.DENY:
            error_msg = f"Command denied by security policy: {command}"
            logger.error(error_msg)
            raise SecurityError(error_msg)

        # 2. Request approval if needed
        approved = True
        if policy == ExecutionPolicy.REQUIRE_APPROVAL:
            if self.approval_callback:
                approved = await self.approval_callback(command, str(cwd))
                if not approved:
                    error_msg = f"Execution denied by user: {command}"
                    logger.warning(error_msg)
                    raise ApprovalDenied(error_msg)
            else:
                error_msg = f"Command requires approval but no callback provided: {command}"
                logger.error(error_msg)
                raise ApprovalRequired(error_msg)

        # 3. Execute with timeout and resource limits
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=env,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            # Truncate output if too large
            stdout = stdout_bytes.decode('utf-8', errors='replace')[:self.max_output_size]
            stderr = stderr_bytes.decode('utf-8', errors='replace')[:self.max_output_size]

            result = ExecutionResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                cwd=str(cwd),
                approved=approved,
                policy=policy,
            )

            # Store in history
            self.execution_history.append(result)

            # Log result
            if result.success():
                logger.info(
                    f"Command succeeded: {command} "
                    f"(exit={result.exit_code}, duration={duration_ms:.0f}ms)"
                )
            else:
                logger.warning(
                    f"Command failed: {command} "
                    f"(exit={result.exit_code}, duration={duration_ms:.0f}ms)"
                )
                if stderr:
                    logger.warning(f"stderr: {stderr[:500]}")

            return result

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Command timed out after {timeout}s: {command}"
            logger.error(error_msg)

            # Kill the process
            try:
                process.kill()
                await process.wait()
            except:
                pass

            raise ExecutionTimeout(error_msg)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Command execution failed: {command} - {e}")
            raise

    def _get_policy(self, command: str) -> ExecutionPolicy:
        """
        Determine execution policy for command.

        Args:
            command: Command to check

        Returns:
            ExecutionPolicy
        """
        command = command.strip()

        # Check exact matches first
        if command in self.safe_commands:
            return self.safe_commands[command]

        # Check if command starts with a whitelisted prefix
        # This allows "pytest tests/" to match "pytest"
        for safe_cmd, policy in self.safe_commands.items():
            if command.startswith(safe_cmd + ' ') or command == safe_cmd:
                return policy

        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf',
            'rm -fr',
            'dd if=',
            '> /dev/',
            'mkfs',
            'format',
            'del /s',
            'chmod 777',
            'chown -R',
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                logger.warning(f"Dangerous pattern detected: {pattern} in {command}")
                return ExecutionPolicy.DENY

        # Default: require approval for unknown commands
        logger.info(f"Unknown command requires approval: {command}")
        return ExecutionPolicy.REQUIRE_APPROVAL

    def add_safe_command(self, command: str, policy: ExecutionPolicy) -> None:
        """
        Add or update a command policy.

        Args:
            command: Command pattern
            policy: Execution policy
        """
        self.safe_commands[command] = policy
        logger.info(f"Added command policy: {command} -> {policy.value}")

    def get_history(self) -> List[ExecutionResult]:
        """Get execution history"""
        return self.execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history"""
        self.execution_history.clear()

    def get_stats(self) -> Dict:
        """Get execution statistics"""
        total = len(self.execution_history)
        if total == 0:
            return {'total': 0}

        successful = sum(1 for r in self.execution_history if r.success())
        failed = total - successful
        avg_duration = sum(r.duration_ms for r in self.execution_history) / total

        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'avg_duration_ms': avg_duration,
        }


# Convenience function for simple execution
async def execute_command(
    command: str,
    cwd: Path = None,
    timeout: int = 60,
    require_approval: bool = False,
) -> ExecutionResult:
    """
    Simple command execution helper.

    Args:
        command: Command to execute
        cwd: Working directory (default: current directory)
        timeout: Timeout in seconds
        require_approval: If True, command will require approval

    Returns:
        ExecutionResult
    """
    executor = SafeExecutor(timeout=timeout)

    # Override policy if approval required
    if require_approval:
        executor.add_safe_command(command, ExecutionPolicy.REQUIRE_APPROVAL)

    cwd = cwd or Path.cwd()

    return await executor.execute(command, cwd)
