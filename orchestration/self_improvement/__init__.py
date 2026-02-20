"""
orchestration.self_improvement
==============================

Self-improving workflow loop: SMARC scoring → prompt patching → A/B testing.

Quick start
-----------
    from orchestration.self_improvement import get_improvement_loop

    loop = get_improvement_loop()
    loop.attach_to_team(team, workflow_id="feature-dev", self_improve=True)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from orchestration.self_improvement.improvement_loop import (
    ImprovementLoop,
    PromptPatch,
    PromptVersion,
    PromptVersionStore,
)
from orchestration.self_improvement.run_recorder import RunRecord, RunRecorder

__all__ = [
    "ImprovementLoop",
    "PromptPatch",
    "PromptVersion",
    "PromptVersionStore",
    "RunRecord",
    "RunRecorder",
    "get_improvement_loop",
]

# Module-level singleton (created lazily)
_default_loop: ImprovementLoop | None = None


def get_improvement_loop(
    db_path: Path | None = None,
    llm_executor: Callable | None = None,
    auto_approve_patches: bool = False,
    ab_test_enabled: bool = True,
    pattern_trigger_n: int = 5,
    stagnation_threshold: float = 0.05,
    *,
    force_new: bool = False,
) -> ImprovementLoop:
    """Return the module-level ImprovementLoop singleton (creates one on first call).

    Args:
        db_path: Path to the SQLite file. Defaults to ~/.agenticom/self_improve.db.
        llm_executor: Optional LLM callable for prompt evolution.
        auto_approve_patches: If True, patches are applied without human review.
        ab_test_enabled: If True, A/B test candidate personas on 50% of runs.
        pattern_trigger_n: Run gap analysis every N runs.
        stagnation_threshold: Idle rate above which AntiIdlingSystem fires.
        force_new: If True, discard the existing singleton and create a fresh one.
    """
    global _default_loop
    if _default_loop is None or force_new:
        _default_loop = ImprovementLoop(
            db_path=db_path,
            llm_executor=llm_executor,
            auto_approve_patches=auto_approve_patches,
            ab_test_enabled=ab_test_enabled,
            pattern_trigger_n=pattern_trigger_n,
            stagnation_threshold=stagnation_threshold,
        )
    return _default_loop
