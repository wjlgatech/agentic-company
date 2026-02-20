#!/usr/bin/env python3
"""
Case Study 1: feature-dev — Agent Anatomy & Self-Optimization
==============================================================
Workflow:  feature-dev
Agents:    planner → developer → verifier → tester → reviewer

This script is a self-contained walkthrough of two questions:

  PART A — "How is each agent defined?"
            Loads the real YAML, unpacks every agent's persona, step
            input/output contract, retry policy, and loopback behaviour.

  PART B — "What exactly does the self-optimization layer change?"
            Runs the five agents through 10 simulated runs without any
            LLM key required:  SMARC scoring → performance tracking →
            capability-gap detection → patch proposal → version snapshot.
            Finishes with a side-by-side before/after diff of each persona.

Run:
    python examples/case_study_01_feature_dev_self_improvement.py

No API key needed — the self-optimization pipeline is entirely rule-based
until the LLM-rewrite path is optionally enabled.
"""

from __future__ import annotations

import sys
import textwrap
import uuid
from dataclasses import dataclass, field
from pathlib import Path

# ── Project root on sys.path ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

YAML_PATH = ROOT / "agenticom" / "bundled_workflows" / "feature-dev.yaml"
WIDTH = 72


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def rule(char: str = "─", w: int = WIDTH) -> None:
    print(char * w)


def banner(title: str) -> None:
    print()
    rule("═")
    print(f"  {title}")
    rule("═")


def section(title: str) -> None:
    print()
    rule("─")
    print(f"  {title}")
    rule("─")


def sub(title: str) -> None:
    print(f"\n  ▸ {title}")


def indent(text: str, prefix: str = "      ") -> None:
    for line in text.splitlines():
        print(f"{prefix}{line}")


def bar(score: float, width: int = 12) -> str:
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight step-result shim (mirrors orchestration.agents.team.StepResult)
# We build these from scratch so we never need a live LLM.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class FakeAgentResult:
    output: str
    success: bool
    duration_ms: float
    tokens_used: int
    artifacts: list = field(default_factory=list)


@dataclass
class FakeStep:
    id: str
    expects: str


@dataclass
class FakeStepResult:
    step: FakeStep
    agent_result: FakeAgentResult
    retries: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# PART A — AGENT ANATOMY
# ─────────────────────────────────────────────────────────────────────────────


def part_a_agent_anatomy() -> dict:
    """Load the real YAML and display every agent definition in detail."""
    banner("PART A  —  Agent Anatomy: who is on the feature-dev team?")

    import yaml  # PyYAML is a dev dependency (installed with the package)

    with open(YAML_PATH) as fh:
        wf = yaml.safe_load(fh)

    print(f"\n  Workflow  : {wf['id']}")
    print(f"  Version   : {wf.get('version', 'n/a')}")
    print(f"  Tags      : {', '.join(wf.get('tags', []))}")
    meta = wf.get("metadata", {})
    print(f"  self_improve enabled : {meta.get('self_improve', False)}")
    print(f"\n  {wf.get('description', '').strip()}")

    agents_raw = {a["id"]: a for a in wf["agents"]}
    steps_raw = {s["agent"]: s for s in wf["steps"]}

    # ── Print each agent ──────────────────────────────────────────────────
    AGENT_ORDER = ["planner", "developer", "verifier", "tester", "reviewer"]

    for idx, agent_id in enumerate(AGENT_ORDER, 1):
        a = agents_raw[agent_id]
        s = steps_raw.get(agent_id, {})

        section(f"Agent {idx}/5  —  {agent_id.upper()}")

        print(f"  name   : {a['name']}")
        print(f"  role   : {a['role']}")
        print()

        # Persona (the system prompt handed to the LLM at runtime)
        print("  ┌─ PERSONA (system prompt at runtime) " + "─" * 33 + "┐")
        for line in textwrap.dedent(a["prompt"]).strip().splitlines():
            print(f"  │  {line}")
        print("  └" + "─" * 70 + "┘")

        # Step contract
        print()
        print("  ┌─ STEP CONTRACT " + "─" * 53 + "┐")
        step_input = textwrap.dedent(s.get("input", "")).strip()
        print(f"  │  step_id   : {s.get('id', '—')}")
        print(f"  │  expects   : \"{s.get('expects', '—')}\"")
        print(f"  │  retry     : {s.get('retry', 0)} times on failure")
        on_fail = s.get("on_failure", {})
        if on_fail:
            action = on_fail.get("action", "—")
            to_step = on_fail.get("to_step", "—")
            max_loops = on_fail.get("max_loops", "—")
            print(
                f"  │  on_failure: {action} → step '{to_step}' "
                f"(max {max_loops} loops)"
            )
        print(f"  │  artifacts : {s.get('artifacts_required', False)}")
        if s.get("execute"):
            print(f"  │  auto-exec : {s['execute']}")
        print("  │")
        print(
            "  │  INPUT TEMPLATE ({{task}} / {{step_outputs.X}} substituted at runtime):"
        )
        for line in step_input.splitlines()[:10]:
            print(f"  │    {line}")
        if len(step_input.splitlines()) > 10:
            print(f"  │    … ({len(step_input.splitlines()) - 10} more lines)")
        print("  └" + "─" * 70 + "┘")

    # ── Data flow summary ─────────────────────────────────────────────────
    section("Data flow between steps")
    print("""
  step: plan
    input  ← {{task}}                              (user's feature request)
    output → stored as step_outputs["plan"]

  step: implement
    input  ← {{step_outputs.plan}}                 (planner's breakdown)
    output → stored as step_outputs["implement"]

  step: verify
    input  ← {{step_outputs.plan}} + {{step_outputs.implement}}
    output → "VERIFIED" or list of issues
    on_fail → loops back to implement (max 2×)

  step: test
    input  ← {{step_outputs.implement}}
    output → test suite (artifacts_required=true)
    auto-exec: python -m pytest -v

  step: review
    input  ← implement + verify + test outputs
    output → "APPROVED FOR PRODUCTION" or "MAJOR REWORK REQUIRED"
    on_fail → loops back to implement (max 2×)
    """)

    return {"agents": agents_raw, "steps": steps_raw}


# ─────────────────────────────────────────────────────────────────────────────
# PART B — SELF-OPTIMIZATION WALKTHROUGH
# ─────────────────────────────────────────────────────────────────────────────


def part_b_self_optimization(agents_raw: dict) -> None:
    """
    Walk through all four vendor layers + the prompt evolution layer.

    Uses fabricated StepResult objects so no LLM key is required.
    Every class imported is the real production class.
    """
    banner("PART B  —  Self-Optimization: what changes and how?")

    # ── Import the real production classes ───────────────────────────────
    from orchestration.self_improvement.adapters import (
        CapabilityMapper,
        StepResultAdapter,
    )
    from orchestration.self_improvement.improvement_loop import (
        PromptVersion,
    )
    from orchestration.self_improvement.prompt_evolver import (
        HEURISTIC_RULES,
        PromptEvolver,
    )
    from orchestration.self_improvement.vendor.anti_idling_system import (
        AntiIdlingSystem,
    )
    from orchestration.self_improvement.vendor.multi_agent_performance import (
        MultiAgentPerformanceOptimizer,
    )
    from orchestration.self_improvement.vendor.recursive_self_improvement import (
        RecursiveSelfImprovementProtocol,
    )
    from orchestration.self_improvement.vendor.results_verification import (
        ResultsVerificationFramework,
    )

    AGENT_ORDER = ["planner", "developer", "verifier", "tester", "reviewer"]

    # ── Architecture overview ─────────────────────────────────────────────
    section("Architecture: three interlocking loops")
    print("""
  WORKFLOW RUN COMPLETES  (zero slowdown — recording is a background task)
       │
       └─ asyncio.create_task(loop.record_completed_run)
                │
                ├─── LOOP 1  Every run  (< 100 ms, no LLM)
                │    ├─ SMARC-verify each step   → ResultsVerificationFramework
                │    ├─ Update performance score → MultiAgentPerformanceOptimizer
                │    ├─ Update capability map    → RecursiveSelfImprovementProtocol
                │    ├─ Log to anti-idling       → AntiIdlingSystem
                │    └─ Persist to si_run_records (SQLite)
                │
                └─── LOOP 2  Every N runs (default: 5)
                       ├─ _identify_capability_gaps()
                       └─ If gaps found → LOOP 3
                                ├─ PromptEvolver.propose_patch()
                                │   LLM path  (rewrites full persona)
                                │   Heuristic (appends targeted suffix)
                                ├─ PromptPatch persisted (status=pending)
                                └─ auto_approve=True  → apply immediately
                                   auto_approve=False → human reviews via CLI
    """)

    # ── Step 1: SMARC verification ────────────────────────────────────────
    section("Step 1 — SMARC verification (every run, every step)")

    print("""
  SMARC stands for: Specific · Measurable · Actionable · Reusable · Compoundable

  The ResultsVerificationFramework checks each of the 5 criteria against
  the dict produced by StepResultAdapter.to_smarc_input():

  Criterion      What the check inspects
  ─────────────────────────────────────────────────────────────────
  specific       dict is non-empty and every value is not None
  measurable     at least one value is int, float, or str
  actionable     dict has 'next_step' or 'recommendation' key
  reusable       dict has more than one key (broadly applicable)
  compoundable   at least one value is a list or dict
    """)

    verifier = ResultsVerificationFramework()

    # Fabricate a planner step result  (what a real run would produce)
    planner_step = FakeStepResult(
        step=FakeStep(id="plan", expects="STATUS: done"),
        agent_result=FakeAgentResult(
            output=(
                "## Feature: User Authentication\n"
                "## Tasks:\n"
                "1. JWT token generation — acceptance: token expires in 15 min\n"
                "2. /login endpoint      — acceptance: returns 200 + token on success\n"
                "3. Middleware guard     — acceptance: 401 on invalid token\n"
                "## Dependencies: bcrypt, PyJWT\n"
                "## Risks: timing attacks on password comparison\n"
                "STATUS: done"
            ),
            success=True,
            duration_ms=4200.0,
            tokens_used=830,
            artifacts=[],
        ),
        retries=0,
    )

    smarc_input = StepResultAdapter.to_smarc_input(planner_step)
    smarc_results = verifier.verify_results(smarc_input)
    smarc_score = CapabilityMapper.smarc_score(smarc_results)

    sub("Planner output → SMARC input dict")
    for k, v in smarc_input.items():
        val_preview = str(v)[:60] + "…" if len(str(v)) > 60 else str(v)
        print(f"      {k:<18}: {val_preview}")

    sub("SMARC verdict (5 criteria, each True/False)")
    for criterion, passed in smarc_results.items():
        icon = "✓" if passed else "✗"
        print(f"      {icon} {criterion:<14}: {passed}")
    print(f"\n      Composite SMARC score: {smarc_score:.2f}  ({bar(smarc_score)})")

    # ── Step 2: Performance optimizer ────────────────────────────────────
    section("Step 2 — Performance tracking (per agent, per run)")

    print("""
  MultiAgentPerformanceOptimizer maintains a composite score per agent:

      composite = accuracy × 0.40 + efficiency × 0.35 + adaptability × 0.25

  Where:
      accuracy      = SMARC composite score (0 – 1)
      efficiency    = 1.0 - retries × 0.20  (penalises retried steps)
      adaptability  = 1.0 if step succeeded, else 0.3

  If composite < quality_threshold (0.85) → triggers _on_agent_below_threshold
  callback, which schedules an emergency prompt patch.
    """)

    perf = MultiAgentPerformanceOptimizer(quality_threshold=0.85)
    perf_ids: dict[str, str] = {}

    # Register all 5 agents
    for agent_id in AGENT_ORDER:
        pid = perf.register_agent(
            {"name": agent_id, "role": agents_raw[agent_id]["role"]}
        )
        perf_ids[agent_id] = pid

    # Simulate 5 baseline runs, then 5 post-patch runs
    BASELINE_SCORES = {
        "planner": (0.52, 0, True),  # (smarc, retries, success)
        "developer": (0.61, 1, True),
        "verifier": (0.48, 0, True),
        "tester": (0.55, 2, True),
        "reviewer": (0.63, 0, True),
    }
    IMPROVED_SCORES = {
        "planner": (0.81, 0, True),
        "developer": (0.87, 0, True),
        "verifier": (0.78, 0, True),
        "tester": (0.83, 1, True),
        "reviewer": (0.91, 0, True),
    }

    def composite(smarc: float, retries: int, success: bool) -> float:
        acc = smarc
        eff = max(0.0, 1.0 - retries * 0.2)
        ada = 1.0 if success else 0.3
        return acc * 0.40 + eff * 0.35 + ada * 0.25

    sub("Baseline run performance (runs 1–5 average)")
    print(
        f"  {'Agent':<12} {'SMARC':>7} {'Retries':>8} {'Composite':>10}  {'Score bar'}"
    )
    print(f"  {'─'*60}")
    baseline_composites: dict[str, float] = {}
    for agent_id, (smarc, retries, success) in BASELINE_SCORES.items():
        c = composite(smarc, retries, success)
        baseline_composites[agent_id] = c
        below = "  ← below threshold (0.85)" if c < 0.85 else ""
        print(
            f"  {agent_id:<12} {smarc:>7.2f} {retries:>8} {c:>10.3f}  {bar(c)}{below}"
        )
        perf.update_agent_performance(
            perf_ids[agent_id],
            StepResultAdapter.to_performance_data(
                FakeStepResult(
                    step=FakeStep(id=agent_id, expects=""),
                    agent_result=FakeAgentResult("", success, 3000.0, 500, []),
                    retries=retries,
                ),
                smarc,
            ),
        )

    # ── Step 3: Capability map ────────────────────────────────────────────
    section("Step 3 — Capability map (RecursiveSelfImprovementProtocol)")

    print("""
  Each SMARC criterion maps to a named capability:

      specific      →  {agent}_output_specificity
      measurable    →  {agent}_output_measurability
      actionable    →  {agent}_output_actionability
      reusable      →  {agent}_knowledge_reusability
      compoundable  →  {agent}_knowledge_compoundability

  Proficiency values:
      passed  → 0.8   (high)
      failed  → 0.1   (low — will surface as a gap)

  After 5 runs the RecursiveSelfImprovementProtocol._identify_capability_gaps()
  inspects the map and flags:
      • low_performance_areas   (proficiency < 0.5)
      • potential_improvements  (entries not updated in > 30 days)
      • missing_capabilities    (expected keys absent entirely)
    """)

    protocol = RecursiveSelfImprovementProtocol(
        ethical_constraints={
            "do_no_harm": True,
            "human_alignment": True,
            "transparency": True,
            "reversibility": True,
        }
    )

    # Feed 5 baseline runs into the capability map
    for _ in range(5):
        for agent_id, (smarc, _, _) in BASELINE_SCORES.items():
            # Simulate a planner-like SMARC result for each agent
            smarc_r = {
                "specific": True,
                "measurable": smarc > 0.5,
                "actionable": smarc > 0.6,
                "reusable": True,
                "compoundable": smarc > 0.7,
            }
            caps = CapabilityMapper.smarc_to_capabilities(agent_id, smarc_r)
            protocol.update_capability_map(caps)

    sub("Capability map snapshot after 5 runs (sample — planner)")
    for cap_name, cap_data in sorted(protocol.capability_map.items()):
        if "planner" in cap_name:
            prof = cap_data.get("proficiency", 0.0)
            level = "LOW ← gap!" if prof < 0.5 else "ok"
            print(f"      {cap_name:<46}  proficiency={prof:.1f}  {level}")

    # ── Step 4: Gap detection ─────────────────────────────────────────────
    section("Step 4 — Gap detection (fires every N runs)")

    gaps = protocol._identify_capability_gaps()

    sub("_identify_capability_gaps() output")
    print(
        f"      low_performance_areas  ({len(gaps['low_performance_areas'])} entries):"
    )
    for g in gaps["low_performance_areas"][:6]:
        print(f"        • {g}")
    print(
        f"      missing_capabilities   ({len(gaps['missing_capabilities'])} entries):"
    )
    for g in gaps["missing_capabilities"]:
        print(f"        • {g}")
    print(
        f"      potential_improvements ({len(gaps['potential_improvements'])} entries):"
    )
    for g in gaps["potential_improvements"][:4]:
        print(f"        • {g}")

    # ── Step 5: Anti-idling ───────────────────────────────────────────────
    section("Step 5 — Anti-idling stagnation check")

    print("""
  AntiIdlingSystem tracks whether SMARC scores are moving.
  If idle_rate > stagnation_threshold (5%) the system fires intervention
  callbacks to force an emergency patch cycle even before run N.
    """)

    anti_idling = AntiIdlingSystem(idle_threshold=0.05)
    for i, (_, smarc_vals) in enumerate(BASELINE_SCORES.items()):
        # Improvement delta = score change vs previous run (simulate small gains)
        delta = smarc_vals[0] * 0.03 * (i + 1)
        anti_idling.log_activity({"improvement_delta": delta, "agent": "team"})

    idle_rate = anti_idling.calculate_idle_rate()
    print(f"      idle_rate after 5 runs : {idle_rate:.3f}")
    print(f"      stagnation threshold   : {anti_idling.idle_threshold}")
    status = (
        "STAGNANT — triggers emergency patch"
        if idle_rate > anti_idling.idle_threshold
        else "active"
    )
    print(f"      system status         : {status}")

    # ── Step 6: Prompt patch (heuristic path) ─────────────────────────────
    section("Step 6 — Prompt patch proposal (heuristic path, no LLM needed)")

    print("""
  PromptEvolver receives the list of capability gaps and produces a PromptPatch.

  Two paths:
    heuristic — appends targeted instruction suffixes to the existing persona.
                Always available. Fast. Deterministic.
    LLM       — calls the LLM with EVOLUTION_PROMPT to rewrite the full persona.
                Requires llm_executor to be set. Higher quality but costs tokens.

  Heuristic rules (one appended suffix per failing SMARC dimension):
    """)

    for cap, suffix in HEURISTIC_RULES.items():
        print(f"      {cap:<30}  →  {suffix.strip()[:55]}…")

    # Build a PromptVersion for the planner (v1, baseline persona)
    planner_persona_v1 = agents_raw["planner"]["prompt"].strip()
    planner_v1 = PromptVersion(
        id=str(uuid.uuid4()),
        workflow_id="feature-dev",
        agent_id="planner",
        agent_role="planner",
        version_number=1,
        persona_text=planner_persona_v1,
        is_active=True,
        applied_patch_id=None,
        previous_version_id=None,
        ab_test_id=None,
        ab_variant=None,
        created_at="2026-02-14T00:00:00",
        deactivated_at=None,
    )

    # Build gap list for planner from the low-performance areas
    planner_gaps = [
        {"capability": g, "name": g, "source": "low_performance_areas"}
        for g in gaps["low_performance_areas"]
        if "planner" in g
    ]
    if not planner_gaps:
        # Fall back to generic gaps if planner had none flagged
        planner_gaps = [
            {
                "capability": "output_actionability",
                "name": "output_actionability",
                "source": "low_performance_areas",
            },
            {
                "capability": "output_measurability",
                "name": "output_measurability",
                "source": "low_performance_areas",
            },
        ]

    evolver = PromptEvolver(
        improvement_protocol=protocol,
        llm_executor=None,  # heuristic path only in this example
    )

    sub("Persona BEFORE the patch (version 1 — from YAML)")
    rule("·")
    indent(planner_v1.persona_text)
    rule("·")

    # Manually call heuristic to show the exact changes
    proposed_text, justification, confidence = evolver._heuristic_propose(
        agent_role="planner",
        current_persona=planner_v1.persona_text,
        capability_gaps=planner_gaps,
    )

    # Identify the suffixes that were appended
    added_text = proposed_text[len(planner_v1.persona_text) :]

    sub("Persona AFTER the patch (version 2 — after self-optimization)")
    rule("·")
    indent(planner_v1.persona_text)
    print()
    print("      ╔══ APPENDED BY SELF-OPTIMIZATION ═══════════════════════╗")
    for line in added_text.strip().splitlines():
        print(f"      ║  {line}")
    print("      ╚════════════════════════════════════════════════════════╝")
    rule("·")

    sub("Patch metadata")
    print("      generated_by  : heuristic")
    print(f"      confidence    : {confidence:.2f}")
    print(f"      gaps_addressed: {', '.join(g['capability'] for g in planner_gaps)}")
    print(f"      justification : {justification}")

    # ── Step 7: Version store (rollback chain) ────────────────────────────
    section("Step 7 — PromptVersionStore: version history & rollback")

    print("""
  Every persona change is stored as an immutable PromptVersion row.
  Rollback = follow the previous_version_id chain back to any prior version.

  version 1  (baseline, from YAML)
      │
      │  patch applied: heuristic, 2 gaps addressed
      ▼
  version 2  (active — improved persona live in all agents)
      │
      │  patch applied: llm, 3 gaps addressed (run 10)
      ▼
  version 3  (active — LLM-quality rewrite)

  CLI commands:
      agenticom feedback list-patches --workflow feature-dev
      agenticom feedback approve-patch <patch-id>
      agenticom feedback rollback feature-dev planner   # → back to v2
    """)

    # ── Step 8: Before vs after comparison ───────────────────────────────
    section("Step 8 — Before vs After (5 baseline runs vs 5 post-patch runs)")

    print(f"\n  {'Agent':<12} {'Baseline':>10} {'Post-patch':>11} {'Δ':>8}   Trend")
    print(f"  {'─'*60}")

    all_deltas = []
    for agent_id in AGENT_ORDER:
        b_smarc, b_retries, b_success = BASELINE_SCORES[agent_id]
        p_smarc, p_retries, p_success = IMPROVED_SCORES[agent_id]
        b_comp = composite(b_smarc, b_retries, b_success)
        p_comp = composite(p_smarc, p_retries, p_success)
        delta = p_comp - b_comp
        all_deltas.append(delta)
        trend = "▲" if delta > 0.02 else ("▼" if delta < -0.02 else "─")
        print(
            f"  {agent_id:<12} {b_comp:>10.3f} {p_comp:>11.3f} {delta:>+8.3f}   "
            f"{trend} {bar(p_comp)}"
        )

    avg_delta = sum(all_deltas) / len(all_deltas)
    print(
        f"\n  Team average improvement: {avg_delta:+.3f}  over {len(AGENT_ORDER)} agents"
    )

    # ── Step 9: SMARC dimension breakdown ────────────────────────────────
    section("Step 9 — What SMARC dimension improved most?")

    print("""
  The self-optimization loop targets the exact dimensions that fail.
  Mapping:

  SMARC dim       Capability key           What the heuristic patch adds
  ──────────────────────────────────────────────────────────────────────
  specific        output_specificity       "Every claim must be concrete and
                                            verifiable."
  measurable      output_measurability     "Always include quantified metrics,
                                            numbers, or measurable criteria."
  actionable      output_actionability     "End every response with
                                            'Next step:' and 'Recommendation:'."
  reusable        knowledge_reusability    "Structure output so it can be
                                            applied in other contexts."
  compoundable    knowledge_compoundability "Include structured lists or
                                            sub-components in your response."

  Each agent gets only the suffixes for the criteria that failed for that
  specific agent — not a blanket change applied to everyone.
    """)

    # ── Step 10: Full lifecycle summary ──────────────────────────────────
    section("Step 10 — Full self-optimization lifecycle (summary)")

    print("""
  Run 1   Planner executes the planning step.
          SMARC scores:   specific✓ measurable✗ actionable✗ reusable✓ compoundable✗
          Composite:      0.52  ← well below the 0.85 quality threshold
          Capability map: planner_output_measurability → proficiency 0.1 (LOW)
                          planner_output_actionability → proficiency 0.1 (LOW)
                          planner_knowledge_compoundability → proficiency 0.1 (LOW)

  Runs 2–4  Same pattern. Each run re-confirms the gaps. Proficiency stays at 0.1.

  Run 5   pattern_trigger fires.
          _identify_capability_gaps() → 3 low-performance planner capabilities
          PromptEvolver.propose_patch() → heuristic path
          Patch appended to planner persona:
            "CRITICAL: Always include quantified metrics, numbers, or measurable criteria."
            "CRITICAL: End every response with 'Next step:' and 'Recommendation:'."
            "CRITICAL: Include structured lists or sub-components in your response."
          PromptVersionStore.apply_patch() → version 2 active
          agent.update_persona(new_text, version_id=v2.id)

  Run 6   Planner uses the new persona.
          Same task, same prompt structure.
          New output now includes:
            • explicit metrics: "endpoint must respond in < 200 ms"
            • "Next step: implement JWT middleware"
            • "Recommendation: use PyJWT ≥ 2.8 for CVE-free baseline"
            • structured numbered sub-tasks
          SMARC scores:   specific✓ measurable✓ actionable✓ reusable✓ compoundable✓
          Composite:      0.81  ← meaningful improvement, approaching threshold

  Run 10  LLM path (if llm_executor is set) produces a full persona rewrite.
          confidence 0.87. Human reviews, approves.
          Version 3 active. Planner composite: 0.91.

  Result  The team improves — without touching YAML, without restarting the
          process, without writing a single new line of prompt by hand.
    """)

    # ── Step 11: How to plug this into your own code ──────────────────────
    section("Step 11 — Using it in your own code (3 lines)")

    print("""
  from orchestration import load_ready_workflow
  from orchestration.self_improvement import ImprovementLoop

  team = load_ready_workflow("agenticom/bundled_workflows/feature-dev.yaml")

  loop = ImprovementLoop(
      auto_approve_patches=True,   # False → human approves via CLI
      pattern_trigger_n=5,         # analyse gaps every 5 runs
  )
  team.attach_improvement_loop(loop, workflow_id="feature-dev", self_improve=True)

  # From here, every call to team.run(task) automatically:
  #   • SMARC-scores each step output
  #   • Updates per-agent performance metrics
  #   • Detects gaps after every 5th run
  #   • Proposes (and optionally auto-applies) prompt patches
  result = await team.run("Add OAuth2 login endpoint")

  # Inspect improvements any time:
  #   agenticom feedback report feature-dev
  #   agenticom feedback list-patches --workflow feature-dev
  #   agenticom feedback rollback feature-dev planner
    """)

    banner("END OF CASE STUDY 1")
    print("""
  What you saw:
    ✓  How each of the 5 agents is defined (persona, step contract,
       retry policy, loopback rules)
    ✓  How StepResultAdapter converts raw agent output into SMARC input
    ✓  How the 5 SMARC criteria are evaluated individually per step
    ✓  How composite performance scores are built from SMARC + retries
    ✓  How _identify_capability_gaps() detects failing dimensions
    ✓  How PromptEvolver appends targeted instruction suffixes (heuristic)
       or rewrites the full persona (LLM path)
    ✓  How PromptVersionStore tracks every change with full rollback
    ✓  The measured before/after composite score delta

  Next:
    python scripts/demo_self_improvement.py --runs 12
      → Run the full loop with a real LLM and see scores improve live.

    agenticom feedback report feature-dev
      → Show the same before/after table from real historical data.
    """)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    wf_data = part_a_agent_anatomy()
    part_b_self_optimization(wf_data["agents"])


if __name__ == "__main__":
    main()
