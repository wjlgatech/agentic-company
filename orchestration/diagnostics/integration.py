"""Integration layer for diagnostics with AgentTeam (Phase 3)."""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from .capture import BrowserAction, DiagnosticCapture, PlaywrightCapture, ActionType
from .config import DiagnosticsConfig
from .iteration_monitor import IterationMonitor
from .meta_analyzer import MetaAnalyzer

logger = structlog.get_logger(__name__)


class DiagnosticsIntegrator:
    """Integration layer between diagnostics system and AgentTeam.

    This class wraps workflow step execution with automated browser testing
    and diagnostic capture. It implements the auto-test-after-fix loop and
    triggers meta-analysis when needed.

    Example:
        ```python
        integrator = DiagnosticsIntegrator(config, executor)

        # Wrap step execution
        result = await integrator.wrap_step_execution(
            step=workflow_step,
            original_execute=agent_team._execute_step_internal,
            agent=agent,
            task=task,
            outputs=outputs,
            context=context,
            workflow_id=workflow_id
        )
        ```
    """

    def __init__(self, config: DiagnosticsConfig, executor: Any):
        """Initialize diagnostics integrator.

        Args:
            config: Diagnostics configuration
            executor: LLM executor for meta-analysis
        """
        self.config = config
        self.executor = executor

        # Initialize subsystems
        self.monitor = IterationMonitor(config)
        self.analyzer = MetaAnalyzer(executor)

    async def wrap_step_execution(
        self,
        step: Any,  # WorkflowStep
        original_execute: Callable,
        *args,
        **kwargs,
    ) -> Any:  # StepResult
        """Wrap step execution with auto-test-after-fix loop.

        This implements the core auto-test loop:
        1. Execute step (agent generates output)
        2. Run browser test to verify
        3. If test passes -> success!
        4. If test fails -> retry (up to max_iterations)
        5. After threshold failures -> trigger meta-analysis

        Args:
            step: Workflow step being executed
            original_execute: Original execution function
            *args: Positional arguments for execution
            **kwargs: Keyword arguments for execution

        Returns:
            StepResult with diagnostics metadata
        """
        logger.info("Starting auto-test loop", step_id=step.id)

        # Check if diagnostics enabled for this step
        if not step.metadata.get("diagnostics_enabled"):
            logger.debug("Diagnostics not enabled for step", step_id=step.id)
            return await original_execute(*args, **kwargs)

        # Start monitoring
        self.monitor.start_step(step.id)

        # Auto-test loop
        iteration = 0
        while iteration < self.config.max_iterations:
            iteration += 1
            logger.info("Starting iteration", step_id=step.id, iteration=iteration)

            # Execute step
            result = await original_execute(*args, **kwargs)

            # Run browser test (if test_url and test_actions provided)
            test_url = step.metadata.get("test_url")
            test_actions = step.metadata.get("test_actions", [])

            if not test_url or not test_actions:
                logger.warning(
                    "No test_url or test_actions in step metadata, skipping diagnostics",
                    step_id=step.id
                )
                # No test configured, return result as-is
                result.metadata["diagnostics"] = {
                    "error": "No test_url or test_actions configured",
                    "captured": False,
                }
                return result

            # Run diagnostics
            try:
                diagnostics = await self._run_diagnostics(test_url, test_actions)
            except Exception as e:
                logger.error("Diagnostics failed", step_id=step.id, error=str(e), exc_info=True)
                diagnostics = DiagnosticCapture(
                    success=False,
                    error=f"Diagnostics execution failed: {str(e)}",
                )

            # Record iteration
            self.monitor.record_iteration(
                error=diagnostics.error if not diagnostics.success else None,
                fix_attempted=result.agent_result.output[:200] if hasattr(result, 'agent_result') else "N/A",
                test_result=diagnostics.success,
                diagnostics=diagnostics,
            )

            # Store diagnostics in result
            if not hasattr(result, "metadata"):
                result.metadata = {}

            result.metadata["diagnostics"] = diagnostics.to_dict()
            result.metadata["iteration"] = iteration
            result.metadata["iterations_total"] = self.monitor.get_iteration_count()

            if diagnostics.success:
                # Tests passed!
                logger.info(
                    "Tests passed!",
                    step_id=step.id,
                    iteration=iteration,
                    final_url=diagnostics.final_url
                )
                return result

            # Check for meta-analysis trigger
            if self.monitor.should_trigger_meta_analysis():
                logger.warning(
                    "Meta-analysis threshold reached",
                    step_id=step.id,
                    iterations=iteration,
                    threshold=self.config.iteration_threshold
                )

                # Run meta-analysis
                try:
                    analysis = await self.analyzer.analyze_failures(
                        self.monitor.get_iterations()
                    )
                    result.metadata["meta_analysis"] = {
                        "pattern": analysis.pattern_detected,
                        "root_cause": analysis.root_cause_hypothesis,
                        "suggestions": analysis.suggested_approaches,
                        "confidence": analysis.confidence,
                    }
                    logger.info("Meta-analysis completed", pattern=analysis.pattern_detected)
                except Exception as e:
                    logger.error("Meta-analysis failed", error=str(e), exc_info=True)

            # Continue to next iteration
            logger.warning(
                "Test failed, retrying",
                step_id=step.id,
                iteration=iteration,
                error=diagnostics.error[:100] if diagnostics.error else "Unknown"
            )

        # Max iterations reached
        logger.error(
            "Max iterations reached without success",
            step_id=step.id,
            max_iterations=self.config.max_iterations
        )

        result.metadata["diagnostics_note"] = f"Max iterations ({self.config.max_iterations}) reached"
        return result

    async def capture_step_diagnostics(
        self, step: Any, result: Any
    ) -> Dict[str, Any]:
        """Capture diagnostics for a completed step.

        This is a simpler interface for Phase 2 compatibility.
        For full auto-test loop, use wrap_step_execution instead.

        Args:
            step: Workflow step
            result: Step execution result

        Returns:
            Dictionary with diagnostic information
        """
        logger.info("Capturing step diagnostics (simple mode)", step_id=step.id)

        # Get test configuration from step metadata
        test_url = step.metadata.get("test_url")
        test_actions = step.metadata.get("test_actions", [])

        if not test_url or not test_actions:
            return {
                "captured": False,
                "error": "No test_url or test_actions configured",
            }

        # Run diagnostics once (no retry loop)
        try:
            diagnostics = await self._run_diagnostics(test_url, test_actions)
            return diagnostics.to_dict()
        except Exception as e:
            logger.error("Diagnostics capture failed", error=str(e), exc_info=True)
            return {
                "captured": False,
                "error": str(e),
            }

    async def _run_diagnostics(
        self, test_url: str, test_actions: List[Dict[str, Any]]
    ) -> DiagnosticCapture:
        """Run browser test and capture diagnostics.

        Args:
            test_url: URL to test
            test_actions: List of browser actions to perform

        Returns:
            DiagnosticCapture with results
        """
        logger.info("Running browser diagnostics", url=test_url, actions_count=len(test_actions))

        # Convert dict actions to BrowserAction objects
        actions = []
        for action_dict in test_actions:
            try:
                actions.append(BrowserAction.from_dict(action_dict))
            except Exception as e:
                logger.error("Invalid action", action=action_dict, error=str(e))
                return DiagnosticCapture(
                    success=False,
                    error=f"Invalid action format: {str(e)}",
                )

        # Determine output directory
        output_dir = self.config.output_dir or Path.cwd() / "outputs" / "diagnostics"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run browser automation
        capture = PlaywrightCapture(self.config)

        try:
            async with capture:
                result = await capture.execute_actions(actions, output_dir)
                logger.info(
                    "Browser test completed",
                    success=result.success,
                    console_errors=len(result.console_errors),
                    screenshots=len(result.screenshots),
                    final_url=result.final_url
                )
                return result
        except Exception as e:
            logger.error("Browser automation failed", error=str(e), exc_info=True)
            return DiagnosticCapture(
                success=False,
                error=f"Browser automation failed: {str(e)}",
            )
