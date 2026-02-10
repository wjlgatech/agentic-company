"""
Agent Team Orchestration

Coordinates multiple specialized agents working together on complex tasks.
Implements the "Ralph Loop" pattern: fresh context per step with cross-verification.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Callable, Awaitable
from datetime import datetime
import uuid
import asyncio

from orchestration.agents.base import (
    Agent,
    AgentRole,
    AgentContext,
    AgentResult,
    VerificationResult,
)


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
    verified_by: Optional[AgentRole] = None
    requires_approval: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
    on_fail: str = "retry"  # retry, skip, escalate, abort
    metadata: dict = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing a workflow step"""
    step: WorkflowStep
    agent_result: AgentResult
    verification: Optional[VerificationResult] = None
    status: StepStatus = StepStatus.COMPLETED
    retries: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class TeamConfig:
    """Configuration for an agent team"""
    name: str
    description: str = ""
    max_concurrent_steps: int = 1  # Sequential by default
    timeout_seconds: int = 3600
    escalation_handler: Optional[Callable[[StepResult], Awaitable[None]]] = None
    approval_handler: Optional[Callable[[StepResult], Awaitable[bool]]] = None
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
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
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

    def add_agent(self, agent: Agent) -> 'AgentTeam':
        """Add an agent to the team"""
        self.agents[agent.role] = agent
        return self

    def add_step(self, step: WorkflowStep) -> 'AgentTeam':
        """Add a step to the workflow"""
        self.steps.append(step)
        return self

    def on_step_complete(self, callback: Callable[[StepResult], Awaitable[None]]) -> 'AgentTeam':
        """Register callback for step completion events"""
        self._observers.append(callback)
        return self

    async def run(self, task: str, context: Optional[dict] = None) -> TeamResult:
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
                    step, agent, task, outputs, context or {}
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
                            completed_at=datetime.utcnow()
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

            return TeamResult(
                team_id=self.id,
                workflow_id=workflow_id,
                task=task,
                steps=step_results,
                success=success,
                final_output=final_output,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            return TeamResult(
                team_id=self.id,
                workflow_id=workflow_id,
                task=task,
                steps=step_results,
                success=False,
                final_output=None,
                error=str(e),
                completed_at=datetime.utcnow()
            )

        finally:
            self._running = False

    async def _execute_step(
        self,
        step: WorkflowStep,
        agent: Agent,
        task: str,
        outputs: dict[str, Any],
        context: dict
    ) -> StepResult:
        """Execute a single step with retries and verification"""
        started_at = datetime.utcnow()
        retries = 0

        while retries <= step.max_retries:
            # Build input from template
            # Merge all context, with explicit task taking precedence
            format_context = {**outputs, **context, "task": task}
            input_data = step.input_template.format(**format_context)

            # Create fresh context for this step
            agent_context = AgentContext(
                task_id=str(uuid.uuid4()),
                step_id=step.id,
                input_data=input_data,
                parent_outputs=outputs,
                metadata={"step_name": step.name, "retry": retries}
            )

            # Execute agent
            agent_result = await agent.execute(input_data, agent_context, fresh_context=True)

            if not agent_result.success:
                retries += 1
                if retries > step.max_retries:
                    return StepResult(
                        step=step,
                        agent_result=agent_result,
                        status=StepStatus.FAILED,
                        retries=retries,
                        started_at=started_at,
                        completed_at=datetime.utcnow()
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
                                completed_at=datetime.utcnow()
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
                    started_at=started_at
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
                        completed_at=datetime.utcnow()
                    )

            # Success!
            return StepResult(
                step=step,
                agent_result=agent_result,
                verification=verification,
                status=StepStatus.COMPLETED,
                retries=retries,
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        # Should not reach here, but handle anyway
        return StepResult(
            step=step,
            agent_result=agent_result,
            status=StepStatus.FAILED,
            retries=retries,
            started_at=started_at,
            completed_at=datetime.utcnow()
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

    def with_config(self, **kwargs) -> 'TeamBuilder':
        """Update team configuration"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self

    def with_agent(self, agent: Agent) -> 'TeamBuilder':
        """Add a custom agent"""
        self._agents.append(agent)
        return self

    def with_planner(self, **kwargs) -> 'TeamBuilder':
        """Add a planner agent"""
        from orchestration.agents.specialized import PlannerAgent
        self._agents.append(PlannerAgent(**kwargs))
        return self

    def with_developer(self, **kwargs) -> 'TeamBuilder':
        """Add a developer agent"""
        from orchestration.agents.specialized import DeveloperAgent
        self._agents.append(DeveloperAgent(**kwargs))
        return self

    def with_verifier(self, **kwargs) -> 'TeamBuilder':
        """Add a verifier agent"""
        from orchestration.agents.specialized import VerifierAgent
        self._agents.append(VerifierAgent(**kwargs))
        return self

    def with_tester(self, **kwargs) -> 'TeamBuilder':
        """Add a tester agent"""
        from orchestration.agents.specialized import TesterAgent
        self._agents.append(TesterAgent(**kwargs))
        return self

    def with_reviewer(self, **kwargs) -> 'TeamBuilder':
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
        verified_by: Optional[AgentRole] = None,
        requires_approval: bool = False,
        **kwargs
    ) -> 'TeamBuilder':
        """Add a workflow step"""
        self._steps.append(WorkflowStep(
            id=name,
            name=name,
            agent_role=agent_role,
            input_template=input_template,
            expects=expects,
            verified_by=verified_by,
            requires_approval=requires_approval,
            **kwargs
        ))
        return self

    def on_escalation(self, handler: Callable[[StepResult], Awaitable[None]]) -> 'TeamBuilder':
        """Set escalation handler"""
        self._config.escalation_handler = handler
        return self

    def on_approval(self, handler: Callable[[StepResult], Awaitable[bool]]) -> 'TeamBuilder':
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
    return (TeamBuilder("feature-dev", "Feature development workflow")
        .with_planner()
        .with_developer()
        .with_verifier()
        .with_tester()
        .with_reviewer()
        .step(
            "plan",
            AgentRole.PLANNER,
            "Create implementation plan for: {task}",
            expects="Plan with atomic stories and acceptance criteria"
        )
        .step(
            "implement",
            AgentRole.DEVELOPER,
            "Implement the following plan:\n{plan}",
            expects="Working code that meets acceptance criteria",
            verified_by=AgentRole.VERIFIER
        )
        .step(
            "test",
            AgentRole.TESTER,
            "Create and run tests for:\n{implement}",
            expects="All tests passing"
        )
        .step(
            "review",
            AgentRole.REVIEWER,
            "Review code and tests:\n{implement}\n\nTests:\n{test}",
            expects="Code approved for merge",
            requires_approval=True
        )
        .build())


def create_bug_fix_team(**kwargs) -> AgentTeam:
    """
    Create a bug fix team.

    Workflow: Investigate → Fix → Verify → Test
    """
    return (TeamBuilder("bug-fix", "Bug fix workflow")
        .with_agent(create_agent_by_role(AgentRole.ANALYST, name="Investigator"))
        .with_developer()
        .with_verifier()
        .with_tester()
        .step(
            "investigate",
            AgentRole.ANALYST,
            "Investigate bug: {task}",
            expects="Root cause identified"
        )
        .step(
            "fix",
            AgentRole.DEVELOPER,
            "Fix bug based on investigation:\n{investigate}",
            expects="Bug fixed without introducing regressions",
            verified_by=AgentRole.VERIFIER
        )
        .step(
            "test",
            AgentRole.TESTER,
            "Test fix:\n{fix}\n\nOriginal issue: {task}",
            expects="Bug fixed and regression tests pass"
        )
        .build())


def create_security_audit_team(**kwargs) -> AgentTeam:
    """
    Create a security audit team.

    Workflow: Scan → Prioritize → Fix → Verify
    """
    return (TeamBuilder("security-audit", "Security audit workflow")
        .with_agent(create_agent_by_role(AgentRole.ANALYST, name="Security Scanner"))
        .with_planner()
        .with_developer()
        .with_verifier()
        .step(
            "scan",
            AgentRole.ANALYST,
            "Perform security scan on: {task}",
            expects="Vulnerabilities identified and documented"
        )
        .step(
            "prioritize",
            AgentRole.PLANNER,
            "Prioritize vulnerabilities:\n{scan}",
            expects="Vulnerabilities ranked by severity"
        )
        .step(
            "fix",
            AgentRole.DEVELOPER,
            "Fix high-priority vulnerabilities:\n{prioritize}",
            expects="Vulnerabilities patched",
            verified_by=AgentRole.VERIFIER
        )
        .step(
            "verify",
            AgentRole.VERIFIER,
            "Verify security fixes:\n{fix}\n\nOriginal vulnerabilities:\n{scan}",
            expects="All high-priority vulnerabilities resolved"
        )
        .build())


def create_agent_by_role(role: AgentRole, **kwargs) -> Agent:
    """Helper to create agent by role"""
    from orchestration.agents.specialized import create_agent
    return create_agent(role, **kwargs)
