#!/usr/bin/env python
"""
Stress Test: Real-Life Examples (No Mock Data)

Tests the 3 README examples using real MCP tools where available,
with graceful fallback for tools that need user connection.

Examples tested:
1. Real Estate Marketing Team
2. Biomedical Research Deep Dive
3. Idea to Product with PMF

Run with: python tests/stress_test_real_examples.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.tools.mcp_bridge import MCPToolBridge


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 50}")
    print(f"  {text}")
    print(f"{'─' * 50}\n")


def print_result(result: dict, indent: int = 2) -> None:
    """Print a tool execution result."""
    prefix = " " * indent

    if result.get("success"):
        print(f"{prefix}✅ SUCCESS ({result.get('status', 'unknown')})")
        print(f"{prefix}   Server: {result.get('server', 'N/A')}")
        if "data" in result:
            data = result["data"]
            if isinstance(data, dict):
                # Show summary of data
                if "results" in data:
                    print(f"{prefix}   Results: {len(data['results'])} items")
                if "articles" in data:
                    print(f"{prefix}   Articles: {len(data['articles'])} found")
                if "posts" in data:
                    print(f"{prefix}   Posts: {len(data['posts'])} found")
                if "competitors" in data:
                    print(f"{prefix}   Competitors: {len(data['competitors'])} found")
                if "note" in data.get("metadata", {}):
                    print(f"{prefix}   Note: {data['metadata']['note']}")

    elif result.get("status") == "waiting":
        print(f"{prefix}⏳ WAITING FOR CONNECTION")
        print(f"{prefix}   Tool: {result.get('tool', 'unknown')}")
        print(f"{prefix}   Server: {result.get('server', 'unknown')}")
        print(
            f"{prefix}   Action: {result.get('action_required', 'Connect MCP server')}"
        )
        if "suggestion" in result:
            print(f"{prefix}   Suggestion: {result['suggestion'][:80]}...")
        if "partial_result" in result:
            partial = result["partial_result"]
            print(f"{prefix}   Would search: {partial.get('would_search', 'N/A')}")

    else:
        print(f"{prefix}❌ FAILED")
        print(f"{prefix}   Error: {result.get('error', 'Unknown error')}")
        if "suggestion" in result:
            print(f"{prefix}   Suggestion: {result['suggestion']}")


async def test_example_1_real_estate():
    """
    Example 1: Real Estate Marketing Team

    Task: Create a complete digital marketing strategy for a luxury real estate
    agency in Miami targeting international buyers.
    """
    print_header("Example 1: Real Estate Marketing Team")

    print("Task: Create digital marketing strategy for luxury real estate in Miami")
    print("Required tools: web_search, social_api, data_analysis, competitor_analysis")
    print()

    # Use bridge without mocks - graceful mode enabled
    bridge = MCPToolBridge(use_mocks=False, graceful_mode=True)

    results = {
        "total": 0,
        "success": 0,
        "waiting": 0,
        "failed": 0,
    }

    # Step 1: Social Media Intelligence - Find pain points
    print_section("Step 1: Social Intelligence - Pain Points & Opportunities")
    result = await bridge.execute(
        "social_api", topic="luxury real estate Miami international buyers frustrations"
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 2: Competitor Analysis
    print_section("Step 2: Competitor Analysis")
    competitors = ["Douglas Elliman", "Compass", "Sotheby's International"]

    for competitor in competitors:
        print(f"\n  Analyzing: {competitor}")
        result = await bridge.execute(
            "competitor_analysis", domain=f"{competitor.lower().replace(' ', '')}.com"
        )
        print_result(result, indent=4)
        results["total"] += 1
        if result.get("success"):
            results["success"] += 1
        elif result.get("status") == "waiting":
            results["waiting"] += 1
        else:
            results["failed"] += 1

    # Step 3: Web Research - Market trends
    print_section("Step 3: Market Research - Trends & Insights")
    result = await bridge.execute(
        "web_search",
        query="Miami luxury real estate market 2024 2025 international buyers trends",
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 4: Data Analysis
    print_section("Step 4: Data Analysis - Market Metrics")
    result = await bridge.execute("data_analysis", dataset="miami_real_estate_metrics")
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    return results


async def test_example_2_biomedical_research():
    """
    Example 2: Biomedical Research Deep Dive

    Task: Research CAR-T cell therapy resistance in solid tumors.
    Scout literature (2020-2024), categorize resistance mechanisms.
    """
    print_header("Example 2: Biomedical Research Deep Dive")

    print("Task: Research CAR-T cell therapy resistance in solid tumors")
    print("Required tools: literature_search, web_search, data_analysis")
    print()

    bridge = MCPToolBridge(use_mocks=False, graceful_mode=True)

    results = {
        "total": 0,
        "success": 0,
        "waiting": 0,
        "failed": 0,
    }

    # Step 1: Literature Search - Main query
    print_section("Step 1: Literature Search - CAR-T Resistance Mechanisms")
    result = await bridge.execute(
        "literature_search",
        query="CAR-T cell therapy resistance solid tumors 2020-2024",
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 2: Literature Search - Specific mechanisms
    print_section("Step 2: Literature Search - Tumor Microenvironment")
    result = await bridge.execute(
        "literature_search",
        query="tumor microenvironment CAR-T immunosuppression 2022-2024",
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 3: Web Search - Latest developments
    print_section("Step 3: Web Search - Latest Clinical Trials")
    result = await bridge.execute(
        "web_search", query="CAR-T solid tumor clinical trials 2024 results"
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 4: Literature Search - Novel approaches
    print_section("Step 4: Literature Search - Novel Approaches")
    result = await bridge.execute(
        "literature_search", query="armored CAR-T fourth generation solid tumors"
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    return results


async def test_example_3_startup_validation():
    """
    Example 3: Idea to Product with PMF

    Task: Validate startup idea - AI copilot for freelance consultants
    that turns client calls into SOWs and invoices.
    """
    print_header("Example 3: Startup Validation - AI Copilot for Consultants")

    print("Task: Validate AI copilot for freelance consultants (calls → SOWs/invoices)")
    print("Required tools: market_research, competitor_analysis, web_search")
    print()

    bridge = MCPToolBridge(use_mocks=False, graceful_mode=True)

    results = {
        "total": 0,
        "success": 0,
        "waiting": 0,
        "failed": 0,
    }

    # Step 1: Market Research - Target market
    print_section("Step 1: Market Research - Freelance Consulting Market")
    result = await bridge.execute(
        "market_research", company="freelance consulting AI automation market"
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 2: Competitor Analysis
    print_section("Step 2: Competitor Analysis")
    competitors = [
        ("Otter.ai", "otter.ai"),
        ("Fireflies.ai", "fireflies.ai"),
        ("Honeybook", "honeybook.com"),
        ("Dubsado", "dubsado.com"),
    ]

    for name, domain in competitors:
        print(f"\n  Analyzing: {name}")
        result = await bridge.execute("competitor_analysis", domain=domain)
        print_result(result, indent=4)
        results["total"] += 1
        if result.get("success"):
            results["success"] += 1
        elif result.get("status") == "waiting":
            results["waiting"] += 1
        else:
            results["failed"] += 1

    # Step 3: Web Search - Problem validation
    print_section("Step 3: Web Search - Problem Validation")
    result = await bridge.execute(
        "web_search",
        query="freelance consultant pain points invoicing scope of work manual process",
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    # Step 4: Web Search - Market size
    print_section("Step 4: Web Search - Market Size")
    result = await bridge.execute(
        "web_search", query="freelance consulting market size 2024 2025 growth TAM SAM"
    )
    print_result(result)
    results["total"] += 1
    if result.get("success"):
        results["success"] += 1
    elif result.get("status") == "waiting":
        results["waiting"] += 1
    else:
        results["failed"] += 1

    return results


async def main():
    """Run all stress tests."""
    print_header("STRESS TEST: Real-Life Examples (No Mock Data)")
    print(f"Started: {datetime.now().isoformat()}")
    print("\nThis test runs WITHOUT mock data.")
    print("Tools will either use real MCP connections or wait gracefully.")

    all_results = {
        "total": 0,
        "success": 0,
        "waiting": 0,
        "failed": 0,
    }

    # Run all examples
    examples = [
        ("Example 1: Real Estate Marketing", test_example_1_real_estate),
        ("Example 2: Biomedical Research", test_example_2_biomedical_research),
        ("Example 3: Startup Validation", test_example_3_startup_validation),
    ]

    example_results = []

    for name, test_func in examples:
        try:
            results = await test_func()
            example_results.append((name, results))

            for key in ["total", "success", "waiting", "failed"]:
                all_results[key] += results[key]

        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback

            traceback.print_exc()

    # Summary
    print_header("STRESS TEST SUMMARY")

    print("Results by Example:")
    print("-" * 50)
    for name, results in example_results:
        print(f"\n  {name}:")
        print(f"    Total calls: {results['total']}")
        print(f"    ✅ Success:  {results['success']}")
        print(f"    ⏳ Waiting:  {results['waiting']}")
        print(f"    ❌ Failed:   {results['failed']}")

    print("\n" + "=" * 50)
    print("OVERALL RESULTS:")
    print("=" * 50)
    print(f"  Total tool calls:     {all_results['total']}")
    print(f"  ✅ Successful:        {all_results['success']}")
    print(f"  ⏳ Waiting for MCP:   {all_results['waiting']}")
    print(f"  ❌ Failed:            {all_results['failed']}")

    # Calculate percentages
    if all_results["total"] > 0:
        success_rate = (all_results["success"] / all_results["total"]) * 100
        waiting_rate = (all_results["waiting"] / all_results["total"]) * 100
        failed_rate = (all_results["failed"] / all_results["total"]) * 100

        print(f"\n  Success rate:         {success_rate:.1f}%")
        print(f"  Waiting rate:         {waiting_rate:.1f}%")
        print(f"  Failed rate:          {failed_rate:.1f}%")

    # Conclusions
    print("\n" + "=" * 50)
    print("CONCLUSIONS:")
    print("=" * 50)

    if all_results["waiting"] > 0:
        print(f"\n⏳ {all_results['waiting']} tool(s) are waiting for MCP connection.")
        print("   To enable real data:")
        print("   1. Connect MCP servers via Claude Desktop or mcporter")
        print("   2. Available servers:")
        print("      • PubMed: https://pubmed.mcp.claude.com")
        print("      • Ahrefs: https://api.ahrefs.com/mcp/mcp")
        print("      • Similarweb: https://mcp.similarweb.com")
        print("      • Harmonic: https://mcp.api.harmonic.ai")

    if all_results["success"] > 0:
        print(f"\n✅ {all_results['success']} tool(s) executed successfully.")
        print("   These used either:")
        print("   • Connected MCP servers")
        print("   • Fallback implementations")

    if all_results["failed"] == 0 and all_results["total"] > 0:
        print("\n🎉 NO FAILURES! All tools handled gracefully.")
        return 0
    elif all_results["failed"] > 0:
        print(f"\n⚠️ {all_results['failed']} tool(s) failed unexpectedly.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
