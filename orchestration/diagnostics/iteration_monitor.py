"""Monitor and track diagnostic iterations."""

from dataclasses import dataclass, field
from datetime import datetime

import structlog

from .capture import DiagnosticCapture
from .config import DiagnosticsConfig

logger = structlog.get_logger(__name__)


@dataclass
class IterationRecord:
    """Record of a single fix-test iteration.

    Attributes:
        iteration: Iteration number (1-indexed)
        step_id: ID of the workflow step
        error: Error message if test failed
        fix_attempted: Brief description of fix attempt (truncated output)
        test_result: Whether test passed
        diagnostics: Full diagnostic capture
        timestamp: When this iteration occurred
    """

    iteration: int
    step_id: str
    error: str | None
    fix_attempted: str
    test_result: bool
    diagnostics: DiagnosticCapture | None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "iteration": self.iteration,
            "step_id": self.step_id,
            "error": self.error,
            "fix_attempted": self.fix_attempted,
            "test_result": self.test_result,
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics else None,
            "timestamp": self.timestamp.isoformat(),
        }


class IterationMonitor:
    """Monitor diagnostic iterations and trigger meta-analysis when needed.

    Tracks iterations per step and determines when meta-analysis should be
    triggered based on the configured threshold.

    Example:
        ```python
        monitor = IterationMonitor(config)
        monitor.start_step("develop")

        # Record iterations
        for i in range(max_iterations):
            # Execute and test
            record = monitor.record_iteration(
                error="Test failed",
                fix_attempted="Fixed button handler",
                test_result=False,
                diagnostics=capture_result
            )

            if monitor.should_trigger_meta_analysis():
                # Run meta-analysis
                break
        ```
    """

    def __init__(self, config: DiagnosticsConfig):
        """Initialize iteration monitor.

        Args:
            config: Diagnostics configuration
        """
        self.config = config

        # Track iterations by step ID
        self.iterations_by_step: dict[str, list[IterationRecord]] = {}
        self.current_step_id: str | None = None

    def start_step(self, step_id: str) -> None:
        """Start monitoring a new step.

        Args:
            step_id: ID of the workflow step
        """
        logger.info("Starting iteration monitoring", step_id=step_id)
        self.current_step_id = step_id

        if step_id not in self.iterations_by_step:
            self.iterations_by_step[step_id] = []

    def record_iteration(
        self,
        error: str | None,
        fix_attempted: str,
        test_result: bool,
        diagnostics: DiagnosticCapture | None = None,
    ) -> IterationRecord:
        """Record a fix-test iteration.

        Args:
            error: Error message if test failed
            fix_attempted: Brief description of fix attempt
            test_result: Whether test passed
            diagnostics: Full diagnostic capture

        Returns:
            IterationRecord for this iteration

        Raises:
            RuntimeError: If no step is currently being monitored
        """
        if not self.current_step_id:
            raise RuntimeError(
                "No step is currently being monitored. Call start_step() first."
            )

        # Get iteration list for current step
        iterations = self.iterations_by_step[self.current_step_id]

        # Create record
        record = IterationRecord(
            iteration=len(iterations) + 1,
            step_id=self.current_step_id,
            error=error,
            fix_attempted=fix_attempted[:200],  # Truncate for brevity
            test_result=test_result,
            diagnostics=diagnostics,
        )

        # Store record
        iterations.append(record)

        logger.info(
            "Iteration recorded",
            step_id=self.current_step_id,
            iteration=record.iteration,
            test_result=test_result,
            error=error[:100] if error else None,
        )

        return record

    def should_trigger_meta_analysis(self) -> bool:
        """Check if meta-analysis should be triggered.

        Meta-analysis is triggered when:
        1. Current step has reached the iteration threshold
        2. There have been consecutive failures

        Returns:
            True if meta-analysis should be triggered
        """
        if not self.current_step_id:
            return False

        iterations = self.iterations_by_step.get(self.current_step_id, [])

        # Need at least threshold iterations
        if len(iterations) < self.config.iteration_threshold:
            return False

        # Check recent iterations for consecutive failures
        recent_iterations = iterations[-self.config.iteration_threshold :]
        consecutive_failures = all(
            not record.test_result for record in recent_iterations
        )

        if consecutive_failures:
            logger.warning(
                "Meta-analysis trigger threshold reached",
                step_id=self.current_step_id,
                iterations=len(iterations),
                threshold=self.config.iteration_threshold,
            )
            return True

        return False

    def get_iterations(self, step_id: str | None = None) -> list[IterationRecord]:
        """Get iteration history for a step.

        Args:
            step_id: Step ID to get iterations for (defaults to current step)

        Returns:
            List of iteration records
        """
        step_id = step_id or self.current_step_id
        if not step_id:
            return []

        return self.iterations_by_step.get(step_id, [])

    def get_iteration_count(self, step_id: str | None = None) -> int:
        """Get iteration count for a step.

        Args:
            step_id: Step ID to get count for (defaults to current step)

        Returns:
            Number of iterations
        """
        return len(self.get_iterations(step_id))

    def reset_step(self, step_id: str | None = None) -> None:
        """Reset iteration history for a step.

        Args:
            step_id: Step ID to reset (defaults to current step)
        """
        step_id = step_id or self.current_step_id
        if step_id:
            self.iterations_by_step[step_id] = []
            logger.info("Iteration history reset", step_id=step_id)
