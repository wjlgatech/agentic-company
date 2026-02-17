#!/usr/bin/env python3
"""
Example demonstrating the diagnostics system (Phase 1).

This example shows how to use the diagnostics infrastructure:
1. Create DiagnosticsConfig
2. Use IterationMonitor to track fix-test iterations
3. Check Playwright installation

Note: This example does NOT require Playwright to be installed.
It demonstrates the core infrastructure that works without it.
"""

import asyncio
from orchestration.diagnostics import (
    DiagnosticsConfig,
    IterationMonitor,
    check_playwright_installation,
)


def main():
    """Demonstrate diagnostics system basics."""
    print("=" * 60)
    print("Diagnostics System Example (Phase 1)")
    print("=" * 60)
    print()

    # 1. Check Playwright installation
    print("1. Checking Playwright installation...")
    playwright_installed = check_playwright_installation()
    print(f"   Playwright installed: {playwright_installed}")
    if not playwright_installed:
        print("   ⚠️  Install with: pip install 'agentic-company[diagnostics]'")
        print("   Then: playwright install")
    print()

    # 2. Create DiagnosticsConfig
    print("2. Creating DiagnosticsConfig...")
    config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        browser_type="chromium",
        viewport_width=1920,
        viewport_height=1080,
        capture_screenshots=True,
        capture_console=True,
        capture_network=True,
        iteration_threshold=3,
        max_iterations=10,
    )
    print(f"   Enabled: {config.enabled}")
    print(f"   Browser: {config.browser_type}")
    print(f"   Viewport: {config.viewport_width}x{config.viewport_height}")
    print(f"   Iteration threshold: {config.iteration_threshold}")
    print(f"   Max iterations: {config.max_iterations}")
    print()

    # 3. Use IterationMonitor
    print("3. Demonstrating IterationMonitor...")
    monitor = IterationMonitor(config)
    monitor.start_step("example_step")
    print(f"   Started monitoring: example_step")
    print()

    # Simulate 3 failed iterations
    print("   Simulating fix-test iterations:")
    for i in range(3):
        record = monitor.record_iteration(
            error=f"Test failed: Error {i+1}",
            fix_attempted=f"Attempted fix {i+1}",
            test_result=False,  # Test failed
        )
        print(f"     Iteration {record.iteration}: FAIL")

        # Check if meta-analysis should trigger
        if monitor.should_trigger_meta_analysis():
            print(f"     ⚠️  Meta-analysis threshold reached!")
            print(f"     (Would trigger meta-analysis in Phase 4)")
            break
    print()

    # 4. Show iteration history
    print("4. Iteration history:")
    iterations = monitor.get_iterations()
    for record in iterations:
        print(f"   Iteration {record.iteration}:")
        print(f"     Error: {record.error}")
        print(f"     Fix: {record.fix_attempted}")
        print(f"     Result: {'PASS' if record.test_result else 'FAIL'}")
    print()

    # 5. Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✅ Core infrastructure working")
    print(f"✅ IterationMonitor tracking {len(iterations)} iterations")
    print(f"✅ Meta-analysis trigger detection working")
    print()
    print("Next Steps:")
    print("  - Phase 2: Integrate with AgentTeam")
    print("  - Phase 3: Implement auto-test loop")
    print("  - Phase 4: Add meta-analysis")
    print("  - Phase 5: Build criteria builder")
    print()


if __name__ == "__main__":
    main()
