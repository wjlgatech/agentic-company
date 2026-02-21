"""
Skill Loader — loads SKILL.md files into agent personas.

Compatible with the Agent Skills open standard (agentskills.io).
Searches: .agent/skills/ → ~/.claude/skills/ → agenticom/bundled_skills/
"""

from __future__ import annotations

import re
from pathlib import Path

# Project-bundled skills, lowest priority (community installs override these)
_BUNDLED_SKILLS_DIR = (
    Path(__file__).parent.parent.parent / "agenticom" / "bundled_skills"
)

# Default search order: project-local → user-global → framework bundled
_DEFAULT_SEARCH_DIRS: list[Path] = [
    Path(".agent/skills"),
    Path.home() / ".claude" / "skills",
    _BUNDLED_SKILLS_DIR,
]

# Strip these clauses — they assume human interaction, unsafe in autonomous mode
_ASK_USER_PATTERN = re.compile(
    r"[Aa]sk the (?:user|client|stakeholder)[^\n]*\n?", re.MULTILINE
)


class SkillLoader:
    """
    Loads SKILL.md-format skill files and injects their body into agent personas.

    Progressive disclosure model:
      Level 1 (metadata): name + description — used by SkillRouter for matching
      Level 2 (instructions): SKILL.md body — injected via this class
      Level 3 (scripts/refs): not loaded (no VM in Agenticom; use execute: field instead)
    """

    def __init__(self, extra_dirs: list[Path] | None = None) -> None:
        self.search_dirs: list[Path] = list(extra_dirs or []) + _DEFAULT_SEARCH_DIRS

    # ── Public API ────────────────────────────────────────────────────────────

    def load(
        self,
        skill_name: str,
        max_tokens: int = 400,
        sections: list[str] | None = None,
    ) -> str:
        """
        Load a skill by name and return injectable text.

        Args:
            skill_name: kebab-case skill directory name
            max_tokens: approximate token budget (1 token ≈ 0.75 words)
            sections:   if given, extract only these ## section headings

        Returns:
            Processed skill body string, or "" if not found.
        """
        path = self._find_skill(skill_name)
        if not path:
            return ""

        text = path.read_text(encoding="utf-8")
        body = self._strip_frontmatter(text)
        body = _ASK_USER_PATTERN.sub("", body)

        if sections:
            body = self._extract_sections(body, sections)

        # Approximate token cap: 1 token ≈ 0.75 words
        words = body.split()
        capped = " ".join(words[: int(max_tokens * 0.75)])
        return capped.strip()

    def load_metadata(self, skill_name: str) -> dict[str, str]:
        """
        Load just the frontmatter metadata (name, description).
        Used by SkillRouter for keyword matching without loading full body.
        """
        path = self._find_skill(skill_name)
        if not path:
            return {}

        text = path.read_text(encoding="utf-8")
        return self._parse_frontmatter(text)

    def list_available(self) -> list[str]:
        """Return sorted list of all discoverable skill names."""
        found: dict[str, str] = {}
        for d in reversed(self.search_dirs):  # lower priority first → higher wins
            if d.exists():
                for p in sorted(d.iterdir()):
                    if (p / "SKILL.md").exists():
                        found[p.name] = p.name
        return sorted(found.keys())

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _find_skill(self, name: str) -> Path | None:
        for d in self.search_dirs:
            p = d / name / "SKILL.md"
            if p.exists():
                return p
        return None

    @staticmethod
    def _strip_frontmatter(text: str) -> str:
        """Remove YAML frontmatter block (--- ... ---)."""
        return re.sub(r"^---.*?---\n?", "", text, flags=re.DOTALL).strip()

    @staticmethod
    def _parse_frontmatter(text: str) -> dict[str, str]:
        """Extract key: value pairs from YAML frontmatter."""
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not m:
            return {}
        result: dict[str, str] = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip().strip('"')
        return result

    @staticmethod
    def _extract_sections(body: str, sections: list[str]) -> str:
        """Extract only the requested ## heading sections from body."""
        lower_sections = [s.lower() for s in sections]
        lines = body.splitlines()
        result: list[str] = []
        in_target = False

        for line in lines:
            if line.startswith("#"):
                heading = line.lstrip("#").strip().lower()
                in_target = any(s in heading for s in lower_sections)
            if in_target:
                result.append(line)

        return "\n".join(result).strip() if result else body
