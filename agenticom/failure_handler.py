"""
Failure handling logic for workflow steps.

Supports:
1. Simple retry with feedback
2. Configurable loop-back in YAML
3. Intelligent LLM-powered recovery
"""

from .state import WorkflowRun
from .workflows import FailureAction, StepDefinition


class FailureHandler:
    """Handles step failures with various strategies."""

    def __init__(self, llm_executor=None):
        """Initialize failure handler.

        Args:
            llm_executor: Optional LLM executor for intelligent recovery
        """
        self.llm_executor = llm_executor

    def handle_failure(
        self,
        step: StepDefinition,
        run: WorkflowRun,
        error_message: str,
        workflow_steps: list[StepDefinition],
    ) -> tuple[str, int | None]:
        """Handle a step failure based on its on_failure configuration.

        Args:
            step: The failed step
            run: Current workflow run
            error_message: The error that occurred
            workflow_steps: All steps in the workflow

        Returns:
            Tuple of (action, step_index):
            - action: "stop", "retry", "loop_back", "escalate"
            - step_index: Index to jump to (for loop_back), or None
        """
        if not step.on_failure:
            return "stop", None

        failure_action = step.on_failure

        # Check loop count limits
        loop_key = f"{step.id}_loops"
        current_loops = run.loop_counts.get(loop_key, 0)

        if current_loops >= failure_action.max_loops:
            # Exceeded max loops, stop
            return "stop", None

        # Use LLM to analyze and decide if configured
        if failure_action.use_llm_analysis and self.llm_executor:
            return self._llm_decide_recovery(
                step, run, error_message, workflow_steps, failure_action
            )

        # Otherwise use configured action
        if failure_action.action == "retry":
            return self._handle_retry(step, run, error_message, failure_action)
        elif failure_action.action == "loop_back":
            return self._handle_loop_back(
                step, run, error_message, workflow_steps, failure_action
            )
        elif failure_action.action == "escalate":
            return self._handle_escalate(step, run, error_message, failure_action)
        else:
            return "stop", None

    def _handle_retry(
        self,
        step: StepDefinition,
        run: WorkflowRun,
        error_message: str,
        failure_action: FailureAction,
    ) -> tuple[str, int | None]:
        """Handle simple retry with feedback."""
        # Increment loop count
        loop_key = f"{step.id}_loops"
        run.loop_counts[loop_key] = run.loop_counts.get(loop_key, 0) + 1

        # Add feedback to context
        feedback = self._build_feedback(error_message, failure_action.feedback_template)
        run.feedback_history.append(
            {
                "step_id": step.id,
                "error": error_message,
                "feedback": feedback,
                "loop_count": run.loop_counts[loop_key],
            }
        )

        # Store feedback in context for next attempt
        run.context[f"{step.id}_feedback"] = feedback
        run.context[f"{step.id}_previous_error"] = error_message

        return "retry", None

    def _handle_loop_back(
        self,
        step: StepDefinition,
        run: WorkflowRun,
        error_message: str,
        workflow_steps: list[StepDefinition],
        failure_action: FailureAction,
    ) -> tuple[str, int | None]:
        """Handle loop-back to a previous step."""
        if not failure_action.to_step:
            return "stop", None

        # Find the target step index
        target_index = None
        for i, s in enumerate(workflow_steps):
            if s.id == failure_action.to_step:
                target_index = i
                break

        if target_index is None:
            return "stop", None

        # Increment loop count
        loop_key = f"{step.id}_to_{failure_action.to_step}_loops"
        run.loop_counts[loop_key] = run.loop_counts.get(loop_key, 0) + 1

        # Add feedback
        feedback = self._build_feedback(error_message, failure_action.feedback_template)
        run.feedback_history.append(
            {
                "step_id": step.id,
                "action": "loop_back",
                "to_step": failure_action.to_step,
                "error": error_message,
                "feedback": feedback,
                "loop_count": run.loop_counts[loop_key],
            }
        )

        # Store feedback for target step
        run.context[f"{failure_action.to_step}_loopback_feedback"] = feedback
        run.context[f"{failure_action.to_step}_failed_at"] = step.id

        return "loop_back", target_index

    def _handle_escalate(
        self,
        step: StepDefinition,
        run: WorkflowRun,
        error_message: str,
        failure_action: FailureAction,
    ) -> tuple[str, int | None]:
        """Handle escalation to a different agent."""
        # Store escalation info in context
        run.context["escalated_from"] = step.id
        run.context["escalated_to"] = failure_action.escalate_to
        run.context["escalation_reason"] = error_message

        # For now, treat escalation as retry with different agent
        # Future: Could modify step agent dynamically
        return "retry", None

    def _llm_decide_recovery(
        self,
        step: StepDefinition,
        run: WorkflowRun,
        error_message: str,
        workflow_steps: list[StepDefinition],
        failure_action: FailureAction,
    ) -> tuple[str, int | None]:
        """Use LLM to intelligently decide recovery strategy."""
        if not self.llm_executor:
            return "stop", None

        # Build analysis prompt
        prompt = f"""You are an intelligent workflow recovery system. A workflow step has failed.

**Failed Step:** {step.id} - {step.description}
**Error:** {error_message}

**Context:**
- Task: {run.task}
- Current step: {step.id}
- Available steps: {", ".join(s.id for s in workflow_steps)}
- Previous failures: {len(run.feedback_history)}

**Available Recovery Options:**
1. RETRY - Try the same step again with feedback
2. LOOP_BACK - Go back to a previous step (specify which)
3. STOP - Stop the workflow (critical failure)

**Analysis Instructions:**
1. Analyze the error message
2. Determine if the error is:
   - Transient (network, timeout) -> RETRY
   - Logic error in current step -> RETRY with specific feedback
   - Missing prerequisite from earlier step -> LOOP_BACK
   - Fundamental impossibility -> STOP
3. If LOOP_BACK, identify which step to return to
4. Provide clear feedback for retry

**Response Format:**
ACTION: <RETRY|LOOP_BACK|STOP>
TO_STEP: <step_id> (only if LOOP_BACK)
FEEDBACK: <concise feedback for the agent>
REASONING: <brief explanation>
"""

        try:
            response = self.llm_executor(prompt)

            # Parse response
            action = "stop"
            to_step = None
            feedback = error_message

            for line in response.split("\n"):
                if line.startswith("ACTION:"):
                    action_str = line.split(":", 1)[1].strip().upper()
                    if action_str == "RETRY":
                        action = "retry"
                    elif action_str == "LOOP_BACK":
                        action = "loop_back"
                    elif action_str == "STOP":
                        action = "stop"
                elif line.startswith("TO_STEP:"):
                    to_step = line.split(":", 1)[1].strip()
                elif line.startswith("FEEDBACK:"):
                    feedback = line.split(":", 1)[1].strip()

            # Execute the decided action
            if action == "retry":
                run.context[f"{step.id}_llm_feedback"] = feedback
                return "retry", None
            elif action == "loop_back" and to_step:
                # Find step index
                target_index = None
                for i, s in enumerate(workflow_steps):
                    if s.id == to_step:
                        target_index = i
                        break
                if target_index is not None:
                    run.context[f"{to_step}_llm_loopback_feedback"] = feedback
                    return "loop_back", target_index

            return "stop", None

        except Exception:
            # LLM analysis failed, fall back to configured action
            return failure_action.action, None

    def _build_feedback(self, error_message: str, template: str | None) -> str:
        """Build feedback message from template."""
        if not template:
            return f"Previous attempt failed with error: {error_message}. Please review and try again."

        # Simple template substitution
        feedback = template.replace("{{error}}", error_message)
        feedback = feedback.replace("{{error_message}}", error_message)
        return feedback
