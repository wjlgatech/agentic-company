"""
Pipeline system for orchestrating multi-step AI workflows.

Provides a flexible framework for building complex agent pipelines.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from orchestration.approval import ApprovalGate, ApprovalRequest
from orchestration.evaluator import BaseEvaluator, EvaluationResult
from orchestration.guardrails import GuardrailPipeline, GuardrailResult
from orchestration.memory import MemoryStore
from orchestration.observability import ObservabilityStack, get_observability


class StepStatus(str, Enum):
    """Status of a pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class StepResult:
    """Result from a pipeline step execution."""

    step_name: str
    status: StepStatus
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    guardrail_results: list[GuardrailResult] = field(default_factory=list)
    evaluation_result: EvaluationResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    name: str = "step"

    @abstractmethod
    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        """Execute the step and return output."""
        pass

    async def validate_input(self, input_data: Any) -> bool:
        """Validate input before execution."""
        return True

    async def validate_output(self, output: Any) -> bool:
        """Validate output after execution."""
        return True


class FunctionStep(PipelineStep):
    """Step that wraps a function."""

    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        is_async: bool = False,
    ):
        self.name = name
        self.func = func
        self.is_async = is_async

    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        if self.is_async:
            return await self.func(input_data, context)
        return self.func(input_data, context)


class LLMStep(PipelineStep):
    """Step that calls an LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        llm_client: Any | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.name = name
        self.prompt_template = prompt_template
        self.llm_client = llm_client
        self.model = model

    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        # Format prompt
        prompt = self.prompt_template.format(input=input_data, **context)

        # If no client, return placeholder
        if self.llm_client is None:
            return f"[LLM Response for: {prompt[:100]}...]"

        # Call LLM
        response = await self.llm_client.generate(prompt)
        return response


class ConditionalStep(PipelineStep):
    """Step that branches based on condition."""

    def __init__(
        self,
        name: str,
        condition: Callable[[Any, dict], bool],
        true_step: PipelineStep,
        false_step: PipelineStep | None = None,
    ):
        self.name = name
        self.condition = condition
        self.true_step = true_step
        self.false_step = false_step

    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        if self.condition(input_data, context):
            return await self.true_step.execute(input_data, context)
        elif self.false_step:
            return await self.false_step.execute(input_data, context)
        return input_data


class ParallelStep(PipelineStep):
    """Step that executes multiple steps in parallel."""

    def __init__(self, name: str, steps: list[PipelineStep]):
        self.name = name
        self.steps = steps

    async def execute(self, input_data: Any, context: dict[str, Any]) -> list[Any]:
        tasks = [step.execute(input_data, context) for step in self.steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


@dataclass
class PipelineConfig:
    """Configuration for a pipeline."""

    name: str
    description: str = ""
    max_retries: int = 3
    timeout_seconds: int = 300
    continue_on_error: bool = False
    enable_guardrails: bool = True
    enable_evaluation: bool = True
    require_approval: bool = False


class Pipeline:
    """Orchestration pipeline for multi-step workflows."""

    def __init__(
        self,
        config: PipelineConfig,
        steps: list[PipelineStep] | None = None,
        guardrails: GuardrailPipeline | None = None,
        evaluator: BaseEvaluator | None = None,
        memory: MemoryStore | None = None,
        approval_gate: ApprovalGate | None = None,
        observability: ObservabilityStack | None = None,
    ):
        self.config = config
        self.steps = steps or []
        self.guardrails = guardrails
        self.evaluator = evaluator
        self.memory = memory
        self.approval_gate = approval_gate
        self.obs = observability or get_observability()
        self.results: list[StepResult] = []

    def add_step(self, step: PipelineStep) -> "Pipeline":
        """Add a step to the pipeline."""
        self.steps.append(step)
        return self

    async def run(
        self,
        input_data: Any,
        context: dict[str, Any] | None = None,
    ) -> tuple[Any, list[StepResult]]:
        """Run the pipeline."""
        context = context or {}
        context["pipeline_id"] = str(uuid.uuid4())
        context["pipeline_name"] = self.config.name
        current_data = input_data
        self.results = []

        with self.obs.observe("pipeline_run", {"pipeline": self.config.name}) as span:
            for step in self.steps:
                result = await self._run_step(step, current_data, context)
                self.results.append(result)

                if result.status == StepStatus.FAILED:
                    if not self.config.continue_on_error:
                        span.set_status("ERROR")
                        return current_data, self.results

                if result.status == StepStatus.COMPLETED:
                    current_data = result.output

            # Store result in memory if available
            if self.memory and current_data:
                self.memory.remember(
                    str(current_data),
                    metadata={"pipeline": self.config.name},
                    tags=[self.config.name],
                )

        return current_data, self.results

    async def _run_step(
        self,
        step: PipelineStep,
        input_data: Any,
        context: dict[str, Any],
    ) -> StepResult:
        """Run a single step with guardrails and evaluation."""
        result = StepResult(
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now(),
        )

        with self.obs.observe("step_run", {"step": step.name}):
            try:
                # Input guardrails
                if self.config.enable_guardrails and self.guardrails:
                    if isinstance(input_data, str):
                        passed, gr_results = self.guardrails.check_all_pass(input_data)
                        result.guardrail_results = gr_results
                        if not passed:
                            result.status = StepStatus.BLOCKED
                            result.error = "Input blocked by guardrails"
                            result.completed_at = datetime.now()
                            return result

                # Approval gate
                if self.config.require_approval and self.approval_gate:
                    approval = await self._request_approval(step, input_data, context)
                    if approval.status.value not in ["approved", "auto_approved"]:
                        result.status = StepStatus.BLOCKED
                        result.error = (
                            f"Approval {approval.status.value}: {approval.reason}"
                        )
                        result.completed_at = datetime.now()
                        return result

                # Execute step
                output = await step.execute(input_data, context)

                # Output evaluation
                if self.config.enable_evaluation and self.evaluator:
                    if isinstance(output, str):
                        eval_result = self.evaluator.evaluate(output, context)
                        result.evaluation_result = eval_result
                        if not eval_result.passed:
                            self.obs.logger.warning(
                                "Step output evaluation failed",
                                step=step.name,
                                score=eval_result.score,
                            )

                result.output = output
                result.status = StepStatus.COMPLETED

            except Exception as e:
                result.status = StepStatus.FAILED
                result.error = str(e)
                self.obs.logger.error(
                    "Step execution failed", step=step.name, error=str(e)
                )

            finally:
                result.completed_at = datetime.now()

        return result

    async def _request_approval(
        self,
        step: PipelineStep,
        input_data: Any,
        context: dict[str, Any],
    ) -> ApprovalRequest:
        """Request approval for a step."""
        request = ApprovalRequest(
            workflow_id=context.get("pipeline_id", ""),
            step_name=step.name,
            content=str(input_data)[:1000],
            metadata={"context": context},
        )
        return await self.approval_gate.request_approval(request)

    def get_status(self) -> dict[str, Any]:
        """Get pipeline execution status."""
        completed = sum(1 for r in self.results if r.status == StepStatus.COMPLETED)
        failed = sum(1 for r in self.results if r.status == StepStatus.FAILED)
        total_duration = sum(r.duration_ms for r in self.results)

        return {
            "pipeline": self.config.name,
            "total_steps": len(self.steps),
            "executed_steps": len(self.results),
            "completed": completed,
            "failed": failed,
            "total_duration_ms": total_duration,
            "steps": [r.to_dict() for r in self.results],
        }


class PipelineBuilder:
    """Builder for creating pipelines."""

    def __init__(self, name: str):
        self.config = PipelineConfig(name=name)
        self.steps: list[PipelineStep] = []
        self.guardrails: GuardrailPipeline | None = None
        self.evaluator: BaseEvaluator | None = None
        self.memory: MemoryStore | None = None
        self.approval_gate: ApprovalGate | None = None

    def with_description(self, description: str) -> "PipelineBuilder":
        self.config.description = description
        return self

    def with_step(self, step: PipelineStep) -> "PipelineBuilder":
        self.steps.append(step)
        return self

    def with_function(
        self,
        name: str,
        func: Callable,
        is_async: bool = False,
    ) -> "PipelineBuilder":
        self.steps.append(FunctionStep(name, func, is_async))
        return self

    def with_guardrails(self, guardrails: GuardrailPipeline) -> "PipelineBuilder":
        self.guardrails = guardrails
        self.config.enable_guardrails = True
        return self

    def with_evaluator(self, evaluator: BaseEvaluator) -> "PipelineBuilder":
        self.evaluator = evaluator
        self.config.enable_evaluation = True
        return self

    def with_memory(self, memory: MemoryStore) -> "PipelineBuilder":
        self.memory = memory
        return self

    def with_approval(self, gate: ApprovalGate) -> "PipelineBuilder":
        self.approval_gate = gate
        self.config.require_approval = True
        return self

    def with_max_retries(self, retries: int) -> "PipelineBuilder":
        self.config.max_retries = retries
        return self

    def continue_on_error(self, continue_: bool = True) -> "PipelineBuilder":
        self.config.continue_on_error = continue_
        return self

    def build(self) -> Pipeline:
        return Pipeline(
            config=self.config,
            steps=self.steps,
            guardrails=self.guardrails,
            evaluator=self.evaluator,
            memory=self.memory,
            approval_gate=self.approval_gate,
        )


# Factory for common pipelines
def create_content_pipeline(
    name: str = "content",
    guardrails: GuardrailPipeline | None = None,
    evaluator: BaseEvaluator | None = None,
) -> Pipeline:
    """Create a standard content processing pipeline."""
    return (
        PipelineBuilder(name)
        .with_description("Standard content processing pipeline")
        .with_guardrails(guardrails or GuardrailPipeline())
        .with_evaluator(evaluator)
        .build()
    )
