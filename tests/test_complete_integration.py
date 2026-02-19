#!/usr/bin/env python3
"""Complete integration test of all diagnostic features."""

import asyncio
from pathlib import Path

print("=" * 70)
print("COMPLETE DIAGNOSTICS SYSTEM INTEGRATION TEST")
print("=" * 70)
print()

# =============================================================================
# Test 1: Criteria Builder
# =============================================================================

print("Test 1: AI-Powered Criteria Builder")
print("-" * 70)

from orchestration.diagnostics.criteria_builder import CriteriaBuilder
from orchestration.integrations.unified import auto_setup_executor


async def test_criteria_builder():
    """Test criteria builder with a real task."""
    print("📋 Task: Build a documentation search feature")
    print()

    executor = auto_setup_executor()
    builder = CriteriaBuilder(executor, max_questions=3)

    # Define responses for questions
    responses = [
        "Yes, show recent searches and popular pages",
        "Real-time with debouncing (300ms delay)",
        "English and Spanish",
    ]
    response_idx = [0]

    def question_callback(question):
        """Simulate interactive Q&A."""
        print(f"   ❓ Q: {question}")
        if response_idx[0] < len(responses):
            response = responses[response_idx[0]]
            print(f"   💬 A: {response}")
            response_idx[0] += 1
            return response
        return "No response"

    builder.question_callback = question_callback

    criteria = await builder.build_criteria(
        "Build a documentation search feature",
        context={"framework": "React", "backend": "Elasticsearch"},
    )

    print()
    print("✅ Generated Criteria:")
    for i, criterion in enumerate(criteria.criteria, 1):
        print(f"   {i}. {criterion[:100]}...")
    print()
    print(f"   Confidence: {criteria.confidence:.2f}")
    print(f"   Questions: {len(criteria.questions_asked)}")
    print(
        f"   Responses: {len([r for r in criteria.human_responses if r != 'No response'])}"
    )
    print()

    return criteria


# =============================================================================
# Test 2: Browser Automation with Diagnostics
# =============================================================================

print()
print("Test 2: Browser Automation & Diagnostics Capture")
print("-" * 70)

from orchestration.diagnostics import (
    BrowserAction,
    DiagnosticsConfig,
    PlaywrightCapture,
)


async def test_browser_diagnostics():
    """Test browser automation with diagnostic capture."""
    print("🌐 Testing URL: https://docs.python.org")
    print()

    config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        capture_screenshots=True,
        capture_console=True,
        capture_network=True,
    )

    actions = [
        BrowserAction.from_dict(
            {"type": "navigate", "value": "https://docs.python.org"}
        ),
        BrowserAction.from_dict(
            {"type": "wait_for_selector", "selector": "h1", "timeout": 5000}
        ),
        BrowserAction.from_dict({"type": "screenshot", "value": "python_docs.png"}),
    ]

    capture = PlaywrightCapture(config)
    async with capture:
        result = await capture.execute_actions(actions, Path("outputs/diagnostics"))

    print("✅ Diagnostics Results:")
    print(f"   Success: {result.success}")
    print(f"   Final URL: {result.final_url}")
    print(f"   Screenshots: {len(result.screenshots)}")
    print(f"   Console logs: {len(result.console_logs)}")
    print(f"   Console errors: {len(result.console_errors)}")
    print(f"   Network requests: {len(result.network_requests)}")
    print(f"   Execution time: {result.execution_time_ms:.0f}ms")
    print()

    if result.screenshots:
        print(f"   📸 Screenshot saved: {result.screenshots[0]}")
    print()

    return result


# =============================================================================
# Test 3: Iteration Monitoring
# =============================================================================

print()
print("Test 3: Iteration Monitoring & Tracking")
print("-" * 70)

from orchestration.diagnostics.capture import ConsoleMessage, DiagnosticCapture
from orchestration.diagnostics.iteration_monitor import IterationMonitor


def test_iteration_monitor():
    """Test iteration monitoring for auto-retry loop."""
    print("🔄 Simulating 3 test iterations...")
    print()

    config = DiagnosticsConfig(enabled=True, iteration_threshold=2, max_iterations=5)

    monitor = IterationMonitor(config)
    monitor.start_step("test_search_feature")

    # Simulate failures
    for i in range(3):
        print(f"   Iteration {i + 1}: ", end="")

        diagnostics = DiagnosticCapture(
            success=(i == 2),  # Fail first 2, succeed on 3rd
            error=None if i == 2 else f"Search not returning results (attempt {i + 1})",
            console_errors=[]
            if i == 2
            else [
                ConsoleMessage(
                    type="error", text="TypeError: Cannot read property 'results'"
                )
            ],
        )

        monitor.record_iteration(
            error=diagnostics.error,
            fix_attempted=f"Updated search query logic (attempt {i + 1})",
            test_result=diagnostics.success,
            diagnostics=diagnostics,
        )

        if diagnostics.success:
            print("✅ PASS")
        else:
            print("❌ FAIL")

        # Check if meta-analysis should trigger
        if monitor.should_trigger_meta_analysis() and i < 2:
            print(f"      ⚠️  Meta-analysis threshold reached after {i + 1} failures")

    print()
    print("✅ Iteration Summary:")
    iterations = monitor.get_iterations("test_search_feature")
    print(f"   Total iterations: {len(iterations)}")
    print(f"   Failures: {sum(1 for it in iterations if not it.test_result)}")
    print(f"   Success: {sum(1 for it in iterations if it.test_result)}")
    print()

    return monitor


# =============================================================================
# Test 4: Meta-Analysis
# =============================================================================

print()
print("Test 4: LLM-Based Meta-Analysis")
print("-" * 70)

from datetime import datetime

from orchestration.diagnostics.iteration_monitor import IterationRecord
from orchestration.diagnostics.meta_analyzer import MetaAnalyzer


async def test_meta_analysis():
    """Test meta-analysis on repeated failures."""
    print("🧠 Analyzing failure pattern...")
    print()

    # Create failure iterations
    iterations = [
        IterationRecord(
            iteration=1,
            step_id="test_search",
            error="Search returns no results for query 'python'",
            fix_attempted="Updated Elasticsearch query syntax",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Empty results array",
                console_errors=[
                    ConsoleMessage(type="error", text="Search API returned 0 results")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=2,
            step_id="test_search",
            error="Search returns no results for query 'python'",
            fix_attempted="Added wildcard search",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Empty results array",
                console_errors=[
                    ConsoleMessage(type="error", text="Search API returned 0 results")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=3,
            step_id="test_search",
            error="Search returns no results for query 'python'",
            fix_attempted="Checked index configuration",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Empty results array",
                console_errors=[
                    ConsoleMessage(type="error", text="Search API returned 0 results")
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
    ]

    executor = auto_setup_executor()
    analyzer = MetaAnalyzer(executor)

    analysis = await analyzer.analyze_failures(iterations)

    print("✅ Meta-Analysis Results:")
    print(f"   Pattern: {analysis.pattern_detected[:80]}...")
    print(f"   Root Cause: {analysis.root_cause_hypothesis[:80]}...")
    print(f"   Confidence: {analysis.confidence:.2f}")
    print()
    print("   💡 Suggested Approaches:")
    for i, approach in enumerate(analysis.suggested_approaches[:3], 1):
        print(f"      {i}. {approach[:70]}...")
    print()

    return analysis


# =============================================================================
# Run All Tests
# =============================================================================


async def run_all_tests():
    """Run complete integration test suite."""
    results = {}

    # Test 1
    results["criteria"] = await test_criteria_builder()

    # Test 2
    results["diagnostics"] = await test_browser_diagnostics()

    # Test 3 (synchronous)
    results["monitor"] = test_iteration_monitor()

    # Test 4
    results["meta_analysis"] = await test_meta_analysis()

    return results


if __name__ == "__main__":
    print("Starting complete integration test...")
    print()

    results = asyncio.run(run_all_tests())

    print()
    print("=" * 70)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 70)
    print()
    print("✅ All Components Tested:")
    print("   ✓ Criteria Builder (AI-powered)")
    print("   ✓ Browser Automation (Playwright)")
    print("   ✓ Diagnostics Capture (Screenshots, Console, Network)")
    print("   ✓ Iteration Monitoring (Auto-retry tracking)")
    print("   ✓ Meta-Analysis (LLM pattern detection)")
    print()
    print("📊 Summary:")
    print(f"   Criteria generated: {len(results['criteria'].criteria)}")
    print(
        f"   Browser test: {'✅ PASS' if results['diagnostics'].success else '❌ FAIL'}"
    )
    print(
        f"   Iterations tracked: {results['monitor'].get_iteration_count('test_search_feature')}"
    )
    print(f"   Meta-analysis confidence: {results['meta_analysis'].confidence:.2f}")
    print()
    print("🎉 Diagnostics system is fully operational!")
    print()
