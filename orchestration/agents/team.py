"""
Agent Team Orchestration

Coordinates multiple specialized agents working together on complex tasks.
Implements the "Ralph Loop" pattern: fresh context per step with cross-verification.
"""

import asyncio
import re
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

from orchestration.agents.base import (
    Agent,
    AgentContext,
    AgentResult,
    AgentRole,
    VerificationResult,
)
from orchestration.artifact_manager import ArtifactManager
from orchestration.artifacts import ArtifactCollection
from orchestration.executor import SafeExecutor

logger = structlog.get_logger(__name__)


class StepStatus(Enum):
    """Status of a workflow step"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_VERIFICATION = "awaiting_verification"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class WorkflowStep:
    """Definition of a single step in a workflow"""

    id: str
    name: str
    agent_role: AgentRole
    input_template: str
    expects: str = ""  # Acceptance criteria
    verified_by: AgentRole | None = None
    requires_approval: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
    on_fail: str = "retry"  # retry, skip, escalate, abort
    execute: str | None = None  # Command to execute after step completes
    artifacts_required: bool = False  # Require artifacts to be created
    metadata: dict = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing a workflow step"""

    step: WorkflowStep
    agent_result: AgentResult
    verification: VerificationResult | None = None
    status: StepStatus = StepStatus.COMPLETED
    retries: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict = field(default_factory=dict)  # Store diagnostics and other metadata


@dataclass
class TeamConfig:
    """Configuration for an agent team"""

    name: str
    description: str = ""
    max_concurrent_steps: int = 1  # Sequential by default
    timeout_seconds: int = 3600
    escalation_handler: Callable[[StepResult], Awaitable[None]] | None = None
    approval_handler: Callable[[StepResult], Awaitable[bool]] | None = None
    diagnostics_config: Any | None = (
        None  # DiagnosticsConfig from orchestration.diagnostics
    )
    metadata: dict = field(default_factory=dict)


@dataclass
class TeamResult:
    """Result of team workflow execution"""

    team_id: str
    workflow_id: str
    task: str
    steps: list[StepResult]
    success: bool
    final_output: Any
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


class AgentTeam:
    """
    Orchestrates multiple specialized agents working together.

    Key features:
    - Fresh context per step (prevents context bloat)
    - Cross-verification (agents verify each other's work)
    - Automatic retry with escalation
    - Human approval gates for risky actions
    """

    def __init__(self, config: TeamConfig):
        self.id = str(uuid.uuid4())
        self.config = config
        self.agents: dict[AgentRole, Agent] = {}
        self.steps: list[WorkflowStep] = []
        self._running = False
        self._observers: list[Callable[[StepResult], Awaitable[None]]] = []
        self.artifact_manager = ArtifactManager()
        # Self-improvement loop (optional, attached via attach_improvement_loop)
        self._improvement_loop: Any | None = None
        self._improvement_workflow_id: str = ""
        self._self_improve: bool = False
        self.safe_executor = SafeExecutor(
            approval_callback=(
                config.approval_handler if hasattr(config, "approval_handler") else None
            )
        )

        # Initialize diagnostics if enabled
        self.diagnostics = None
        if config.diagnostics_config and getattr(
            config.diagnostics_config, "enabled", False
        ):
            try:
                from orchestration.diagnostics import (
                    DiagnosticsIntegrator,
                    require_playwright,
                )

                require_playwright()

                # Get executor for meta-analysis
                from orchestration.integrations.unified import auto_setup_executor

                executor = auto_setup_executor()

                self.diagnostics = DiagnosticsIntegrator(
                    config.diagnostics_config, executor
                )
                logger.info("Diagnostics system enabled", team_id=self.id)
            except ImportError as e:
                logger.warning("Diagnostics disabled: %s", str(e))
                self.diagnostics = None

    def add_agent(self, agent: Agent) -> "AgentTeam":
        """Add an agent to the team"""
        self.agents[agent.role] = agent
        return self

    def add_step(self, step: WorkflowStep) -> "AgentTeam":
        """Add a step to the workflow"""
        self.steps.append(step)
        return self

    def on_step_complete(
        self, callback: Callable[[StepResult], Awaitable[None]]
    ) -> "AgentTeam":
        """Register callback for step completion events"""
        self._observers.append(callback)
        return self

    def attach_improvement_loop(
        self,
        loop: Any,
        workflow_id: str,
        self_improve: bool = False,
    ) -> "AgentTeam":
        """Attach a self-improvement loop that records every run and evolves prompts."""
        self._improvement_loop = loop
        self._improvement_workflow_id = workflow_id
        self._self_improve = self_improve
        loop.attach_to_team(self, workflow_id, self_improve)
        return self

    async def run(self, task: str, context: dict | None = None) -> TeamResult:
        """
        Execute the workflow with the given task.

        Args:
            task: The task description
            context: Optional additional context

        Returns:
            TeamResult with all step results
        """
        self._running = True
        workflow_id = str(uuid.uuid4())
        step_results: list[StepResult] = []
        outputs: dict[str, Any] = {"task": task}

        try:
            for step in self.steps:
                if not self._running:
                    break

                # Get the agent for this step
                agent = self.agents.get(step.agent_role)
                if agent is None:
                    raise ValueError(f"No agent for role {step.agent_role}")

                # Execute step with retries
                step_result = await self._execute_step(
                    step, agent, task, outputs, context or {}, workflow_id
                )
                step_results.append(step_result)

                # Handle step failure
                if step_result.status == StepStatus.FAILED:
                    if step.on_fail == "abort":
                        return TeamResult(
                            team_id=self.id,
                            workflow_id=workflow_id,
                            task=task,
                            steps=step_results,
                            success=False,
                            final_output=None,
                            error=f"Step {step.name} failed: {step_result.agent_result.error}",
                            completed_at=datetime.utcnow(),
                        )
                    elif step.on_fail == "skip":
                        continue
                    elif step.on_fail == "escalate":
                        if self.config.escalation_handler:
                            await self.config.escalation_handler(step_result)
                        continue

                # Store output for next steps
                if step_result.agent_result.success:
                    outputs[step.id] = step_result.agent_result.output

                # Notify observers
                for observer in self._observers:
                    await observer(step_result)

            # Determine final output
            final_output = outputs.get(self.steps[-1].id) if self.steps else None
            success = all(
                sr.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
                for sr in step_results
            )

            result = TeamResult(
                team_id=self.id,
                workflow_id=workflow_id,
                task=task,
                steps=step_results,
                success=success,
                final_output=final_output,
                completed_at=datetime.utcnow(),
            )

            # Fire-and-forget: record run in improvement loop (zero hot-path impact)
            if self._improvement_loop is not None:
                asyncio.create_task(
                    self._improvement_loop.record_completed_run(
                        result,
                        self._improvement_workflow_id,
                        self._self_improve,
                    )
                )

            return result

        except Exception as e:
            result = TeamResult(
                team_id=self.id,
                workflow_id=workflow_id,
                task=task,
                steps=step_results,
                success=False,
                final_output=None,
                error=str(e),
                completed_at=datetime.utcnow(),
            )

            if self._improvement_loop is not None:
                asyncio.create_task(
                    self._improvement_loop.record_completed_run(
                        result,
                        self._improvement_workflow_id,
                        self._self_improve,
                    )
                )

            return result

        finally:
            self._running = False

    def _preprocess_template(self, template: str) -> str:
        """
        Convert YAML-style template variables to Python .format() style.

        YAML workflows use {{step_outputs.X}} syntax, but Python's .format()
        treats {{ as an escaped literal {. This method converts:
          - {{step_outputs.X}} → {X}  (for referencing previous step outputs)
          - {{task}} → {task}          (for the main task)
          - {{X}} → {X}                (for any other variables)

        Example:
            Input:  "Based on: {{step_outputs.plan}}"
            Output: "Based on: {plan}"
        """
        # Convert {{step_outputs.X}} to {X}
        template = re.sub(r"\{\{step_outputs\.([^}]+)\}\}", r"{\1}", template)
        # Convert remaining {{X}} to {X}
        template = re.sub(r"\{\{([^}]+)\}\}", r"{\1}", template)
        return template

    async def _execute_step(
        self,
        step: WorkflowStep,
        agent: Agent,
        task: str,
        outputs: dict[str, Any],
        context: dict,
        workflow_id: str,
    ) -> StepResult:
        """Execute a single step with retries and verification"""
        started_at = datetime.utcnow()
        retries = 0

        while retries <= step.max_retries:
            # Build input from template
            # First, preprocess to convert {{step_outputs.X}} to {X}
            processed_template = self._preprocess_template(step.input_template)
            # Merge all context, with explicit task taking precedence
            format_context = {**outputs, **context, "task": task}
            input_data = processed_template.format(**format_context)

            # Create fresh context for this step
            agent_context = AgentContext(
                task_id=str(uuid.uuid4()),
                step_id=step.id,
                input_data=input_data,
                parent_outputs=outputs,
                metadata={"step_name": step.name, "retry": retries},
            )

            # Execute agent
            agent_result = await agent.execute(
                input_data, agent_context, fresh_context=True
            )

            if not agent_result.success:
                retries += 1
                if retries > step.max_retries:
                    return StepResult(
                        step=step,
                        agent_result=agent_result,
                        status=StepStatus.FAILED,
                        retries=retries,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                    )
                continue

            # Cross-verification if configured
            verification = None
            if step.verified_by:
                verifier = self.agents.get(step.verified_by)
                if verifier:
                    verification = await verifier.verify(agent_result, step.expects)

                    if not verification.passed:
                        retries += 1
                        if retries > step.max_retries:
                            return StepResult(
                                step=step,
                                agent_result=agent_result,
                                verification=verification,
                                status=StepStatus.FAILED,
                                retries=retries,
                                started_at=started_at,
                                completed_at=datetime.utcnow(),
                            )
                        continue

            # Human approval if required
            if step.requires_approval and self.config.approval_handler:
                step_result = StepResult(
                    step=step,
                    agent_result=agent_result,
                    verification=verification,
                    status=StepStatus.AWAITING_APPROVAL,
                    retries=retries,
                    started_at=started_at,
                )

                approved = await self.config.approval_handler(step_result)
                if not approved:
                    return StepResult(
                        step=step,
                        agent_result=agent_result,
                        verification=verification,
                        status=StepStatus.FAILED,
                        retries=retries,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                    )

            # Extract and save artifacts
            artifacts = self.artifact_manager.extract_artifacts_from_text(
                agent_result.output, run_id=workflow_id
            )

            # Add artifacts to agent result
            agent_result.artifacts = artifacts

            # Save artifacts to disk
            if artifacts:
                collection = ArtifactCollection(run_id=workflow_id, artifacts=artifacts)
                output_dir = self.artifact_manager.save_collection(collection)
                agent_result.metadata["artifact_dir"] = str(output_dir)
                agent_result.metadata["artifact_count"] = len(artifacts)

            # Check if artifacts are required
            if step.artifacts_required and not artifacts:
                return StepResult(
                    step=step,
                    agent_result=agent_result,
                    verification=verification,
                    status=StepStatus.FAILED,
                    retries=retries,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )

            # Execute command if specified
            execution_result = None
            if step.execute and artifacts:
                try:
                    # Run in the output directory where artifacts are saved
                    output_dir = self.artifact_manager.get_run_dir(workflow_id)
                    execution_result = await self.safe_executor.execute(
                        step.execute, cwd=output_dir
                    )
                    agent_result.metadata["execution"] = execution_result.to_dict()
                except Exception as e:
                    # Execution failure doesn't necessarily fail the step
                    # (depends on use case - could make configurable)
                    agent_result.metadata["execution_error"] = str(e)

            # Success! Create result
            result = StepResult(
                step=step,
                agent_result=agent_result,
                verification=verification,
                status=StepStatus.COMPLETED,
                retries=retries,
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

            # Diagnostics capture (if enabled)
            if self.diagnostics and step.metadata.get("diagnostics_enabled"):
                try:
                    diagnostics = await self.diagnostics.capture_step_diagnostics(
                        step, result
                    )
                    result.metadata["diagnostics"] = diagnostics
                except Exception as e:
                    logger.warning("Diagnostics capture failed: %s", str(e))

            return result

        # Should not reach here, but handle anyway
        return StepResult(
            step=step,
            agent_result=agent_result,
            status=StepStatus.FAILED,
            retries=retries,
            started_at=started_at,
            completed_at=datetime.utcnow(),
        )

    def stop(self):
        """Stop the running workflow"""
        self._running = False

    def __repr__(self) -> str:
        return f"AgentTeam(name={self.config.name}, agents={list(self.agents.keys())}, steps={len(self.steps)})"


class TeamBuilder:
    """
    Fluent builder for creating agent teams.

    Example:
        team = (TeamBuilder("feature-dev")
            .with_planner()
            .with_developer()
            .with_verifier()
            .with_tester()
            .with_reviewer()
            .step("plan", AgentRole.PLANNER, "Create plan for: {task}")
            .step("implement", AgentRole.DEVELOPER, "Implement: {plan}", verified_by=AgentRole.VERIFIER)
            .step("test", AgentRole.TESTER, "Test: {implement}")
            .step("review", AgentRole.REVIEWER, "Review: {implement}")
            .build())
    """

    def __init__(self, name: str, description: str = ""):
        self._config = TeamConfig(name=name, description=description)
        self._agents: list[Agent] = []
        self._steps: list[WorkflowStep] = []

    def with_config(self, **kwargs) -> "TeamBuilder":
        """Update team configuration"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self

    def with_agent(self, agent: Agent) -> "TeamBuilder":
        """Add a custom agent"""
        self._agents.append(agent)
        return self

    def with_planner(self, **kwargs) -> "TeamBuilder":
        """Add a planner agent"""
        from orchestration.agents.specialized import PlannerAgent

        self._agents.append(PlannerAgent(**kwargs))
        return self

    def with_developer(self, **kwargs) -> "TeamBuilder":
        """Add a developer agent"""
        from orchestration.agents.specialized import DeveloperAgent

        self._agents.append(DeveloperAgent(**kwargs))
        return self

    def with_verifier(self, **kwargs) -> "TeamBuilder":
        """Add a verifier agent"""
        from orchestration.agents.specialized import VerifierAgent

        self._agents.append(VerifierAgent(**kwargs))
        return self

    def with_tester(self, **kwargs) -> "TeamBuilder":
        """Add a tester agent"""
        from orchestration.agents.specialized import TesterAgent

        self._agents.append(TesterAgent(**kwargs))
        return self

    def with_reviewer(self, **kwargs) -> "TeamBuilder":
        """Add a reviewer agent"""
        from orchestration.agents.specialized import ReviewerAgent

        self._agents.append(ReviewerAgent(**kwargs))
        return self

    def step(
        self,
        name: str,
        agent_role: AgentRole,
        input_template: str,
        expects: str = "",
        verified_by: AgentRole | None = None,
        requires_approval: bool = False,
        **kwargs,
    ) -> "TeamBuilder":
        """Add a workflow step"""
        self._steps.append(
            WorkflowStep(
                id=name,
                name=name,
                agent_role=agent_role,
                input_template=input_template,
                expects=expects,
                verified_by=verified_by,
                requires_approval=requires_approval,
                **kwargs,
            )
        )
        return self

    def on_escalation(
        self, handler: Callable[[StepResult], Awaitable[None]]
    ) -> "TeamBuilder":
        """Set escalation handler"""
        self._config.escalation_handler = handler
        return self

    def on_approval(
        self, handler: Callable[[StepResult], Awaitable[bool]]
    ) -> "TeamBuilder":
        """Set approval handler"""
        self._config.approval_handler = handler
        return self

    def build(self) -> AgentTeam:
        """Build the agent team"""
        team = AgentTeam(self._config)

        for agent in self._agents:
            team.add_agent(agent)

        for step in self._steps:
            team.add_step(step)

        return team


# Pre-built team configurations
def create_feature_dev_team(**kwargs) -> AgentTeam:
    """
    Create a feature development team.

    Workflow: Plan → Develop → Verify → Test → Review
    """
    return (
        TeamBuilder("feature-dev", "Feature development workflow")
        .with_planner()
        .with_developer()
        .with_verifier()
        .with_tester()
        .with_reviewer()
        .step(
            "plan",
            AgentRole.PLANNER,
            "Create implementation plan for: {task}",
            expects="Plan with atomic stories and acceptance criteria",
        )
        .step(
            "implement",
            AgentRole.DEVELOPER,
            "Implement the following plan:\n{plan}",
            expects="Working code that meets acceptance criteria",
            verified_by=AgentRole.VERIFIER,
        )
        .step(
            "test",
            AgentRole.TESTER,
            "Create and run tests for:\n{implement}",
            expects="All tests passing",
        )
        .step(
            "review",
            AgentRole.REVIEWER,
            "Review code and tests:\n{implement}\n\nTests:\n{test}",
            expects="Code approved for merge",
            requires_approval=True,
        )
        .build()
    )


def create_bug_fix_team(**kwargs) -> AgentTeam:
    """
    Create a bug fix team.

    Workflow: Investigate → Fix → Verify → Test
    """
    return (
        TeamBuilder("bug-fix", "Bug fix workflow")
        .with_agent(create_agent_by_role(AgentRole.ANALYST, name="Investigator"))
        .with_developer()
        .with_verifier()
        .with_tester()
        .step(
            "investigate",
            AgentRole.ANALYST,
            "Investigate bug: {task}",
            expects="Root cause identified",
        )
        .step(
            "fix",
            AgentRole.DEVELOPER,
            "Fix bug based on investigation:\n{investigate}",
            expects="Bug fixed without introducing regressions",
            verified_by=AgentRole.VERIFIER,
        )
        .step(
            "test",
            AgentRole.TESTER,
            "Test fix:\n{fix}\n\nOriginal issue: {task}",
            expects="Bug fixed and regression tests pass",
        )
        .build()
    )


def create_security_audit_team(**kwargs) -> AgentTeam:
    """
    Create a security audit team.

    Workflow: Scan → Prioritize → Fix → Verify
    """
    return (
        TeamBuilder("security-audit", "Security audit workflow")
        .with_agent(create_agent_by_role(AgentRole.ANALYST, name="Security Scanner"))
        .with_planner()
        .with_developer()
        .with_verifier()
        .step(
            "scan",
            AgentRole.ANALYST,
            "Perform security scan on: {task}",
            expects="Vulnerabilities identified and documented",
        )
        .step(
            "prioritize",
            AgentRole.PLANNER,
            "Prioritize vulnerabilities:\n{scan}",
            expects="Vulnerabilities ranked by severity",
        )
        .step(
            "fix",
            AgentRole.DEVELOPER,
            "Fix high-priority vulnerabilities:\n{prioritize}",
            expects="Vulnerabilities patched",
            verified_by=AgentRole.VERIFIER,
        )
        .step(
            "verify",
            AgentRole.VERIFIER,
            "Verify security fixes:\n{fix}\n\nOriginal vulnerabilities:\n{scan}",
            expects="All high-priority vulnerabilities resolved",
        )
        .build()
    )


def create_agent_by_role(role: AgentRole, **kwargs) -> Agent:
    """Helper to create agent by role"""
    from orchestration.agents.specialized import create_agent

    return create_agent(role, **kwargs)
