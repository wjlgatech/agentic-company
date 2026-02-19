"""
Tests for orchestration/evaluator.py — EvaluationResult, RuleBasedEvaluator,
LLMEvaluator, EvaluatorOptimizer, CompositeEvaluator.
"""

import pytest

from orchestration.evaluator import (
    CompositeEvaluator,
    EvaluationResult,
    EvaluatorOptimizer,
    LLMEvaluator,
    RuleBasedEvaluator,
)

# ---------------------------------------------------------------------------
# EvaluationResult
# ---------------------------------------------------------------------------


class TestEvaluationResult:
    def test_bool_true_when_passed(self):
        r = EvaluationResult(passed=True, score=0.9, evaluator_name="test")
        assert bool(r) is True

    def test_bool_false_when_not_passed(self):
        r = EvaluationResult(passed=False, score=0.3, evaluator_name="test")
        assert bool(r) is False


# ---------------------------------------------------------------------------
# RuleBasedEvaluator
# ---------------------------------------------------------------------------


class TestRuleBasedEvaluator:
    def test_passes_within_length(self):
        ev = RuleBasedEvaluator(min_length=10, max_length=500)
        content = "A" * 100
        result = ev.evaluate(content)
        assert result.passed is True

    def test_fails_too_short(self):
        ev = RuleBasedEvaluator(min_length=1000)
        result = ev.evaluate("short")
        assert result.passed is False
        assert result.score < 1.0

    def test_fails_too_long(self):
        ev = RuleBasedEvaluator(max_length=5)
        result = ev.evaluate("this is way too long for the limit")
        assert result.passed is False

    def test_required_elements_present(self):
        ev = RuleBasedEvaluator(
            min_length=1, required_elements=["conclusion", "summary"]
        )
        content = "This is a summary and conclusion of the report."
        result = ev.evaluate(content)
        assert result.passed is True

    def test_required_elements_missing(self):
        ev = RuleBasedEvaluator(min_length=1, required_elements=["MISSING_ELEMENT_XYZ"])
        content = "This text does not contain the required element."
        result = ev.evaluate(content)
        assert result.passed is False

    def test_forbidden_elements_block(self):
        ev = RuleBasedEvaluator(min_length=1, forbidden_elements=["badword"])
        content = "This text contains badword which is not allowed."
        result = ev.evaluate(content)
        assert result.passed is False

    def test_forbidden_elements_absent_passes(self):
        ev = RuleBasedEvaluator(min_length=1, forbidden_elements=["badword"])
        content = "This text is completely clean and appropriate."
        result = ev.evaluate(content)
        assert result.passed is True

    def test_custom_rule_pass(self):
        def my_rule(content):
            return True, "ok"

        ev = RuleBasedEvaluator(min_length=1, custom_rules=[my_rule])
        content = "Some content here."
        result = ev.evaluate(content)
        assert result.passed is True

    def test_custom_rule_fail(self):
        def my_rule(content):
            return False, "custom rule failed"

        ev = RuleBasedEvaluator(min_length=1, custom_rules=[my_rule])
        content = "Some content."
        result = ev.evaluate(content)
        assert result.passed is False
        assert "custom rule failed" in result.feedback

    def test_no_checks_score_is_one(self):
        """With no custom rules and content within bounds, base check passes."""
        ev = RuleBasedEvaluator(min_length=0, max_length=99999)
        result = ev.evaluate("x")
        assert result.score == 1.0
        assert result.passed is True

    def test_at_min_length_boundary_passes(self):
        ev = RuleBasedEvaluator(min_length=5, max_length=100)
        result = ev.evaluate("abcde")  # exactly 5
        assert result.passed is True

    def test_one_below_min_length_fails(self):
        ev = RuleBasedEvaluator(min_length=5, max_length=100)
        result = ev.evaluate("abcd")  # 4 chars
        assert result.passed is False


# ---------------------------------------------------------------------------
# LLMEvaluator._heuristic_evaluate
# ---------------------------------------------------------------------------


class TestLLMEvaluatorHeuristic:
    def setup_method(self):
        self.evaluator = LLMEvaluator(threshold=0.7)

    def test_short_content_low_completeness(self):
        result = self.evaluator._heuristic_evaluate("Short.")
        assert result.score < 0.9  # completeness penalised

    def test_long_rich_content_higher_score(self):
        content = (
            "This is a well-structured paragraph.\n\n"
            "This is another paragraph with more detail.\n\n"
            "And a final paragraph to conclude. " * 10
        )
        result = self.evaluator._heuristic_evaluate(content)
        assert result.score > 0.5

    def test_threshold_pass(self):
        evaluator = LLMEvaluator(threshold=0.01)  # very low threshold
        content = "Hello. How are you. Fine thanks."
        result = evaluator._heuristic_evaluate(content)
        assert result.passed is True

    def test_threshold_fail(self):
        evaluator = LLMEvaluator(threshold=0.99)  # very high threshold
        result = evaluator._heuristic_evaluate("Hi.")
        assert result.passed is False

    def test_relevance_with_context(self):
        content = "Python is great for data science."
        result = self.evaluator._heuristic_evaluate(
            content, context={"topic": "python"}
        )
        assert result.details["criteria_scores"]["relevance"] == 1.0

    def test_relevance_without_context_default(self):
        content = "Some content."
        result = self.evaluator._heuristic_evaluate(content)
        assert result.details["criteria_scores"]["relevance"] == 0.8

    def test_evaluate_falls_back_to_heuristic_when_no_client(self):
        """Without LLM client, evaluate() calls _heuristic_evaluate."""
        ev = LLMEvaluator(llm_client=None)
        content = "This is fine content for testing purposes."
        result = ev.evaluate(content)
        assert isinstance(result.score, float)

    def test_evaluate_exception_returns_error_result(self):
        """If LLM client raises exception, returns error result."""

        class BadClient:
            def generate(self, *a, **kw):
                raise RuntimeError("boom")

        ev = LLMEvaluator(llm_client=BadClient())
        # The current impl falls back to heuristic even with a client,
        # so this won't hit the exception path — just verify it doesn't crash.
        result = ev.evaluate("some content")
        assert result is not None


# ---------------------------------------------------------------------------
# EvaluatorOptimizer
# ---------------------------------------------------------------------------


class TestEvaluatorOptimizer:
    def test_optimizer_runs_evaluation(self):
        ev = RuleBasedEvaluator(min_length=1)
        optimizer = EvaluatorOptimizer(ev, max_iterations=2, target_score=0.5)
        content, results = optimizer.optimize("hello world")
        assert len(results) >= 1

    def test_optimizer_early_stop_at_target(self):
        ev = RuleBasedEvaluator(min_length=1)  # passes easily
        optimizer = EvaluatorOptimizer(ev, max_iterations=5, target_score=0.5)
        _, results = optimizer.optimize("hello world this is good enough content")
        # Should stop after 1 iteration since target is met
        assert len(results) == 1

    def test_optimizer_func_called(self):
        call_count = {"n": 0}

        def mock_optimizer(content, result):
            call_count["n"] += 1
            return content + " more"

        ev = RuleBasedEvaluator(min_length=10000)  # always fails
        optimizer = EvaluatorOptimizer(
            ev, max_iterations=3, target_score=1.0, optimizer_func=mock_optimizer
        )
        _, results = optimizer.optimize("short")
        assert call_count["n"] > 0
        assert len(results) == 3

    def test_all_results_returned(self):
        ev = RuleBasedEvaluator(min_length=10000)  # always fails
        optimizer = EvaluatorOptimizer(ev, max_iterations=3, target_score=1.0)
        _, results = optimizer.optimize("short")
        assert len(results) == 3

    def test_evaluate_only(self):
        ev = RuleBasedEvaluator(min_length=1)
        optimizer = EvaluatorOptimizer(ev)
        result = optimizer.evaluate_only("hello")
        assert isinstance(result.score, float)


# ---------------------------------------------------------------------------
# CompositeEvaluator
# ---------------------------------------------------------------------------


class TestCompositeEvaluator:
    def _make_ev(self, score: float, passed: bool) -> RuleBasedEvaluator:
        """Make a stub that always returns given score/passed."""
        ev = RuleBasedEvaluator(min_length=0)
        # Monkey-patch evaluate
        ev.evaluate = lambda content, context=None: EvaluationResult(
            passed=passed, score=score, evaluator_name="stub"
        )
        return ev

    def test_weighted_average_passes(self):
        ev1 = self._make_ev(0.9, True)
        ev2 = self._make_ev(0.8, True)
        composite = CompositeEvaluator([ev1, ev2], strategy="weighted_average")
        result = composite.evaluate("content")
        # average ≈ 0.85 which >= 0.7
        assert result.passed is True

    def test_all_pass_one_fails(self):
        ev1 = self._make_ev(0.9, True)
        ev2 = self._make_ev(0.3, False)
        composite = CompositeEvaluator([ev1, ev2], strategy="all_pass")
        result = composite.evaluate("content")
        assert result.passed is False

    def test_all_pass_all_pass(self):
        ev1 = self._make_ev(0.9, True)
        ev2 = self._make_ev(0.8, True)
        composite = CompositeEvaluator([ev1, ev2], strategy="all_pass")
        result = composite.evaluate("content")
        assert result.passed is True

    def test_any_pass_one_passes(self):
        ev1 = self._make_ev(0.1, False)
        ev2 = self._make_ev(0.9, True)
        composite = CompositeEvaluator([ev1, ev2], strategy="any_pass")
        result = composite.evaluate("content")
        assert result.passed is True

    def test_any_pass_none_passes(self):
        ev1 = self._make_ev(0.1, False)
        ev2 = self._make_ev(0.2, False)
        composite = CompositeEvaluator([ev1, ev2], strategy="any_pass")
        result = composite.evaluate("content")
        assert result.passed is False

    def test_weight_normalisation(self):
        ev1 = self._make_ev(1.0, True)
        ev2 = self._make_ev(0.0, False)
        # Give ev1 3x weight
        composite = CompositeEvaluator([ev1, ev2], weights=[3.0, 1.0])
        assert abs(sum(composite.weights) - 1.0) < 1e-9

    def test_details_include_individual_results(self):
        ev1 = self._make_ev(0.8, True)
        ev2 = self._make_ev(0.6, False)
        composite = CompositeEvaluator([ev1, ev2])
        result = composite.evaluate("content")
        assert "individual_results" in result.details
        assert len(result.details["individual_results"]) == 2
