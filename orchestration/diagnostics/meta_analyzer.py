"""Meta-analysis of repeated test failures (Phase 4 - To be implemented)."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

import structlog

from .iteration_monitor import IterationRecord

logger = structlog.get_logger(__name__)


@dataclass
class MetaAnalysis:
    """Result of meta-analysis on repeated failures.

    Attributes:
        pattern_detected: Description of the failure pattern
        root_cause_hypothesis: Hypothesized root cause
        suggested_approaches: List of alternative approaches to try
        confidence: Confidence level in analysis (0-1)
        metadata: Additional metadata
    """

    pattern_detected: str
    root_cause_hypothesis: str
    suggested_approaches: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_detected": self.pattern_detected,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "suggested_approaches": self.suggested_approaches,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class MetaAnalyzer:
    """LLM-based failure pattern analysis.

    Analyzes repeated test failures to identify patterns, hypothesize root causes,
    and suggest alternative approaches.

    Note: This is a Phase 4 feature. Basic structure is provided but full
    implementation will be added in Phase 4.

    Example:
        ```python
        analyzer = MetaAnalyzer(executor)
        analysis = await analyzer.analyze_failures(iteration_records)

        print(f"Pattern: {analysis.pattern_detected}")
        print(f"Root cause: {analysis.root_cause_hypothesis}")
        for approach in analysis.suggested_approaches:
            print(f"  - {approach}")
        ```
    """

    def __init__(self, executor: Any):
        """Initialize meta-analyzer.

        Args:
            executor: LLM executor for analysis
        """
        self.executor = executor

    async def analyze_failures(
        self, iterations: List[IterationRecord]
    ) -> MetaAnalysis:
        """Analyze repeated failures and suggest alternatives.

        Args:
            iterations: List of iteration records

        Returns:
            MetaAnalysis with pattern detection and suggestions
        """
        logger.info("Running meta-analysis", iteration_count=len(iterations))

        if not iterations:
            logger.warning("No iterations to analyze")
            return MetaAnalysis(
                pattern_detected="No iterations available",
                root_cause_hypothesis="No data to analyze",
                suggested_approaches=[],
                confidence=0.0,
            )

        # Format iteration history for LLM
        iteration_history = self._format_iterations(iterations)
        failure_count = sum(1 for it in iterations if not it.test_result)

        # Build comprehensive prompt for LLM
        prompt = f"""You are an expert software debugging assistant analyzing repeated test failures.

## Test Failure History

{iteration_history}

## Analysis Task

After {failure_count} failed attempts with automated browser testing, identify:

1. **Pattern Detection**: What keeps failing? Look for common elements:
   - Same error messages repeated?
   - Same element selectors failing?
   - Timing/race condition issues?
   - API/network failures?
   - JavaScript errors?

2. **Root Cause Hypothesis**: What is the most likely underlying cause?
   - Consider: timing issues, incorrect selectors, missing elements, API problems
   - Look for patterns across multiple failures
   - Consider both implementation bugs and test configuration issues

3. **Alternative Approaches**: Suggest 3-5 concrete alternative strategies:
   - Different implementation approaches
   - Better error handling
   - Improved waiting strategies
   - Alternative selectors or APIs
   - Configuration changes

4. **Confidence**: Rate your confidence (0.0-1.0) based on:
   - Pattern clarity (same error repeatedly = high confidence)
   - Available diagnostic data (console errors, network logs)
   - Number of iterations analyzed

## Response Format

Provide analysis as JSON:

```json
{{
  "pattern_detected": "Clear description of what keeps failing (1-2 sentences)",
  "root_cause_hypothesis": "Most likely root cause (2-3 sentences)",
  "suggested_approaches": [
    "Specific actionable approach 1",
    "Specific actionable approach 2",
    "Specific actionable approach 3",
    "Specific actionable approach 4 (optional)",
    "Specific actionable approach 5 (optional)"
  ],
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your analysis (2-3 sentences)"
}}
```

Focus on actionable insights. Be specific about what to change and why."""

        try:
            # Call LLM executor
            logger.debug("Calling LLM for meta-analysis")
            response = await self.executor.execute(prompt)

            # Parse response - handle both string and dict formats
            if isinstance(response, dict):
                result_text = response.get("content", "")
                usage = response.get("usage", {})
            else:
                # UnifiedExecutor returns string directly
                result_text = response
                usage = {}

            # Extract JSON from response (handle code blocks)
            json_text = result_text
            if "```json" in result_text:
                # Extract from code block
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                json_text = result_text[start:end].strip()
            elif "```" in result_text:
                # Extract from generic code block
                start = result_text.find("```") + 3
                end = result_text.find("```", start)
                json_text = result_text[start:end].strip()

            # Parse JSON
            try:
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError:
                # Fallback: try to parse the whole response
                logger.warning("Failed to parse JSON from LLM response, attempting fallback")
                analysis_data = json.loads(result_text)

            # Extract fields with defaults
            pattern = analysis_data.get("pattern_detected", "Unknown pattern")
            root_cause = analysis_data.get("root_cause_hypothesis", "Unknown root cause")
            approaches = analysis_data.get("suggested_approaches", [])
            confidence = float(analysis_data.get("confidence", 0.5))
            reasoning = analysis_data.get("reasoning", "")

            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))

            logger.info(
                "Meta-analysis completed",
                pattern=pattern[:100],
                confidence=confidence,
                approaches_count=len(approaches)
            )

            return MetaAnalysis(
                pattern_detected=pattern,
                root_cause_hypothesis=root_cause,
                suggested_approaches=approaches,
                confidence=confidence,
                metadata={
                    "reasoning": reasoning,
                    "failure_count": failure_count,
                    "total_iterations": len(iterations),
                    "llm_tokens": usage,
                },
            )

        except Exception as e:
            logger.error("Meta-analysis failed", error=str(e), exc_info=True)

            # Fallback to basic analysis
            return MetaAnalysis(
                pattern_detected=f"Repeated failures after {failure_count} attempts",
                root_cause_hypothesis=f"Analysis failed: {str(e)}",
                suggested_approaches=[
                    "Review console errors in diagnostic screenshots",
                    "Check network requests for API failures",
                    "Verify element selectors match the actual DOM",
                    "Add explicit waits for dynamic content",
                    "Check for JavaScript errors preventing page load",
                ],
                confidence=0.3,
                metadata={
                    "error": str(e),
                    "failure_count": failure_count,
                    "fallback": True,
                },
            )

    def _format_iterations(self, iterations: List[IterationRecord]) -> str:
        """Format iteration history for LLM prompt.

        Args:
            iterations: List of iteration records

        Returns:
            Formatted string for LLM prompt
        """
        lines = []
        for record in iterations:
            lines.append(f"Iteration {record.iteration}:")
            lines.append(f"  Error: {record.error}")
            lines.append(f"  Fix attempted: {record.fix_attempted}")
            lines.append(f"  Test result: {'PASS' if record.test_result else 'FAIL'}")

            if record.diagnostics:
                lines.append(f"  Console errors: {len(record.diagnostics.console_errors)}")
                if record.diagnostics.console_errors:
                    for error in record.diagnostics.console_errors[:3]:  # First 3
                        lines.append(f"    - {error.text[:100]}")

            lines.append("")

        return "\n".join(lines)
