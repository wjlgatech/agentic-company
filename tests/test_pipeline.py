"""
Tests for orchestration/pipeline.py — previously zero-coverage module.

Covers:
- StepResult: to_dict, duration_ms
- FunctionStep, LLMStep, ConditionalStep, ParallelStep
- Pipeline: happy path, chaining, failure, continue_on_error, get_status
- PipelineBuilder fluent API
- create_content_pipeline factory
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from orchestration.pipeline import (
    ConditionalStep,
    FunctionStep,
    LLMStep,
    ParallelStep,
    Pipeline,
    PipelineBuilder,
    PipelineConfig,
    StepResult,
    StepStatus,
    create_content_pipeline,
)

# ---------------------------------------------------------------------------
# StepResult
# ---------------------------------------------------------------------------


class TestStepResult:
    def test_to_dict_contains_required_keys(self):
        r = StepResult(step_name="foo", status=StepStatus.COMPLETED, output="bar")
        d = r.to_dict()
        assert d["step_name"] == "foo"
        assert d["status"] == "completed"
        assert d["output"] == "bar"
        assert d["error"] is None
        assert "duration_ms" in d

    def test_duration_ms_zero_when_no_timestamps(self):
        r = StepResult(step_name="foo", status=StepStatus.PENDING)
        assert r.duration_ms == 0.0

    def test_duration_ms_calculated_correctly(self):
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = start + timedelta(seconds=2)
        r = StepResult(
            step_name="foo",
            status=StepStatus.COMPLETED,
            started_at=start,
            completed_at=end,
        )
        assert r.duration_ms == pytest.approx(2000.0)

    def test_failed_status_preserved_in_dict(self):
        r = StepResult(step_name="err", status=StepStatus.FAILED, error="boom")
        d = r.to_dict()
        assert d["status"] == "failed"
        assert d["error"] == "boom"


# ---------------------------------------------------------------------------
# FunctionStep
# ---------------------------------------------------------------------------


class TestFunctionStep:
    async def test_sync_function_step(self):
        def double(data, ctx):
            return data * 2

        step = FunctionStep("double", double, is_async=False)
        result = await step.execute(5, {})
        assert result == 10

    async def test_async_function_step(self):
        async def upper(data, ctx):
            return data.upper()

        step = FunctionStep("upper", upper, is_async=True)
        result = await step.execute("hello", {})
        assert result == "HELLO"

    async def test_default_validate_input_returns_true(self):
        step = FunctionStep("x", lambda d, c: d)
        assert await step.validate_input("anything") is True

    async def test_default_validate_output_returns_true(self):
        step = FunctionStep("x", lambda d, c: d)
        assert await step.validate_output("anything") is True

    async def test_context_passed_to_function(self):
        def use_ctx(data, ctx):
            return ctx.get("key", "missing")

        step = FunctionStep("ctx", use_ctx)
        result = await step.execute("ignored", {"key": "found"})
        assert result == "found"


# ---------------------------------------------------------------------------
# LLMStep
# ---------------------------------------------------------------------------


class TestLLMStep:
    async def test_no_client_returns_placeholder(self):
        step = LLMStep("test", "Process: {input}", llm_client=None)
        result = await step.execute("hello world", {})
        assert "[LLM Response for:" in result

    async def test_with_mock_client_calls_generate(self):
        mock_client = AsyncMock()
        mock_client.generate.return_value = "LLM output"
        step = LLMStep("test", "Prompt: {input}", llm_client=mock_client)
        result = await step.execute("test input", {})
        assert result == "LLM output"
        mock_client.generate.assert_called_once()

    async def test_prompt_template_formatted(self):
        """Template {input} is replaced with input_data."""
        step = LLMStep("test", "Do: {input}", llm_client=None)
        result = await step.execute("something", {})
        assert "something" in result


# ---------------------------------------------------------------------------
# ConditionalStep
# ---------------------------------------------------------------------------


class TestConditionalStep:
    async def test_true_branch_taken_when_condition_true(self):
        true_step = FunctionStep("yes", lambda d, c: "yes")
        false_step = FunctionStep("no", lambda d, c: "no")
        step = ConditionalStep(
            "check",
            condition=lambda data, ctx: data > 0,
            true_step=true_step,
            false_step=false_step,
        )
        assert await step.execute(1, {}) == "yes"

    async def test_false_branch_taken_when_condition_false(self):
        true_step = FunctionStep("yes", lambda d, c: "yes")
        false_step = FunctionStep("no", lambda d, c: "no")
        step = ConditionalStep(
            "check",
            condition=lambda data, ctx: data > 0,
            true_step=true_step,
            false_step=false_step,
        )
        assert await step.execute(-1, {}) == "no"

    async def test_no_false_branch_returns_input_unchanged(self):
        true_step = FunctionStep("yes", lambda d, c: "yes")
        step = ConditionalStep(
            "check",
            condition=lambda data, ctx: False,
            true_step=true_step,
            false_step=None,
        )
        result = await step.execute("original", {})
        assert result == "original"


# ---------------------------------------------------------------------------
# ParallelStep
# ---------------------------------------------------------------------------


class TestParallelStep:
    async def test_all_steps_execute(self):
        steps = [
            FunctionStep("a", lambda d, c: d + "_a"),
            FunctionStep("b", lambda d, c: d + "_b"),
            FunctionStep("c", lambda d, c: d + "_c"),
        ]
        parallel = ParallelStep("parallel", steps)
        results = await parallel.execute("base", {})
        assert len(results) == 3
        assert "base_a" in results
        assert "base_b" in results
        assert "base_c" in results

    async def test_exception_in_one_step_captured_not_raised(self):
        """ParallelStep uses gather(return_exceptions=True), so exceptions are values."""

        def raise_error(d, c):
            raise ValueError("parallel boom")

        steps = [
            FunctionStep("ok", lambda d, c: "ok"),
            FunctionStep("bad", raise_error),
        ]
        parallel = ParallelStep("parallel", steps)
        results = await parallel.execute("data", {})
        assert len(results) == 2
        assert results[0] == "ok"
        assert isinstance(results[1], ValueError)

    async def test_empty_parallel_returns_empty_list(self):
        parallel = ParallelStep("empty", [])
        results = await parallel.execute("data", {})
        assert results == []


# ---------------------------------------------------------------------------
# Pipeline: happy paths
# ---------------------------------------------------------------------------


class TestPipelineHappyPath:
    async def test_empty_pipeline_returns_input_unchanged(self):
        config = PipelineConfig(name="empty")
        pipeline = Pipeline(config)
        result, step_results = await pipeline.run("input data")
        assert result == "input data"
        assert step_results == []

    async def test_single_step_completes(self):
        config = PipelineConfig(
            name="single", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("upper", lambda d, c: d.upper()))
        result, step_results = await pipeline.run("hello")
        assert result == "HELLO"
        assert len(step_results) == 1
        assert step_results[0].status == StepStatus.COMPLETED

    async def test_multi_step_chains_output(self):
        """Each step receives the previous step's output."""
        config = PipelineConfig(
            name="chain", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("strip", lambda d, c: d.strip()))
        pipeline.add_step(FunctionStep("upper", lambda d, c: d.upper()))
        pipeline.add_step(FunctionStep("exclaim", lambda d, c: d + "!"))
        result, _ = await pipeline.run("  hello  ")
        assert result == "HELLO!"

    async def test_step_result_has_timestamps(self):
        config = PipelineConfig(
            name="ts", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("noop", lambda d, c: d))
        _, step_results = await pipeline.run("data")
        sr = step_results[0]
        assert sr.started_at is not None
        assert sr.completed_at is not None
        assert sr.duration_ms >= 0

    async def test_add_step_returns_pipeline_for_fluency(self):
        config = PipelineConfig(
            name="fluent", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        returned = pipeline.add_step(FunctionStep("x", lambda d, c: d))
        assert returned is pipeline

    async def test_context_injected_into_steps(self):
        """Context dict passed to run() is available in each step."""

        def read_ctx(data, ctx):
            return ctx.get("extra", "missing")

        config = PipelineConfig(
            name="ctx", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("read", read_ctx))
        result, _ = await pipeline.run("ignored", context={"extra": "found"})
        assert result == "found"


# ---------------------------------------------------------------------------
# Pipeline: failure modes
# ---------------------------------------------------------------------------


class TestPipelineFailure:
    async def test_exception_marks_step_failed(self):
        def explode(d, c):
            raise RuntimeError("boom")

        config = PipelineConfig(
            name="fail", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("explode", explode))
        _, step_results = await pipeline.run("data")
        assert step_results[0].status == StepStatus.FAILED
        assert "boom" in step_results[0].error

    async def test_failure_stops_subsequent_steps_by_default(self):
        def explode(d, c):
            raise RuntimeError("boom")

        config = PipelineConfig(
            name="fail", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("explode", explode))
        pipeline.add_step(FunctionStep("should_not_run", lambda d, c: "ran"))
        _, step_results = await pipeline.run("data")
        # Only first step ran
        assert len(step_results) == 1
        assert step_results[0].status == StepStatus.FAILED

    async def test_continue_on_error_runs_subsequent_steps(self):
        def explode(d, c):
            raise RuntimeError("boom")

        config = PipelineConfig(
            name="continue",
            continue_on_error=True,
            enable_guardrails=False,
            enable_evaluation=False,
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("explode", explode))
        pipeline.add_step(FunctionStep("second", lambda d, c: "ran"))
        _, step_results = await pipeline.run("data")
        assert len(step_results) == 2
        assert step_results[0].status == StepStatus.FAILED
        assert step_results[1].status == StepStatus.COMPLETED

    async def test_failed_step_error_message_stored(self):
        def explode(d, c):
            raise ValueError("specific error message")

        config = PipelineConfig(
            name="fail", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("explode", explode))
        _, step_results = await pipeline.run("data")
        assert "specific error message" in step_results[0].error


# ---------------------------------------------------------------------------
# Pipeline: get_status
# ---------------------------------------------------------------------------


class TestPipelineStatus:
    async def test_get_status_after_successful_run(self):
        config = PipelineConfig(
            name="status_test", enable_guardrails=False, enable_evaluation=False
        )
        pipeline = Pipeline(config, steps=[FunctionStep("s1", lambda d, c: d)])
        await pipeline.run("input")
        status = pipeline.get_status()
        assert status["pipeline"] == "status_test"
        assert status["total_steps"] == 1
        assert status["executed_steps"] == 1
        assert status["completed"] == 1
        assert status["failed"] == 0

    async def test_get_status_counts_failures(self):
        def explode(d, c):
            raise RuntimeError("x")

        config = PipelineConfig(
            name="fail_status",
            continue_on_error=True,
            enable_guardrails=False,
            enable_evaluation=False,
        )
        pipeline = Pipeline(config)
        pipeline.add_step(FunctionStep("fail", explode))
        pipeline.add_step(FunctionStep("ok", lambda d, c: d))
        await pipeline.run("data")
        status = pipeline.get_status()
        assert status["failed"] == 1
        assert status["completed"] == 1

    async def test_get_status_before_run_has_zero_counts(self):
        config = PipelineConfig(name="pre_run")
        pipeline = Pipeline(config, steps=[FunctionStep("s", lambda d, c: d)])
        status = pipeline.get_status()
        assert status["executed_steps"] == 0
        assert status["completed"] == 0
        assert status["failed"] == 0


# ---------------------------------------------------------------------------
# PipelineBuilder fluent API
# ---------------------------------------------------------------------------


class TestPipelineBuilder:
    def test_builder_sets_name_and_description(self):
        pipeline = (
            PipelineBuilder("my-pipeline").with_description("A test pipeline").build()
        )
        assert pipeline.config.name == "my-pipeline"
        assert pipeline.config.description == "A test pipeline"

    def test_builder_adds_function_steps(self):
        pipeline = (
            PipelineBuilder("test")
            .with_function("step1", lambda d, c: d + 1)
            .with_function("step2", lambda d, c: d * 2)
            .build()
        )
        assert len(pipeline.steps) == 2

    async def test_builder_pipeline_executes_correctly(self):
        pipeline = (
            PipelineBuilder("test")
            .with_function("upper", lambda d, c: d.upper())
            .build()
        )
        pipeline.config.enable_guardrails = False
        pipeline.config.enable_evaluation = False
        result, _ = await pipeline.run("hello")
        assert result == "HELLO"

    def test_continue_on_error_method(self):
        pipeline = PipelineBuilder("x").continue_on_error(True).build()
        assert pipeline.config.continue_on_error is True

    def test_max_retries_method(self):
        builder = PipelineBuilder("x").with_max_retries(5)
        assert builder.config.max_retries == 5

    def test_with_step_method(self):
        custom_step = FunctionStep("custom", lambda d, c: d)
        pipeline = PipelineBuilder("x").with_step(custom_step).build()
        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].name == "custom"


# ---------------------------------------------------------------------------
# create_content_pipeline factory
# ---------------------------------------------------------------------------


class TestCreateContentPipeline:
    def test_factory_creates_pipeline_with_guardrails(self):
        p = create_content_pipeline("test-content")
        assert p.config.name == "test-content"
        assert p.guardrails is not None

    def test_factory_uses_custom_name(self):
        p = create_content_pipeline("my-custom-pipeline")
        assert p.config.name == "my-custom-pipeline"
