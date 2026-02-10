"""
Evaluator-Optimizer system for assessing and improving AI outputs.

Provides rule-based and LLM-based evaluation with optimization loops.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass
class EvaluationResult:
    """Result from an evaluation."""

    passed: bool
    score: float  # 0.0 to 1.0
    evaluator_name: str
    feedback: str = ""
    suggestions: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __bool__(self) -> bool:
        return self.passed


class BaseEvaluator(ABC):
    """Abstract base class for evaluators."""

    name: str = "base"

    @abstractmethod
    def evaluate(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Evaluate content and return result."""
        pass


class RuleBasedEvaluator(BaseEvaluator):
    """Rule-based evaluator with configurable criteria."""

    name = "rule_based"

    def __init__(
        self,
        min_length: int = 100,
        max_length: int = 10000,
        required_elements: Optional[list[str]] = None,
        forbidden_elements: Optional[list[str]] = None,
        custom_rules: Optional[list[Callable[[str], tuple[bool, str]]]] = None,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.required_elements = required_elements or []
        self.forbidden_elements = forbidden_elements or []
        self.custom_rules = custom_rules or []

    def evaluate(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Evaluate content against rules."""
        issues = []
        suggestions = []
        checks_passed = 0
        total_checks = 4 + len(self.custom_rules)

        content_lower = content.lower()

        # Length check
        if len(content) < self.min_length:
            issues.append(f"Content too short ({len(content)} < {self.min_length})")
            suggestions.append(f"Add more content to reach at least {self.min_length} characters")
        elif len(content) > self.max_length:
            issues.append(f"Content too long ({len(content)} > {self.max_length})")
            suggestions.append(f"Reduce content to under {self.max_length} characters")
        else:
            checks_passed += 1

        # Required elements
        missing_elements = [
            elem for elem in self.required_elements
            if elem.lower() not in content_lower
        ]
        if missing_elements:
            issues.append(f"Missing required elements: {missing_elements}")
            suggestions.append(f"Include these elements: {missing_elements}")
        else:
            checks_passed += 1

        # Forbidden elements
        found_forbidden = [
            elem for elem in self.forbidden_elements
            if elem.lower() in content_lower
        ]
        if found_forbidden:
            issues.append(f"Contains forbidden elements: {found_forbidden}")
            suggestions.append(f"Remove these elements: {found_forbidden}")
        else:
            checks_passed += 1

        # Custom rules
        custom_passed = 0
        for rule in self.custom_rules:
            passed, message = rule(content)
            if passed:
                custom_passed += 1
            else:
                issues.append(message)
                suggestions.append(f"Fix: {message}")

        checks_passed += custom_passed
        checks_passed += 1  # Base check always passes

        score = checks_passed / total_checks if total_checks > 0 else 1.0
        passed = len(issues) == 0

        return EvaluationResult(
            passed=passed,
            score=score,
            evaluator_name=self.name,
            feedback="; ".join(issues) if issues else "All checks passed",
            suggestions=suggestions,
            details={
                "length": len(content),
                "missing_elements": missing_elements,
                "forbidden_found": found_forbidden,
                "checks_passed": checks_passed,
                "total_checks": total_checks,
            },
        )


class LLMEvaluator(BaseEvaluator):
    """LLM-based evaluator using AI to assess content."""

    name = "llm"

    def __init__(
        self,
        criteria: Optional[list[str]] = None,
        llm_client: Optional[Any] = None,
        model: str = "claude-sonnet-4-20250514",
        threshold: float = 0.7,
    ):
        self.criteria = criteria or [
            "clarity",
            "completeness",
            "accuracy",
            "relevance",
        ]
        self.llm_client = llm_client
        self.model = model
        self.threshold = threshold

    def evaluate(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Evaluate content using LLM."""
        # If no LLM client, fall back to heuristic evaluation
        if self.llm_client is None:
            return self._heuristic_evaluate(content, context)

        try:
            # Build evaluation prompt
            criteria_list = "\n".join(f"- {c}" for c in self.criteria)
            prompt = f"""Evaluate the following content on these criteria:
{criteria_list}

For each criterion, provide a score from 0 to 10.
Then provide overall feedback and suggestions for improvement.

Content:
{content}

Respond in JSON format:
{{
    "scores": {{"criterion": score, ...}},
    "overall_score": float (0-1),
    "feedback": "string",
    "suggestions": ["suggestion1", ...]
}}
"""
            # This would call the actual LLM
            # response = self.llm_client.generate(prompt)
            # For now, use heuristic
            return self._heuristic_evaluate(content, context)

        except Exception as e:
            return EvaluationResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                feedback=f"Evaluation failed: {str(e)}",
                suggestions=["Try again or use rule-based evaluation"],
            )

    def _heuristic_evaluate(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Heuristic evaluation when LLM is not available."""
        scores = {}
        suggestions = []

        # Clarity: sentence structure
        sentences = content.split(".")
        avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        scores["clarity"] = min(1.0, 1.0 - abs(15 - avg_sentence_len) / 30)
        if avg_sentence_len > 25:
            suggestions.append("Consider shorter sentences for clarity")

        # Completeness: length relative to typical content
        scores["completeness"] = min(1.0, len(content) / 500)
        if len(content) < 200:
            suggestions.append("Content may be incomplete, consider adding more detail")

        # Structure: paragraphs and formatting
        paragraphs = content.split("\n\n")
        scores["structure"] = min(1.0, len(paragraphs) / 3)
        if len(paragraphs) < 2:
            suggestions.append("Consider breaking content into paragraphs")

        # Relevance: based on context if provided
        if context and "topic" in context:
            topic = context["topic"].lower()
            scores["relevance"] = 1.0 if topic in content.lower() else 0.5
        else:
            scores["relevance"] = 0.8  # Default when no context

        overall_score = sum(scores.values()) / len(scores)
        passed = overall_score >= self.threshold

        return EvaluationResult(
            passed=passed,
            score=overall_score,
            evaluator_name=self.name,
            feedback=f"Overall score: {overall_score:.2f}",
            suggestions=suggestions,
            details={"criteria_scores": scores},
        )


class EvaluatorOptimizer:
    """Optimization loop that evaluates and improves content iteratively."""

    def __init__(
        self,
        evaluator: BaseEvaluator,
        max_iterations: int = 3,
        target_score: float = 0.8,
        optimizer_func: Optional[Callable[[str, EvaluationResult], str]] = None,
    ):
        self.evaluator = evaluator
        self.max_iterations = max_iterations
        self.target_score = target_score
        self.optimizer_func = optimizer_func

    def optimize(
        self,
        content: str,
        context: Optional[dict] = None,
    ) -> tuple[str, list[EvaluationResult]]:
        """Run optimization loop to improve content."""
        results = []
        current_content = content

        for i in range(self.max_iterations):
            result = self.evaluator.evaluate(current_content, context)
            results.append(result)

            # Check if we've reached target
            if result.score >= self.target_score:
                break

            # Try to optimize if we have an optimizer function
            if self.optimizer_func and i < self.max_iterations - 1:
                current_content = self.optimizer_func(current_content, result)

        return current_content, results

    def evaluate_only(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Run evaluation without optimization."""
        return self.evaluator.evaluate(content, context)


class CompositeEvaluator(BaseEvaluator):
    """Combine multiple evaluators."""

    name = "composite"

    def __init__(
        self,
        evaluators: list[BaseEvaluator],
        weights: Optional[list[float]] = None,
        strategy: str = "weighted_average",  # weighted_average, all_pass, any_pass
    ):
        self.evaluators = evaluators
        self.weights = weights or [1.0] * len(evaluators)
        self.strategy = strategy

        # Normalize weights
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]

    def evaluate(self, content: str, context: Optional[dict] = None) -> EvaluationResult:
        """Evaluate using all evaluators."""
        results = []
        for evaluator in self.evaluators:
            result = evaluator.evaluate(content, context)
            results.append(result)

        if self.strategy == "weighted_average":
            weighted_score = sum(
                r.score * w for r, w in zip(results, self.weights)
            )
            passed = weighted_score >= 0.7
        elif self.strategy == "all_pass":
            weighted_score = sum(r.score * w for r, w in zip(results, self.weights))
            passed = all(r.passed for r in results)
        else:  # any_pass
            weighted_score = max(r.score for r in results)
            passed = any(r.passed for r in results)

        all_feedback = [r.feedback for r in results if r.feedback]
        all_suggestions = []
        for r in results:
            all_suggestions.extend(r.suggestions)

        return EvaluationResult(
            passed=passed,
            score=weighted_score,
            evaluator_name=self.name,
            feedback="; ".join(all_feedback),
            suggestions=all_suggestions,
            details={
                "individual_results": [
                    {"evaluator": r.evaluator_name, "score": r.score, "passed": r.passed}
                    for r in results
                ]
            },
        )
