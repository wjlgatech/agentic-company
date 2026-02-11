"""
Tests for MCPToolBridge - the integration layer between Agenticom and MCP.

These tests verify:
1. Tool resolution from workflow YAML declarations
2. MCP registry queries
3. Tool execution (mock mode)
4. Agent binding
"""

import asyncio
import pytest
from pathlib import Path

from orchestration.tools.registry import MCPRegistry, RegistryEntry, get_registry
from orchestration.tools.mcp_bridge import (
    MCPToolBridge,
    MCPTool,
    ToolMapping,
    ToolStatus,
    get_bridge,
    resolve_workflow_tools,
    execute_tool,
)


# =============================================================================
# Registry Tests
# =============================================================================

class TestMCPRegistry:
    """Tests for MCP Registry."""

    def test_registry_initialization(self):
        """Registry should initialize with built-in mappings."""
        registry = MCPRegistry()

        assert registry is not None
        assert len(registry.BUILTIN_MAPPINGS) > 0
        assert "web_search" in registry.BUILTIN_MAPPINGS
        assert "literature_search" in registry.BUILTIN_MAPPINGS

    def test_list_categories(self):
        """Registry should list all tool categories."""
        registry = MCPRegistry()
        categories = registry.list_categories()

        assert "web_search" in categories
        assert "literature_search" in categories
        assert "social_api" in categories
        assert "market_research" in categories

    def test_get_tools_for_category(self):
        """Registry should return tools for a category."""
        registry = MCPRegistry()

        # Literature search should have PubMed
        tools = registry.get_tools_for_category("literature_search")
        assert len(tools) > 0
        assert any(t.name == "PubMed" for t in tools)

        # Web search should have Ahrefs
        tools = registry.get_tools_for_category("web_search")
        assert len(tools) > 0
        assert any(t.name == "Ahrefs" for t in tools)

    def test_resolve_tool(self):
        """Registry should resolve tool names to entries."""
        registry = MCPRegistry()

        # Known tool
        entry = registry.resolve_tool("literature_search")
        assert entry is not None
        assert entry.name == "PubMed"

        # Unknown tool
        entry = registry.resolve_tool("nonexistent_tool")
        assert entry is None

    def test_search(self):
        """Registry should search for tools by keyword."""
        registry = MCPRegistry()

        results = registry.search(["pubmed", "research"])
        assert len(results) > 0

        results = registry.search(["web", "search"])
        assert len(results) > 0


# =============================================================================
# Tool Resolution Tests
# =============================================================================

class TestToolResolution:
    """Tests for tool resolution."""

    def test_resolve_single_tool(self):
        """Bridge should resolve a single tool."""
        bridge = MCPToolBridge()

        tool = bridge.resolve_tool("web_search")

        assert tool is not None
        assert tool.declared_name == "web_search"
        assert tool.server_name in ["Ahrefs", "Similarweb"]
        assert tool.status in [ToolStatus.RESOLVED, ToolStatus.UNAVAILABLE]

    def test_resolve_workflow_tools(self):
        """Bridge should resolve multiple tools from workflow."""
        bridge = MCPToolBridge()

        tools = bridge.resolve_workflow_tools([
            "web_search",
            "literature_search",
            "social_api",
        ])

        assert len(tools) == 3
        assert all(isinstance(t, MCPTool) for t in tools)

    def test_resolution_caching(self):
        """Bridge should cache resolved tools."""
        bridge = MCPToolBridge()

        tool1 = bridge.resolve_tool("web_search")
        tool2 = bridge.resolve_tool("web_search")

        assert tool1 is tool2  # Same object from cache

    def test_resolution_report(self):
        """Bridge should generate resolution report."""
        bridge = MCPToolBridge(use_mocks=True)

        report = bridge.get_resolution_report([
            "web_search",
            "literature_search",
            "nonexistent_tool",
        ])

        assert "resolved" in report
        assert "mocked" in report
        assert "unresolved" in report
        assert "summary" in report
        assert report["summary"]["total"] == 3


# =============================================================================
# Tool Execution Tests (Mock Mode)
# =============================================================================

class TestToolExecution:
    """Tests for tool execution in mock mode."""

    @pytest.mark.asyncio
    async def test_execute_web_search(self):
        """Should execute mock web search."""
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("web_search", query="CAR-T therapy")

        assert result["success"] is True
        assert "data" in result
        assert "results" in result["data"]
        assert len(result["data"]["results"]) > 0

    @pytest.mark.asyncio
    async def test_execute_literature_search(self):
        """Should execute mock literature search."""
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("literature_search", query="cancer immunotherapy")

        assert result["success"] is True
        assert "data" in result
        assert "articles" in result["data"]
        assert len(result["data"]["articles"]) > 0

        # Check article structure
        article = result["data"]["articles"][0]
        assert "pmid" in article
        assert "title" in article
        assert "authors" in article

    @pytest.mark.asyncio
    async def test_execute_social_api(self):
        """Should execute mock social API."""
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("social_api", topic="AI startups")

        assert result["success"] is True
        assert "data" in result
        assert "posts" in result["data"]

    @pytest.mark.asyncio
    async def test_execute_market_research(self):
        """Should execute mock market research."""
        bridge = MCPToolBridge(use_mocks=True)

        result = await bridge.execute("market_research", company="Anthropic")

        assert result["success"] is True
        assert "data" in result
        assert "profile" in result["data"]

    @pytest.mark.asyncio
    async def test_execute_unavailable_tool(self):
        """Should handle unavailable tool gracefully."""
        bridge = MCPToolBridge(use_mocks=False)

        result = await bridge.execute("nonexistent_tool")

        assert result["success"] is False
        assert "error" in result


# =============================================================================
# Workflow Integration Tests
# =============================================================================

class TestWorkflowIntegration:
    """Tests for workflow integration."""

    def test_parse_workflow_tools(self):
        """Should parse tools from workflow YAML."""
        from orchestration.workflows.parser import WorkflowParser

        parser = WorkflowParser()

        # Load marketing workflow
        workflow_path = Path("agenticom/bundled_workflows/marketing-campaign.yaml")
        if workflow_path.exists():
            definition = parser.parse_file(workflow_path)

            # Check that agents have tools
            tools_found = []
            for agent in definition.agents:
                if agent.tools:
                    tools_found.extend(agent.tools)

            assert len(tools_found) > 0
            assert "web_search" in tools_found or "social_api" in tools_found

    def test_resolve_marketing_workflow_tools(self):
        """Should resolve all tools from marketing workflow."""
        bridge = MCPToolBridge(use_mocks=True)

        # Tools declared in marketing-campaign.yaml
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

        # Should resolve most tools
        assert report["summary"]["resolved"] + report["summary"]["mocked"] >= 4

    @pytest.mark.asyncio
    async def test_execute_marketing_workflow_tools(self):
        """Should execute tools needed for marketing workflow."""
        bridge = MCPToolBridge(use_mocks=True)

        # Step 1: Social intelligence
        social_result = await bridge.execute("social_api", topic="luxury real estate Miami")
        assert social_result["success"] is True

        # Step 2: Competitor analysis
        competitor_result = await bridge.execute("web_search", query="Douglas Elliman Miami")
        assert competitor_result["success"] is True

        # Step 3: Market research
        market_result = await bridge.execute("market_research", company="Compass Real Estate")
        assert market_result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_research_workflow_tools(self):
        """Should execute tools needed for research workflow."""
        bridge = MCPToolBridge(use_mocks=True)

        # Literature search
        lit_result = await bridge.execute(
            "literature_search",
            query="CAR-T cell therapy resistance solid tumors 2020-2024"
        )
        assert lit_result["success"] is True
        assert "articles" in lit_result["data"]

        # Each article should have required fields
        for article in lit_result["data"]["articles"]:
            assert "pmid" in article
            assert "title" in article
            assert "authors" in article


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_bridge(self):
        """Should return bridge instance."""
        bridge = get_bridge()
        assert isinstance(bridge, MCPToolBridge)

        bridge_mocked = get_bridge(use_mocks=True)
        assert bridge_mocked.use_mocks is True

    def test_resolve_workflow_tools_function(self):
        """Should resolve tools via convenience function."""
        tools = resolve_workflow_tools(["web_search", "literature_search"])
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_execute_tool_function(self):
        """Should execute tool via convenience function."""
        result = await execute_tool("web_search", query="test")
        assert result["success"] is True


# =============================================================================
# Stress Tests
# =============================================================================

class TestStress:
    """Stress tests for MCP bridge."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Should handle concurrent tool calls."""
        bridge = MCPToolBridge(use_mocks=True)

        # Execute multiple tools concurrently
        tasks = [
            bridge.execute("web_search", query="test 1"),
            bridge.execute("literature_search", query="test 2"),
            bridge.execute("social_api", topic="test 3"),
            bridge.execute("market_research", company="test 4"),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 4
        assert all(r["success"] for r in results)

    def test_large_tool_list_resolution(self):
        """Should handle resolving many tools."""
        bridge = MCPToolBridge(use_mocks=True)

        # Resolve many tools
        tools = bridge.resolve_workflow_tools([
            "web_search",
            "literature_search",
            "social_api",
            "market_research",
            "competitor_analysis",
            "data_analysis",
            "crm",
            "analytics",
            "reporting",
            "messaging",
        ])

        assert len(tools) == 10


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
