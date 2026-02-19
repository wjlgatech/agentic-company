#!/usr/bin/env python
"""
Stress Test: MCP Tool Integration for Agenticom

This script tests the full MCP integration flow:
1. Load workflow from YAML
2. Extract tool declarations
3. Resolve tools via MCPToolBridge
4. Execute tools (mock mode)
5. Verify results

Run with: python tests/stress_test_mcp_integration.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.tools.mcp_bridge import MCPToolBridge
from orchestration.tools.registry import MCPRegistry
from orchestration.workflows.parser import WorkflowParser


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n--- {text} ---\n")


async def stress_test_mcp_integration():
    """Run comprehensive MCP integration stress test."""

    print_header("MCP Tool Integration Stress Test")
    print(f"Started: {datetime.now().isoformat()}")

    results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "errors": [],
    }

    # =========================================================================
    # TEST 1: Registry Initialization
    # =========================================================================
    print_section("Test 1: Registry Initialization")

    try:
        registry = MCPRegistry()
        categories = registry.list_categories()

        print("✓ Registry initialized")
        print(f"  Categories: {len(categories)}")
        print(f"  Sample: {', '.join(categories[:5])}...")

        assert len(categories) >= 8, "Expected at least 8 categories"
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Registry init: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 2: Tool Resolution for Marketing Workflow
    # =========================================================================
    print_section("Test 2: Tool Resolution - Marketing Workflow")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        marketing_tools = [
            "web_search",
            "social_api",
            "data_analysis",
            "text_generation",
            "image_generation",
            "messaging",
            "analytics",
            "reporting",
        ]

        report = bridge.get_resolution_report(marketing_tools)

        print("✓ Tools resolved")
        print(f"  Total: {report['summary']['total']}")
        print(f"  Resolved: {report['summary']['resolved']}")
        print(f"  Mocked: {report['summary']['mocked']}")
        print(f"  Unresolved: {report['summary']['unresolved']}")

        # Should resolve or mock at least 6 tools
        available = report["summary"]["resolved"] + report["summary"]["mocked"]
        assert available >= 6, f"Expected at least 6 available tools, got {available}"
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Marketing resolution: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 3: Tool Resolution for Research Workflow
    # =========================================================================
    print_section("Test 3: Tool Resolution - Research Workflow")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        research_tools = [
            "literature_search",
            "web_search",
            "data_analysis",
        ]

        report = bridge.get_resolution_report(research_tools)

        print("✓ Research tools resolved")
        for item in report["resolved"]:
            print(f"  → {item['name']}: {item.get('server', 'N/A')}")
        for item in report["mocked"]:
            print(f"  → {item['name']}: (mocked)")

        available = report["summary"]["resolved"] + report["summary"]["mocked"]
        assert available >= 2, f"Expected at least 2 available tools, got {available}"
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Research resolution: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 4: Mock Tool Execution - Web Search
    # =========================================================================
    print_section("Test 4: Mock Execution - Web Search")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("web_search", query="luxury real estate Miami")

        print("✓ Web search executed")
        print(f"  Success: {result['success']}")
        print(f"  Results: {len(result['data']['results'])} items")
        print(f"  Sample: {result['data']['results'][0]['title'][:50]}...")

        assert result["success"] is True
        assert len(result["data"]["results"]) > 0
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Web search exec: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 5: Mock Tool Execution - Literature Search
    # =========================================================================
    print_section("Test 5: Mock Execution - Literature Search")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute(
            "literature_search",
            query="CAR-T cell therapy resistance solid tumors 2020-2024",
        )

        print("✓ Literature search executed")
        print(f"  Success: {result['success']}")
        print(f"  Articles: {len(result['data']['articles'])}")

        for article in result["data"]["articles"]:
            print(f"  → {article['pmid']}: {article['title'][:40]}...")

        assert result["success"] is True
        assert len(result["data"]["articles"]) > 0
        assert "pmid" in result["data"]["articles"][0]
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Literature search exec: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 6: Mock Tool Execution - Social API
    # =========================================================================
    print_section("Test 6: Mock Execution - Social API")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("social_api", topic="AI startups funding")

        print("✓ Social API executed")
        print(f"  Success: {result['success']}")
        print(f"  Posts: {len(result['data']['posts'])}")
        print(f"  Metrics: sentiment={result['data']['metrics']['sentiment_score']}")

        assert result["success"] is True
        assert "posts" in result["data"]
        assert "metrics" in result["data"]
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Social API exec: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 7: Mock Tool Execution - Market Research
    # =========================================================================
    print_section("Test 7: Mock Execution - Market Research")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("market_research", company="Anthropic")

        print("✓ Market research executed")
        print(f"  Success: {result['success']}")
        print(f"  Company: {result['data']['profile']['name']}")
        print(f"  Revenue: {result['data']['metrics']['annual_revenue']}")

        assert result["success"] is True
        assert "profile" in result["data"]
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Market research exec: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 8: Concurrent Tool Execution
    # =========================================================================
    print_section("Test 8: Concurrent Tool Execution")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        # Execute 5 tools concurrently
        tasks = [
            bridge.execute("web_search", query="test 1"),
            bridge.execute("literature_search", query="test 2"),
            bridge.execute("social_api", topic="test 3"),
            bridge.execute("market_research", company="test 4"),
            bridge.execute("competitor_analysis", domain="test.com"),
        ]

        import time

        start = time.time()
        concurrent_results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print("✓ Concurrent execution completed")
        print(f"  Tasks: {len(concurrent_results)}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  All succeeded: {all(r['success'] for r in concurrent_results)}")

        assert len(concurrent_results) == 5
        assert all(r["success"] for r in concurrent_results)
        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Concurrent exec: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 9: Workflow YAML Parsing + Tool Extraction
    # =========================================================================
    print_section("Test 9: Workflow Parsing + Tool Extraction")

    try:
        parser = WorkflowParser()
        workflow_path = Path("agenticom/bundled_workflows/marketing-campaign.yaml")

        if workflow_path.exists():
            definition = parser.parse_file(workflow_path)

            # Extract all tools
            all_tools = set()
            for agent in definition.agents:
                if agent.tools:
                    all_tools.update(agent.tools)

            print(f"✓ Workflow parsed: {definition.id}")
            print(f"  Agents: {len(definition.agents)}")
            print(f"  Steps: {len(definition.steps)}")
            print(f"  Unique tools: {len(all_tools)}")
            print(f"  Tools: {', '.join(sorted(all_tools))}")

            assert len(all_tools) >= 6, "Expected at least 6 tools"
            results["tests_passed"] += 1
            print("✅ PASSED")
        else:
            print("⚠️ SKIPPED: Workflow file not found")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Workflow parsing: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # TEST 10: Full Pipeline Simulation
    # =========================================================================
    print_section("Test 10: Full Pipeline Simulation")

    try:
        bridge = MCPToolBridge(use_mocks=True)

        # Simulate marketing workflow execution
        print("Simulating marketing workflow...")

        # Step 1: Social Intelligence
        print("  Step 1: Social Intelligence")
        social = await bridge.execute("social_api", topic="luxury real estate Miami")
        assert social["success"]

        # Step 2: Competitor Analysis
        print("  Step 2: Competitor Analysis")
        competitors = await bridge.execute(
            "web_search", query="Douglas Elliman Miami real estate"
        )
        assert competitors["success"]

        # Step 3: Market Research
        print("  Step 3: Market Research")
        market = await bridge.execute("market_research", company="Compass Real Estate")
        assert market["success"]

        # Step 4: Data Analysis
        print("  Step 4: Data Analysis")
        analysis = await bridge.execute("data_analysis", dataset="market_trends")
        assert analysis["success"]

        print("✓ Pipeline completed")
        print("  Steps executed: 4/4")
        print("  All successful: True")

        results["tests_passed"] += 1
        print("✅ PASSED")

    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Pipeline simulation: {e}")
        print(f"❌ FAILED: {e}")

    results["tests_run"] += 1

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("Test Summary")

    print(f"Tests Run:    {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  ✗ {error}")

    success_rate = (results["tests_passed"] / results["tests_run"]) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if results["tests_failed"] == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ {results['tests_failed']} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(stress_test_mcp_integration())
    sys.exit(exit_code)
