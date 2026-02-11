"""
MCP Tool Bridge for Agenticom.

This module bridges the gap between Agenticom's workflow tool declarations
and actual MCP (Model Context Protocol) servers. It:

1. Reads tool declarations from workflow YAML
2. Queries MCP registry for matching tools
3. Binds tools to agent executors
4. Executes tool calls and returns real data

Architecture:
    Workflow YAML → MCPToolBridge → MCP Registry → MCP Servers → Real Data
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from enum import Enum

from .registry import MCPRegistry, RegistryEntry, get_registry

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Status of a tool binding."""
    UNRESOLVED = "unresolved"      # Not yet looked up
    RESOLVED = "resolved"          # Found in registry
    CONNECTED = "connected"        # Authenticated and ready
    UNAVAILABLE = "unavailable"    # Not found or not accessible
    MOCK = "mock"                  # Using mock implementation


@dataclass
class MCPTool:
    """
    Represents a resolved MCP tool ready for execution.

    This is the bridge between an Agenticom tool declaration
    and an actual MCP server endpoint.
    """

    # From Agenticom workflow
    declared_name: str  # e.g., "web_search"

    # From MCP registry
    server_name: str = ""           # e.g., "Ahrefs"
    server_url: str = ""            # e.g., "https://api.ahrefs.com/mcp/mcp"
    available_tools: list[str] = field(default_factory=list)

    # Status
    status: ToolStatus = ToolStatus.UNRESOLVED

    # Execution
    executor: Optional[Callable] = None

    def __str__(self) -> str:
        return f"MCPTool({self.declared_name} → {self.server_name} [{self.status.value}])"

    @property
    def is_ready(self) -> bool:
        """Check if tool is ready for execution."""
        return self.status in (ToolStatus.CONNECTED, ToolStatus.MOCK)


@dataclass
class ToolMapping:
    """
    Maps Agenticom tool categories to MCP servers.

    This allows workflows to declare abstract tools like "web_search"
    and have them automatically resolved to concrete MCP implementations.
    """

    category: str           # e.g., "web_search"
    primary: str            # Primary MCP server name
    fallbacks: list[str] = field(default_factory=list)  # Backup servers

    @classmethod
    def from_dict(cls, data: dict) -> "ToolMapping":
        return cls(
            category=data.get("category", ""),
            primary=data.get("primary", ""),
            fallbacks=data.get("fallbacks", []),
        )


class MCPToolBridge:
    """
    Bridge between Agenticom workflow tools and MCP servers.

    This is the main integration class that:
    1. Parses tool declarations from workflow definitions
    2. Resolves them to MCP servers via the registry
    3. Provides executors that agents can use
    4. Handles tool calls and returns results

    Example:
        bridge = MCPToolBridge()

        # From a workflow YAML with tools: [web_search, literature_search]
        tools = bridge.resolve_workflow_tools(["web_search", "literature_search"])

        # Bind to an agent
        agent.set_tools(tools)

        # Execute a tool
        result = await bridge.execute("web_search", query="CAR-T therapy")
    """

    def __init__(
        self,
        registry: Optional[MCPRegistry] = None,
        use_mocks: bool = False,
        mcporter_path: Optional[str] = None,
    ):
        """
        Initialize the MCP Tool Bridge.

        Args:
            registry: MCP registry to use (default: built-in registry)
            use_mocks: If True, use mock implementations for testing
            mcporter_path: Path to mcporter CLI (for direct MCP calls)
        """
        self.registry = registry or get_registry()
        self.use_mocks = use_mocks
        self.mcporter_path = mcporter_path or self._find_mcporter()

        # Cache of resolved tools
        self._resolved_tools: dict[str, MCPTool] = {}

        # Mock implementations for testing
        self._mocks: dict[str, Callable] = self._setup_mocks()

    def _find_mcporter(self) -> Optional[str]:
        """Find mcporter CLI in PATH."""
        try:
            result = subprocess.run(
                ["which", "mcporter"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _setup_mocks(self) -> dict[str, Callable]:
        """Setup mock implementations for testing."""
        return {
            "web_search": self._mock_web_search,
            "literature_search": self._mock_literature_search,
            "social_api": self._mock_social_api,
            "market_research": self._mock_market_research,
            "competitor_analysis": self._mock_competitor_analysis,
            "data_analysis": self._mock_data_analysis,
        }

    # =========================================================================
    # TOOL RESOLUTION
    # =========================================================================

    def resolve_workflow_tools(self, tool_names: list[str]) -> list[MCPTool]:
        """
        Resolve a list of tool names from a workflow to MCPTools.

        Args:
            tool_names: List of tool names from workflow YAML

        Returns:
            List of resolved MCPTool objects
        """
        resolved = []
        for name in tool_names:
            tool = self.resolve_tool(name)
            resolved.append(tool)
        return resolved

    def resolve_tool(self, tool_name: str) -> MCPTool:
        """
        Resolve a single tool name to an MCPTool.

        Args:
            tool_name: Tool name from workflow (e.g., "web_search")

        Returns:
            Resolved MCPTool object
        """
        # Check cache
        if tool_name in self._resolved_tools:
            return self._resolved_tools[tool_name]

        # Query registry
        entry = self.registry.resolve_tool(tool_name)

        if entry:
            tool = MCPTool(
                declared_name=tool_name,
                server_name=entry.name,
                server_url=entry.url,
                available_tools=entry.tools,
                status=ToolStatus.RESOLVED,
            )

            # Check if connected
            if self.registry.is_connected(entry.name):
                tool.status = ToolStatus.CONNECTED
                tool.executor = self._create_mcp_executor(entry)
            elif self.use_mocks and tool_name in self._mocks:
                tool.status = ToolStatus.MOCK
                tool.executor = self._mocks[tool_name]

        else:
            # Not found in registry
            tool = MCPTool(
                declared_name=tool_name,
                status=ToolStatus.UNAVAILABLE,
            )

            # Use mock if available
            if self.use_mocks and tool_name in self._mocks:
                tool.status = ToolStatus.MOCK
                tool.executor = self._mocks[tool_name]

        # Cache and return
        self._resolved_tools[tool_name] = tool
        return tool

    def get_resolution_report(self, tool_names: list[str]) -> dict:
        """
        Get a detailed report of tool resolution.

        Args:
            tool_names: List of tool names to check

        Returns:
            Dict with resolution details for each tool
        """
        report = {
            "resolved": [],
            "unresolved": [],
            "mocked": [],
            "summary": {},
        }

        for name in tool_names:
            tool = self.resolve_tool(name)

            if tool.status == ToolStatus.CONNECTED:
                report["resolved"].append({
                    "name": name,
                    "server": tool.server_name,
                    "url": tool.server_url,
                    "tools": tool.available_tools,
                })
            elif tool.status == ToolStatus.MOCK:
                report["mocked"].append({
                    "name": name,
                    "note": "Using mock implementation",
                })
            elif tool.status == ToolStatus.RESOLVED:
                report["resolved"].append({
                    "name": name,
                    "server": tool.server_name,
                    "url": tool.server_url,
                    "note": "Found but not connected",
                })
            else:
                report["unresolved"].append({
                    "name": name,
                    "note": "No MCP server found",
                })

        report["summary"] = {
            "total": len(tool_names),
            "resolved": len(report["resolved"]),
            "mocked": len(report["mocked"]),
            "unresolved": len(report["unresolved"]),
        }

        return report

    # =========================================================================
    # TOOL EXECUTION
    # =========================================================================

    async def execute(
        self,
        tool_name: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute a tool call.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        tool = self.resolve_tool(tool_name)

        if not tool.is_ready:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not ready: {tool.status.value}",
                "suggestion": self._get_setup_suggestion(tool_name),
            }

        if tool.executor:
            try:
                result = await tool.executor(**kwargs)
                return {
                    "success": True,
                    "tool": tool_name,
                    "server": tool.server_name,
                    "data": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "tool": tool_name,
                }

        return {
            "success": False,
            "error": "No executor available",
        }

    def _create_mcp_executor(self, entry: RegistryEntry) -> Callable:
        """Create an executor for an MCP server."""

        async def executor(**kwargs) -> dict:
            # Use mcporter if available
            if self.mcporter_path:
                return await self._call_via_mcporter(entry, kwargs)

            # Otherwise return placeholder
            return {
                "note": f"Would call {entry.name} MCP server",
                "url": entry.url,
                "args": kwargs,
            }

        return executor

    async def _call_via_mcporter(
        self,
        entry: RegistryEntry,
        args: dict,
    ) -> dict:
        """Execute MCP call via mcporter CLI."""
        # Find appropriate tool
        tool_name = entry.tools[0] if entry.tools else "default"

        cmd = [
            self.mcporter_path,
            "call",
            f"{entry.name.lower()}.{tool_name}",
            "--output", "json",
        ]

        # Add arguments
        for key, value in args.items():
            cmd.append(f"{key}={value}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr}

        except Exception as e:
            return {"error": str(e)}

    def _get_setup_suggestion(self, tool_name: str) -> str:
        """Get setup suggestion for an unavailable tool."""
        suggestions = {
            "web_search": "Connect Ahrefs or Similarweb via MCP",
            "literature_search": "Connect PubMed MCP: https://pubmed.mcp.claude.com",
            "social_api": "Connect LunarCrush or Twitter MCP",
            "market_research": "Connect Harmonic or S&P Global MCP",
        }
        return suggestions.get(tool_name, f"Search MCP registry for '{tool_name}'")

    # =========================================================================
    # MOCK IMPLEMENTATIONS (for testing)
    # =========================================================================

    async def _mock_web_search(self, query: str = "", **kwargs) -> dict:
        """Mock web search results."""
        return {
            "source": "mock",
            "query": query,
            "results": [
                {
                    "title": f"Result 1 for: {query}",
                    "url": "https://example.com/1",
                    "snippet": f"This is a mock search result about {query}...",
                    "traffic": "2.3M monthly visits",
                },
                {
                    "title": f"Result 2 for: {query}",
                    "url": "https://example.com/2",
                    "snippet": f"Another relevant result discussing {query}...",
                    "traffic": "1.1M monthly visits",
                },
            ],
            "metadata": {
                "total_results": 2,
                "search_time_ms": 142,
                "note": "MOCK DATA - Connect real MCP for live results",
            },
        }

    async def _mock_literature_search(self, query: str = "", **kwargs) -> dict:
        """Mock literature search results."""
        return {
            "source": "mock",
            "query": query,
            "articles": [
                {
                    "pmid": "12345678",
                    "title": f"Research on {query}: A Comprehensive Review",
                    "authors": ["Smith J", "Jones A", "Williams B"],
                    "journal": "Nature Medicine",
                    "year": 2024,
                    "abstract": f"This study investigates {query} and its implications...",
                    "doi": "10.1038/nm.12345",
                },
                {
                    "pmid": "87654321",
                    "title": f"Novel Approaches to {query}",
                    "authors": ["Chen X", "Kumar R"],
                    "journal": "Cell",
                    "year": 2023,
                    "abstract": f"We present new findings regarding {query}...",
                    "doi": "10.1016/j.cell.2023.12345",
                },
            ],
            "metadata": {
                "total_results": 2,
                "database": "PubMed (mock)",
                "note": "MOCK DATA - Connect PubMed MCP for real papers",
            },
        }

    async def _mock_social_api(self, topic: str = "", **kwargs) -> dict:
        """Mock social media data."""
        return {
            "source": "mock",
            "topic": topic,
            "posts": [
                {
                    "platform": "Twitter",
                    "author": "@researcher",
                    "content": f"Interesting developments in {topic}! 🧵",
                    "engagement": {"likes": 1234, "retweets": 456},
                    "sentiment": "positive",
                },
                {
                    "platform": "Reddit",
                    "subreddit": "r/science",
                    "title": f"Question about {topic}",
                    "upvotes": 892,
                    "comments": 156,
                    "sentiment": "neutral",
                },
            ],
            "metrics": {
                "total_mentions": 15420,
                "sentiment_score": 0.72,
                "trending": True,
            },
            "metadata": {
                "note": "MOCK DATA - Connect LunarCrush for real social data",
            },
        }

    async def _mock_market_research(self, company: str = "", **kwargs) -> dict:
        """Mock market research data."""
        return {
            "source": "mock",
            "company": company,
            "profile": {
                "name": company or "Example Corp",
                "industry": "Technology",
                "founded": 2015,
                "employees": "500-1000",
                "funding": "$50M Series C",
                "headquarters": "San Francisco, CA",
            },
            "metrics": {
                "annual_revenue": "$25M",
                "growth_rate": "45% YoY",
                "market_share": "3.2%",
            },
            "metadata": {
                "note": "MOCK DATA - Connect Harmonic or S&P Global for real data",
            },
        }

    async def _mock_competitor_analysis(self, domain: str = "", **kwargs) -> dict:
        """Mock competitor analysis."""
        return {
            "source": "mock",
            "domain": domain,
            "competitors": [
                {
                    "name": "Competitor A",
                    "domain": "competitor-a.com",
                    "monthly_traffic": "5.2M",
                    "traffic_sources": {"organic": 45, "paid": 20, "referral": 35},
                },
                {
                    "name": "Competitor B",
                    "domain": "competitor-b.com",
                    "monthly_traffic": "3.8M",
                    "traffic_sources": {"organic": 60, "paid": 15, "referral": 25},
                },
            ],
            "market_position": {
                "your_rank": 3,
                "total_competitors": 12,
            },
            "metadata": {
                "note": "MOCK DATA - Connect Similarweb for real competitor data",
            },
        }

    async def _mock_data_analysis(self, dataset: str = "", **kwargs) -> dict:
        """Mock data analysis."""
        return {
            "source": "mock",
            "dataset": dataset,
            "analysis": {
                "row_count": 10000,
                "columns": ["date", "value", "category"],
                "summary": {
                    "mean": 42.5,
                    "median": 38.2,
                    "std_dev": 12.3,
                },
            },
            "metadata": {
                "note": "MOCK DATA - Connect Amplitude for real analytics",
            },
        }

    # =========================================================================
    # AGENT BINDING
    # =========================================================================

    def bind_to_agent(self, agent, tool_names: list[str]) -> None:
        """
        Bind resolved tools to an agent.

        Args:
            agent: Agent instance to bind tools to
            tool_names: List of tool names to bind
        """
        tools = self.resolve_workflow_tools(tool_names)

        # Create tool executor for agent
        async def tool_executor(tool_name: str, **kwargs) -> dict:
            return await self.execute(tool_name, **kwargs)

        # Set on agent if it supports tools
        if hasattr(agent, "set_tools"):
            agent.set_tools(tools, tool_executor)
        elif hasattr(agent, "_tools"):
            agent._tools = tools
            agent._tool_executor = tool_executor

    def create_tool_aware_executor(self, base_executor: Callable) -> Callable:
        """
        Wrap a base executor with tool awareness.

        This allows the executor to intercept tool calls and
        route them through the MCP bridge.

        Args:
            base_executor: The original executor function

        Returns:
            Enhanced executor with tool support
        """
        bridge = self

        async def enhanced_executor(prompt: str, context: Any = None) -> str:
            # Check if prompt contains tool call markers
            # This is a simplified implementation
            # Real implementation would parse LLM tool call responses

            # For now, just call base executor
            result = await base_executor(prompt, context)

            # TODO: Parse result for tool calls
            # If tool call detected, execute via bridge
            # and return result to LLM

            return result

        return enhanced_executor


# =========================================================================
# CONVENIENCE FUNCTIONS
# =========================================================================

def get_bridge(use_mocks: bool = False) -> MCPToolBridge:
    """Get the default MCP tool bridge instance."""
    return MCPToolBridge(use_mocks=use_mocks)


def resolve_workflow_tools(tool_names: list[str]) -> list[MCPTool]:
    """Resolve tools for a workflow."""
    bridge = get_bridge()
    return bridge.resolve_workflow_tools(tool_names)


async def execute_tool(tool_name: str, **kwargs) -> dict:
    """Execute a tool call."""
    bridge = get_bridge(use_mocks=True)
    return await bridge.execute(tool_name, **kwargs)
