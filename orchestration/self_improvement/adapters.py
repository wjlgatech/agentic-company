"""
Adapters — Convert Agenticom types into the dicts expected by vendor classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from orchestration.agents.team import StepResult


class StepResultAdapter:
    """Convert a StepResult into dicts for the vendor SMARC verifier."""

    @staticmethod
    def to_smarc_input(step_result: StepResult) -> dict[str, Any]:
        """Build a dict that satisfies all 5 SMARC criteria when a step succeeds.

        - specific/measurable  → output, duration_ms, tokens_used (non-None scalars)
        - actionable           → next_step, recommendation keys
        - reusable             → multiple top-level keys
        - compoundable         → artifacts list
        """
        return {
            "output": step_result.agent_result.output or "",
            "step_id": step_result.step.id,
            "success": step_result.agent_result.success,
            "duration_ms": step_result.agent_result.duration_ms,
            "tokens_used": step_result.agent_result.tokens_used,
            "retries": step_result.retries,
            "artifacts": step_result.agent_result.artifacts,
            # actionability keys required by ResultsVerificationFramework
            "next_step": step_result.step.id,
            "recommendation": step_result.step.expects,
        }

    @staticmethod
    def to_performance_data(
        step_result: StepResult, smarc_score: float
    ) -> dict[str, float]:
        """Map SMARC composite score + execution stats → {accuracy, efficiency, adaptability}."""
        return {
            "accuracy": smarc_score,
            "efficiency": max(0.0, 1.0 - step_result.retries * 0.2),
            "adaptability": 1.0 if step_result.agent_result.success else 0.3,
        }


class CapabilityMapper:
    """Map SMARC criterion results → RecursiveSelfImprovementProtocol capability dicts."""

    SMARC_TO_CAPABILITY: dict[str, str] = {
        "specific": "output_specificity",
        "measurable": "output_measurability",
        "actionable": "output_actionability",
        "reusable": "knowledge_reusability",
        "compoundable": "knowledge_compoundability",
    }

    @staticmethod
    def smarc_to_capabilities(
        agent_role: str, smarc_results: dict[str, bool]
    ) -> dict[str, Any]:
        """Return a capability map update suitable for update_capability_map()."""
        cap_name = CapabilityMapper.SMARC_TO_CAPABILITY
        return {
            f"{agent_role}_{cap_name.get(criterion, criterion)}": {
                "proficiency": 0.8 if passed else 0.1,
                "source": "smarc_verification",
                "evidence": f"{'passed' if passed else 'failed'} {criterion} check",
            }
            for criterion, passed in smarc_results.items()
        }

    @staticmethod
    def smarc_score(smarc_results: dict[str, bool]) -> float:
        """Return fraction of SMARC criteria that passed (0.0 – 1.0)."""
        if not smarc_results:
            return 0.0
        return sum(smarc_results.values()) / len(smarc_results)
