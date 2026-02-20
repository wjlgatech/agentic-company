"""
PromptEvolver — turn SMARC capability gaps into prompt patches.

Two paths:
  • heuristic  — rule-based suffix appended to current persona (no LLM, always works)
  • LLM        — full persona rewrite via EVOLUTION_PROMPT (requires llm_executor)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from orchestration.self_improvement.improvement_loop import (
        PromptPatch,
        PromptVersion,
    )
    from orchestration.self_improvement.vendor.recursive_self_improvement import (
        RecursiveSelfImprovementProtocol,
    )

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Heuristic rules                                                               #
# --------------------------------------------------------------------------- #

HEURISTIC_RULES: dict[str, str] = {
    "output_specificity": (
        "\n\nCRITICAL: Be specific. " "Every claim must be concrete and verifiable."
    ),
    "output_measurability": (
        "\n\nCRITICAL: Always include quantified metrics, "
        "numbers, or measurable criteria."
    ),
    "output_actionability": (
        "\n\nCRITICAL: End every response with " "'Next step:' and 'Recommendation:'."
    ),
    "knowledge_reusability": (
        "\n\nCRITICAL: Structure output so it can be " "applied in other contexts."
    ),
    "knowledge_compoundability": (
        "\n\nCRITICAL: Include structured lists or " "sub-components in your response."
    ),
}

# SMARC capability suffix → heuristic key mapping
CAPABILITY_TO_HEURISTIC: dict[str, str] = {
    "output_specificity": "output_specificity",
    "output_measurability": "output_measurability",
    "output_actionability": "output_actionability",
    "knowledge_reusability": "knowledge_reusability",
    "knowledge_compoundability": "knowledge_compoundability",
}

# --------------------------------------------------------------------------- #
# LLM evolution prompt                                                          #
# --------------------------------------------------------------------------- #

EVOLUTION_PROMPT = """You are a prompt engineering expert.

Agent role: {agent_role}
Current persona:
{current_persona}

SMARC gap analysis over {run_count} runs:
{capability_gaps}

Approved lessons relevant to this role:
{relevant_lessons}

Rewrite the persona to fix the identified gaps.
Rules:
- Keep the core identity intact
- Add specific, actionable instructions that directly address the gaps
- Maximum 20% length increase vs the current persona
- Do NOT add unrelated instructions

Return valid JSON only (no markdown):
{{"proposed_persona": "...", "justification": "...", "confidence": 0.0}}"""


class PromptEvolver:
    """Map identified capability gaps into PromptPatch proposals."""

    def __init__(
        self,
        improvement_protocol: RecursiveSelfImprovementProtocol,
        llm_executor: Callable | None = None,
        lesson_manager: Any | None = None,
    ) -> None:
        self.improvement_protocol = improvement_protocol
        self.llm_executor = llm_executor
        self.lesson_manager = lesson_manager

    async def propose_patch(
        self,
        workflow_id: str,
        agent_id: str,
        agent_role: str,
        current_version: PromptVersion,
        capability_gaps: list[dict[str, Any]],
        run_count: int = 0,
    ) -> PromptPatch:
        """
        Produce a PromptPatch (status=pending) for the given gaps.

        Tries LLM path first; falls back to heuristic if unavailable or erroring.
        """
        import uuid
        from datetime import datetime

        from orchestration.self_improvement.improvement_loop import PromptPatch

        # Filter gaps relevant to this agent_role
        relevant_gaps = [
            g
            for g in capability_gaps
            if agent_role in g.get("capability", "")
            or g.get("source") in {"low_performance_areas", "missing_capabilities"}
        ]
        if not relevant_gaps:
            relevant_gaps = capability_gaps

        generated_by = "heuristic"
        proposed_persona = current_version.persona_text
        justification = "No gaps found; persona unchanged."
        confidence = 0.5

        if relevant_gaps:
            if self.llm_executor is not None:
                try:
                    proposed_persona, justification, confidence, generated_by = (
                        await self._llm_propose(
                            agent_role=agent_role,
                            current_persona=current_version.persona_text,
                            capability_gaps=relevant_gaps,
                            run_count=run_count,
                        )
                    )
                except Exception as exc:
                    logger.warning(
                        "LLM persona evolution failed (%s); using heuristic.", exc
                    )

            if generated_by == "heuristic":
                proposed_persona, justification, confidence = self._heuristic_propose(
                    agent_role=agent_role,
                    current_persona=current_version.persona_text,
                    capability_gaps=relevant_gaps,
                )

        # Record each gap as an executed improvement in the protocol
        for gap in relevant_gaps:
            cap_name = gap.get("capability", gap.get("name", ""))
            if cap_name:
                try:
                    self.improvement_protocol.execute_improvement(
                        {
                            "target": cap_name,
                            "type": "prompt_patch",
                            "meets_do_no_harm": True,
                            "meets_human_alignment": True,
                            "meets_transparency": True,
                            "meets_reversibility": True,
                        }
                    )
                except Exception as exc:
                    logger.debug("execute_improvement skipped: %s", exc)

        gap_names = [g.get("capability", g.get("name", str(g))) for g in relevant_gaps]

        return PromptPatch(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            agent_id=agent_id,
            agent_role=agent_role,
            capability_gaps=gap_names,
            base_prompt_version_id=current_version.id,
            proposed_persona_text=proposed_persona,
            justification=justification,
            generated_by=generated_by,
            status="pending",
            confidence=confidence,
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
            created_at=datetime.utcnow().isoformat(),
        )

    # ------------------------------------------------------------------ #
    # Heuristic path                                                       #
    # ------------------------------------------------------------------ #

    def _heuristic_propose(
        self,
        agent_role: str,
        current_persona: str,
        capability_gaps: list[dict[str, Any]],
    ) -> tuple[str, str, float]:
        """Append targeted instruction suffixes based on failing SMARC criteria."""
        suffixes: list[str] = []
        addressed: list[str] = []

        for gap in capability_gaps:
            cap = gap.get("capability", "")
            # Strip agent_role prefix if present
            bare_cap = cap.replace(f"{agent_role}_", "")
            rule = HEURISTIC_RULES.get(bare_cap) or HEURISTIC_RULES.get(cap)
            if rule and rule not in suffixes:
                suffixes.append(rule)
                addressed.append(bare_cap or cap)

        if not suffixes:
            return current_persona, "No matching heuristic rules found.", 0.4

        proposed = current_persona + "".join(suffixes)
        justification = (
            f"Heuristic patch addressing: {', '.join(addressed)}. "
            "Specific instruction suffixes appended to existing persona."
        )
        return proposed, justification, 0.6

    # ------------------------------------------------------------------ #
    # LLM path                                                             #
    # ------------------------------------------------------------------ #

    async def _llm_propose(
        self,
        agent_role: str,
        current_persona: str,
        capability_gaps: list[dict[str, Any]],
        run_count: int,
    ) -> tuple[str, str, float, str]:
        """Call LLM to rewrite the persona and return (persona, justification, confidence, "llm")."""
        # Fetch relevant approved lessons
        relevant_lessons = "None available."
        if self.lesson_manager is not None:
            try:
                lessons = self.lesson_manager.get_approved(limit=3)
                if lessons:
                    relevant_lessons = "\n".join(
                        f"- {l.title}: {l.recommendation}" for l in lessons
                    )
            except Exception:
                pass

        prompt = EVOLUTION_PROMPT.format(
            agent_role=agent_role,
            current_persona=current_persona,
            run_count=run_count,
            capability_gaps=json.dumps(capability_gaps, indent=2),
            relevant_lessons=relevant_lessons,
        )

        response_text = await self._call_llm(prompt)

        # Parse JSON from response
        json_str = response_text
        for marker in ("```json", "```"):
            if marker in json_str:
                parts = json_str.split(marker)
                json_str = parts[1].split("```")[0] if len(parts) > 1 else json_str
                break

        data = json.loads(json_str.strip())
        proposed_persona = data.get("proposed_persona", current_persona)
        justification = data.get("justification", "LLM rewrite.")
        confidence = float(data.get("confidence", 0.75))
        return proposed_persona, justification, confidence, "llm"

    async def _call_llm(self, prompt: str) -> str:
        """Invoke the llm_executor (handles both sync and async callables)."""
        import inspect

        if self.llm_executor is None:
            raise ValueError("No LLM executor configured.")

        result = self.llm_executor(prompt, None)
        if inspect.isawaitable(result):
            result = await result
        return str(result)
