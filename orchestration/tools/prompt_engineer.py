"""
Prompt Engineer for Agenticom.

Automatically improves user prompts and agent personas using prompt engineering
best practices. Uses either:
1. Anthropic's experimental Prompt Generator API (if available)
2. A metaprompt approach using Claude to improve prompts

Based on Anthropic's prompt engineering techniques:
- Role setting and persona definition
- Chain-of-thought reasoning
- Clear task decomposition
- Output format specification
- Edge case handling
"""

import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PromptStyle(Enum):
    """Style of prompt to generate."""

    AGENT = "agent"  # For AI agent system prompts
    TASK = "task"  # For specific task prompts
    ANALYSIS = "analysis"  # For analytical/research tasks
    CREATIVE = "creative"  # For creative writing tasks
    CODING = "coding"  # For code generation tasks


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""

    style: PromptStyle = PromptStyle.AGENT
    include_cot: bool = True  # Chain-of-thought reasoning
    include_examples: bool = False  # Few-shot examples
    include_guardrails: bool = True  # Safety guidelines
    max_length: int = 2000  # Max prompt length
    target_model: str = "claude-sonnet-4-5-20250514"


@dataclass
class ImprovedPrompt:
    """Result of prompt improvement."""

    original: str
    improved: str
    improvements: list[str] = field(default_factory=list)
    style: PromptStyle = PromptStyle.AGENT
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)


# ============================================================================
# METAPROMPT - The prompt that generates better prompts
# ============================================================================

METAPROMPT = """You are an expert prompt engineer. Your task is to transform a basic prompt
or task description into a highly effective, production-ready prompt.

Apply these prompt engineering best practices:

1. **Role Setting**: Give the AI a clear identity and expertise level
2. **Context**: Provide relevant background information
3. **Task Clarity**: Break down complex tasks into clear steps
4. **Output Format**: Specify exactly what format the response should take
5. **Chain-of-Thought**: Include reasoning steps when helpful
6. **Edge Cases**: Address potential ambiguities or special cases
7. **Guardrails**: Include appropriate safety and quality guidelines

<original_prompt>
{original_prompt}
</original_prompt>

<task_context>
{task_context}
</task_context>

<style>
{style}
</style>

Generate an improved prompt that is:
- Clear and unambiguous
- Structured for optimal AI understanding
- Production-ready for use in an agent system

Respond with JSON in this format:
{{
    "improved_prompt": "The full improved prompt text",
    "improvements": ["List of specific improvements made"],
    "confidence": 0.95,
    "reasoning": "Brief explanation of key changes"
}}
"""

AGENT_SYSTEM_PROMPT_TEMPLATE = """You are {role_name}, a specialized AI agent.

## Role & Expertise
{role_description}

## Core Responsibilities
{responsibilities}

## Working Style
{working_style}

## Output Guidelines
{output_guidelines}

## Guardrails
{guardrails}
"""


class PromptEngineer:
    """
    Automatically improves prompts using prompt engineering best practices.

    Can use either:
    1. Anthropic's experimental Prompt Generator API
    2. A metaprompt approach with any LLM

    Example:
        engineer = PromptEngineer()

        # Improve a basic prompt
        result = await engineer.improve(
            "You are a researcher. Find papers about AI.",
            style=PromptStyle.AGENT
        )
        print(result.improved)

        # Generate agent persona
        persona = await engineer.generate_agent_persona(
            role="Senior Data Analyst",
            task="Analyze customer data and identify trends"
        )
    """

    def __init__(
        self,
        executor: Callable[[str], Awaitable[str]] | None = None,
        use_api: bool = False,
        api_key: str | None = None,
    ):
        """
        Initialize the Prompt Engineer.

        Args:
            executor: Async function to call LLM (prompt -> response)
            use_api: Whether to use Anthropic's experimental API
            api_key: Anthropic API key (for experimental API)
        """
        self.executor = executor
        self.use_api = use_api
        self.api_key = api_key

    async def improve(
        self,
        prompt: str,
        style: PromptStyle = PromptStyle.AGENT,
        context: str = "",
        config: PromptConfig | None = None,
    ) -> ImprovedPrompt:
        """
        Improve a prompt using prompt engineering best practices.

        Args:
            prompt: The original prompt to improve
            style: Style of prompt (agent, task, analysis, etc.)
            context: Additional context about the use case
            config: Configuration options

        Returns:
            ImprovedPrompt with original and improved versions
        """
        config = config or PromptConfig(style=style)

        if self.use_api and self.api_key:
            return await self._improve_via_api(prompt, style, context, config)
        elif self.executor:
            return await self._improve_via_metaprompt(prompt, style, context, config)
        else:
            # Fallback to rule-based improvement
            return self._improve_rule_based(prompt, style, context, config)

    async def _improve_via_api(
        self,
        prompt: str,
        style: PromptStyle,
        context: str,
        config: PromptConfig,
    ) -> ImprovedPrompt:
        """Use Anthropic's experimental Prompt Generator API."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/experimental/generate_prompt",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2024-01-01",
                        "anthropic-beta": "prompt-tools-2025-04-02",
                        "content-type": "application/json",
                    },
                    json={
                        "task": prompt,
                        "target_model": config.target_model,
                        "context": context,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return ImprovedPrompt(
                        original=prompt,
                        improved=data.get("prompt", prompt),
                        improvements=["Generated via Anthropic Prompt API"],
                        style=style,
                        confidence=0.95,
                        metadata={"source": "anthropic_api", "response": data},
                    )
                else:
                    logger.warning(f"Prompt API failed: {response.status_code}")
                    # Fallback to metaprompt
                    return await self._improve_via_metaprompt(
                        prompt, style, context, config
                    )

        except Exception as e:
            logger.error(f"Prompt API error: {e}")
            return await self._improve_via_metaprompt(prompt, style, context, config)

    async def _improve_via_metaprompt(
        self,
        prompt: str,
        style: PromptStyle,
        context: str,
        config: PromptConfig,
    ) -> ImprovedPrompt:
        """Use metaprompt approach with executor."""
        if not self.executor:
            return self._improve_rule_based(prompt, style, context, config)

        # Build the metaprompt
        metaprompt = METAPROMPT.format(
            original_prompt=prompt,
            task_context=context or "General AI agent task",
            style=style.value,
        )

        try:
            # Call the executor
            response = await self.executor(metaprompt)

            # Parse JSON response
            result = self._parse_json_response(response)

            return ImprovedPrompt(
                original=prompt,
                improved=result.get("improved_prompt", prompt),
                improvements=result.get("improvements", []),
                style=style,
                confidence=result.get("confidence", 0.8),
                metadata={
                    "source": "metaprompt",
                    "reasoning": result.get("reasoning", ""),
                },
            )

        except Exception as e:
            logger.error(f"Metaprompt failed: {e}")
            return self._improve_rule_based(prompt, style, context, config)

    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        try:
            # Direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere
        json_match = re.search(
            r'\{[^{}]*"improved_prompt"[^{}]*\}', response, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return the response as the improved prompt
        return {"improved_prompt": response, "improvements": ["Parsed as raw text"]}

    def _improve_rule_based(
        self,
        prompt: str,
        style: PromptStyle,
        context: str,
        config: PromptConfig,
    ) -> ImprovedPrompt:
        """Apply rule-based improvements when no LLM is available."""
        improvements = []
        improved = prompt

        # 1. Add role setting if missing
        if not any(
            phrase in prompt.lower() for phrase in ["you are", "your role", "as a"]
        ):
            role_prefix = self._get_role_prefix(style)
            improved = f"{role_prefix}\n\n{improved}"
            improvements.append("Added role setting")

        # 2. Add structure markers
        if len(prompt) > 200 and "\n##" not in prompt:
            improved = self._add_structure(improved, style)
            improvements.append("Added section structure")

        # 3. Add output format guidance
        if not any(
            phrase in prompt.lower() for phrase in ["respond with", "output", "format"]
        ):
            format_guidance = self._get_format_guidance(style)
            improved = f"{improved}\n\n{format_guidance}"
            improvements.append("Added output format guidance")

        # 4. Add chain-of-thought if enabled
        if config.include_cot and "step by step" not in prompt.lower():
            improved = improved.replace(
                "## Output",
                "## Approach\nThink through the problem step by step before providing your final answer.\n\n## Output",
            )
            if "## Approach" in improved:
                improvements.append("Added chain-of-thought guidance")

        # 5. Add guardrails if enabled
        if config.include_guardrails and "guardrail" not in prompt.lower():
            guardrails = self._get_guardrails(style)
            improved = f"{improved}\n\n{guardrails}"
            improvements.append("Added guardrails")

        return ImprovedPrompt(
            original=prompt,
            improved=improved,
            improvements=improvements,
            style=style,
            confidence=0.6,  # Lower confidence for rule-based
            metadata={"source": "rule_based"},
        )

    def _get_role_prefix(self, style: PromptStyle) -> str:
        """Get appropriate role prefix for style."""
        prefixes = {
            PromptStyle.AGENT: "You are a specialized AI agent with deep expertise in your domain.",
            PromptStyle.TASK: "You are a helpful assistant focused on completing the following task.",
            PromptStyle.ANALYSIS: "You are an expert analyst with strong research and critical thinking skills.",
            PromptStyle.CREATIVE: "You are a creative writer with a talent for engaging, original content.",
            PromptStyle.CODING: "You are an expert software engineer with deep knowledge of best practices.",
        }
        return prefixes.get(style, prefixes[PromptStyle.TASK])

    def _add_structure(self, prompt: str, style: PromptStyle) -> str:
        """Add section structure to prompt."""
        sections = {
            PromptStyle.AGENT: [
                "## Role",
                "## Responsibilities",
                "## Guidelines",
                "## Output",
            ],
            PromptStyle.TASK: ["## Task", "## Context", "## Requirements", "## Output"],
            PromptStyle.ANALYSIS: [
                "## Objective",
                "## Data",
                "## Analysis Approach",
                "## Deliverables",
            ],
            PromptStyle.CREATIVE: [
                "## Brief",
                "## Tone & Style",
                "## Requirements",
                "## Output",
            ],
            PromptStyle.CODING: [
                "## Task",
                "## Requirements",
                "## Constraints",
                "## Output",
            ],
        }

        # Simple heuristic: wrap content in first section
        section_headers = sections.get(style, sections[PromptStyle.TASK])
        return f"{section_headers[0]}\n{prompt}"

    def _get_format_guidance(self, style: PromptStyle) -> str:
        """Get output format guidance for style."""
        guidance = {
            PromptStyle.AGENT: "## Output Guidelines\nProvide clear, actionable responses. Structure complex answers with headers. Be concise but thorough.",
            PromptStyle.TASK: "## Output\nProvide a clear, complete response to the task. Include all requested information.",
            PromptStyle.ANALYSIS: "## Deliverables\nPresent findings with supporting evidence. Include key insights and recommendations.",
            PromptStyle.CREATIVE: "## Output\nDeliver polished, engaging content that meets the brief requirements.",
            PromptStyle.CODING: "## Output\nProvide clean, well-documented code. Include comments explaining complex logic.",
        }
        return guidance.get(style, guidance[PromptStyle.TASK])

    def _get_guardrails(self, style: PromptStyle) -> str:
        """Get appropriate guardrails for style."""
        base = "## Guardrails\n"
        guardrails = {
            PromptStyle.AGENT: base
            + "- Stay within your defined role and expertise\n- Ask for clarification when requirements are ambiguous\n- Acknowledge limitations when appropriate",
            PromptStyle.TASK: base
            + "- Focus on the specific task at hand\n- Provide accurate information only\n- Clarify assumptions made",
            PromptStyle.ANALYSIS: base
            + "- Base conclusions on available evidence\n- Acknowledge data limitations\n- Distinguish facts from interpretations",
            PromptStyle.CREATIVE: base
            + "- Maintain appropriate tone and style\n- Avoid sensitive or controversial content\n- Respect intellectual property",
            PromptStyle.CODING: base
            + "- Follow security best practices\n- Write maintainable, readable code\n- Handle edge cases and errors",
        }
        return guardrails.get(style, guardrails[PromptStyle.TASK])

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    async def generate_agent_persona(
        self,
        role: str,
        task: str,
        expertise: list[str] = None,
        tone: str = "professional",
    ) -> str:
        """
        Generate a complete agent persona/system prompt.

        Args:
            role: Agent role (e.g., "Senior Data Analyst")
            task: Primary task description
            expertise: List of expertise areas
            tone: Communication tone

        Returns:
            Complete system prompt for the agent
        """
        expertise = expertise or []
        expertise_str = (
            ", ".join(expertise) if expertise else "relevant domain knowledge"
        )

        basic_prompt = f"""
Role: {role}
Task: {task}
Expertise: {expertise_str}
Tone: {tone}
"""

        result = await self.improve(
            basic_prompt,
            style=PromptStyle.AGENT,
            context="This is for a multi-agent workflow system. The agent needs to work autonomously and produce high-quality outputs.",
        )

        return result.improved

    async def improve_workflow_agents(
        self,
        workflow_config: dict,
    ) -> dict:
        """
        Improve all agent prompts in a workflow configuration.

        Args:
            workflow_config: Workflow YAML parsed as dict

        Returns:
            Updated workflow config with improved prompts
        """
        improved_config = workflow_config.copy()

        if "agents" in improved_config:
            for agent in improved_config["agents"]:
                if "persona" in agent:
                    result = await self.improve(
                        agent["persona"],
                        style=PromptStyle.AGENT,
                        context=f"Agent role: {agent.get('role', 'unknown')}",
                    )
                    agent["persona"] = result.improved
                    agent["_prompt_improvements"] = result.improvements

        return improved_config


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def get_prompt_engineer(
    executor: Callable[[str], Awaitable[str]] | None = None,
) -> PromptEngineer:
    """Get a prompt engineer instance."""
    return PromptEngineer(executor=executor)


async def improve_prompt(
    prompt: str,
    style: PromptStyle = PromptStyle.AGENT,
    executor: Callable[[str], Awaitable[str]] | None = None,
) -> str:
    """Quick function to improve a prompt."""
    engineer = PromptEngineer(executor=executor)
    result = await engineer.improve(prompt, style=style)
    return result.improved


def improve_prompt_sync(
    prompt: str,
    style: PromptStyle = PromptStyle.AGENT,
) -> str:
    """Synchronous prompt improvement using rule-based approach."""
    engineer = PromptEngineer()
    result = engineer._improve_rule_based(prompt, style, "", PromptConfig(style=style))
    return result.improved
