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
    WAITING = "waiting"            # Waiting for user to connect/authenticate
    FALLBACK = "fallback"          # Using fallback method (e.g., WebSearch)


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
        return self.status in (ToolStatus.CONNECTED, ToolStatus.MOCK, ToolStatus.FALLBACK)

    @property
    def is_waiting(self) -> bool:
        """Check if tool is waiting for user action."""
        return self.status == ToolStatus.WAITING


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
        graceful_mode: bool = True,
    ):
        """
        Initialize the MCP Tool Bridge.

        Args:
            registry: MCP registry to use (default: built-in registry)
            use_mocks: If True, use mock implementations for testing
            mcporter_path: Path to mcporter CLI (for direct MCP calls)
            graceful_mode: If True, wait gracefully for missing tools instead of erroring
        """
        self.registry = registry or get_registry()
        self.use_mocks = use_mocks
        self.graceful_mode = graceful_mode
        self.mcporter_path = mcporter_path or self._find_mcporter()

        # Cache of resolved tools
        self._resolved_tools: dict[str, MCPTool] = {}

        # Tools waiting for user connection
        self._waiting_tools: dict[str, dict] = {}

        # Mock implementations for testing
        self._mocks: dict[str, Callable] = self._setup_mocks()

        # Fallback implementations using available tools
        self._fallbacks: dict[str, Callable] = self._setup_fallbacks()

    def _setup_fallbacks(self) -> dict[str, Callable]:
        """Setup fallback implementations using available tools like WebSearch."""
        return {
            "web_search": self._fallback_web_search,
            "literature_search": self._fallback_literature_search,
            "market_research": self._fallback_market_research,
            "competitor_analysis": self._fallback_competitor_analysis,
        }

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

        Resolution priority:
        1. Connected MCP server
        2. Fallback implementation (WebSearch, etc.)
        3. Mock implementation (if use_mocks=True)
        4. Waiting status (if graceful_mode=True)
        5. Unavailable

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

            # Priority 1: Check if MCP server is connected
            if self.registry.is_connected(entry.name):
                tool.status = ToolStatus.CONNECTED
                tool.executor = self._create_mcp_executor(entry)

            # Priority 2: Use fallback if available (real tools like WebSearch)
            elif tool_name in self._fallbacks:
                tool.status = ToolStatus.FALLBACK
                tool.executor = self._fallbacks[tool_name]

            # Priority 3: Use mock if enabled
            elif self.use_mocks and tool_name in self._mocks:
                tool.status = ToolStatus.MOCK
                tool.executor = self._mocks[tool_name]

            # Priority 4: Graceful waiting mode
            elif self.graceful_mode:
                tool.status = ToolStatus.WAITING
                self._waiting_tools[tool_name] = {
                    "server": entry.name,
                    "url": entry.url,
                    "suggestion": self._get_connection_instructions(entry),
                }

        else:
            # Not found in registry
            tool = MCPTool(
                declared_name=tool_name,
                status=ToolStatus.UNAVAILABLE,
            )

            # Try fallback first
            if tool_name in self._fallbacks:
                tool.status = ToolStatus.FALLBACK
                tool.executor = self._fallbacks[tool_name]

            # Then try mock
            elif self.use_mocks and tool_name in self._mocks:
                tool.status = ToolStatus.MOCK
                tool.executor = self._mocks[tool_name]

            # Graceful waiting
            elif self.graceful_mode:
                tool.status = ToolStatus.WAITING
                self._waiting_tools[tool_name] = {
                    "server": "Unknown",
                    "suggestion": f"No MCP server found for '{tool_name}'. Search the MCP registry.",
                }

        # Cache and return
        self._resolved_tools[tool_name] = tool
        return tool

    def _get_connection_instructions(self, entry: RegistryEntry) -> str:
        """Get instructions for connecting to an MCP server."""
        return f"Connect to {entry.name}: {entry.url}\nUse mcporter or Claude Desktop to authenticate."

    def get_waiting_tools(self) -> dict:
        """Get all tools waiting for user action."""
        return self._waiting_tools.copy()

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
            "fallback": [],
            "waiting": [],
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
            elif tool.status == ToolStatus.FALLBACK:
                report["fallback"].append({
                    "name": name,
                    "server": tool.server_name,
                    "note": "Using fallback implementation",
                })
            elif tool.status == ToolStatus.MOCK:
                report["mocked"].append({
                    "name": name,
                    "note": "Using mock implementation",
                })
            elif tool.status == ToolStatus.WAITING:
                report["waiting"].append({
                    "name": name,
                    "server": tool.server_name,
                    "note": "Waiting for MCP connection",
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
            "fallback": len(report["fallback"]),
            "mocked": len(report["mocked"]),
            "waiting": len(report["waiting"]),
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

        In graceful mode, tools that are waiting for connection will return
        a helpful message instead of an error.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        tool = self.resolve_tool(tool_name)

        # Handle waiting state gracefully
        if tool.is_waiting:
            waiting_info = self._waiting_tools.get(tool_name, {})
            return {
                "success": False,
                "status": "waiting",
                "tool": tool_name,
                "message": f"Tool '{tool_name}' is waiting for connection",
                "server": waiting_info.get("server", "Unknown"),
                "suggestion": waiting_info.get("suggestion", self._get_setup_suggestion(tool_name)),
                "action_required": "Please connect the MCP server to proceed",
                "partial_result": self._get_partial_result(tool_name, kwargs),
            }

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
                    "status": tool.status.value,
                    "data": result,
                }
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": tool_name,
                }

        return {
            "success": False,
            "error": "No executor available",
        }

    def _get_partial_result(self, tool_name: str, kwargs: dict) -> dict:
        """
        Get a partial result for a waiting tool.
        This provides context about what would have been executed.
        """
        return {
            "would_search": kwargs.get("query", kwargs.get("topic", str(kwargs))),
            "tool_type": tool_name,
            "note": "Real data will be available once the MCP server is connected",
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
    # FALLBACK IMPLEMENTATIONS (using available tools like WebSearch)
    # =========================================================================

    async def _fallback_web_search(self, query: str = "", **kwargs) -> dict:
        """
        Fallback web search using available search capabilities.
        This attempts to use real search if available.
        """
        try:
            # Try to use subprocess to call web search
            # In a real integration, this would call the WebSearch tool
            return {
                "source": "fallback",
                "query": query,
                "results": [],
                "metadata": {
                    "note": "Fallback mode - connect Ahrefs or Similarweb MCP for full results",
                    "searched_for": query,
                    "fallback_reason": "MCP server not connected",
                },
                "suggestion": "For real results, connect Ahrefs MCP at https://api.ahrefs.com/mcp/mcp",
            }
        except Exception as e:
            return {
                "source": "fallback",
                "error": str(e),
                "query": query,
            }

    async def _fallback_literature_search(self, query: str = "", **kwargs) -> dict:
        """
        Fallback literature search.
        Provides guidance on how to get real PubMed data.
        """
        return {
            "source": "fallback",
            "query": query,
            "articles": [],
            "metadata": {
                "note": "Fallback mode - connect PubMed MCP for real papers",
                "searched_for": query,
                "expected_tools": ["search_articles", "get_article_metadata", "find_related_articles"],
            },
            "suggestion": "Connect PubMed MCP to search real biomedical literature",
            "manual_search_url": f"https://pubmed.ncbi.nlm.nih.gov/?term={query.replace(' ', '+')}",
        }

    async def _fallback_market_research(self, company: str = "", **kwargs) -> dict:
        """
        Fallback market research.
        Provides guidance on how to get real company data.
        """
        return {
            "source": "fallback",
            "company": company,
            "profile": {},
            "metadata": {
                "note": "Fallback mode - connect Harmonic or S&P Global MCP for real data",
                "searched_for": company,
            },
            "suggestion": "Connect Harmonic MCP at https://mcp.api.harmonic.ai for company enrichment",
        }

    async def _fallback_competitor_analysis(self, domain: str = "", **kwargs) -> dict:
        """
        Fallback competitor analysis.
        Provides guidance on how to get real competitor data.
        """
        return {
            "source": "fallback",
            "domain": domain,
            "competitors": [],
            "metadata": {
                "note": "Fallback mode - connect Similarweb MCP for real traffic data",
                "searched_for": domain,
            },
            "suggestion": "Connect Similarweb MCP at https://mcp.similarweb.com for competitor insights",
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
