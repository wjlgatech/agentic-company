"""
Tests for template variable substitution in multi-step workflows.

This tests the critical bug fix where {{step_outputs.X}} was not being
substituted with actual step outputs, causing agents to work in isolation.
"""

import pytest
from orchestration.agents.team import AgentTeam, TeamConfig, WorkflowStep, StepResult
from orchestration.agents.base import AgentRole


class TestTemplatePreprocessing:
    """Test the _preprocess_template method."""

    def setup_method(self):
        """Create a minimal AgentTeam for testing."""
        self.team = AgentTeam(TeamConfig(name="test"))

    def test_step_outputs_substitution(self):
        """Should convert {{step_outputs.X}} to {X}."""
        template = "Based on: {{step_outputs.plan}}"
        result = self.team._preprocess_template(template)
        assert result == "Based on: {plan}"

    def test_multiple_step_outputs(self):
        """Should handle multiple step_outputs references."""
        template = """
        Plan: {{step_outputs.plan}}
        Code: {{step_outputs.implement}}
        Tests: {{step_outputs.test}}
        """
        result = self.team._preprocess_template(template)
        assert "{plan}" in result
        assert "{implement}" in result
        assert "{test}" in result
        assert "step_outputs" not in result

    def test_task_variable(self):
        """Should convert {{task}} to {task}."""
        template = "Create implementation plan for: {{task}}"
        result = self.team._preprocess_template(template)
        assert result == "Create implementation plan for: {task}"

    def test_mixed_variables(self):
        """Should handle mix of task and step_outputs."""
        template = """
        Original task: {{task}}
        Previous output: {{step_outputs.research}}
        """
        result = self.team._preprocess_template(template)
        assert "{task}" in result
        assert "{research}" in result
        assert "{{" not in result

    def test_hyphenated_step_ids(self):
        """Should handle hyphenated step IDs like discover-pain-points."""
        template = "Pain points: {{step_outputs.discover-pain-points}}"
        result = self.team._preprocess_template(template)
        assert result == "Pain points: {discover-pain-points}"

    def test_complex_marketing_template(self):
        """Should handle complex marketing workflow template."""
        template = """
        Based on our research:
        - Research: {{step_outputs.discover-pain-points}}
        - Competition: {{step_outputs.analyze-competitors}}
        - Content: {{step_outputs.create-content-calendar}}
        - Outreach: {{step_outputs.plan-outreach}}

        Create a comprehensive campaign for: {{task}}
        """
        result = self.team._preprocess_template(template)

        # All step_outputs should be converted
        assert "{discover-pain-points}" in result
        assert "{analyze-competitors}" in result
        assert "{create-content-calendar}" in result
        assert "{plan-outreach}" in result
        assert "{task}" in result

        # No {{}} should remain
        assert "{{" not in result
        assert "}}" not in result

    def test_preserves_plain_braces(self):
        """Should preserve single braces that aren't template variables."""
        template = "JSON example: {\"key\": \"value\"}"
        result = self.team._preprocess_template(template)
        # Single braces should remain unchanged
        assert '{"key": "value"}' in result

    def test_no_change_for_simple_braces(self):
        """Should not modify templates that already use {X} syntax."""
        template = "Plan: {plan}\nTask: {task}"
        result = self.team._preprocess_template(template)
        assert result == template


class TestTemplateFormatting:
    """Test full template formatting with actual step outputs."""

    def setup_method(self):
        """Create AgentTeam for testing."""
        self.team = AgentTeam(TeamConfig(name="test"))

    def test_format_with_step_outputs(self):
        """Should correctly substitute step outputs into template."""
        template = "Based on plan: {{step_outputs.plan}}"
        processed = self.team._preprocess_template(template)

        # Simulate step outputs
        outputs = {
            "plan": "1. Build login page\n2. Add validation\n3. Connect to API"
        }

        result = processed.format(**outputs)
        assert "1. Build login page" in result
        assert "2. Add validation" in result
        assert "3. Connect to API" in result

    def test_format_with_multiple_outputs(self):
        """Should correctly substitute multiple step outputs."""
        template = """
        Code: {{step_outputs.implement}}
        Tests: {{step_outputs.test}}
        """
        processed = self.team._preprocess_template(template)

        outputs = {
            "implement": "def login(): pass",
            "test": "def test_login(): assert True"
        }

        result = processed.format(**outputs)
        assert "def login(): pass" in result
        assert "def test_login(): assert True" in result

    def test_format_with_task(self):
        """Should correctly substitute task variable."""
        template = "Create a {{task}}"
        processed = self.team._preprocess_template(template)

        result = processed.format(task="login button")
        assert "Create a login button" in result


class TestRegressionPrevention:
    """Tests to prevent regression of the template substitution bug."""

    def test_literal_step_outputs_not_in_result(self):
        """
        CRITICAL: Ensure {step_outputs.X} is NEVER passed to agents.

        This was the original bug - agents received literal string
        "{step_outputs.plan}" instead of the actual plan content.
        """
        team = AgentTeam(TeamConfig(name="test"))

        # Simulate what happens during step execution
        template = "Review this code: {{step_outputs.implement}}"
        processed = team._preprocess_template(template)

        outputs = {
            "implement": "def hello():\n    print('Hello World')"
        }

        result = processed.format(**outputs)

        # CRITICAL ASSERTIONS
        assert "step_outputs" not in result.lower(), \
            "BUG: Literal 'step_outputs' should never appear in formatted output"
        assert "{{" not in result, \
            "BUG: Template markers {{ should be substituted"
        assert "}}" not in result, \
            "BUG: Template markers }} should be substituted"

        # Should contain actual code
        assert "def hello():" in result
        assert "print('Hello World')" in result

    def test_multi_step_workflow_simulation(self):
        """
        Simulate a complete multi-step workflow to verify outputs flow correctly.
        """
        team = AgentTeam(TeamConfig(name="test"))

        # Step 1: Plan
        step1_template = "Create plan for: {{task}}"
        step1_processed = team._preprocess_template(step1_template)
        step1_input = step1_processed.format(task="build login")
        assert step1_input == "Create plan for: build login"

        # Simulate step 1 output
        outputs = {
            "task": "build login",
            "plan": "Step 1: Create form\nStep 2: Add validation"
        }

        # Step 2: Implement (depends on plan)
        step2_template = "Implement this plan:\n{{step_outputs.plan}}"
        step2_processed = team._preprocess_template(step2_template)
        step2_input = step2_processed.format(**outputs)

        assert "Step 1: Create form" in step2_input
        assert "Step 2: Add validation" in step2_input
        assert "step_outputs" not in step2_input

        # Add step 2 output
        outputs["implement"] = "class LoginForm:\n    pass"

        # Step 3: Test (depends on implement)
        step3_template = "Write tests for:\n{{step_outputs.implement}}"
        step3_processed = team._preprocess_template(step3_template)
        step3_input = step3_processed.format(**outputs)

        assert "class LoginForm:" in step3_input
        assert "step_outputs" not in step3_input

        # Step 4: Review (depends on implement and test)
        outputs["test"] = "def test_login(): pass"

        step4_template = """
        Review code and tests:
        Code: {{step_outputs.implement}}
        Tests: {{step_outputs.test}}
        """
        step4_processed = team._preprocess_template(step4_template)
        step4_input = step4_processed.format(**outputs)

        assert "class LoginForm:" in step4_input
        assert "def test_login():" in step4_input
        assert "step_outputs" not in step4_input


class TestEdgeCases:
    """Test edge cases and potential issues."""

    def setup_method(self):
        self.team = AgentTeam(TeamConfig(name="test"))

    def test_empty_output(self):
        """Should handle empty step outputs gracefully."""
        template = "Previous: {{step_outputs.plan}}"
        processed = self.team._preprocess_template(template)

        outputs = {"plan": ""}
        result = processed.format(**outputs)
        assert result == "Previous: "

    def test_multiline_output(self):
        """Should preserve multiline step outputs."""
        template = "Code:\n{{step_outputs.implement}}"
        processed = self.team._preprocess_template(template)

        outputs = {
            "implement": """def login():
    username = input("Username: ")
    password = input("Password: ")
    return authenticate(username, password)"""
        }

        result = processed.format(**outputs)
        assert "def login():" in result
        assert 'input("Username: ")' in result

    def test_special_characters_in_output(self):
        """Should handle special characters in step outputs."""
        template = "Analysis: {{step_outputs.analysis}}"
        processed = self.team._preprocess_template(template)

        outputs = {
            "analysis": "Success rate: 85% (p < 0.05)\nCI: [0.82, 0.88]"
        }

        result = processed.format(**outputs)
        assert "85%" in result
        assert "p < 0.05" in result

    def test_missing_output_raises_keyerror(self):
        """Should raise KeyError for missing step outputs (expected behavior)."""
        template = "Based on: {{step_outputs.nonexistent}}"
        processed = self.team._preprocess_template(template)

        outputs = {"plan": "some plan"}

        with pytest.raises(KeyError):
            processed.format(**outputs)
