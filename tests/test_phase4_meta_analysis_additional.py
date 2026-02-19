#!/usr/bin/env python3
"""Manual test of Phase 4 meta-analysis with real LLM."""

import asyncio
from datetime import datetime

from orchestration.diagnostics.meta_analyzer import MetaAnalyzer
from orchestration.diagnostics.iteration_monitor import IterationRecord
from orchestration.diagnostics.capture import DiagnosticCapture, ConsoleMessage
from orchestration.integrations.unified import auto_setup_executor


async def test_meta_analysis():
    """Test meta-analysis with real LLM."""
    print("=" * 60)
    print("Phase 4 Manual Test: Meta-Analysis with Real LLM")
    print("=" * 60)
    print()

    # Create executor
    print("✅ Setting up LLM executor...")
    try:
        executor = auto_setup_executor()
        print(f"   Executor: {executor.__class__.__name__}")
    except Exception as e:
        print(f"❌ Failed to setup executor: {e}")
        return
    print()

    # Create sample failure iterations
    print("📋 Creating sample failure iterations...")
    iterations = [
        IterationRecord(
            iteration=1,
            step_id="test_login",
            error="Element '#login-button' not found",
            fix_attempted="Updated selector to use ID",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Timeout waiting for selector '#login-button'",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="Uncaught TypeError: Cannot read property 'click' of null at login.js:15"
                    ),
                    ConsoleMessage(
                        type="error",
                        text="Failed to load resource: the server responded with a status of 404 ()"
                    ),
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=2,
            step_id="test_login",
            error="Element '#login-button' not found",
            fix_attempted="Added explicit wait for button to appear",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="Timeout waiting for selector '#login-button'",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="Uncaught TypeError: Cannot read property 'click' of null at login.js:15"
                    ),
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
                error="Timeout waiting for selector '#login-button'",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="Uncaught TypeError: Cannot read property 'click' of null at login.js:15"
                    ),
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
    ]

    print(f"   Created {len(iterations)} failure iterations")
    print(f"   All failures involve: Element '#login-button' not found")
    print()

    # Create analyzer
    print("🔬 Creating MetaAnalyzer...")
    analyzer = MetaAnalyzer(executor)
    print("   Analyzer ready")
    print()

    # Run analysis
    print("🚀 Running meta-analysis with LLM...")
    print("   (This may take 5-10 seconds)")
    print()

    try:
        result = await analyzer.analyze_failures(iterations)

        print("=" * 60)
        print("Meta-Analysis Results")
        print("=" * 60)
        print()

        print("📊 Pattern Detected:")
        print(f"   {result.pattern_detected}")
        print()

        print("🔍 Root Cause Hypothesis:")
        print(f"   {result.root_cause_hypothesis}")
        print()

        print("💡 Suggested Approaches:")
        for i, approach in enumerate(result.suggested_approaches, 1):
            print(f"   {i}. {approach}")
        print()

        print(f"📈 Confidence: {result.confidence:.2f}")
        print()

        if "reasoning" in result.metadata:
            print("💭 LLM Reasoning:")
            print(f"   {result.metadata['reasoning']}")
            print()

        print("📊 Metadata:")
        print(f"   Failure count: {result.metadata.get('failure_count')}")
        print(f"   Total iterations: {result.metadata.get('total_iterations')}")
        if "llm_tokens" in result.metadata:
            tokens = result.metadata["llm_tokens"]
            print(f"   LLM tokens: {tokens.get('input_tokens', 0)} in, {tokens.get('output_tokens', 0)} out")
        print()

        print("=" * 60)
        print("✅ Phase 4 Manual Test: SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


async def test_different_error_pattern():
    """Test with a different error pattern (CORS issues)."""
    print("\n\n")
    print("=" * 60)
    print("Phase 4 Test: Different Error Pattern (CORS)")
    print("=" * 60)
    print()

    # Setup executor
    print("✅ Setting up LLM executor...")
    try:
        executor = auto_setup_executor()
    except Exception as e:
        print(f"❌ Failed to setup executor: {e}")
        return
    print()

    # Create CORS-related failures
    print("📋 Creating CORS failure iterations...")
    iterations = [
        IterationRecord(
            iteration=1,
            step_id="test_api",
            error="Network request blocked by CORS policy",
            fix_attempted="Added Access-Control-Allow-Origin header",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="CORS policy: No 'Access-Control-Allow-Origin' header",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="Access to fetch at 'https://api.example.com/data' from origin 'http://localhost:3000' has been blocked by CORS policy"
                    ),
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
        IterationRecord(
            iteration=2,
            step_id="test_api",
            error="Network request blocked by CORS policy",
            fix_attempted="Configured CORS middleware",
            test_result=False,
            diagnostics=DiagnosticCapture(
                success=False,
                error="CORS policy: No 'Access-Control-Allow-Origin' header",
                console_errors=[
                    ConsoleMessage(
                        type="error",
                        text="Access to fetch at 'https://api.example.com/data' from origin 'http://localhost:3000' has been blocked by CORS policy"
                    ),
                ],
            ),
            timestamp=datetime.utcnow(),
        ),
    ]

    print(f"   Created {len(iterations)} CORS failure iterations")
    print()

    # Run analysis
    print("🚀 Running meta-analysis...")
    analyzer = MetaAnalyzer(executor)

    try:
        result = await analyzer.analyze_failures(iterations)

        print("=" * 60)
        print("CORS Analysis Results")
        print("=" * 60)
        print()

        print(f"📊 Pattern: {result.pattern_detected}")
        print(f"🔍 Root Cause: {result.root_cause_hypothesis}")
        print(f"📈 Confidence: {result.confidence:.2f}")
        print()

        print("💡 Suggested Approaches:")
        for i, approach in enumerate(result.suggested_approaches, 1):
            print(f"   {i}. {approach}")
        print()

        print("=" * 60)
        print("✅ CORS Pattern Test: SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_meta_analysis())
    asyncio.run(test_different_error_pattern())
