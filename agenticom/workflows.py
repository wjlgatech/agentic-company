"""
Workflow Definitions and Runner.

Following antfarm pattern:
- YAML workflow definitions
- Fresh context per step
- Cross-agent verification
- Automatic retry & escalation
"""

import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

from .state import StateManager, WorkflowRun, StepResult, StepStatus


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
                verify_with=s.get("verify_with")
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
    - Automatic retry on failure
    - State persisted to SQLite
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        executor: Optional[Callable[[str, str], str]] = None
    ):
        self.state = state_manager or StateManager()
        self.executor = executor or self._default_executor

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

        # Build the prompt
        input_text = step.input_template
        for key, value in context.items():
            input_text = input_text.replace(f"{{{{{key}}}}}", str(value))

        agent_prompt = f"""You are {agent.name} - {agent.role}.

{agent.prompt_template}

YOUR TASK FOR THIS STEP:
{step.description}
"""

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

            # Check if output matches expected pattern
            if step.expects and step.expects not in output:
                result.status = StepStatus.FAILED
                result.error = f"Output did not contain expected: {step.expects}"
            else:
                result.status = StepStatus.COMPLETED
                result.output = output

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
        """Run all steps in the workflow."""
        run = self.start(workflow, task, initial_context)
        results = []

        for i, step in enumerate(workflow.steps):
            result = self.execute_step(workflow, run, i)
            results.append(result)

            if result.status == StepStatus.FAILED and stop_on_failure:
                self.state.update_run(run.id, status=StepStatus.FAILED, error=result.error)
                run = self.state.get_run(run.id)
                break

            # Refresh run state
            run = self.state.get_run(run.id)

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
        results = existing_results.copy()

        # Find the first incomplete step
        completed_steps = {r.step_id for r in existing_results if r.status == StepStatus.COMPLETED}

        for i, step in enumerate(workflow.steps):
            if step.id in completed_steps:
                continue

            result = self.execute_step(workflow, run, i)
            results.append(result)

            if result.status == StepStatus.FAILED:
                self.state.update_run(run.id, status=StepStatus.FAILED, error=result.error)
                break

        run = self.state.get_run(run_id)

        if all(r.status == StepStatus.COMPLETED for r in results):
            self.state.update_run(run.id, status=StepStatus.COMPLETED)
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
