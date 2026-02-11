"""
Tool integration module for Agenticom.

Provides:
- MCP (Model Context Protocol) integration for connecting workflow tools to real services
- Prompt engineering for automatically improving agent prompts
"""

from .mcp_bridge import MCPToolBridge, MCPTool, ToolMapping
from .registry import MCPRegistry, RegistryEntry
from .prompt_engineer import (
    PromptEngineer,
    PromptStyle,
    PromptConfig,
    ImprovedPrompt,
    get_prompt_engineer,
    improve_prompt,
    improve_prompt_sync,
)

__all__ = [
    # MCP Integration
    "MCPToolBridge",
    "MCPTool",
    "ToolMapping",
    "MCPRegistry",
    "RegistryEntry",
    # Prompt Engineering
    "PromptEngineer",
    "PromptStyle",
    "PromptConfig",
    "ImprovedPrompt",
    "get_prompt_engineer",
    "improve_prompt",
    "improve_prompt_sync",
]
