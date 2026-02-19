"""
Tool integration module for Agenticom.

Provides:
- MCP (Model Context Protocol) integration for connecting workflow tools to real services
- Prompt engineering for automatically improving agent prompts
- Intent refinement for transforming vague user input into well-defined prompts
"""

from .conversational_refiner import (
    ClarificationCard,
    ConversationalRefiner,
    ConversationState,
    DraftPreview,
    QuickOption,
    RefinementSession,
    create_refiner,
    quick_refine,
)
from .intent_refiner import (
    ClarificationQuestion,
    Complexity,
    Domain,
    ExtractedSpecifics,
    IntentClassification,
    IntentModel,
    IntentRefiner,
    QualityScore,
    TaskType,
    extract_input_specifics,
    generate_system_prompt,
    get_clarification_questions,
    refine_intent,
    refine_intent_iterative,
)
from .mcp_bridge import MCPTool, MCPToolBridge, ToolMapping
from .prompt_engineer import (
    ImprovedPrompt,
    PromptConfig,
    PromptEngineer,
    PromptStyle,
    get_prompt_engineer,
    improve_prompt,
    improve_prompt_sync,
)
from .registry import MCPRegistry, RegistryEntry
from .smart_refiner import (
    ConversationTurn,
    Session,
    SmartRefiner,
    SyncSmartRefiner,
    Understanding,
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
    # Intent Refinement
    "IntentRefiner",
    "IntentClassification",
    "IntentModel",
    "ClarificationQuestion",
    "ExtractedSpecifics",
    "QualityScore",
    "TaskType",
    "Complexity",
    "Domain",
    "refine_intent",
    "refine_intent_iterative",
    "get_clarification_questions",
    "generate_system_prompt",
    "extract_input_specifics",
    # Conversational Refinement
    "ConversationalRefiner",
    "ConversationState",
    "RefinementSession",
    "ClarificationCard",
    "DraftPreview",
    "QuickOption",
    "create_refiner",
    "quick_refine",
    # Smart Refiner (LLM-based interview → coherent prompt synthesis)
    "SmartRefiner",
    "SyncSmartRefiner",
    "Session",
    "Understanding",
    "ConversationTurn",
]
