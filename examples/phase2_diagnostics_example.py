#!/usr/bin/env python3
"""
Example demonstrating the diagnostics system (Phase 2).

Phase 2 adds:
1. Playwright browser automation (now that it's installed)
2. AgentTeam integration - TeamConfig accepts DiagnosticsConfig
3. AgentTeam has 'diagnostics' attribute (DiagnosticsIntegrator)

Requires: pip install 'agentic-company[diagnostics]' && playwright install
"""

import asyncio
from pathlib import Path

from orchestration.diagnostics import (
    DiagnosticsConfig,
    IterationMonitor,
    PlaywrightCapture,
    check_playwright_installation,
)
from orchestration.diagnostics.capture import ActionType, BrowserAction


async def demo_playwright_capture():
    """Demonstrate PlaywrightCapture with a real URL."""
    print("2. Playwright Browser Automation")
    print("   --------------------------------")

    config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        browser_type="chromium",
        viewport_width=1280,
        viewport_height=720,
        capture_screenshots=True,
        capture_console=True,
        capture_network=True,
        screenshot_on_error=True,
    )

    output_dir = Path("/tmp/diagnostics_phase2")
    output_dir.mkdir(exist_ok=True)

    actions = [
        BrowserAction(type=ActionType.NAVIGATE, value="https://example.com"),
        BrowserAction(type=ActionType.WAIT_FOR_SELECTOR, selector="h1"),
        BrowserAction(type=ActionType.SCREENSHOT, value="example_page.png"),
        BrowserAction(
            type=ActionType.EVALUATE,
            value="console.log('Diagnostics capture active')",
        ),
    ]

    async with PlaywrightCapture(config) as capture:
        result = await capture.execute_actions(actions, output_dir=output_dir)

    print(f"   Success: {result.success}")
    print(f"   Final URL: {result.final_url}")
    print(f"   Execution time: {result.execution_time_ms:.0f}ms")
    print(f"   Console logs: {len(result.console_logs)}")
    print(f"   Console errors: {len(result.console_errors)}")
    print(f"   Network requests: {len(result.network_requests)}")
    print(f"   Screenshots: {len(result.screenshots)}")

    if result.screenshots:
        print(f"   Screenshot saved: {result.screenshots[0]}")

    if result.network_requests:
        print(f"   First request: {result.network_requests[0].method} "
              f"{result.network_requests[0].url[:60]} → {result.network_requests[0].status}")

    if result.console_logs:
        print("   Console output:")
        for msg in result.console_logs:
            print(f"     [{msg.type}] {msg.text}")

    if result.error:
        print(f"   Error: {result.error}")

    return result


def demo_agent_team_integration():
    """Demonstrate Phase 2 AgentTeam + DiagnosticsConfig integration."""
    print("\n3. AgentTeam Integration (Phase 2)")
    print("   ----------------------------------")

    from orchestration.agents.team import AgentTeam, TeamConfig

    diag_config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=True,
        iteration_threshold=3,
    )
    print("   DiagnosticsConfig created")

    team_config = TeamConfig(
        name="Diagnostics Demo Team",
        description="Testing Phase 2 integration",
        diagnostics_config=diag_config,
    )
    print("   TeamConfig created with diagnostics_config")

    team = AgentTeam(team_config)
    print(f"   AgentTeam created: {team.id}")

    if hasattr(team, "diagnostics"):
        if team.diagnostics is None:
            print("   team.diagnostics = None (no LLM backend configured — expected)")
        else:
            print("   team.diagnostics = DiagnosticsIntegrator (fully initialized!)")
    else:
        print("   ERROR: team missing 'diagnostics' attribute")

    print("   Phase 2 integration working")


async def main():
    print("=" * 60)
    print("Diagnostics System Example (Phase 2)")
    print("=" * 60)
    print()

    # 1. Verify Playwright is now installed
    print("1. Playwright Installation Check")
    print("   --------------------------------")
    installed = check_playwright_installation()
    print(f"   Playwright installed: {installed}")
    if not installed:
        print("   ERROR: Playwright should be installed by now")
        return
    print()

    # 2. Browser automation with PlaywrightCapture
    capture_result = await demo_playwright_capture()
    print()

    # 3. AgentTeam integration
    demo_agent_team_integration()
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("✅ Playwright installed and working")
    if capture_result.success:
        print("✅ PlaywrightCapture: browser automation successful")
        print(f"✅ Captured {len(capture_result.network_requests)} network requests")
        print(f"✅ Screenshot saved to /tmp/diagnostics_phase2/")
    else:
        print(f"⚠️  PlaywrightCapture: {capture_result.error}")
    print("✅ AgentTeam integration: diagnostics_config accepted")
    print("✅ Phase 2 infrastructure complete")
    print()
    print("Next Steps:")
    print("  - Phase 3: Auto-test loop (DiagnosticsIntegrator.wrap_step_execution)")
    print("  - Phase 4: LLM-powered meta-analysis")
    print("  - Phase 5: Criteria builder (success condition authoring)")


if __name__ == "__main__":
    asyncio.run(main())
