"""
Tool integration module for Agenticom.

Provides MCP (Model Context Protocol) integration for connecting
workflow tool declarations to real external services.
"""

from .mcp_bridge import MCPToolBridge, MCPTool, ToolMapping
from .registry import MCPRegistry, RegistryEntry

__all__ = [
    "MCPToolBridge",
    "MCPTool",
    "ToolMapping",
    "MCPRegistry",
    "RegistryEntry",
]
