"""
Base Agent Class

Provides the foundation for specialized agents with role-based behavior,
guardrail integration, and fresh context management.
"""

import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentRole(Enum):
    """Standard agent roles for multi-agent workflows"""

    PLANNER = "planner"
    DEVELOPER = "developer"
    VERIFIER = "verifier"
    TESTER = "tester"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    WRITER = "writer"
    ANALYST = "analyst"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Configuration for an agent instance"""

    role: AgentRole
    name: str
    persona: str = ""
    guardrails: list[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: int = 300
    workspace_files: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentContext:
    """Fresh context for each agent execution"""

    task_id: str
    step_id: str
    input_data: Any
    workspace: dict = field(default_factory=dict)
    parent_outputs: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResult:
    """Result from agent execution"""

    agent_id: str
    agent_role: AgentRole
    step_id: str
    output: Any
    success: bool
    error: str | None = None
    duration_ms: float = 0
    tokens_used: int = 0
    artifacts: list = field(default_factory=list)  # List of Artifact objects
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class Agent(ABC):
    """
    Base class for all agents in the system.

    Each agent has a specific role, persona, and set of capabilities.
    Agents operate with fresh context per execution to prevent
    context window bloat and ensure focused task completion.
    """

    def __init__(self, config: AgentConfig):
        self.id = str(uuid.uuid4())
        self.config = config
        self.role = config.role
        self.name = config.name
        self.persona = config.persona
        # base_persona stores the original persona before any runtime updates
        # (used by Phase 2 task-time skill routing to reset between runs)
        self.base_persona = config.persona
        self._guardrail_pipeline = None
        self._executor: Callable[[str, AgentContext], Awaitable[str]] | None = None

    @property
    def system_prompt(self) -> str:
        """Generate system prompt based on role and persona"""
        base_prompt = f"You are {self.name}, a specialized AI agent with the role of {self.role.value}."
        if self.persona:
            base_prompt += f"\n\nPersona: {self.persona}"
        return base_prompt

    def set_executor(self, executor: Callable[[str, AgentContext], Awaitable[str]]):
        """Set the LLM executor function (e.g., OpenClaw, Anthropic API)"""
        self._executor = executor

    @property
    def executor(self) -> Callable[[str, AgentContext], Awaitable[str]] | None:
        """Get the current executor (None if not set)"""
        return self._executor

    @property
    def has_executor(self) -> bool:
        """Check if executor is configured"""
        return self._executor is not None

    def set_guardrails(self, guardrail_pipeline):
        """Set guardrail pipeline for input/output filtering"""
        self._guardrail_pipeline = guardrail_pipeline

    def update_persona(self, new_persona: str, version_id: str = "") -> None:
        """Update the agent's persona at runtime (used by ImprovementLoop).

        The system_prompt property reads self.persona dynamically, so this
        takes effect on the very next execution call.
        """
        self.persona = new_persona
        if version_id:
            self.metadata = {
                **(
                    self.metadata if hasattr(self, "metadata") and self.metadata else {}
                ),
                "active_prompt_version_id": version_id,
            }

    async def execute(
        self, task: str, context: AgentContext | None = None, fresh_context: bool = True
    ) -> AgentResult:
        """
        Execute a task with fresh context.

        Args:
            task: The task description
            context: Optional execution context
            fresh_context: If True, start with clean slate (default: True)

        Returns:
            AgentResult with output and metadata
        """
        import time

        start_time = time.time()

        # Create fresh context if needed
        if context is None or fresh_context:
            context = AgentContext(
                task_id=str(uuid.uuid4()), step_id=str(uuid.uuid4()), input_data=task
            )

        try:
            # Apply input guardrails
            if self._guardrail_pipeline:
                guard_results = self._guardrail_pipeline.check(task)
                if not all(r.passed for r in guard_results):
                    failed = [r for r in guard_results if not r.passed]
                    return AgentResult(
                        agent_id=self.id,
                        agent_role=self.role,
                        step_id=context.step_id,
                        output=None,
                        success=False,
                        error=f"Input guardrail failed: {failed[0].reason}",
                        duration_ms=(time.time() - start_time) * 1000,
                    )

            # Execute the task
            output = await self._execute_task(task, context)

            # Apply output guardrails
            if self._guardrail_pipeline and output:
                guard_results = self._guardrail_pipeline.check(str(output))
                if not all(r.passed for r in guard_results):
                    failed = [r for r in guard_results if not r.passed]
                    return AgentResult(
                        agent_id=self.id,
                        agent_role=self.role,
                        step_id=context.step_id,
                        output=output,
                        success=False,
                        error=f"Output guardrail failed: {failed[0].reason}",
                        duration_ms=(time.time() - start_time) * 1000,
                    )

            return AgentResult(
                agent_id=self.id,
                agent_role=self.role,
                step_id=context.step_id,
                output=output,
                success=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return AgentResult(
                agent_id=self.id,
                agent_role=self.role,
                step_id=context.step_id,
                output=None,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    @abstractmethod
    async def _execute_task(self, task: str, context: AgentContext) -> Any:
        """
        Implement task execution logic.

        Override this method in specialized agents.
        """
        pass

    async def verify(self, result: AgentResult, criteria: str) -> "VerificationResult":
        """
        Verify another agent's output against acceptance criteria.

        Used for cross-verification where agents don't self-assess.
        """
        verification_prompt = f"""
        Verify this work against the acceptance criteria:

        === WORK OUTPUT ===
        {result.output}

        === ACCEPTANCE CRITERIA ===
        {criteria}

        Provide your assessment:
        1. Does the output meet ALL criteria? (YES/NO)
        2. List each criterion and whether it's met
        3. If NO, explain what's missing or incorrect

        Format: Start your response with "PASS" or "FAIL"
        """

        context = AgentContext(
            task_id=result.step_id,
            step_id=f"verify-{result.step_id}",
            input_data=verification_prompt,
        )

        verify_result = await self.execute(verification_prompt, context)

        passed = verify_result.success and str(
            verify_result.output
        ).strip().upper().startswith("PASS")

        return VerificationResult(
            verifier_id=self.id,
            verified_result=result,
            passed=passed,
            reasoning=(
                str(verify_result.output)
                if verify_result.success
                else verify_result.error
            ),
            criteria=criteria,
        )

    def __repr__(self) -> str:
        return f"Agent(role={self.role.value}, name={self.name})"


@dataclass
class VerificationResult:
    """Result from cross-verification"""

    verifier_id: str
    verified_result: AgentResult
    passed: bool
    reasoning: str
    criteria: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class MockAgent(Agent):
    """
    Mock agent for testing purposes.

    Returns predefined outputs or echoes input.
    """

    def __init__(
        self,
        config: AgentConfig,
        mock_output: Any | None = None,
        should_fail: bool = False,
        fail_message: str = "Mock failure",
    ):
        super().__init__(config)
        self.mock_output = mock_output
        self.should_fail = should_fail
        self.fail_message = fail_message

    async def _execute_task(self, task: str, context: AgentContext) -> Any:
        if self.should_fail:
            raise Exception(self.fail_message)

        if self.mock_output is not None:
            return self.mock_output

        return f"[{self.role.value}] Processed: {task}"


class LLMAgent(Agent):
    """
    Agent that uses an LLM executor for task completion.

    Requires setting an executor function that calls the LLM API.
    """

    async def _execute_task(self, task: str, context: AgentContext) -> Any:
        if self._executor is None:
            raise ValueError("LLM executor not set. Call set_executor() first.")

        # Build full prompt with system context
        full_prompt = f"{self.system_prompt}\n\nTask: {task}"

        # Add workspace context if available
        if context.workspace:
            workspace_context = "\n".join(
                f"File: {k}\n{v}" for k, v in context.workspace.items()
            )
            full_prompt += f"\n\nWorkspace Context:\n{workspace_context}"

        # Add parent outputs if available
        if context.parent_outputs:
            parent_context = "\n".join(
                f"Previous Step ({k}):\n{v}" for k, v in context.parent_outputs.items()
            )
            full_prompt += f"\n\nPrevious Steps:\n{parent_context}"

        # Execute via LLM
        return await self._executor(full_prompt, context)
