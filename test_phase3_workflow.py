#!/usr/bin/env python3
"""Manual test of Phase 3 auto-test loop."""

import asyncio
from pathlib import Path

from orchestration.diagnostics import DiagnosticsConfig
from orchestration.diagnostics.integration import DiagnosticsIntegrator
from orchestration.diagnostics.capture import BrowserAction, ActionType


async def test_simple_browser_automation():
    """Test simple browser automation."""
    print("=" * 60)
    print("Phase 3 Manual Test: Browser Automation")
    print("=" * 60)
    print()

    # Create diagnostics config
    config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=False,  # Set to True to run headless
        max_iterations=3,
        iteration_threshold=2,
        capture_screenshots=True,
        capture_console=True,
        capture_network=True,
    )

    print("✅ DiagnosticsConfig created")
    print(f"   Max iterations: {config.max_iterations}")
    print(f"   Headless: {config.playwright_headless}")
    print()

    # Create integrator
    integrator = DiagnosticsIntegrator(config, executor=None)
    print("✅ DiagnosticsIntegrator created")
    print()

    # Define test actions
    test_url = "https://example.com"
    test_actions = [
        {"type": "navigate", "value": "https://example.com"},
        {"type": "wait_for_selector", "selector": "h1", "timeout": 5000},
        {"type": "screenshot", "value": "example_page.png"},
    ]

    print("📋 Test Configuration:")
    print(f"   URL: {test_url}")
    print(f"   Actions: {len(test_actions)}")
    for i, action in enumerate(test_actions, 1):
        print(f"     {i}. {action['type']}", end="")
        if 'selector' in action:
            print(f" ({action['selector']})", end="")
        if 'value' in action:
            print(f" → {action['value']}", end="")
        print()
    print()

    # Run diagnostics
    print("🚀 Running browser automation...")
    print()

    try:
        result = await integrator._run_diagnostics(test_url, test_actions)

        print("=" * 60)
        print("Results")
        print("=" * 60)
        print(f"✅ Success: {result.success}")
        print(f"📊 Console logs: {len(result.console_logs)}")
        print(f"❌ Console errors: {len(result.console_errors)}")
        print(f"🌐 Network requests: {len(result.network_requests)}")
        print(f"📸 Screenshots: {len(result.screenshots)}")
        print(f"🔗 Final URL: {result.final_url}")
        print(f"⏱️  Execution time: {result.execution_time_ms:.0f}ms")
        print()

        if result.screenshots:
            print("📸 Screenshots saved:")
            for screenshot in result.screenshots:
                print(f"   • {screenshot}")
            print()

        if result.console_logs:
            print("📋 Console logs (first 3):")
            for log in result.console_logs[:3]:
                print(f"   [{log.type}] {log.text[:80]}")
            print()

        if result.network_requests:
            print("🌐 Network requests (first 5):")
            for req in result.network_requests[:5]:
                print(f"   {req.method} {req.url[:60]}... ({req.status or 'pending'})")
            print()

        print("=" * 60)
        print("✅ Phase 3 Manual Test: SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_browser_automation())
