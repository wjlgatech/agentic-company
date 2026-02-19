"""
Agenticom Core - Main orchestration engine.
"""

import shutil
from pathlib import Path

from .state import StateManager
from .workflows import WorkflowDefinition, WorkflowRunner

# Default installation paths
AGENTICOM_HOME = Path.home() / ".agenticom"
WORKFLOWS_DIR = AGENTICOM_HOME / "workflows"
AGENTS_DIR = AGENTICOM_HOME / "agents"


class AgenticomCore:
    """
    Core orchestration engine for Agenticom.

    Manages workflow installation, execution, and state.
    """

    def __init__(self, home_dir: Path | None = None):
        self.home = home_dir or AGENTICOM_HOME
        self.workflows_dir = self.home / "workflows"
        self.agents_dir = self.home / "agents"
        self.state = StateManager(self.home / "state.db")

        # Ensure directories exist
        self.home.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(exist_ok=True)
        self.agents_dir.mkdir(exist_ok=True)

    def install(self, source_dir: Path | None = None) -> dict:
        """
        Install Agenticom workflows and agents.

        If source_dir is None, installs bundled workflows.
        """
        results = {"workflows": [], "agents": [], "errors": []}

        # Find bundled workflows
        if source_dir is None:
            # Look for bundled_workflows in package
            source_dir = Path(__file__).parent / "bundled_workflows"

        if not source_dir.exists():
            results["errors"].append(f"Source directory not found: {source_dir}")
            return results

        # Copy workflow files
        for yaml_file in source_dir.glob("*.yaml"):
            try:
                dest = self.workflows_dir / yaml_file.name
                shutil.copy(yaml_file, dest)
                results["workflows"].append(yaml_file.name)
            except Exception as e:
                results["errors"].append(f"Failed to install {yaml_file.name}: {e}")

        # Copy agent files if they exist
        agents_source = source_dir.parent / "agents"
        if agents_source.exists():
            for agent_dir in agents_source.iterdir():
                if agent_dir.is_dir():
                    try:
                        dest = self.agents_dir / agent_dir.name
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(agent_dir, dest)
                        results["agents"].append(agent_dir.name)
                    except Exception as e:
                        results["errors"].append(
                            f"Failed to install agent {agent_dir.name}: {e}"
                        )

        return results

    def uninstall(self, force: bool = False) -> dict:
        """Remove all Agenticom data."""
        if not force:
            return {
                "warning": "This will delete all workflows, agents, and state.",
                "hint": "Use force=True to confirm",
            }

        try:
            if self.home.exists():
                shutil.rmtree(self.home)
            return {"status": "uninstalled", "path": str(self.home)}
        except Exception as e:
            return {"error": str(e)}

    def list_workflows(self) -> list[dict]:
        """List all installed workflows."""
        workflows = []

        for yaml_file in self.workflows_dir.glob("*.yaml"):
            try:
                wf = WorkflowDefinition.from_yaml(yaml_file)
                workflows.append(
                    {
                        "id": wf.id,
                        "name": wf.name,
                        "description": wf.description,
                        "steps": len(wf.steps),
                        "agents": len(wf.agents),
                        "file": yaml_file.name,
                    }
                )
            except Exception as e:
                workflows.append(
                    {"id": yaml_file.stem, "error": str(e), "file": yaml_file.name}
                )

        return workflows

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Load a workflow by ID."""
        # Try direct file match
        yaml_file = self.workflows_dir / f"{workflow_id}.yaml"
        if yaml_file.exists():
            return WorkflowDefinition.from_yaml(yaml_file)

        # Search all files for matching ID
        for yaml_file in self.workflows_dir.glob("*.yaml"):
            try:
                wf = WorkflowDefinition.from_yaml(yaml_file)
                if wf.id == workflow_id:
                    return wf
            except Exception:
                continue

        return None

    def _create_llm_executor(self):
        """Create an LLM executor from available backends, or None."""
        try:
            from orchestration.integrations.unified import (
                Backend,
                UnifiedConfig,
                UnifiedExecutor,
                get_ready_backends,
            )

            ready = get_ready_backends()
            if not ready:
                return None

            # Prefer cloud backends when API keys are set (higher quality)
            if Backend.OPENCLAW in ready:
                config = UnifiedConfig(preferred_backend=Backend.OPENCLAW)
            elif Backend.NANOBOT in ready:
                config = UnifiedConfig(preferred_backend=Backend.NANOBOT)
            else:
                config = UnifiedConfig()

            executor = UnifiedExecutor(config, eager_init=True)

            def llm_executor(agent_prompt: str, task_context: str) -> str:
                import asyncio

                prompt = f"{agent_prompt}\n\n{task_context}"
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    # Already in an async context — run in a new thread
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, executor.execute(prompt))
                        return future.result()
                else:
                    return asyncio.run(executor.execute(prompt))

            return llm_executor
        except Exception:
            return None

    def run_workflow(
        self, workflow_id: str, task: str, context: dict | None = None
    ) -> dict:
        """Run a workflow with the given task."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow '{workflow_id}' not found"}

        executor = self._create_llm_executor()
        runner = WorkflowRunner(self.state, executor=executor)
        run, results = runner.run_all(workflow, task, context)

        return {
            "run_id": run.id,
            "workflow": workflow.name,
            "status": run.status.value,
            "task": task,
            "steps_completed": len(
                [r for r in results if r.status.value == "completed"]
            ),
            "total_steps": len(workflow.steps),
            "results": [
                {
                    "step": r.step_id,
                    "agent": r.agent,
                    "status": r.status.value,
                    "output_preview": (
                        r.output[:200] + "..." if len(r.output) > 200 else r.output
                    ),
                }
                for r in results
            ],
        }

    def get_run_status(self, run_id: str) -> dict:
        """Get the status of a workflow run."""
        runner = WorkflowRunner(self.state)
        return runner.get_status(run_id)

    def resume_run(self, run_id: str) -> dict:
        """Resume a failed workflow run."""
        run = self.state.get_run(run_id)
        if not run:
            return {"error": f"Run '{run_id}' not found"}

        workflow = self.get_workflow(run.workflow_id)
        if not workflow:
            return {"error": f"Workflow '{run.workflow_id}' not found"}

        runner = WorkflowRunner(self.state)
        updated_run, results = runner.resume(run_id, workflow)

        return {
            "run_id": updated_run.id,
            "status": updated_run.status.value,
            "steps_completed": len(
                [r for r in results if r.status.value == "completed"]
            ),
            "total_steps": updated_run.total_steps,
        }

    def inspect_run(self, run_id: str, step_id: str | None = None) -> dict:
        """Get full observability for a workflow run including inputs/outputs."""
        run = self.state.get_run(run_id)
        if not run:
            return {"error": f"Run '{run_id}' not found"}

        results = self.state.get_step_results(run_id)

        steps = []
        for r in results:
            if step_id and r.step_id != step_id:
                continue
            steps.append(
                {
                    "step_id": r.step_id,
                    "agent": r.agent,
                    "status": r.status.value,
                    "input": r.input_context,
                    "output": r.output,
                    "error": r.error,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                }
            )

        return {
            "run_id": run.id,
            "workflow": run.workflow_id,
            "task": run.task,
            "status": run.status.value,
            "steps": steps,
        }

    def get_stats(self) -> dict:
        """Get overall statistics."""
        workflows = self.list_workflows()
        state_stats = self.state.get_stats()

        return {
            "installed_workflows": len(workflows),
            "workflow_names": [w.get("name", w.get("id")) for w in workflows],
            **state_stats,
        }
