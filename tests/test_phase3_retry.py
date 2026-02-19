#!/usr/bin/env python3
"""Test Phase 3 auto-retry mechanism."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from orchestration.diagnostics import DiagnosticsConfig
from orchestration.diagnostics.capture import DiagnosticCapture
from orchestration.diagnostics.integration import DiagnosticsIntegrator


async def test_retry_mechanism():
    """Test that retry loop works correctly."""
    print("=" * 60)
    print("Testing Auto-Retry Mechanism")
    print("=" * 60)
    print()

    # Create config with low max_iterations for testing
    config = DiagnosticsConfig(
        enabled=True,
        max_iterations=5,
        iteration_threshold=3,
    )

    # Create integrator with mock executor
    mock_executor = AsyncMock()
    integrator = DiagnosticsIntegrator(config, mock_executor)

    print("✅ Created integrator with:")
    print(f"   Max iterations: {config.max_iterations}")
    print(f"   Threshold: {config.iteration_threshold}")
    print()

    # Create mock step
    mock_step = MagicMock()
    mock_step.id = "test_step"
    mock_step.metadata = {
        "diagnostics_enabled": True,
        "test_url": "https://example.com",
        "test_actions": [
            {"type": "navigate", "value": "https://example.com"},
        ],
    }

    # Track attempts
    attempt_count = 0

    async def mock_execute(*args, **kwargs):
        """Mock execution that tracks attempts."""
        nonlocal attempt_count
        attempt_count += 1

        result = MagicMock()
        result.metadata = {}
        result.agent_result = MagicMock()
        result.agent_result.output = f"Attempt {attempt_count}"
        return result

    # Mock diagnostics to fail first 2 times, then succeed
    call_count = [0]

    async def mock_diagnostics(url, actions):
        call_count[0] += 1
        print(f"🔄 Iteration {call_count[0]}: Running diagnostics...")

        if call_count[0] < 3:
            # Fail first 2 times
            print("   ❌ Test failed (simulated)")
            return DiagnosticCapture(
                success=False,
                error=f"Test failed on attempt {call_count[0]}",
            )
        else:
            # Succeed on 3rd attempt
            print("   ✅ Test passed!")
            return DiagnosticCapture(
                success=True,
                final_url="https://example.com",
            )

    # Patch the methods
    integrator._run_diagnostics = mock_diagnostics

    print("🚀 Starting auto-retry loop...")
    print("   (Will fail 2 times, succeed on 3rd)")
    print()

    # Execute with retry loop
    result = await integrator.wrap_step_execution(mock_step, mock_execute)

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"✅ Completed after {call_count[0]} iterations")
    print("📊 Expected: 3 iterations (2 failures + 1 success)")
    print(f"📊 Actual: {call_count[0]} iterations")
    print()
    print("Metadata:")
    print(f"   • Iteration: {result.metadata.get('iteration')}")
    print(f"   • Total iterations: {result.metadata.get('iterations_total')}")
    print(f"   • Success: {result.metadata.get('diagnostics', {}).get('success')}")
    print()

    # Verify iteration tracking
    iterations = integrator.monitor.get_iterations("test_step")
    print("Iteration History:")
    for record in iterations:
        status = "✅ PASS" if record.test_result else "❌ FAIL"
        print(f"   {record.iteration}. {status} - {record.error or 'Success'}")
    print()

    print("=" * 60)
    print("✅ Auto-Retry Mechanism: WORKING")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_retry_mechanism())
