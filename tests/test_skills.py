"""
Tests for Phase 1 skill injection system.

Covers:
  - SkillLoader: load, metadata, list, frontmatter stripping,
                 "ask the user" stripping, token cap, section extraction,
                 search path priority, missing skill fallback
  - AgentConfig: skills field
  - Agent: base_persona attribute
  - WorkflowParser: reads skills from YAML, injects into persona,
                    skills field on AgentDefinition
  - Integration: full parse → agent.persona contains skill content
"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestration.agents.base import AgentConfig, AgentRole
from orchestration.agents.specialized import create_agent
from orchestration.tools.skill_loader import SkillLoader
from orchestration.workflows.parser import AgentDefinition, WorkflowParser

# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with one test skill."""
    s = tmp_path / "my-skill"
    s.mkdir()
    (s / "SKILL.md").write_text(
        "---\n"
        "name: my-skill\n"
        "description: A test skill for unit testing.\n"
        "---\n"
        "\n"
        "# My Skill\n"
        "\n"
        "## Overview\n"
        "This skill does X.\n"
        "\n"
        "## Step-by-Step\n"
        "1. Do step one.\n"
        "2. Do step two.\n"
    )
    return tmp_path


@pytest.fixture
def loader(skill_dir: Path) -> SkillLoader:
    return SkillLoader(extra_dirs=[skill_dir])


@pytest.fixture
def bundled_loader() -> SkillLoader:
    """Loader that only searches the bundled skills directory."""
    from orchestration.tools.skill_loader import _BUNDLED_SKILLS_DIR

    return SkillLoader(extra_dirs=[_BUNDLED_SKILLS_DIR])


# ─────────────────────────────────────────────────────────────────────────────
#  SkillLoader — basic load
# ─────────────────────────────────────────────────────────────────────────────


class TestSkillLoaderLoad:
    def test_load_existing_skill_returns_body(self, loader: SkillLoader) -> None:
        result = loader.load("my-skill")
        assert "My Skill" in result or "step one" in result.lower()

    def test_load_missing_skill_returns_empty_string(self, loader: SkillLoader) -> None:
        result = loader.load("nonexistent-skill")
        assert result == ""

    def test_frontmatter_stripped(self, loader: SkillLoader) -> None:
        result = loader.load("my-skill")
        assert "---" not in result
        assert "name: my-skill" not in result

    def test_body_content_present(self, loader: SkillLoader) -> None:
        result = loader.load("my-skill")
        assert "step one" in result.lower() or "overview" in result.lower()

    def test_ask_the_user_stripped(self, tmp_path: Path) -> None:
        s = tmp_path / "ask-skill"
        s.mkdir()
        (s / "SKILL.md").write_text(
            "---\nname: ask-skill\ndescription: test\n---\n"
            "Ask the user for their name.\n"
            "Here is the real content.\n"
        )
        result = SkillLoader(extra_dirs=[tmp_path]).load("ask-skill")
        assert "Ask the user" not in result
        assert "real content" in result

    def test_ask_client_stripped(self, tmp_path: Path) -> None:
        s = tmp_path / "ask-client-skill"
        s.mkdir()
        (s / "SKILL.md").write_text(
            "---\nname: ask-client-skill\ndescription: test\n---\n"
            "Ask the client for their requirements.\n"
            "Proceed with implementation.\n"
        )
        result = SkillLoader(extra_dirs=[tmp_path]).load("ask-client-skill")
        assert "Ask the client" not in result
        assert "implementation" in result

    def test_max_tokens_cap(self, tmp_path: Path) -> None:
        # Write a very long skill body
        s = tmp_path / "long-skill"
        s.mkdir()
        body = "word " * 1000  # 1000 words ≈ 1333 tokens
        (s / "SKILL.md").write_text(
            f"---\nname: long-skill\ndescription: x\n---\n{body}"
        )
        result = SkillLoader(extra_dirs=[tmp_path]).load("long-skill", max_tokens=100)
        # 100 tokens * 0.75 ≈ 75 words
        word_count = len(result.split())
        assert word_count <= 80  # slight tolerance

    def test_default_max_tokens_400(self, tmp_path: Path) -> None:
        s = tmp_path / "med-skill"
        s.mkdir()
        body = "word " * 1000
        (s / "SKILL.md").write_text(
            f"---\nname: med-skill\ndescription: x\n---\n{body}"
        )
        result = SkillLoader(extra_dirs=[tmp_path]).load("med-skill")
        word_count = len(result.split())
        assert word_count <= 320  # 400 * 0.75 = 300, slight tolerance

    def test_empty_skill_returns_empty_string(self, tmp_path: Path) -> None:
        s = tmp_path / "empty-skill"
        s.mkdir()
        (s / "SKILL.md").write_text("---\nname: empty-skill\ndescription: test\n---\n")
        result = SkillLoader(extra_dirs=[tmp_path]).load("empty-skill")
        assert result == ""


# ─────────────────────────────────────────────────────────────────────────────
#  SkillLoader — section extraction
# ─────────────────────────────────────────────────────────────────────────────


class TestSkillLoaderSections:
    def test_section_extraction_returns_only_target(self, loader: SkillLoader) -> None:
        result = loader.load("my-skill", sections=["step-by-step"])
        assert "Step-by-Step" in result
        # Overview section should not appear
        assert "Overview" not in result

    def test_section_extraction_case_insensitive(self, loader: SkillLoader) -> None:
        result = loader.load("my-skill", sections=["STEP-BY-STEP"])
        assert "step" in result.lower()

    def test_section_not_found_returns_full_body(self, loader: SkillLoader) -> None:
        # When requested section doesn't exist, fall back to full body
        result = loader.load("my-skill", sections=["nonexistent-section"])
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
#  SkillLoader — metadata and discovery
# ─────────────────────────────────────────────────────────────────────────────


class TestSkillLoaderMetadata:
    def test_load_metadata_returns_name_and_description(
        self, loader: SkillLoader
    ) -> None:
        meta = loader.load_metadata("my-skill")
        assert meta.get("name") == "my-skill"
        assert "test skill" in meta.get("description", "").lower()

    def test_load_metadata_missing_skill_returns_empty(
        self, loader: SkillLoader
    ) -> None:
        assert loader.load_metadata("no-such-skill") == {}

    def test_list_available_includes_installed_skill(self, loader: SkillLoader) -> None:
        available = loader.list_available()
        assert "my-skill" in available

    def test_list_available_sorted(self, tmp_path: Path) -> None:
        for name in ["zzz-skill", "aaa-skill", "mmm-skill"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n")
        result = SkillLoader(extra_dirs=[tmp_path]).list_available()
        assert result == sorted(result)


# ─────────────────────────────────────────────────────────────────────────────
#  SkillLoader — search path priority
# ─────────────────────────────────────────────────────────────────────────────


class TestSkillLoaderPriority:
    def test_extra_dirs_take_priority_over_bundled(self, tmp_path: Path) -> None:
        """A skill in extra_dirs should shadow one in bundled_skills."""
        from orchestration.tools.skill_loader import _BUNDLED_SKILLS_DIR

        # Shadowing bundled lint-and-validate with a custom version
        override = tmp_path / "lint-and-validate"
        override.mkdir()
        (override / "SKILL.md").write_text(
            "---\nname: lint-and-validate\ndescription: overridden\n---\nCUSTOM CONTENT"
        )
        loader = SkillLoader(extra_dirs=[tmp_path, _BUNDLED_SKILLS_DIR])
        result = loader.load("lint-and-validate")
        assert "CUSTOM CONTENT" in result

    def test_bundled_skill_found_when_not_in_extra(self) -> None:
        """Bundled skills should be found even without extra_dirs."""
        from orchestration.tools.skill_loader import _BUNDLED_SKILLS_DIR

        loader = SkillLoader(extra_dirs=[_BUNDLED_SKILLS_DIR])
        result = loader.load("lint-and-validate")
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
#  Bundled skills sanity checks
# ─────────────────────────────────────────────────────────────────────────────


BUNDLED_SKILLS = [
    "lint-and-validate",
    "code-review-checklist",
    "tdd-patterns",
    "technical-planning",
    "security-code-review",
    "python-coding-standards",
]


class TestBundledSkills:
    @pytest.mark.parametrize("skill_name", BUNDLED_SKILLS)
    def test_bundled_skill_loads(
        self, bundled_loader: SkillLoader, skill_name: str
    ) -> None:
        result = bundled_loader.load(skill_name)
        assert len(result) > 50, f"{skill_name} body is too short"

    @pytest.mark.parametrize("skill_name", BUNDLED_SKILLS)
    def test_bundled_skill_has_metadata(
        self, bundled_loader: SkillLoader, skill_name: str
    ) -> None:
        meta = bundled_loader.load_metadata(skill_name)
        assert meta.get("name") == skill_name
        assert len(meta.get("description", "")) > 20

    @pytest.mark.parametrize("skill_name", BUNDLED_SKILLS)
    def test_bundled_skill_no_ask_the_user(
        self, bundled_loader: SkillLoader, skill_name: str
    ) -> None:
        result = bundled_loader.load(skill_name)
        assert "ask the user" not in result.lower()
        assert "ask the client" not in result.lower()

    def test_all_bundled_skills_discoverable(self, bundled_loader: SkillLoader) -> None:
        available = bundled_loader.list_available()
        for skill in BUNDLED_SKILLS:
            assert skill in available, f"{skill} not found in available skills"


# ─────────────────────────────────────────────────────────────────────────────
#  AgentConfig — skills field
# ─────────────────────────────────────────────────────────────────────────────


class TestAgentConfigSkills:
    def test_skills_field_defaults_to_empty_list(self) -> None:
        config = AgentConfig(role=AgentRole.DEVELOPER, name="Dev")
        assert config.skills == []

    def test_skills_field_accepts_list(self) -> None:
        config = AgentConfig(
            role=AgentRole.DEVELOPER,
            name="Dev",
            skills=["python-coding-standards", "tdd-patterns"],
        )
        assert len(config.skills) == 2
        assert "python-coding-standards" in config.skills


# ─────────────────────────────────────────────────────────────────────────────
#  Agent — base_persona
# ─────────────────────────────────────────────────────────────────────────────


class TestAgentBasePersona:
    def test_base_persona_matches_initial_persona(self) -> None:
        agent = create_agent(AgentRole.DEVELOPER, persona="I am a developer.")
        assert agent.base_persona == "I am a developer."

    def test_base_persona_unchanged_after_update_persona(self) -> None:
        agent = create_agent(AgentRole.DEVELOPER, persona="Original persona.")
        agent.update_persona("New persona from improvement loop.")
        assert agent.persona == "New persona from improvement loop."
        assert agent.base_persona == "Original persona."

    def test_base_persona_empty_string_when_no_persona(self) -> None:
        agent = create_agent(AgentRole.DEVELOPER)
        assert isinstance(agent.base_persona, str)


# ─────────────────────────────────────────────────────────────────────────────
#  WorkflowParser — AgentDefinition skills field
# ─────────────────────────────────────────────────────────────────────────────


class TestAgentDefinitionSkills:
    def test_agent_definition_skills_defaults_empty(self) -> None:
        defn = AgentDefinition(role="developer")
        assert defn.skills == []

    def test_agent_definition_skills_set(self) -> None:
        defn = AgentDefinition(role="developer", skills=["python-coding-standards"])
        assert "python-coding-standards" in defn.skills


# ─────────────────────────────────────────────────────────────────────────────
#  WorkflowParser — reads skills from YAML
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_YAML_WITH_SKILLS = """
id: test-workflow
name: Test
agents:
  - id: developer
    name: Dev
    skills:
      - python-coding-standards
    prompt: "Write code."
  - id: verifier
    name: Ver
    skills:
      - lint-and-validate
    prompt: "Verify output."
steps:
  - id: build
    agent: developer
    input: "{{task}}"
  - id: check
    agent: verifier
    input: "{{step_outputs.build}}"
"""

MINIMAL_YAML_NO_SKILLS = """
id: test-workflow-plain
name: Test Plain
agents:
  - id: developer
    name: Dev
    prompt: "Write code."
steps:
  - id: build
    agent: developer
    input: "{{task}}"
"""


class TestWorkflowParserSkills:
    def test_parser_reads_skills_from_yaml(self) -> None:
        parser = WorkflowParser()
        defn = parser.parse(MINIMAL_YAML_WITH_SKILLS)
        dev = next(a for a in defn.agents if a.role == "developer")
        assert "python-coding-standards" in dev.skills

    def test_parser_reads_multiple_skills(self) -> None:
        parser = WorkflowParser()
        defn = parser.parse(MINIMAL_YAML_WITH_SKILLS)
        ver = next(a for a in defn.agents if a.role == "verifier")
        assert "lint-and-validate" in ver.skills

    def test_parser_skills_default_empty(self) -> None:
        parser = WorkflowParser()
        defn = parser.parse(MINIMAL_YAML_NO_SKILLS)
        dev = next(a for a in defn.agents if a.role == "developer")
        assert dev.skills == []

    def test_to_team_injects_skill_into_persona(self) -> None:
        parser = WorkflowParser()
        defn = parser.parse(MINIMAL_YAML_WITH_SKILLS)
        team = parser.to_team(defn)
        dev_agent = team.agents[AgentRole.DEVELOPER]
        # The skill body should be present in the agent's persona
        assert "Skill:" in dev_agent.persona or len(dev_agent.persona) > len(
            "Write code."
        )

    def test_to_team_skill_content_in_persona(self, skill_dir: Path) -> None:
        """With a custom loader, verify skill content appears in persona."""
        parser = WorkflowParser()
        defn = parser.parse(
            "id: x\nname: X\nagents:\n"
            "  - id: developer\n    name: Dev\n"
            "    skills:\n      - my-skill\n"
            "    prompt: 'Base persona.'\n"
            "steps:\n  - id: s\n    agent: developer\n    input: '{{task}}'\n"
        )
        loader = SkillLoader(extra_dirs=[skill_dir])
        team = parser.to_team(defn, skill_loader=loader)
        dev_agent = team.agents[AgentRole.DEVELOPER]
        assert "Base persona." in dev_agent.persona
        assert (
            "my-skill" in dev_agent.persona.lower()
            or "step one" in dev_agent.persona.lower()
        )

    def test_to_team_missing_skill_does_not_crash(self) -> None:
        """A skill that doesn't exist should silently be skipped."""
        parser = WorkflowParser()
        defn = parser.parse(
            "id: x\nname: X\nagents:\n"
            "  - id: developer\n    name: Dev\n"
            "    skills:\n      - does-not-exist\n"
            "    prompt: 'Base persona.'\n"
            "steps:\n  - id: s\n    agent: developer\n    input: '{{task}}'\n"
        )
        team = parser.to_team(defn)  # Should not raise
        dev_agent = team.agents[AgentRole.DEVELOPER]
        assert "Base persona." in dev_agent.persona

    def test_to_team_agent_skills_field_set(self) -> None:
        parser = WorkflowParser()
        defn = parser.parse(MINIMAL_YAML_WITH_SKILLS)
        team = parser.to_team(defn)
        dev_agent = team.agents[AgentRole.DEVELOPER]
        assert "python-coding-standards" in dev_agent.config.skills


# ─────────────────────────────────────────────────────────────────────────────
#  Integration: feature-dev.yaml loads with skills
# ─────────────────────────────────────────────────────────────────────────────


_BUNDLED_WORKFLOWS_DIR = (
    Path(__file__).parent.parent / "agenticom" / "bundled_workflows"
)


class TestFeatureDevWorkflowSkills:
    def test_feature_dev_yaml_loads_with_skills(self) -> None:
        path = _BUNDLED_WORKFLOWS_DIR / "feature-dev.yaml"
        parser = WorkflowParser()
        defn = parser.parse_file(path)

        dev = next(a for a in defn.agents if a.role == "developer")
        assert "python-coding-standards" in dev.skills

        ver = next(a for a in defn.agents if a.role == "verifier")
        assert "lint-and-validate" in ver.skills
        assert "security-code-review" in ver.skills

    def test_feature_dev_team_developer_persona_has_skill(self) -> None:
        path = _BUNDLED_WORKFLOWS_DIR / "feature-dev.yaml"
        parser = WorkflowParser()
        defn = parser.parse_file(path)
        team = parser.to_team(defn)

        dev_agent = team.agents[AgentRole.DEVELOPER]
        # Base persona from YAML + injected skill content
        assert "python-coding-standards" in dev_agent.persona.lower()

    def test_feature_dev_team_verifier_persona_has_skills(self) -> None:
        path = _BUNDLED_WORKFLOWS_DIR / "feature-dev.yaml"
        parser = WorkflowParser()
        defn = parser.parse_file(path)
        team = parser.to_team(defn)

        ver_agent = team.agents[AgentRole.VERIFIER]
        assert "lint-and-validate" in ver_agent.persona.lower()
        assert "security" in ver_agent.persona.lower()
