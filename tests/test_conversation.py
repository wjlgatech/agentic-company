"""
Tests for orchestration/conversation.py — ConversationBuilder.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from orchestration.conversation import (
    ConversationBuilder,
    QuestionType,
    get_voice_input,
    install_voice_support,
)

# ---------------------------------------------------------------------------
# ConversationBuilder — basic navigation
# ---------------------------------------------------------------------------


class TestConversationBuilderBasic:
    def test_initial_step_is_zero(self):
        builder = ConversationBuilder()
        assert builder.current_step == 0
        assert builder.answers == {}

    def test_get_current_question_returns_question(self):
        builder = ConversationBuilder()
        q = builder.get_current_question()
        assert q is not None
        assert q.id == "goal"

    def test_get_current_question_after_completion_returns_none(self):
        builder = ConversationBuilder()
        # skip to end
        builder.current_step = len(builder.questions)
        assert builder.get_current_question() is None

    def test_is_complete_false_at_start(self):
        builder = ConversationBuilder()
        assert builder.is_complete() is False

    def test_get_progress_returns_tuple(self):
        builder = ConversationBuilder()
        current, total = builder.get_progress()
        assert current == 1
        assert total == len(builder.questions)

    def test_answer_valid_choice_returns_true(self):
        builder = ConversationBuilder()
        assert builder.answer("a") is True
        assert builder.answers["goal"] == "feature"

    def test_answer_invalid_choice_returns_false(self):
        builder = ConversationBuilder()
        assert builder.answer("z") is False
        # step should not advance
        assert builder.current_step == 0

    def test_answer_case_insensitive(self):
        builder = ConversationBuilder()
        assert builder.answer("A") is True
        assert builder.answers["goal"] == "feature"


# ---------------------------------------------------------------------------
# Conditional question skipping
# ---------------------------------------------------------------------------


class TestConditionalSkipping:
    def test_custom_goal_shown_when_goal_is_custom(self):
        builder = ConversationBuilder()
        builder.answer("e")  # goal = "custom"
        q = builder.get_current_question()
        assert q is not None
        assert q.id == "custom_goal"

    def test_custom_goal_skipped_when_goal_not_custom(self):
        builder = ConversationBuilder()
        builder.answer("a")  # goal = "feature"
        q = builder.get_current_question()
        assert q is not None
        assert q.id != "custom_goal"  # should skip to "name"
        assert q.id == "name"

    def test_custom_name_shown_when_name_is_custom(self):
        builder = ConversationBuilder()
        builder.answer("a")  # goal
        builder.answer("e")  # name = "custom"
        q = builder.get_current_question()
        assert q is not None
        assert q.id == "custom_name"

    def test_custom_name_skipped_when_name_not_custom(self):
        builder = ConversationBuilder()
        builder.answer("a")  # goal = feature
        builder.answer("a")  # name = feature-builder
        q = builder.get_current_question()
        assert q is not None
        assert q.id != "custom_name"

    def test_custom_agents_skipped_when_agents_not_custom(self):
        builder = ConversationBuilder()
        builder.answer("a")  # goal
        builder.answer("a")  # name
        builder.answer("a")  # agents = full
        q = builder.get_current_question()
        assert q is not None
        assert q.id != "custom_agents"

    def test_custom_agents_shown_when_agents_is_custom(self):
        builder = ConversationBuilder()
        builder.answer("a")  # goal
        builder.answer("a")  # name
        builder.answer("e")  # agents = custom
        q = builder.get_current_question()
        assert q is not None
        assert q.id == "custom_agents"


# ---------------------------------------------------------------------------
# Confirm resets conversation
# ---------------------------------------------------------------------------


class TestConfirmReset:
    def _answer_all_until_confirm(self, builder: ConversationBuilder):
        """Drive through all questions until we hit confirm."""
        while True:
            q = builder.get_current_question()
            if q is None:
                break
            if q.id == "confirm":
                return
            if q.question_type == QuestionType.TEXT:
                builder.answer("test-text")
            else:
                builder.answer(q.choices[0].key)

    def test_confirm_no_resets(self):
        builder = ConversationBuilder()
        self._answer_all_until_confirm(builder)
        # Answer "n" to confirm
        ok = builder.answer("n")
        assert ok is True
        assert builder.current_step == 0
        assert builder.answers == {}

    def test_confirm_yes_completes(self):
        builder = ConversationBuilder()
        self._answer_all_until_confirm(builder)
        builder.answer("y")
        assert builder.is_complete() is True


# ---------------------------------------------------------------------------
# Multiple-choice mapping
# ---------------------------------------------------------------------------


class TestChoiceMapping:
    def test_agents_full_preset(self):
        builder = ConversationBuilder()
        builder.answers["agents"] = "full"
        agents = builder._get_agents_list()
        assert agents == ["planner", "developer", "verifier", "tester", "reviewer"]

    def test_agents_quick_preset(self):
        builder = ConversationBuilder()
        builder.answers["agents"] = "quick"
        assert builder._get_agents_list() == ["planner", "developer", "verifier"]

    def test_agents_research_preset(self):
        builder = ConversationBuilder()
        builder.answers["agents"] = "research"
        assert builder._get_agents_list() == ["researcher", "analyst", "writer"]

    def test_agents_single_preset(self):
        builder = ConversationBuilder()
        builder.answers["agents"] = "single"
        assert builder._get_agents_list() == ["developer"]

    def test_agents_custom(self):
        builder = ConversationBuilder()
        builder.answers["agents"] = "custom"
        builder.answers["custom_agents"] = "1,2,3"
        agents = builder._get_agents_list()
        assert agents == ["planner", "developer", "verifier"]

    def test_guardrails_standard(self):
        builder = ConversationBuilder()
        builder.answers["guardrails"] = "standard"
        assert builder._get_guardrails_list() == ["content-filter", "pii-detection"]

    def test_guardrails_maximum(self):
        builder = ConversationBuilder()
        builder.answers["guardrails"] = "maximum"
        assert builder._get_guardrails_list() == [
            "content-filter",
            "pii-detection",
            "rate-limiter",
        ]

    def test_guardrails_minimal(self):
        builder = ConversationBuilder()
        builder.answers["guardrails"] = "minimal"
        assert builder._get_guardrails_list() == ["content-filter"]

    def test_guardrails_none(self):
        builder = ConversationBuilder()
        builder.answers["guardrails"] = "none"
        assert builder._get_guardrails_list() == []


# ---------------------------------------------------------------------------
# generate_yaml
# ---------------------------------------------------------------------------


class TestGenerateYaml:
    def _make_minimal_builder(self) -> ConversationBuilder:
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "quick",
            "verification": True,
            "approval": False,
            "guardrails": "none",
            "confirm": True,
        }
        return builder

    def test_generate_yaml_returns_string(self):
        builder = self._make_minimal_builder()
        yaml_str = builder.generate_yaml()
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0

    def test_generate_yaml_contains_id(self):
        builder = self._make_minimal_builder()
        yaml_str = builder.generate_yaml()
        assert "id: feature-builder" in yaml_str

    def test_generate_yaml_full_team(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "full",
            "verification": True,
            "approval": False,
            "guardrails": "standard",
            "confirm": True,
        }
        yaml_str = builder.generate_yaml()
        assert "planner" in yaml_str
        assert "developer" in yaml_str
        assert "verifier" in yaml_str

    def test_generate_yaml_no_guardrails(self):
        builder = self._make_minimal_builder()
        yaml_str = builder.generate_yaml()
        assert "content-filter" not in yaml_str

    def test_generate_yaml_custom_name(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "custom",
            "custom_name": "my-special-workflow",
            "agents": "single",
            "verification": False,
            "approval": False,
            "guardrails": "none",
            "confirm": True,
        }
        yaml_str = builder.generate_yaml()
        assert "my-special-workflow" in yaml_str

    def test_generate_yaml_with_approval(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "single",
            "verification": False,
            "approval": True,
            "guardrails": "none",
            "confirm": True,
        }
        yaml_str = builder.generate_yaml()
        assert "requires_approval: true" in yaml_str


# ---------------------------------------------------------------------------
# generate_python
# ---------------------------------------------------------------------------


class TestGeneratePython:
    def test_generate_python_returns_string(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "quick",
            "verification": True,
            "approval": False,
            "guardrails": "none",
        }
        py_str = builder.generate_python()
        assert isinstance(py_str, str)
        assert len(py_str) > 0

    def test_generate_python_contains_imports(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "quick",
            "verification": False,
            "approval": False,
            "guardrails": "none",
        }
        py_str = builder.generate_python()
        assert "TeamBuilder" in py_str
        assert "AgentRole" in py_str

    def test_generate_python_with_guardrails(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "quick",
            "verification": False,
            "approval": False,
            "guardrails": "standard",
        }
        py_str = builder.generate_python()
        assert "GuardrailPipeline" in py_str


# ---------------------------------------------------------------------------
# get_summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    def test_get_summary_returns_string(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "feature-builder",
            "agents": "quick",
            "verification": True,
            "approval": False,
            "guardrails": "standard",
        }
        summary = builder.get_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_summary_includes_workflow_name(self):
        builder = ConversationBuilder()
        builder.answers = {
            "goal": "feature",
            "name": "my-test-flow",
            "agents": "quick",
            "verification": False,
            "approval": False,
            "guardrails": "none",
        }
        summary = builder.get_summary()
        assert "my-test-flow" in summary


# ---------------------------------------------------------------------------
# Voice helpers (mocked)
# ---------------------------------------------------------------------------


class TestVoiceHelpers:
    def test_get_voice_input_when_unavailable(self):
        """When speech_recognition is not importable, returns None."""
        with patch("orchestration.conversation.VOICE_AVAILABLE", False):
            result = get_voice_input()
            assert result is None

    def test_install_voice_support_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_voice_support()
            assert result is True

    def test_install_voice_support_failure(self):
        with patch("subprocess.run", side_effect=Exception("failed")):
            result = install_voice_support()
            assert result is False
