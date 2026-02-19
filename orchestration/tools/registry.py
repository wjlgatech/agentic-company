"""
MCP Registry client for discovering and managing MCP tools.

This module provides a Python interface to query MCP registries
and discover available tools for Agenticom workflows.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RegistryEntry:
    """A single MCP server entry from the registry."""

    name: str
    description: str
    url: str
    tools: list[str]
    icon_url: str = ""
    directory_uuid: str = ""
    connected: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "RegistryEntry":
        """Create a RegistryEntry from a dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            tools=data.get("tools", []),
            icon_url=data.get("iconUrl", ""),
            directory_uuid=data.get("directoryUuid", ""),
            connected=data.get("connected", False),
        )


@dataclass
class MCPRegistry:
    """
    Client for querying MCP registries.

    Supports multiple registry backends:
    - Built-in tool mappings (default)
    - mcporter CLI (if available)
    - HTTP API (for direct registry access)
    """

    cache_dir: Path = field(
        default_factory=lambda: Path.home() / ".agenticom" / "mcp_cache"
    )
    cache_ttl: int = 3600  # 1 hour

    # Built-in tool mappings for common categories
    BUILTIN_MAPPINGS: dict = field(
        default_factory=lambda: {
            # Research & Literature
            "literature_search": [
                RegistryEntry(
                    name="PubMed",
                    description="Search biomedical literature",
                    url="https://pubmed.mcp.claude.com/mcp",
                    tools=[
                        "search_articles",
                        "get_article_metadata",
                        "find_related_articles",
                    ],
                ),
                RegistryEntry(
                    name="bioRxiv",
                    description="Access bioRxiv and medRxiv preprints",
                    url="https://mcp.deepsense.ai/biorxiv/mcp",
                    tools=["search_biorxiv_publications", "get_preprint"],
                ),
                RegistryEntry(
                    name="Consensus",
                    description="Explore scientific research",
                    url="https://mcp.consensus.app/mcp",
                    tools=["search"],
                ),
                RegistryEntry(
                    name="Scholar Gateway",
                    description="Scholarly research and citations",
                    url="https://connector.scholargateway.ai/mcp",
                    tools=["Semantic Search"],
                ),
            ],
            # Web & SEO
            "web_search": [
                RegistryEntry(
                    name="Ahrefs",
                    description="SEO & AI search analytics",
                    url="https://api.ahrefs.com/mcp/mcp",
                    tools=["batch-analysis", "keyword-suggestions", "backlinks"],
                ),
                RegistryEntry(
                    name="Similarweb",
                    description="Real time web and market data",
                    url="https://mcp.similarweb.com",
                    tools=[
                        "get-websites-traffic-and-engagement",
                        "get-websites-similar-sites-agg",
                    ],
                ),
            ],
            # Social Media & Analytics
            "social_api": [
                RegistryEntry(
                    name="LunarCrush",
                    description="Social intelligence for crypto and beyond",
                    url="https://lunarcrush.com/mcp",
                    tools=["Topic", "Topic_Posts", "Topic_Time_Series"],
                ),
                RegistryEntry(
                    name="Amplitude",
                    description="Analytics and insights",
                    url="https://mcp.amplitude.com/mcp",
                    tools=["query_dataset", "query_charts", "query_metric"],
                ),
            ],
            # Business & Market Research
            "market_research": [
                RegistryEntry(
                    name="Harmonic",
                    description="Discover, research, and enrich companies",
                    url="https://mcp.api.harmonic.ai",
                    tools=[
                        "enrich_company",
                        "enrich_person",
                        "get_saved_search_companies_results",
                    ],
                ),
                RegistryEntry(
                    name="S&P Global",
                    description="Query S&P Global datasets",
                    url="https://kfinance.kensho.com/integrations/mcp",
                    tools=[
                        "get_company_summary_from_identifiers",
                        "get_info_from_identifiers",
                    ],
                ),
            ],
            "competitor_analysis": [
                RegistryEntry(
                    name="Similarweb",
                    description="Competitor traffic and engagement",
                    url="https://mcp.similarweb.com",
                    tools=[
                        "get-websites-traffic-and-engagement",
                        "get-websites-similar-sites-agg",
                    ],
                ),
                RegistryEntry(
                    name="Ahrefs",
                    description="Competitor backlink analysis",
                    url="https://api.ahrefs.com/mcp/mcp",
                    tools=["batch-analysis", "competing-domains"],
                ),
            ],
            # Data Analysis
            "data_analysis": [
                RegistryEntry(
                    name="Amplitude",
                    description="Analytics queries",
                    url="https://mcp.amplitude.com/mcp",
                    tools=["query_dataset", "query_charts"],
                ),
                RegistryEntry(
                    name="Windsor.ai",
                    description="Connect 325+ data sources",
                    url="https://mcp.windsor.ai",
                    tools=["get_data", "get_schema"],
                ),
            ],
            # Content & Media
            "image_generation": [
                RegistryEntry(
                    name="OpenAI Images",
                    description="DALL-E image generation",
                    url="",  # Built-in to OpenAI
                    tools=["generate_image"],
                ),
            ],
            "text_generation": [
                # This is handled by the LLM itself, not an external tool
            ],
            # CRM & Business
            "crm": [
                RegistryEntry(
                    name="HubSpot",
                    description="Chat with your CRM data",
                    url="https://mcp.hubspot.com/anthropic",
                    tools=["search_crm_objects", "get_crm_objects"],
                ),
                RegistryEntry(
                    name="Day AI",
                    description="Analyze & update CRM records",
                    url="https://day.ai/api/mcp",
                    tools=["create_or_update_person_organization", "read_crm_schema"],
                ),
            ],
            # Communication
            "messaging": [
                # Slack, Discord - typically handled via native integrations
            ],
            "analytics": [
                RegistryEntry(
                    name="Amplitude",
                    description="Product analytics",
                    url="https://mcp.amplitude.com/mcp",
                    tools=["get_charts", "query_metric"],
                ),
            ],
            "reporting": [
                RegistryEntry(
                    name="Gamma",
                    description="Generate presentations and docs",
                    url="https://gamma.app/mcp",
                    tools=["generate"],
                ),
            ],
        }
    )

    def __post_init__(self):
        """Initialize the registry."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, list[RegistryEntry]] = {}

    def search(self, keywords: list[str]) -> list[RegistryEntry]:
        """
        Search the registry for tools matching keywords.

        Args:
            keywords: List of search terms

        Returns:
            List of matching registry entries
        """
        results = []

        # First, check built-in mappings
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Direct mapping match
            if keyword_lower in self.BUILTIN_MAPPINGS:
                results.extend(self.BUILTIN_MAPPINGS[keyword_lower])

            # Partial match in mapping keys
            for key, entries in self.BUILTIN_MAPPINGS.items():
                if keyword_lower in key:
                    results.extend(entries)

        # Deduplicate by name
        seen = set()
        unique_results = []
        for entry in results:
            if entry.name not in seen:
                seen.add(entry.name)
                unique_results.append(entry)

        return unique_results

    def get_tools_for_category(self, category: str) -> list[RegistryEntry]:
        """
        Get all MCP tools for a given category.

        Args:
            category: Tool category (e.g., "web_search", "literature_search")

        Returns:
            List of registry entries for that category
        """
        return self.BUILTIN_MAPPINGS.get(category, [])

    def resolve_tool(self, tool_name: str) -> RegistryEntry | None:
        """
        Resolve a single tool name to an MCP entry.

        Args:
            tool_name: Name of the tool to resolve

        Returns:
            Best matching registry entry, or None
        """
        entries = self.get_tools_for_category(tool_name)
        if entries:
            # Return first available (primary)
            return entries[0]

        # Try searching
        results = self.search([tool_name])
        if results:
            return results[0]

        return None

    def list_categories(self) -> list[str]:
        """List all available tool categories."""
        return list(self.BUILTIN_MAPPINGS.keys())

    def is_connected(self, server_name: str) -> bool:
        """
        Check if an MCP server is connected/authenticated.

        This would typically check for stored credentials or
        active connections. For now, returns False.
        """
        # TODO: Implement actual connection checking
        # This would check ~/.agenticom/mcp_credentials.json
        # or query mcporter for connection status
        return False

    def get_connection_status(self) -> dict[str, bool]:
        """Get connection status for all known servers."""
        status = {}
        for _category, entries in self.BUILTIN_MAPPINGS.items():
            for entry in entries:
                status[entry.name] = self.is_connected(entry.name)
        return status


# Convenience function
def get_registry() -> MCPRegistry:
    """Get the default MCP registry instance."""
    return MCPRegistry()
