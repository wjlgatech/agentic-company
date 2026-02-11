"""
Tests for Intent Refiner module.

Tests the Progressive Intent Refinement (PIR) pipeline:
1. PARSE - Intent classification
2. PROBE - Clarification questions
3. MODEL - Mental model building
4. GENERATE - Prompt generation
"""

import pytest
from orchestration.tools.intent_refiner import (
    IntentRefiner,
    IntentClassification,
    TaskType,
    Complexity,
    Domain,
    refine_intent,
    get_clarification_questions,
    generate_system_prompt,
)


class TestIntentClassification:
    """Test intent parsing and classification."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_analysis_detection(self):
        """Should detect analysis tasks."""
        inputs = [
            "analyze our sales data",
            "why are customers leaving",
            "explain how the algorithm works",
            "investigate the bug",
        ]

        for inp in inputs:
            result = self.refiner.parse(inp)
            assert result.task_type == TaskType.ANALYSIS, f"Failed for: {inp}"

    def test_creation_detection(self):
        """Should detect creation tasks."""
        inputs = [
            "write a blog post about AI",
            "create a marketing plan",
            "build a dashboard",
            "design a new logo",
        ]

        for inp in inputs:
            result = self.refiner.parse(inp)
            assert result.task_type == TaskType.CREATION, f"Failed for: {inp}"

    def test_research_detection(self):
        """Should detect research tasks."""
        inputs = [
            "find information about competitors",
            "research market trends",
            "what is machine learning",
            "look up best practices",
        ]

        for inp in inputs:
            result = self.refiner.parse(inp)
            assert result.task_type == TaskType.RESEARCH, f"Failed for: {inp}"

    def test_decision_detection(self):
        """Should detect decision tasks."""
        inputs = [
            "should I use React or Vue",
            "which database is better",
            "compare AWS vs GCP",
            "recommend a framework",
        ]

        for inp in inputs:
            result = self.refiner.parse(inp)
            assert result.task_type == TaskType.DECISION, f"Failed for: {inp}"

    def test_domain_detection(self):
        """Should detect domains correctly."""
        tests = [
            ("fix the bug in my code", Domain.TECHNICAL),
            ("improve our revenue growth", Domain.BUSINESS),
            ("write a creative story", Domain.CREATIVE),
            ("find papers about neural networks", Domain.RESEARCH),
            ("help me organize my personal schedule", Domain.PERSONAL),
        ]

        for inp, expected_domain in tests:
            result = self.refiner.parse(inp)
            assert result.domain == expected_domain, f"Failed for: {inp}"

    def test_complexity_detection(self):
        """Should detect complexity levels."""
        # Atomic - simple request
        simple = self.refiner.parse("what is Python")
        assert simple.complexity == Complexity.ATOMIC

        # Composite - multi-step
        composite = self.refiner.parse(
            "first analyze the data, and then create a report with charts"
        )
        assert composite.complexity == Complexity.COMPOSITE

        # Exploratory - uncertain
        exploratory = self.refiner.parse(
            "I'm not sure what I need, help me figure out my options"
        )
        assert exploratory.complexity == Complexity.EXPLORATORY

    def test_confidence_scoring(self):
        """Should have higher confidence with more signals."""
        vague = self.refiner.parse("help me")
        specific = self.refiner.parse("analyze our customer churn data and create retention strategy")

        assert specific.confidence > vague.confidence


class TestClarificationQuestions:
    """Test question generation."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_vague_input_gets_more_questions(self):
        """Vague input should generate more questions."""
        vague_classification = IntentClassification(
            task_type=TaskType.CREATION,
            complexity=Complexity.ATOMIC,
            domain=Domain.BUSINESS,
            confidence=0.3,  # Low confidence
        )

        specific_classification = IntentClassification(
            task_type=TaskType.CREATION,
            complexity=Complexity.ATOMIC,
            domain=Domain.BUSINESS,
            confidence=0.9,  # High confidence
        )

        vague_questions = self.refiner.get_questions("help", vague_classification)
        specific_questions = self.refiner.get_questions(
            "create a detailed financial report for Q4 sales",
            specific_classification
        )

        assert len(vague_questions) >= len(specific_questions)

    def test_questions_have_required_fields(self):
        """Questions should have all required fields."""
        questions = get_clarification_questions("analyze something")

        for q in questions:
            assert "id" in q
            assert "question" in q
            assert "dimension" in q
            assert "type" in q

    def test_max_questions_respected(self):
        """Should respect max questions limit."""
        refiner = IntentRefiner(max_questions=3)
        classification = refiner.parse("do something vague")
        questions = refiner.get_questions("do something vague", classification)

        assert len(questions) <= 3


class TestMentalModel:
    """Test mental model building."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_model_has_all_components(self):
        """Model should have inputs, process, outputs."""
        classification = self.refiner.parse("analyze sales data")
        model = self.refiner.build_model("analyze sales data", classification)

        assert len(model.inputs) > 0
        assert len(model.process) > 0
        assert len(model.outputs) > 0

    def test_process_varies_by_task_type(self):
        """Different task types should have different processes."""
        analysis_class = IntentClassification(
            task_type=TaskType.ANALYSIS,
            complexity=Complexity.ATOMIC,
            domain=Domain.BUSINESS,
            confidence=0.8,
        )
        creation_class = IntentClassification(
            task_type=TaskType.CREATION,
            complexity=Complexity.ATOMIC,
            domain=Domain.CREATIVE,
            confidence=0.8,
        )

        analysis_model = self.refiner.build_model("analyze data", analysis_class)
        creation_model = self.refiner.build_model("create content", creation_class)

        # Process steps should be different
        analysis_actions = [p["action"] for p in analysis_model.process]
        creation_actions = [p["action"] for p in creation_model.process]

        assert analysis_actions != creation_actions

    def test_ascii_diagram_renders(self):
        """Should render ASCII diagram without errors."""
        classification = self.refiner.parse("write a report")
        model = self.refiner.build_model("write a report", classification)

        ascii_diagram = model.to_ascii()

        assert "INTENT MODEL" in ascii_diagram
        assert "INPUTS" in ascii_diagram
        assert "PROCESS" in ascii_diagram
        assert "OUTPUTS" in ascii_diagram

    def test_mermaid_diagram_renders(self):
        """Should render Mermaid diagram without errors."""
        classification = self.refiner.parse("analyze data")
        model = self.refiner.build_model("analyze data", classification)

        mermaid = model.to_mermaid()

        assert "flowchart" in mermaid
        assert "-->" in mermaid

    def test_assumptions_tracked(self):
        """Should track assumptions made."""
        classification = self.refiner.parse("help me with marketing")
        model = self.refiner.build_model("help me with marketing", classification)

        assert len(model.assumptions) > 0

        # Should include task type assumption
        assumption_keys = [a["key"] for a in model.assumptions]
        assert "Task type" in assumption_keys


class TestPromptGeneration:
    """Test system prompt generation."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_prompt_has_required_sections(self):
        """Generated prompt should have all best practice sections."""
        result = refine_intent("analyze our customer data")
        prompt = result["prompt"]

        assert "## Context" in prompt or "Context" in prompt
        assert "## Task" in prompt or "Task" in prompt
        assert "## Guardrails" in prompt or "Guardrails" in prompt

    def test_prompt_role_matches_domain(self):
        """Prompt role should match the domain."""
        tech_result = refine_intent("debug this code")
        business_result = refine_intent("analyze revenue growth")

        assert "engineer" in tech_result["prompt"].lower() or "technical" in tech_result["prompt"].lower()
        assert "business" in business_result["prompt"].lower() or "strategist" in business_result["prompt"].lower()

    def test_prompt_includes_success_criteria(self):
        """Prompt should include success criteria."""
        result = refine_intent("create a presentation")
        prompt = result["prompt"]

        assert "Success Criteria" in prompt or "success" in prompt.lower()

    def test_answers_influence_prompt(self):
        """User answers should influence generated prompt."""
        without_answers = generate_system_prompt("write a report")
        with_answers = generate_system_prompt(
            "write a report",
            answers={
                "audience": "C-level executives",
                "success": "Clear, actionable recommendations",
            }
        )

        # With answers should be more specific
        assert "executives" in with_answers or "C-level" in with_answers


class TestParaphrase:
    """Test paraphrase generation."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_paraphrase_includes_understanding(self):
        """Paraphrase should explain what was understood."""
        classification = self.refiner.parse("analyze our sales")
        model = self.refiner.build_model("analyze our sales", classification)

        paraphrase = self.refiner.paraphrase("analyze our sales", classification, model)

        assert "understood" in paraphrase.lower()
        assert "analysis" in paraphrase.lower()

    def test_paraphrase_shows_assumptions(self):
        """Paraphrase should highlight assumptions."""
        classification = self.refiner.parse("help with marketing")
        model = self.refiner.build_model("help with marketing", classification)

        paraphrase = self.refiner.paraphrase("help with marketing", classification, model)

        assert "assumed" in paraphrase.lower()

    def test_paraphrase_asks_for_confirmation(self):
        """Paraphrase should ask for user confirmation."""
        classification = self.refiner.parse("create something")
        model = self.refiner.build_model("create something", classification)

        paraphrase = self.refiner.paraphrase("create something", classification, model)

        assert "correct" in paraphrase.lower() or "confirm" in paraphrase.lower()


class TestFullPipeline:
    """Test complete refinement pipeline."""

    def test_refine_intent_returns_all_components(self):
        """Full pipeline should return all components."""
        result = refine_intent("help me analyze customer feedback")

        assert "original_input" in result
        assert "classification" in result
        assert "questions" in result
        assert "model" in result
        assert "prompt" in result

    def test_pipeline_handles_various_inputs(self):
        """Pipeline should handle various input types."""
        inputs = [
            "help",
            "analyze our Q4 sales data and create a presentation",
            "should I use React or Vue for my new project?",
            "write a blog post about machine learning",
            "fix the bug in line 42 of main.py",
        ]

        for inp in inputs:
            result = refine_intent(inp)
            assert result["prompt"], f"No prompt generated for: {inp}"
            assert result["classification"]["task_type"], f"No task type for: {inp}"

    def test_pipeline_with_answers(self):
        """Pipeline should incorporate user answers."""
        result = refine_intent(
            "create a report",
            answers={
                "goal": "Help leadership make Q1 budget decisions",
                "audience": "Executive team",
                "success": "Clear data visualization with recommendations",
            }
        )

        # Answers should influence the output
        prompt = result["prompt"]
        assert "executive" in prompt.lower() or "leadership" in prompt.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        self.refiner = IntentRefiner()

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        result = self.refiner.parse("")
        assert result.task_type is not None
        assert result.confidence < 0.5  # Low confidence

    def test_very_long_input(self):
        """Should handle very long input."""
        long_input = "analyze " * 100 + "data"
        result = self.refiner.parse(long_input)
        assert result.task_type == TaskType.ANALYSIS

    def test_special_characters(self):
        """Should handle special characters."""
        result = self.refiner.parse("analyze data with $pecial ch@racters!!!")
        assert result is not None

    def test_unicode_input(self):
        """Should handle unicode input."""
        result = self.refiner.parse("分析数据 and créer un rapport")
        assert result is not None


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_clarification_questions(self):
        """Convenience function should work."""
        questions = get_clarification_questions("help me")
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_generate_system_prompt(self):
        """Convenience function should work."""
        prompt = generate_system_prompt("analyze data")
        assert isinstance(prompt, str)
        assert len(prompt) > 100
