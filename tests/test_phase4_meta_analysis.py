"""Tests for Phase 4: Meta-Analysis."""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from orchestration.diagnostics.meta_analyzer import MetaAnalyzer, MetaAnalysis
from orchestration.diagnostics.iteration_monitor import IterationRecord
from orchestration.diagnostics.capture import DiagnosticCapture, ConsoleMessage


# ============== Fixtures ==============


@pytest.fixture
def mock_executor():
    """Create a mock LLM executor."""
    executor = AsyncMock()
    executor.execute = AsyncMock()
    return executor


@pytest.fixture
def sample_iterations():
    """Create sample iteration records for testing."""
    return [
        IterationRecord(
            iteration=1,
            step_id="test_login",
            error="Element '#login-button' not found",
            fix_attempted="Updated selector to use ID",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Timeout waiting for selector",
                console_errors=[
                    ConsoleMessage(type="error", text="Uncaught TypeError: Cannot read property 'click' of null")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=2,
            step_id="test_login",
            error="Element '#login-button' not found",
            fix_attempted="Added wait for element to load",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Timeout waiting for selector",
                console_errors=[
                    ConsoleMessage(type="error", text="Uncaught TypeError: Cannot read property 'click' of null")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=3,
            step_id="test_login",
            error="Element '#login-button' not found",
            fix_attempted="Changed selector to button[type='submit']",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Timeout waiting for selector",
                console_errors=[
                    ConsoleMessage(type="error", text="Uncaught TypeError: Cannot read property 'click' of null")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
    ]


# ============== Unit Tests ==============


def test_meta_analyzer_initialization(mock_executor):
    """Test MetaAnalyzer initializes correctly."""
    analyzer = MetaAnalyzer(mock_executor)
    assert analyzer.executor == mock_executor


@pytest.mark.asyncio
async def test_analyze_failures_empty_iterations(mock_executor):
    """Test analyze_failures with empty iteration list."""
    analyzer = MetaAnalyzer(mock_executor)

    result = await analyzer.analyze_failures([])

    assert result.pattern_detected == "No iterations available"
    assert result.root_cause_hypothesis == "No data to analyze"
    assert result.confidence == 0.0
    assert result.suggested_approaches == []


@pytest.mark.asyncio
async def test_analyze_failures_with_mock_llm(mock_executor, sample_iterations):
    """Test analyze_failures with mocked LLM response."""
    # Mock LLM response
    mock_executor.execute.return_value = {
        "content": json.dumps({
            "pattern_detected": "Same element selector failing repeatedly",
            "root_cause_hypothesis": "The login button selector is incorrect or the element loads dynamically",
            "suggested_approaches": [
                "Use a more specific CSS selector like button.login-btn",
                "Add explicit wait for button to be clickable",
                "Check if button is inside an iframe",
                "Verify button exists in the DOM using browser console",
            ],
            "confidence": 0.85,
            "reasoning": "The same selector error appears in all 3 iterations, indicating a persistent selector issue",
        }),
        "usage": {"input_tokens": 500, "output_tokens": 100},
    }

    analyzer = MetaAnalyzer(mock_executor)
    result = await analyzer.analyze_failures(sample_iterations)

    # Verify LLM was called
    assert mock_executor.execute.called

    # Verify result structure
    assert result.pattern_detected == "Same element selector failing repeatedly"
    assert "selector is incorrect" in result.root_cause_hypothesis
    assert len(result.suggested_approaches) == 4
    assert result.confidence == 0.85
    assert "reasoning" in result.metadata
    assert result.metadata["failure_count"] == 3
    assert result.metadata["total_iterations"] == 3


@pytest.mark.asyncio
async def test_analyze_failures_json_in_code_block(mock_executor, sample_iterations):
    """Test parsing JSON from LLM code block."""
    # Mock LLM response with code block
    mock_executor.execute.return_value = {
        "content": """Here's my analysis:

```json
{
  "pattern_detected": "Selector timing issue",
  "root_cause_hypothesis": "Button loads after page render",
  "suggested_approaches": ["Add wait", "Use data attributes"],
  "confidence": 0.75,
  "reasoning": "Pattern is clear"
}
```

Hope this helps!""",
        "usage": {"input_tokens": 500, "output_tokens": 100},
    }

    analyzer = MetaAnalyzer(mock_executor)
    result = await analyzer.analyze_failures(sample_iterations)

    assert result.pattern_detected == "Selector timing issue"
    assert result.confidence == 0.75


@pytest.mark.asyncio
async def test_analyze_failures_llm_error_fallback(mock_executor, sample_iterations):
    """Test fallback when LLM call fails."""
    # Mock LLM to raise exception
    mock_executor.execute.side_effect = Exception("LLM API error")

    analyzer = MetaAnalyzer(mock_executor)
    result = await analyzer.analyze_failures(sample_iterations)

    # Should return fallback analysis
    assert "Repeated failures" in result.pattern_detected
    assert "Analysis failed" in result.root_cause_hypothesis
    assert len(result.suggested_approaches) >= 3
    assert result.confidence == 0.3
    assert result.metadata.get("fallback") is True
    assert "error" in result.metadata


@pytest.mark.asyncio
async def test_analyze_failures_invalid_json_fallback(mock_executor, sample_iterations):
    """Test fallback when LLM returns invalid JSON."""
    # Mock LLM response with invalid JSON
    mock_executor.execute.return_value = {
        "content": "This is not valid JSON at all!",
        "usage": {"input_tokens": 500, "output_tokens": 50},
    }

    analyzer = MetaAnalyzer(mock_executor)
    result = await analyzer.analyze_failures(sample_iterations)

    # Should return fallback analysis
    assert result.confidence == 0.3
    assert result.metadata.get("fallback") is True


@pytest.mark.asyncio
async def test_confidence_clamped_to_range(mock_executor, sample_iterations):
    """Test that confidence is clamped to [0.0, 1.0] range."""
    # Mock LLM response with out-of-range confidence
    mock_executor.execute.return_value = {
        "content": json.dumps({
            "pattern_detected": "Test pattern",
            "root_cause_hypothesis": "Test cause",
            "suggested_approaches": ["Approach 1"],
            "confidence": 1.5,  # Out of range
            "reasoning": "Test reasoning",
        }),
        "usage": {},
    }

    analyzer = MetaAnalyzer(mock_executor)
    result = await analyzer.analyze_failures(sample_iterations)

    # Confidence should be clamped to 1.0
    assert result.confidence == 1.0


def test_format_iterations(mock_executor, sample_iterations):
    """Test _format_iterations helper method."""
    analyzer = MetaAnalyzer(mock_executor)
    formatted = analyzer._format_iterations(sample_iterations)

    # Verify formatting
    assert "Iteration 1:" in formatted
    assert "Iteration 2:" in formatted
    assert "Iteration 3:" in formatted
    assert "Error: Element '#login-button' not found" in formatted
    assert "Fix attempted:" in formatted
    assert "Test result: FAIL" in formatted
    assert "Console errors:" in formatted


# ============== Integration Tests (Require LLM) ==============


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analyze_failures_real_llm(sample_iterations):
    """Test analyze_failures with real LLM executor.

    Note: This test requires a real LLM executor to be configured.
    Skip if no LLM backend is available.
    """
    pytest.importorskip("anthropic")  # Skip if Anthropic not installed

    try:
        from orchestration.integrations.unified import auto_setup_executor
        executor = auto_setup_executor()
    except Exception:
        pytest.skip("No LLM executor available")

    analyzer = MetaAnalyzer(executor)
    result = await analyzer.analyze_failures(sample_iterations)

    # Verify result structure
    assert isinstance(result, MetaAnalysis)
    assert len(result.pattern_detected) > 0
    assert len(result.root_cause_hypothesis) > 0
    assert len(result.suggested_approaches) >= 3
    assert 0.0 <= result.confidence <= 1.0
    assert "failure_count" in result.metadata

    # Log for manual inspection
    print("\n" + "="*60)
    print("Real LLM Meta-Analysis Result")
    print("="*60)
    print(f"Pattern: {result.pattern_detected}")
    print(f"Root Cause: {result.root_cause_hypothesis}")
    print(f"Confidence: {result.confidence}")
    print("\nSuggested Approaches:")
    for i, approach in enumerate(result.suggested_approaches, 1):
        print(f"  {i}. {approach}")
    print("="*60)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_meta_analysis_with_different_error_types():
    """Test meta-analysis with different types of errors."""
    pytest.importorskip("anthropic")

    try:
        from orchestration.integrations.unified import auto_setup_executor
        executor = auto_setup_executor()
    except Exception:
        pytest.skip("No LLM executor available")

    # Create iterations with different error types
    iterations = [
        IterationRecord(
            iteration=1,
            step_id="test_api",
            error="Network timeout",
            fix_attempted="Increased timeout to 10s",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Network request failed",
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=2,
            step_id="test_api",
            error="CORS policy error",
            fix_attempted="Added CORS headers",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Access-Control-Allow-Origin missing",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="CORS policy: No 'Access-Control-Allow-Origin' header"
                    )
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=3,
            step_id="test_api",
            error="CORS policy error",
            fix_attempted="Configured proxy",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Access-Control-Allow-Origin missing",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="CORS policy: No 'Access-Control-Allow-Origin' header"
                    )
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
    ]

    analyzer = MetaAnalyzer(executor)
    result = await analyzer.analyze_failures(iterations)

    # Verify analysis addresses CORS issue
    assert isinstance(result, MetaAnalysis)
    assert result.confidence > 0.5  # Should be confident about CORS pattern

    # Pattern should mention CORS or network issues
    pattern_lower = result.pattern_detected.lower()
    assert "cors" in pattern_lower or "network" in pattern_lower or "access" in pattern_lower


# ============== MetaAnalysis Dataclass Tests ==============


def test_meta_analysis_to_dict():
    """Test MetaAnalysis.to_dict() conversion."""
    analysis = MetaAnalysis(
        pattern_detected="Test pattern",
        root_cause_hypothesis="Test cause",
        suggested_approaches=["Approach 1", "Approach 2"],
        confidence=0.8,
        metadata={"key": "value"},
    )

    result = analysis.to_dict()

    assert result["pattern_detected"] == "Test pattern"
    assert result["root_cause_hypothesis"] == "Test cause"
    assert result["suggested_approaches"] == ["Approach 1", "Approach 2"]
    assert result["confidence"] == 0.8
    assert result["metadata"] == {"key": "value"}


def test_meta_analysis_defaults():
    """Test MetaAnalysis default values."""
    analysis = MetaAnalysis(
        pattern_detected="Pattern",
        root_cause_hypothesis="Cause",
    )

    assert analysis.suggested_approaches == []
    assert analysis.confidence == 0.0
    assert analysis.metadata == {}
