"""
SemanticSMARCVerifier — LLM-based quality scoring for agent step outputs.

Replaces the rule-based ResultsVerificationFramework with a single LLM call
that semantically evaluates all five SMARC criteria and returns float scores
(0.0–1.0) per criterion, plus one-sentence reasoning for each score.

Falls back to the structural rule-based checks when no LLM executor is
available or when the LLM call fails.

Compoundable — the Flywheel Criterion
--------------------------------------
The compoundable check goes beyond "does the output have a list field?".
It asks: does this output create a self-reinforcing flywheel across the
entire workflow, where every downstream agent is measurably stronger because
of this output, and that amplification compounds across runs?

    0.0  output is consumed once — no downstream amplification
    0.3  feeds the immediate next step only (linear, not compounding)
    0.6  feeds 2–3 downstream steps; some cross-step reinforcement
    1.0  genuine flywheel: every downstream agent is stronger, AND the
         pattern carries over to future runs of this workflow
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Pass threshold ────────────────────────────────────────────────────────────
# Scores >= PASS_THRESHOLD are treated as True (passed) for downstream consumers
# that expect dict[str, bool].  0.6 means "clearly above mediocre".
PASS_THRESHOLD = 0.6

# ── Prompt ────────────────────────────────────────────────────────────────────

SEMANTIC_SMARC_PROMPT = """\
You are a strict quality auditor for AI agent workflows.

Evaluate the agent step output below against five SMARC quality criteria.
Return ONLY valid JSON — no markdown fences, no text outside the JSON object.

Context:
  Agent role            : {agent_role}
  Workflow step         : {step_id}
  Acceptance criteria   : {expects}

Output to evaluate:
<output>
{output}
</output>

Score each criterion from 0.0 to 1.0 (two decimal places):

SPECIFIC (S):
  Are the claims concrete, precise, and independently verifiable?
  0.0 = vague generalities ("it will work well", "good solution")
  0.5 = some specifics but significant gaps remain
  1.0 = every claim is concrete, precise, and verifiable without ambiguity

MEASURABLE (M):
  Does the output include quantified metrics, numbers, timelines, or testable
  criteria that allow objective pass/fail evaluation?
  0.0 = no numbers, thresholds, or testable criteria whatsoever
  0.5 = some quantification but key outcomes remain unmeasured
  1.0 = all key outcomes have explicit numeric or testable success criteria

ACTIONABLE (A):
  Does the output give the next agent an unambiguous, immediately executable
  next step — no further clarification required?
  0.0 = no clear path forward; recipient must figure out what to do
  0.5 = direction given but requires significant interpretation
  1.0 = explicit next actions with clear ownership and sequencing

REUSABLE (R):
  Could the structure, patterns, or insights apply to a similar task in a
  different context without being rebuilt from scratch?
  0.0 = so context-specific it cannot be transferred or templated
  0.5 = partially transferable; some rework needed
  1.0 = structured as a reusable template or pattern

COMPOUNDABLE (C) — THE FLYWHEEL CRITERION:
  This is the most critical criterion. A compoundable output does NOT just
  produce a linear result. Instead it creates a FLYWHEEL EFFECT:

  - It FEEDS INTO and STRENGTHENS every subsequent agent step — not just
    the next one but all remaining steps downstream
  - It creates a self-reinforcing loop: past outputs keep producing returns
    even as new steps build on top of the existing success
  - Total workflow value grows EXPONENTIALLY — each downstream agent is
    measurably stronger BECAUSE of this output, and that amplification
    compounds across future runs of the workflow

  Concrete signals of high compoundability:
  • Planner breakdown is structured so precisely that the verifier can
    auto-check each criterion AND the reviewer can reuse those criteria
    as quality gates in every future run
  • Developer code is built as reusable, composable modules the tester,
    reviewer, AND future feature iterations can extend — not one-off code
  • Verifier report surfaces patterns that sharpen the tester's coverage
    AND gives the improvement loop a precise target for which agent persona
    to patch first

  0.0 = output is consumed once; zero downstream amplification
  0.3 = feeds the immediate next step only (linear, not compounding)
  0.6 = feeds 2–3 downstream steps; meaningful cross-step reinforcement
  1.0 = genuine flywheel: every downstream agent is measurably stronger,
        AND the compound effect carries forward to future workflow runs

Return this JSON object and nothing else:
{{
  "specific":     0.00,
  "measurable":   0.00,
  "actionable":   0.00,
  "reusable":     0.00,
  "compoundable": 0.00,
  "reasoning": {{
    "specific":     "one sentence explaining the score",
    "measurable":   "one sentence explaining the score",
    "actionable":   "one sentence explaining the score",
    "reusable":     "one sentence explaining the score",
    "compoundable": "one sentence analysing the flywheel effect"
  }}
}}"""


# ── Data models ───────────────────────────────────────────────────────────────


@dataclass
class SMARCResult:
    """Full SMARC evaluation result with float scores and LLM reasoning."""

    agent_role: str
    step_id: str
    scores: dict[str, float]  # {"specific": 0.82, …}
    reasoning: dict[str, str]  # {"specific": "Because …", …}
    source: str  # "llm" | "rule"
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def passed(self) -> dict[str, bool]:
        """Threshold the float scores to bool for backward-compat consumers."""
        return {k: v >= PASS_THRESHOLD for k, v in self.scores.items()}

    @property
    def composite(self) -> float:
        """Simple mean of the 5 scores (0.0 – 1.0)."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_role": self.agent_role,
            "step_id": self.step_id,
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
            "reasoning": {k: v[:200] for k, v in self.reasoning.items()},
            "composite": round(self.composite, 3),
            "passed": self.passed,
            "source": self.source,
            "evaluated_at": self.evaluated_at,
        }


# ── Rule-based fallback ───────────────────────────────────────────────────────
# Used when no LLM executor is configured or when the LLM call fails.


def _rule_based_scores(smarc_input: dict[str, Any]) -> dict[str, float]:
    """
    Convert rule-based bool checks into float scores.

    These are the same logic as ResultsVerificationFramework but mapped
    to a 0.0/0.8 float pair so they fit the SMARCResult schema.
    """
    output = smarc_input.get("output", "") or ""
    has_numbers = any(c.isdigit() for c in output)
    next_step_present = "next_step" in smarc_input or "recommendation" in smarc_input
    artifacts = smarc_input.get("artifacts", [])

    specific = (
        smarc_input is not None
        and len(smarc_input) > 0
        and all(v is not None for v in smarc_input.values())
    )
    measurable = bool(smarc_input) and any(
        isinstance(v, (int, float, str)) for v in smarc_input.values()
    )
    actionable = next_step_present
    reusable = len(smarc_input) > 1
    # Compoundable rule: output is non-trivial and has structured artifacts
    compoundable = (
        isinstance(artifacts, (list, dict)) and len(output) > 200  # substantive output
    )

    def f(b: bool) -> float:
        return 0.8 if b else 0.1

    return {
        "specific": f(specific),
        "measurable": f(measurable) if has_numbers else 0.3,
        "actionable": f(actionable),
        "reusable": f(reusable),
        "compoundable": f(compoundable),
    }


_RULE_REASONING: dict[str, str] = {
    "specific": "Rule-based: all values non-None in result dict.",
    "measurable": "Rule-based: numeric or string values present.",
    "actionable": "Rule-based: next_step or recommendation key present.",
    "reusable": "Rule-based: dict has more than one key.",
    "compoundable": "Rule-based: output length and artifacts list checked.",
}


# ── Main class ────────────────────────────────────────────────────────────────


class SemanticSMARCVerifier:
    """
    LLM-based SMARC evaluator.  Drops into RunRecorder in place of the
    structural ResultsVerificationFramework.

    Usage:
        verifier = SemanticSMARCVerifier(llm_executor=my_async_llm_fn)
        result = await verifier.verify(
            output="<agent output text>",
            agent_role="planner",
            step_id="plan",
            expects="STATUS: done",
        )
        print(result.scores)      # {"specific": 0.82, "compoundable": 0.94, …}
        print(result.passed)      # {"specific": True,  "compoundable": True, …}
        print(result.composite)   # 0.87
        print(result.reasoning["compoundable"])
    """

    def __init__(
        self,
        llm_executor: Callable | None = None,
        pass_threshold: float = PASS_THRESHOLD,
        max_output_chars: int = 3000,
    ) -> None:
        self.llm_executor = llm_executor
        self.pass_threshold = pass_threshold
        self.max_output_chars = max_output_chars

        # Rolling history (last 100 results) for trend queries
        self._history: list[SMARCResult] = []

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def verify(
        self,
        output: str,
        agent_role: str,
        step_id: str,
        expects: str = "",
        smarc_input: dict[str, Any] | None = None,
    ) -> SMARCResult:
        """
        Evaluate a step output against all 5 SMARC criteria.

        Args:
            output:      The raw text produced by the agent LLM.
            agent_role:  E.g. "planner", "developer".
            step_id:     E.g. "plan", "implement".
            expects:     The step's acceptance criteria string.
            smarc_input: Optional pre-built dict (used for rule fallback).

        Returns:
            SMARCResult with float scores, bool passed dict, and reasoning.
        """
        if self.llm_executor is not None:
            try:
                result = await self._llm_verify(output, agent_role, step_id, expects)
                self._history.append(result)
                if len(self._history) > 100:
                    self._history = self._history[-100:]
                return result
            except Exception as exc:
                logger.warning(
                    "SemanticSMARCVerifier LLM call failed (%s); using rule-based fallback.",
                    exc,
                )

        # Rule-based fallback
        return self._rule_verify(
            output=output,
            agent_role=agent_role,
            step_id=step_id,
            smarc_input=smarc_input or {},
        )

    def history_for_agent(self, agent_role: str) -> list[SMARCResult]:
        """Return all stored results for a given agent role."""
        return [r for r in self._history if r.agent_role == agent_role]

    def avg_scores(self, agent_role: str | None = None) -> dict[str, float]:
        """Average per-criterion scores across stored history."""
        items = (
            [r for r in self._history if r.agent_role == agent_role]
            if agent_role
            else list(self._history)
        )
        if not items:
            return {}
        criteria = list(items[0].scores)
        return {
            c: sum(r.scores.get(c, 0.0) for r in items) / len(items) for c in criteria
        }

    # ------------------------------------------------------------------ #
    # LLM path                                                             #
    # ------------------------------------------------------------------ #

    async def _llm_verify(
        self,
        output: str,
        agent_role: str,
        step_id: str,
        expects: str,
    ) -> SMARCResult:
        truncated = output[: self.max_output_chars]
        if len(output) > self.max_output_chars:
            truncated += (
                f"\n… [truncated — {len(output) - self.max_output_chars} chars omitted]"
            )

        prompt = SEMANTIC_SMARC_PROMPT.format(
            agent_role=agent_role,
            step_id=step_id,
            expects=expects or "(none specified)",
            output=truncated,
        )

        raw = await self._call_llm(prompt)
        data = self._parse_json(raw)

        scores: dict[str, float] = {}
        reasoning: dict[str, str] = {}
        for criterion in (
            "specific",
            "measurable",
            "actionable",
            "reusable",
            "compoundable",
        ):
            scores[criterion] = float(max(0.0, min(1.0, data.get(criterion, 0.0))))
            reasoning[criterion] = str(data.get("reasoning", {}).get(criterion, ""))[
                :200
            ]

        return SMARCResult(
            agent_role=agent_role,
            step_id=step_id,
            scores=scores,
            reasoning=reasoning,
            source="llm",
        )

    async def _call_llm(self, prompt: str) -> str:
        if self.llm_executor is None:
            raise ValueError("No LLM executor configured.")
        result = self.llm_executor(prompt, None)
        if inspect.isawaitable(result):
            result = await result
        return str(result)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Strip optional markdown fences and parse JSON."""
        text = raw.strip()
        for fence in ("```json", "```"):
            if fence in text:
                parts = text.split(fence)
                if len(parts) >= 3:
                    text = parts[1].strip()
                elif len(parts) == 2:
                    text = parts[1].split("```")[0].strip()
                break
        return json.loads(text)

    # ------------------------------------------------------------------ #
    # Rule-based fallback                                                  #
    # ------------------------------------------------------------------ #

    def _rule_verify(
        self,
        output: str,
        agent_role: str,
        step_id: str,
        smarc_input: dict[str, Any],
    ) -> SMARCResult:
        scores = _rule_based_scores(smarc_input or {"output": output})
        return SMARCResult(
            agent_role=agent_role,
            step_id=step_id,
            scores=scores,
            reasoning=dict(_RULE_REASONING),
            source="rule",
        )
