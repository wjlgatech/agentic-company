"""
Workflow Definitions and Runner.

Following antfarm pattern:
- YAML workflow definitions
- Fresh context per step
- Cross-agent verification
- Automatic retry & escalation
"""

import re
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

from .state import StateManager, WorkflowRun, StepResult, StepStatus, WorkflowStage
from orchestration.artifact_manager import ArtifactManager

# Lazy import to avoid circular dependency
def get_failure_handler():
    from .failure_handler import FailureHandler
    return FailureHandler
from orchestration.artifacts import ArtifactCollection


@dataclass
class AgentDefinition:
    """Definition of an agent in a workflow."""
    id: str
    name: str
    role: str
    prompt_template: str
    workspace_files: dict[str, str] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)


@dataclass
class FailureAction:
    """Configuration for what to do when a step fails."""
    action: str  # "stop", "retry", "loop_back", "escalate", "llm_decide"
    to_step: Optional[str] = None  # For loop_back: which step to return to
    max_loops: int = 2  # Maximum number of loop-backs
    feedback_template: Optional[str] = None  # Feedback to provide on retry
    escalate_to: Optional[str] = None  # For escalate: which agent
    use_llm_analysis: bool = False  # Use LLM to analyze failure and decide


@dataclass
class StepDefinition:
    """Definition of a step in a workflow."""
    id: str
    agent: str
    description: str
    input_template: str
    expects: Optional[str] = None  # Expected output pattern
    retry_count: int = 2
    timeout_seconds: int = 300
    requires_approval: bool = False
    verify_with: Optional[str] = None  # Agent ID for cross-verification
    on_failure: Optional[FailureAction] = None  # What to do if step fails


@dataclass
class WorkflowDefinition:
    """Complete workflow definition loaded from YAML."""
    id: str
    name: str
    description: str
    agents: list[AgentDefinition]
    steps: list[StepDefinition]
    version: str = "1.0"
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "WorkflowDefinition":
        """Load workflow from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        agents = [
            AgentDefinition(
                id=a["id"],
                name=a.get("name", a.get("role", a["id"])),
                role=a.get("role", a.get("name", a["id"])),
                prompt_template=a.get("prompt", ""),
                workspace_files=a.get("workspace", {}).get("files", {}),
                tools=a.get("tools", [])
            )
            for a in data.get("agents", [])
        ]

        steps = [
            StepDefinition(
                id=s["id"],
                agent=s["agent"],
                description=s.get("description", s["id"]),
                input_template=s["input"],
                expects=s.get("expects"),
                retry_count=s.get("retry", 2),
                timeout_seconds=s.get("timeout", 300),
                requires_approval=s.get("approval", False),
                verify_with=s.get("verify_with"),
                on_failure=FailureAction(
                    action=s.get("on_failure", {}).get("action", "stop"),
                    to_step=s.get("on_failure", {}).get("to_step"),
                    max_loops=s.get("on_failure", {}).get("max_loops", 2),
                    feedback_template=s.get("on_failure", {}).get("feedback_template"),
                    escalate_to=s.get("on_failure", {}).get("escalate_to"),
                    use_llm_analysis=s.get("on_failure", {}).get("use_llm_analysis", False)
                ) if s.get("on_failure") else None
            )
            for s in data.get("steps", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            agents=agents,
            steps=steps,
            version=data.get("version", "1.0"),
            tags=data.get("tags", [])
        )

    def to_yaml(self) -> str:
        """Export workflow to YAML."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "prompt": a.prompt_template,
                    "workspace": {"files": a.workspace_files} if a.workspace_files else {},
                    "tools": a.tools
                }
                for a in self.agents
            ],
            "steps": [
                {
                    "id": s.id,
                    "agent": s.agent,
                    "description": s.description,
                    "input": s.input_template,
                    "expects": s.expects,
                    "retry": s.retry_count,
                    "timeout": s.timeout_seconds,
                    "approval": s.requires_approval,
                    "verify_with": s.verify_with
                }
                for s in self.steps
            ]
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)


class WorkflowRunner:
    """
    Executes workflows step by step.

    Key principles (from antfarm):
    - Fresh context per step (no bloat)
    - Cross-agent verification
    - Automatic retry on failure with intelligent recovery
    - State persisted to SQLite
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        executor: Optional[Callable[[str, str], str]] = None,
        failure_handler: Optional["FailureHandler"] = None
    ):
        self.state = state_manager or StateManager()
        self.executor = executor or self._default_executor
        self.artifact_manager = ArtifactManager()
        self.failure_handler = failure_handler
        if self.failure_handler is None and self.executor:
            # Auto-create failure handler with LLM support
            FailureHandler = get_failure_handler()
            self.failure_handler = FailureHandler(llm_executor=self.executor)

    @staticmethod
    def _detect_stage_from_step_id(step_id: str) -> Optional[WorkflowStage]:
        """Detect workflow stage from step ID.

        Matches step IDs like 'plan', 'develop'/'implement', 'verify', 'test', 'review'.
        """
        step_id_lower = step_id.lower()

        # Direct matches
        stage_keywords = {
            WorkflowStage.PLAN: ["plan", "planning", "analyze", "breakdown"],
            WorkflowStage.IMPLEMENT: ["develop", "implement", "code", "build", "create"],
            WorkflowStage.VERIFY: ["verify", "check", "validate", "review-code"],
            WorkflowStage.TEST: ["test", "testing", "qa"],
            WorkflowStage.REVIEW: ["review", "finalize", "approve", "feedback"],
        }

        for stage, keywords in stage_keywords.items():
            if any(kw in step_id_lower for kw in keywords):
                return stage

        return None

    @staticmethod
    def _output_matches_expects(output: str, expects: str) -> bool:
        """Check if output matches expects using flexible keyword matching.

        At least half of the significant words (4+ chars) from expects must
        appear in the output.  Falls back to exact substring match first.
        """
        output_lower = output.lower()
        expects_lower = expects.lower()

        # Try exact substring first
        if expects_lower in output_lower:
            return True

        # Keyword matching: at least half of significant words must be present
        skip_words = {"with", "and", "the", "for", "from", "that", "this", "into"}
        keywords = [w for w in expects_lower.split() if len(w) >= 4 and w not in skip_words]
        if not keywords:
            return False

        def word_found(kw: str) -> bool:
            """Check keyword with morphological flexibility."""
            if kw in output_lower:
                return True
            # Try without trailing 's' or with added 's'
            if kw.endswith("s") and kw[:-1] in output_lower:
                return True
            if (kw + "s") in output_lower:
                return True

            # Enhanced stemming: try removing common endings to find base form
            # E.g., "verified" -> "verify", "approved" -> "approve"
            base_endings = [
                ("ied", "y"),      # verified -> verify
                ("ed", ""),        # approved -> approve, tested -> test
                ("ing", ""),       # testing -> test
                ("ion", ""),       # verification -> verif (partial, but helps)
                ("ation", ""),     # creation -> cre
            ]

            for ending, replacement in base_endings:
                if kw.endswith(ending):
                    base = kw[:-len(ending)] + replacement
                    if base in output_lower:
                        return True

            # Try common suffixes from the base: -tion/-sion, -ing, -ed, -ment, -ity
            stem = kw.rstrip("s")
            for suffix in ("tion", "sion", "ing", "ed", "ment", "ity", "ies", "ation", "ication"):
                if (stem + suffix) in output_lower:
                    return True
            return False

        matched = sum(1 for kw in keywords if word_found(kw))
        threshold = max(1, len(keywords) // 2)  # At least half, minimum 1
        return matched >= threshold

    def _check_quality_gate(self, step_id: str, output: str) -> tuple[bool, Optional[str]]:
        """
        Check if output passes quality gate for critical review steps.
        Returns (passed, error_message).

        For REVIEW steps, look for negative indicators that suggest rejection.
        """
        # Only apply quality gate to review/verification steps
        if not any(keyword in step_id.lower() for keyword in ['review', 'verify', 'validate', 'approve']):
            return True, None

        output_lower = output.lower()

        # Negative indicators that suggest review failed
        negative_indicators = [
            'not approved',
            'cannot be approved',
            'major rework required',
            'not suitable for production',
            'fails to meet',
            'recommendation: reject',
            'must be rejected',
            'does not meet requirements',
            'incomplete implementation',
            'missing critical',
            'security vulnerabilities',
            'not production-ready',
            'requires complete redesign',
            'approximately 0%',
            'approximately 10%',
            'approximately 15%',
            'approximately 20%',  # Less than 25% completion is failure
        ]

        # Check for negative indicators
        found_negative = [ind for ind in negative_indicators if ind in output_lower]
        if found_negative:
            return False, f"Quality gate failed: Review contains rejection indicators: {', '.join(found_negative[:3])}"

        # Positive indicators that suggest approval
        positive_indicators = [
            'approved for production',
            'production-ready',
            'meets all requirements',
            'ready for deployment',
            'passes all checks',
            'recommendation: approve',
            'fully implemented',
        ]

        # If it's a review step with expects pattern, we need either:
        # 1. Positive indicator present, OR
        # 2. No negative indicators (neutral review)
        has_positive = any(ind in output_lower for ind in positive_indicators)

        # For review steps, we want explicit approval OR at least no rejection
        if found_negative:
            return False, f"Quality gate failed: Review rejected with: {found_negative[0]}"

        return True, None

    def _default_executor(self, agent_prompt: str, task_context: str) -> str:
        """
        Default executor - returns the prompt for manual execution.
        In production, this would call the LLM API.
        """
        return f"""
=== AGENT PROMPT ===
{agent_prompt}

=== TASK CONTEXT ===
{task_context}

=== INSTRUCTION ===
Execute this prompt with your preferred LLM (Claude, GPT, etc.)
and provide the output back to continue the workflow.
"""

    def start(
        self,
        workflow: WorkflowDefinition,
        task: str,
        initial_context: Optional[dict] = None
    ) -> WorkflowRun:
        """Start a new workflow run."""
        run_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        run = WorkflowRun(
            id=run_id,
            workflow_id=workflow.id,
            task=task,
            status=StepStatus.PENDING,
            current_step=0,
            total_steps=len(workflow.steps),
            context=initial_context or {"task": task},
            created_at=now,
            updated_at=now
        )

        self.state.create_run(run)
        return run

    def execute_step(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        step_index: int
    ) -> StepResult:
        """Execute a single step in the workflow."""
        if step_index >= len(workflow.steps):
            raise ValueError(f"Step index {step_index} out of range")

        step = workflow.steps[step_index]
        agent = next((a for a in workflow.agents if a.id == step.agent), None)

        if not agent:
            raise ValueError(f"Agent '{step.agent}' not found in workflow")

        # Build the context for this step
        context = run.context.copy()
        context["step_number"] = step_index + 1
        context["step_id"] = step.id

        # Get previous step output if available
        previous_results = self.state.get_step_results(run.id)
        if previous_results:
            last_result = previous_results[-1]
            context["previous_output"] = last_result.output
            context["previous_agent"] = last_result.agent

        # Build the prompt with dot-notation support (e.g. {{step_outputs.plan}})
        input_text = step.input_template
        for match in re.findall(r"\{\{([\w.\-]+)\}\}", input_text):
            parts = match.split(".")
            val = context
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    val = None
                    break
            if val is not None:
                input_text = input_text.replace(f"{{{{{match}}}}}", str(val))

        agent_prompt = f"""You are {agent.name} - {agent.role}.

{agent.prompt_template}

YOUR TASK FOR THIS STEP:
{step.description}
"""

        # Detect and start stage if applicable
        detected_stage = self._detect_stage_from_step_id(step.id)
        if detected_stage:
            run.start_stage(detected_stage, step.id)
            self.state.update_run(run.id, stages=run.stages, current_stage=run.current_stage)

        # Record step start
        now = datetime.now().isoformat()
        result = StepResult(
            run_id=run.id,
            step_id=step.id,
            agent=agent.name,
            status=StepStatus.RUNNING,
            input_context=input_text,
            output="",
            started_at=now
        )

        # Update run status
        self.state.update_run(run.id, current_step=step_index, status=StepStatus.RUNNING)

        try:
            # Execute the step
            output = self.executor(agent_prompt, input_text)

            # Always save output (even on expects failure, for debugging)
            result.output = output

            # Extract artifacts FIRST, before validation
            # This ensures we capture code even if validation fails
            extracted_artifacts = []
            output_dir = None
            if output:
                try:
                    extracted_artifacts = self.artifact_manager.extract_artifacts_from_text(output, run_id=run.id)
                    if extracted_artifacts:
                        collection = ArtifactCollection(run_id=run.id, artifacts=extracted_artifacts)
                        output_dir = self.artifact_manager.save_collection(collection)

                        # Add artifacts to current stage
                        if detected_stage and output_dir:
                            run.add_artifact(detected_stage, str(output_dir))
                            self.state.update_run(run.id, stages=run.stages)
                except Exception as e:
                    # Don't fail the step if artifact extraction fails
                    pass

            # Check quality gate FIRST (for review/validation steps)
            quality_passed, quality_error = self._check_quality_gate(step.id, output)

            if not quality_passed:
                # Quality gate failed - mark as failed even if expectations match
                result.status = StepStatus.FAILED
                result.error = quality_error
            # Check if output covers expected topics (keyword matching)
            # Special handling for "STATUS: done" - make it optional if code was generated
            elif step.expects:
                has_artifacts = len(extracted_artifacts) > 0

                # If step has artifacts OR matches expected output, it's successful
                if not (has_artifacts or self._output_matches_expects(output, step.expects)):
                    result.status = StepStatus.FAILED
                    result.error = f"Output did not contain expected: {step.expects}"
                else:
                    result.status = StepStatus.COMPLETED
                    # Complete stage on successful step completion
                    if detected_stage:
                        run.complete_stage(detected_stage)
                        self.state.update_run(run.id, stages=run.stages)
            else:
                result.status = StepStatus.COMPLETED
                # Complete stage on successful step completion
                if detected_stage:
                    run.complete_stage(detected_stage)
                    self.state.update_run(run.id, stages=run.stages)

            result.completed_at = datetime.now().isoformat()

        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now().isoformat()

        self.state.save_step_result(result)

        # Update run context with step output
        context["step_outputs"] = context.get("step_outputs", {})
        context["step_outputs"][step.id] = result.output
        self.state.update_run(run.id, context=context)

        return result

    def run_all(
        self,
        workflow: WorkflowDefinition,
        task: str,
        initial_context: Optional[dict] = None,
        stop_on_failure: bool = True
    ) -> tuple[WorkflowRun, list[StepResult]]:
        """Run all steps in the workflow with intelligent failure recovery."""
        run = self.start(workflow, task, initial_context)
        results = []
        i = 0

        while i < len(workflow.steps):
            step = workflow.steps[i]
            result = self.execute_step(workflow, run, i)

            # Update or replace result in list
            if len(results) > i:
                results[i] = result
            else:
                results.append(result)

            if result.status == StepStatus.FAILED:
                # Use failure handler if available
                if self.failure_handler and step.on_failure:
                    action, target_index = self.failure_handler.handle_failure(
                        step, run, result.error or "Unknown error", workflow.steps
                    )

                    if action == "retry":
                        # Retry current step
                        continue  # Loop back to retry same step
                    elif action == "loop_back" and target_index is not None:
                        # Jump back to target step
                        i = target_index
                        continue
                    # else: action is "stop", fall through to break

                # No handler or handler says stop
                if stop_on_failure:
                    self.state.update_run(run.id, status=StepStatus.FAILED, error=result.error)
                    run = self.state.get_run(run.id)
                    break

            # Refresh run state
            run = self.state.get_run(run.id)
            i += 1

        # Mark complete if all steps passed
        if all(r.status == StepStatus.COMPLETED for r in results):
            self.state.update_run(run.id, status=StepStatus.COMPLETED)
            run = self.state.get_run(run.id)

        return run, results

    def resume(self, run_id: str, workflow: WorkflowDefinition) -> tuple[WorkflowRun, list[StepResult]]:
        """Resume a failed or paused workflow run."""
        run = self.state.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        existing_results = self.state.get_step_results(run_id)

        # Build results dict by step_id, keeping only latest result per step
        results_by_step = {}
        for r in existing_results:
            results_by_step[r.step_id] = r

        # Find the first incomplete step
        completed_steps = {r.step_id for r in existing_results if r.status == StepStatus.COMPLETED}

        for i, step in enumerate(workflow.steps):
            if step.id in completed_steps:
                continue

            result = self.execute_step(workflow, run, i)
            results_by_step[step.id] = result  # Replace old result

            if result.status == StepStatus.FAILED:
                self.state.update_run(run.id, status=StepStatus.FAILED, error=result.error)
                break

        # Convert back to list in step order
        results = [results_by_step[step.id] for step in workflow.steps if step.id in results_by_step]

        run = self.state.get_run(run_id)

        if all(r.status == StepStatus.COMPLETED for r in results):
            self.state.update_run(run.id, status=StepStatus.COMPLETED, error=None)
            run = self.state.get_run(run_id)

        return run, results

    def get_status(self, run_id: str) -> dict[str, Any]:
        """Get detailed status of a workflow run."""
        run = self.state.get_run(run_id)
        if not run:
            return {"error": f"Run {run_id} not found"}

        results = self.state.get_step_results(run_id)

        return {
            "run_id": run.id,
            "workflow": run.workflow_id,
            "task": run.task,
            "status": run.status.value,
            "progress": f"{run.current_step}/{run.total_steps}",
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "error": run.error,
            "steps": [
                {
                    "step_id": r.step_id,
                    "agent": r.agent,
                    "status": r.status.value,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "error": r.error
                }
                for r in results
            ]
        }
