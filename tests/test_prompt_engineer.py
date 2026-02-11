"""
Tests for Prompt Engineer module.

Tests the automatic prompt improvement capabilities.
"""

import pytest
import asyncio
from orchestration.tools.prompt_engineer import (
    PromptEngineer,
    PromptStyle,
    PromptConfig,
    ImprovedPrompt,
    improve_prompt_sync,
)


class TestPromptEngineer:
    """Test PromptEngineer class."""

    def test_initialization(self):
        """Should initialize without executor."""
        engineer = PromptEngineer()
        assert engineer.executor is None
        assert engineer.use_api is False

    def test_initialization_with_executor(self):
        """Should initialize with executor."""
        async def mock_executor(prompt: str) -> str:
            return '{"improved_prompt": "test", "improvements": []}'

        engineer = PromptEngineer(executor=mock_executor)
        assert engineer.executor is not None


class TestRuleBasedImprovement:
    """Test rule-based prompt improvement."""

    def test_adds_role_setting(self):
        """Should add role setting to prompts without one."""
        engineer = PromptEngineer()
        result = engineer._improve_rule_based(
            "Find papers about AI.",
            PromptStyle.AGENT,
            "",
            PromptConfig()
        )

        assert "You are" in result.improved
        assert "Added role setting" in result.improvements

    def test_preserves_existing_role(self):
        """Should not add role setting if already present."""
        engineer = PromptEngineer()
        prompt = "You are a researcher. Find papers about AI."
        result = engineer._improve_rule_based(
            prompt,
            PromptStyle.AGENT,
            "",
            PromptConfig()
        )

        # Should not duplicate role setting
        assert result.improved.count("You are") == 1

    def test_adds_output_format(self):
        """Should add output format guidance."""
        engineer = PromptEngineer()
        result = engineer._improve_rule_based(
            "Analyze this data.",
            PromptStyle.ANALYSIS,
            "",
            PromptConfig()
        )

        assert "Added output format guidance" in result.improvements

    def test_adds_guardrails_when_enabled(self):
        """Should add guardrails when config enables them."""
        engineer = PromptEngineer()
        config = PromptConfig(include_guardrails=True)
        result = engineer._improve_rule_based(
            "Write some code.",
            PromptStyle.CODING,
            "",
            config
        )

        assert "Guardrails" in result.improved
        assert "Added guardrails" in result.improvements

    def test_no_guardrails_when_disabled(self):
        """Should not add guardrails when config disables them."""
        engineer = PromptEngineer()
        config = PromptConfig(include_guardrails=False)
        result = engineer._improve_rule_based(
            "Write some code.",
            PromptStyle.CODING,
            "",
            config
        )

        assert "Added guardrails" not in result.improvements

    def test_different_styles(self):
        """Should apply different improvements based on style."""
        engineer = PromptEngineer()

        # Agent style
        agent_result = engineer._improve_rule_based(
            "Help with tasks.",
            PromptStyle.AGENT,
            "",
            PromptConfig()
        )
        assert "specialized AI agent" in agent_result.improved

        # Analysis style
        analysis_result = engineer._improve_rule_based(
            "Analyze data.",
            PromptStyle.ANALYSIS,
            "",
            PromptConfig()
        )
        assert "analyst" in analysis_result.improved

        # Coding style
        coding_result = engineer._improve_rule_based(
            "Write code.",
            PromptStyle.CODING,
            "",
            PromptConfig()
        )
        assert "software engineer" in coding_result.improved

    def test_confidence_score(self):
        """Should return lower confidence for rule-based improvement."""
        engineer = PromptEngineer()
        result = engineer._improve_rule_based(
            "Test prompt.",
            PromptStyle.TASK,
            "",
            PromptConfig()
        )

        assert result.confidence == 0.6  # Rule-based has lower confidence
        assert result.metadata.get("source") == "rule_based"


class TestSyncImprovement:
    """Test synchronous improvement function."""

    def test_improve_prompt_sync(self):
        """Should improve prompt synchronously."""
        result = improve_prompt_sync(
            "Find information about AI.",
            style=PromptStyle.AGENT
        )

        assert "You are" in result
        assert len(result) > len("Find information about AI.")


class TestAsyncImprovement:
    """Test async improvement with mock executor."""

    @pytest.mark.asyncio
    async def test_improve_with_executor(self):
        """Should use executor when available."""
        async def mock_executor(prompt: str) -> str:
            return '''{
                "improved_prompt": "IMPROVED: Test prompt with better structure.",
                "improvements": ["Added structure", "Added clarity"],
                "confidence": 0.9
            }'''

        engineer = PromptEngineer(executor=mock_executor)
        result = await engineer.improve("Test prompt.", style=PromptStyle.TASK)

        assert "IMPROVED" in result.improved
        assert len(result.improvements) == 2
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_fallback_on_executor_error(self):
        """Should fallback to rule-based on executor error."""
        async def failing_executor(prompt: str) -> str:
            raise Exception("API error")

        engineer = PromptEngineer(executor=failing_executor)
        result = await engineer.improve("Test prompt.", style=PromptStyle.TASK)

        # Should still return a result via rule-based fallback
        assert result.improved is not None
        assert result.metadata.get("source") == "rule_based"

    @pytest.mark.asyncio
    async def test_parse_json_from_markdown(self):
        """Should parse JSON from markdown code blocks."""
        async def markdown_executor(prompt: str) -> str:
            return '''Here's the improved prompt:

```json
{
    "improved_prompt": "Better prompt here.",
    "improvements": ["Improvement 1"],
    "confidence": 0.85
}
```

This prompt is better because...'''

        engineer = PromptEngineer(executor=markdown_executor)
        result = await engineer.improve("Basic prompt.", style=PromptStyle.AGENT)

        assert result.improved == "Better prompt here."
        assert result.confidence == 0.85


class TestAgentPersonaGeneration:
    """Test agent persona generation."""

    @pytest.mark.asyncio
    async def test_generate_persona_without_executor(self):
        """Should generate persona using rule-based approach."""
        engineer = PromptEngineer()
        persona = await engineer.generate_agent_persona(
            role="Data Analyst",
            task="Analyze customer data",
            expertise=["Python", "SQL", "Statistics"],
            tone="professional"
        )

        assert len(persona) > 0
        assert "Data Analyst" in persona or "analyst" in persona.lower()


class TestWorkflowImprovement:
    """Test workflow-level prompt improvement."""

    @pytest.mark.asyncio
    async def test_improve_workflow_agents(self):
        """Should improve all agent prompts in workflow config."""
        engineer = PromptEngineer()

        workflow_config = {
            "name": "test-workflow",
            "agents": [
                {
                    "role": "researcher",
                    "persona": "Find papers."
                },
                {
                    "role": "writer",
                    "persona": "Write summaries."
                }
            ]
        }

        improved = await engineer.improve_workflow_agents(workflow_config)

        # Both agents should have improved personas
        for agent in improved["agents"]:
            assert len(agent["persona"]) > 20  # Should be expanded
            assert "_prompt_improvements" in agent


class TestPromptConfig:
    """Test PromptConfig dataclass."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = PromptConfig()

        assert config.style == PromptStyle.AGENT
        assert config.include_cot is True
        assert config.include_guardrails is True
        assert config.max_length == 2000

    def test_custom_config(self):
        """Should accept custom values."""
        config = PromptConfig(
            style=PromptStyle.CODING,
            include_cot=False,
            max_length=5000
        )

        assert config.style == PromptStyle.CODING
        assert config.include_cot is False
        assert config.max_length == 5000


class TestImprovedPrompt:
    """Test ImprovedPrompt dataclass."""

    def test_improved_prompt_creation(self):
        """Should create improved prompt result."""
        result = ImprovedPrompt(
            original="Basic prompt",
            improved="Better prompt with structure",
            improvements=["Added structure"],
            style=PromptStyle.AGENT,
            confidence=0.8
        )

        assert result.original == "Basic prompt"
        assert "structure" in result.improved
        assert len(result.improvements) == 1
        assert result.confidence == 0.8


class TestIntegration:
    """Integration tests for prompt engineering."""

    @pytest.mark.asyncio
    async def test_full_improvement_pipeline(self):
        """Test complete improvement pipeline."""
        # Mock a realistic LLM response
        async def realistic_executor(prompt: str) -> str:
            return '''{
                "improved_prompt": "You are a Senior Research Analyst specializing in market intelligence.\\n\\n## Role & Expertise\\nYou have deep expertise in analyzing market trends, competitive landscapes, and business opportunities.\\n\\n## Responsibilities\\n- Conduct thorough market research\\n- Identify key trends and patterns\\n- Provide actionable insights\\n\\n## Output Guidelines\\n- Structure findings clearly\\n- Support claims with data\\n- Highlight key takeaways",
                "improvements": [
                    "Added specific role definition",
                    "Added expertise areas",
                    "Added structured sections",
                    "Added output guidelines"
                ],
                "confidence": 0.92,
                "reasoning": "Transformed vague prompt into structured agent persona"
            }'''

        engineer = PromptEngineer(executor=realistic_executor)

        result = await engineer.improve(
            "Research market trends.",
            style=PromptStyle.AGENT,
            context="For a VC fund analyzing AI startups"
        )

        assert "Senior Research Analyst" in result.improved
        assert "## Role & Expertise" in result.improved
        assert len(result.improvements) >= 3
        assert result.confidence > 0.9

    def test_rule_based_comprehensive(self):
        """Test comprehensive rule-based improvement."""
        engineer = PromptEngineer()

        # Very basic prompt
        basic_prompt = "analyze data"

        result = engineer._improve_rule_based(
            basic_prompt,
            PromptStyle.ANALYSIS,
            "",
            PromptConfig(include_cot=True, include_guardrails=True)
        )

        # Should have multiple improvements
        assert len(result.improvements) >= 2

        # Should be significantly longer
        assert len(result.improved) > len(basic_prompt) * 5

        # Should have structure
        assert "##" in result.improved or "analyst" in result.improved.lower()
