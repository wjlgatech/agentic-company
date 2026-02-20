#!/usr/bin/env python3
"""
Case Study 2: feature-dev-with-diagnostics — Agent Anatomy & Self-Optimization
===============================================================================
Workflow:  feature-dev-with-diagnostics
Agents:    criteria_builder → planner → developer → verifier → tester → reviewer

This script answers two questions:

  PART A — "How is each agent defined?"
            Loads the real YAML and unpacks every agent's persona, step input
            template, acceptance criteria, retry policy, and loopback behaviour.
            Also explains the diagnostics_config block and how browser telemetry
            flows between agents.

  PART B — "What exactly does the self-optimization layer change?"
            Shows all four decision layers (SMARC → performance → capability
            gaps → prompt patches) using fabricated run data — no API key
            required.  Focuses on what is DIFFERENT vs case_study_01:

              1. The criteria_builder agent creates compoundable success
                 criteria that compound through ALL five remaining steps.
              2. Browser diagnostics data (diagnostics.success, console_errors,
                 execution_time_ms, iterations_total) feeds directly into the
                 SMARC Measurable dimension.
              3. The developer's 10-retry limit means efficiency scoring is more
                 sensitive: each retry costs 0.20 off the efficiency dimension.
              4. The verifier has live Playwright data, so its SMARC Actionable
                 score reflects whether it pointed at concrete browser failures
                 rather than abstract code observations.
              5. After 3 browser test failures, AI meta-analysis fires and injects
                 a pattern hypothesis into the developer's next-attempt context
                 — this is a separate automatic feedback channel that works in
                 parallel with the improvement-loop prompt patch system.

Run:
    python examples/case_study_02_feature_dev_with_diagnostics.py

No API key needed — all classes used are the real production classes running
in their rule-based / heuristic modes.
"""

from __future__ import annotations

import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# ── Project root on sys.path ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

YAML_PATH = (
    ROOT / "agenticom" / "bundled_workflows" / "feature-dev-with-diagnostics.yaml"
)
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
# Lightweight step-result shim (same as case_study_01)
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
    """Load the real YAML and display every agent definition in full detail."""
    banner("PART A  —  Agent Anatomy: who is on the feature-dev-with-diagnostics team?")

    import yaml

    with open(YAML_PATH) as fh:
        wf = yaml.safe_load(fh)

    print(f"\n  Workflow  : {wf['id']}")
    print(f"  Version   : {wf.get('version', 'n/a')}")
    print(f"  Tags      : {', '.join(wf.get('tags', []))}")
    meta = wf.get("metadata", {})
    print(f"  self_improve enabled : {meta.get('self_improve', False)}")
    print(f"\n  {wf.get('description', '').strip()}")

    # ── Diagnostics configuration ──────────────────────────────────────────
    section("Diagnostics Configuration Block")
    dc = wf.get("diagnostics_config", {})
    print("""
  This block is NEW vs feature-dev. It controls the Playwright browser
  automation layer that runs automatically after each developer attempt.

  Key settings and what they do:
""")
    DIAG_DESCRIPTIONS = {
        "enabled": "Master switch for browser automation",
        "playwright_headless": "true = silent background, false = visible browser (debug)",
        "browser_type": "chromium | firefox | webkit — which engine to test with",
        "timeout_ms": "Max time for the entire browser test sequence per attempt",
        "capture_screenshots": "Screenshot after every action → stored in outputs/diagnostics/",
        "capture_console": "Capture console.log/error/warn → injected into verifier's context",
        "capture_network": "Track XHR/fetch requests → reveals missing API calls or 4xx errors",
        "screenshot_on_error": "Auto-screenshot the page state at the moment of failure",
        "max_iterations": "Developer retry ceiling — up to 10 implementation attempts",
        "iteration_threshold": "Trigger AI meta-analysis after this many consecutive failures",
        "output_dir": "Where screenshots and logs are written (gitignored)",
    }
    for key, description in DIAG_DESCRIPTIONS.items():
        val = dc.get(key, "—")
        print(f"  {key:<26}  {val!s:<10}  {description}")

    print("""
  What the meta-analysis does after iteration_threshold failures:
    • LLM-based MetaAnalyzer inspects all failure screenshots + console logs
    • Detects recurring patterns: "CSS selector missing", "CORS error on /api/login"
    • Injects a hypothesis into the next developer attempt:
        META-ANALYSIS: Pattern detected — "element not found" recurring on
        selector '#login-btn'. Root cause: React app not yet mounted.
        Suggested approach: wait_for_selector on app root before any click.
    • This is SEPARATE from the self-optimization patch system.
      Meta-analysis is per-run feedback; the improvement loop is cross-run learning.
""")

    agents_raw = {a["id"]: a for a in wf["agents"]}
    # Build step map indexed by agent id
    steps_raw = {}
    for s in wf["steps"]:
        steps_raw[s["agent"]] = s

    # ── Agent order matches the pipeline ──────────────────────────────────
    AGENT_ORDER = [
        "criteria_builder",
        "planner",
        "developer",
        "verifier",
        "tester",
        "reviewer",
    ]

    for idx, agent_id in enumerate(AGENT_ORDER, 1):
        a = agents_raw[agent_id]
        s = steps_raw.get(agent_id, {})

        section(f"Agent {idx}/6  —  {agent_id.upper()}")

        print(f"  name   : {a['name']}")
        print(f"  role   : {a['role']}")
        print()

        # Persona
        print("  ┌─ PERSONA (system prompt at runtime) " + "─" * 33 + "┐")
        for line in textwrap.dedent(a["prompt"]).strip().splitlines():
            print(f"  │  {line}")
        print("  └" + "─" * 70 + "┘")

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

        # Diagnostics metadata (only developer step has it)
        step_meta = s.get("metadata", {})
        if step_meta.get("diagnostics_enabled"):
            print("  │  diagnostics_enabled : True")
            test_url = step_meta.get("test_url", "—")
            print(f"  │  test_url            : {test_url}")
            actions = step_meta.get("test_actions", [])
            print(
                f"  │  test_actions        : {len(actions)} browser actions configured"
            )
            for act in actions:
                act_type = act.get("type", "?")
                act_val = act.get("selector") or act.get("value") or ""
                act_timeout = act.get("timeout", "")
                timeout_str = f" (timeout={act_timeout}ms)" if act_timeout else ""
                print(f"  │    → {act_type:<20} {act_val}{timeout_str}")

        print("  │")
        print(
            "  │  INPUT TEMPLATE ({{task}} / {{step_outputs.X}} / {{diagnostics.X}} substituted):"
        )
        lines = step_input.splitlines()
        for line in lines[:12]:
            print(f"  │    {line}")
        if len(lines) > 12:
            print(f"  │    … ({len(lines) - 12} more lines)")
        print("  └" + "─" * 70 + "┘")

        # Agent-specific callouts
        if agent_id == "criteria_builder":
            print("""
  ★  NEW vs feature-dev: This agent runs BEFORE the planner.
     It defines 3–5 measurable success criteria that flow forward into every
     subsequent step (SUCCESS CRITERIA: {{step_outputs.build_criteria}}).
     This is the seed of the compoundable flywheel — one tight criteria
     definition makes all five downstream agents measurably more precise.
""")
        elif agent_id == "developer":
            print("""
  ★  ENHANCED vs feature-dev: retry raised from 3 → 10.
     The extra retries exist because browser automation gives concrete failure
     signals (console errors, screenshots) rather than just "tests didn't pass".
     Each retry consumes efficiency score: composite -= 0.20 per retry.
     With 10 retries, a developer that takes 5 attempts scores:
       efficiency = 1.0 - 5×0.20 = 0.0  ← immediate emergency patch trigger
""")
        elif agent_id == "verifier":
            print("""
  ★  ENHANCED vs feature-dev: verifier receives {{diagnostics.*}} variables:
       diagnostics.success         — did the Playwright test sequence pass?
       diagnostics.final_url       — what URL was the browser on when done?
       diagnostics.console_errors  — list of JS console errors captured
       diagnostics.screenshots     — paths to screenshots taken
       diagnostics.network_requests — HTTP requests made during the test
     This means SMARC Measurable and Actionable scores for the verifier are
     anchored to real browser evidence, not just code analysis.
""")
        elif agent_id == "reviewer":
            print("""
  ★  ENHANCED vs feature-dev: reviewer sees {{diagnostics.success}},
     {{diagnostics.console_errors}}, {{diagnostics.execution_time_ms}}, and
     {{iterations_total}}.  A reviewer that approves code which required 8
     browser iterations will produce a lower SMARC Compoundable score than
     one that approves code that passed on iteration 1 — because code that
     required many iterations is less likely to be reusable across future runs.
""")

    # ── Full data flow diagram ─────────────────────────────────────────────
    section("Data Flow: all 6 agents + diagnostics variables")
    print("""
  step: build_criteria
    input  ← {{task}}
    output → stored as step_outputs["build_criteria"]
    purpose: create measurable criteria that compound through ALL later steps

  step: plan
    input  ← {{task}}  +  {{step_outputs.build_criteria}}
    output → stored as step_outputs["plan"]
    note:    planner knows the criteria from step 0 — plan addresses them explicitly

  step: implement          ← THE BROWSER AUTOMATION LOOP
    input  ← {{step_outputs.plan}}  +  {{step_outputs.build_criteria}}
    output → stored as step_outputs["implement"]
    retry: 10  (browser test runs after EACH attempt)
    after attempt 1:
      Playwright launches → navigates → actions → screenshot
      If FAIL:  console_errors + screenshot injected into next attempt context
    after attempt 3+ failures:
      MetaAnalyzer fires:  pattern_detected, root_cause_hypothesis,
      suggested_approaches → all injected into attempt 4's developer context

  step: verify
    input  ← {{step_outputs.plan}}
            + {{step_outputs.build_criteria}}
            + {{step_outputs.implement}}
            + {{diagnostics.success}}          ← live browser test result
            + {{diagnostics.final_url}}
            + {{diagnostics.console_errors}}   ← specific JS error list
            + {{diagnostics.screenshots}}
            + {{diagnostics.network_requests}}
            + {{meta_analysis.*}}              ← LLM root-cause hypothesis
    expects: "VERIFIED"
    on_fail → loops back to implement (max 2×), with diagnostics in feedback

  step: test
    input  ← {{step_outputs.implement}}  +  {{diagnostics}} (full blob)
    purpose: write unit/integration tests given the browser results already ran
    auto-exec: python -m pytest -v

  step: review
    input  ← implement + verify + test outputs
            + {{diagnostics.success}}
            + {{diagnostics.console_errors}}
            + {{diagnostics.execution_time_ms}}
            + {{iterations_total}}
    expects: "APPROVED"
    on_fail → loops back to implement (max 2×)
""")

    return {"agents": agents_raw, "steps": steps_raw, "workflow": wf}


# ─────────────────────────────────────────────────────────────────────────────
# PART B — SELF-OPTIMIZATION WALKTHROUGH
# ─────────────────────────────────────────────────────────────────────────────


def part_b_self_optimization(agents_raw: dict, wf: dict) -> None:
    """
    Walk through all four vendor layers and the prompt evolution layer.

    Highlights what is DIFFERENT vs case_study_01 (feature-dev).
    Uses fabricated StepResult objects — no LLM key required.
    """
    banner(
        "PART B  —  Self-Optimization: what the loop changes and why it is different"
    )

    # ── Import production classes ─────────────────────────────────────────
    from orchestration.self_improvement.adapters import (
        CapabilityMapper,
        StepResultAdapter,
    )
    from orchestration.self_improvement.prompt_evolver import (
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

    AGENT_ORDER = [
        "criteria_builder",
        "planner",
        "developer",
        "verifier",
        "tester",
        "reviewer",
    ]

    # ── Architecture overview ─────────────────────────────────────────────
    section("Architecture: how diagnostics feeds the self-optimization loop")
    print("""
  feature-dev-with-diagnostics adds a BROWSER TELEMETRY CHANNEL on top of
  the standard self-optimization pipeline.  Two separate feedback systems
  run in parallel:

  ┌──────────────────────────────────────────────────────────────────┐
  │  BROWSER TELEMETRY (per-run, per-attempt, built into Playwright) │
  │                                                                  │
  │  After each developer attempt:                                   │
  │    Playwright → screenshots + console_errors + network           │
  │    → injected into NEXT attempt's developer input                │
  │                                                                  │
  │  After 3 failures:                                               │
  │    MetaAnalyzer(LLM) → pattern + root_cause + suggestions       │
  │    → injected into verifier AND developer contexts               │
  │                                                                  │
  │  This is instant within-run feedback.  It does NOT touch         │
  │  the self-improvement SQLite DB or prompt versions.              │
  └──────────────────────────────────────────────────────────────────┘
                         ↕  results feed into ↕
  ┌──────────────────────────────────────────────────────────────────┐
  │  SELF-IMPROVEMENT LOOP (cross-run, SMARC → patches → versions)  │
  │                                                                  │
  │  After run completes (background, zero slowdown):               │
  │    SMARC-score each step output (diagnostics data is part of    │
  │    the "output" text the verifier and reviewer produce)          │
  │    → MultiAgentPerformanceOptimizer composite                    │
  │    → RecursiveSelfImprovementProtocol capability map             │
  │    → AntiIdlingSystem stagnation check                           │
  │    → PromptVersionStore + PromptEvolver (every N runs)           │
  │                                                                  │
  │  This is deferred cross-run learning.  It DOES modify prompts.  │
  └──────────────────────────────────────────────────────────────────┘
""")

    # ── Step 1: SMARC for the criteria_builder ────────────────────────────
    section("Step 1 — SMARC and the criteria_builder (the flywheel seed)")

    print("""
  The criteria_builder is the ONLY agent that has no equivalent in feature-dev.
  Its job is to produce 3–5 success criteria that every downstream step can
  reference.  This makes it the primary source of Compoundable value.

  SMARC scoring for criteria_builder:

  Criterion      What a HIGH score looks like
  ──────────────────────────────────────────────────────────────────────
  specific       Each criterion is unambiguous: "Login page renders within 2s"
  measurable     Each criterion has a numeric threshold or pass/fail test
  actionable     The developer knows exactly what to build; no interpretation
  reusable       Criteria are generic enough for other auth-like features
  compoundable   ★ THE KEY ONE — criteria flow into plan, implement, verify,
                   test, AND reviewer without restatement:
                   • planner uses them to scope tasks
                   • developer receives them as acceptance targets
                   • verifier auto-checks each criterion number-by-number
                   • tester derives test cases directly from them
                   • reviewer gates approval against them
                   • improvement loop uses failed criteria to target patches
                   = genuine flywheel, 1.0 compoundable score
""")

    verifier_rule = ResultsVerificationFramework()

    # A good criteria_builder output
    good_criteria_output = (
        "## Success Criteria:\n"
        "1. Login form renders at /login within 2 seconds on a cold start.\n"
        "2. Valid email + password returns HTTP 200 with a JWT in the body.\n"
        "3. Invalid credentials return HTTP 401 with message 'Invalid credentials'.\n"
        "4. JWT expires after exactly 15 minutes (exp claim = issued_at + 900s).\n"
        "5. Consecutive 5 failed logins within 60 s trigger a 429 with Retry-After.\n"
        "\n"
        "## Test Actions Required:\n"
        "- Navigate to /login, assert form renders < 2s (Playwright: performance.now)\n"
        "- POST /auth/token with test user, assert 200 + {token: <jwt>}\n"
        "- POST /auth/token bad password, assert 401 + {error: 'Invalid credentials'}\n"
        "- Decode token.exp, assert exp - iat == 900\n"
        "- Loop 5 bad logins, assert 6th returns 429\n"
        "STATUS: done"
    )

    good_step = FakeStepResult(
        step=FakeStep(id="build_criteria", expects="STATUS: done"),
        agent_result=FakeAgentResult(
            output=good_criteria_output,
            success=True,
            duration_ms=3100.0,
            tokens_used=620,
            artifacts=[],
        ),
        retries=0,
    )

    smarc_input_good = StepResultAdapter.to_smarc_input(good_step)
    smarc_results_good = verifier_rule.verify_results(smarc_input_good)
    score_good = CapabilityMapper.smarc_score(smarc_results_good)

    # A poor criteria_builder output
    poor_criteria_output = (
        "The login should work well and be secure. "
        "Users should be able to log in easily. "
        "STATUS: done"
    )
    poor_step = FakeStepResult(
        step=FakeStep(id="build_criteria", expects="STATUS: done"),
        agent_result=FakeAgentResult(
            output=poor_criteria_output,
            success=True,
            duration_ms=800.0,
            tokens_used=120,
            artifacts=[],
        ),
        retries=0,
    )
    smarc_input_poor = StepResultAdapter.to_smarc_input(poor_step)
    smarc_results_poor = verifier_rule.verify_results(smarc_input_poor)
    score_poor = CapabilityMapper.smarc_score(smarc_results_poor)

    sub("Comparing good vs poor criteria_builder output (rule-based SMARC)")
    print(f"  {'Criterion':<15} {'Good output':>14} {'Poor output':>12}")
    print(f"  {'─' * 45}")
    for criterion in (
        "specific",
        "measurable",
        "actionable",
        "reusable",
        "compoundable",
    ):
        g = "✓" if smarc_results_good[criterion] else "✗"
        p = "✓" if smarc_results_poor[criterion] else "✗"
        print(f"  {criterion:<15} {g:>14} {p:>12}")
    print()
    print(f"  Composite (good)  : {score_good:.2f}  {bar(score_good)}")
    print(f"  Composite (poor)  : {score_poor:.2f}  {bar(score_poor)}")
    print()
    print("  Rule-based detects the structural gap.")
    print("  SemanticSMARCVerifier (with LLM) would give a much more granular")
    print("  score: good ≈ 0.92, poor ≈ 0.08, flagging exactly which criteria are")
    print("  vague ('secure', 'easily') vs concrete (HTTP 200, 900s, 429).")

    # ── Step 2: How diagnostics.success feeds SMARC Measurable ───────────
    section("Step 2 — How browser diagnostics feed the verifier's SMARC score")

    print("""
  The verifier step is unique: its input template contains real Playwright data:

    AUTOMATED TEST RESULTS:
    - Test Success: {{diagnostics.success}}          ← bool: True or False
    - Final URL: {{diagnostics.final_url}}           ← e.g. http://localhost:3000/dashboard
    - Console Errors: {{diagnostics.console_errors}} ← e.g. ["TypeError: Cannot read..."]
    - Screenshots: {{diagnostics.screenshots}}       ← ["implementation_loaded.png"]
    - Network Requests: {{diagnostics.network_requests}}
    - Execution Time: {{diagnostics.execution_time_ms}}ms

  This data is IN the verifier's output text (the LLM references it in its
  VERIFIED / issues list).  That means:

  SMARC Measurable dimension for the verifier:
    High score (0.85+): verifier mentions "Test Success: True", "200ms",
                        "0 console errors" — concrete, numeric, verifiable
    Low score  (0.20 ): verifier says "code looks good" without citing
                        the browser test results — not measurable

  SMARC Actionable dimension for the verifier:
    High score (0.85+): "Fix selector '#submit-btn' — Playwright could not
                        find it (screenshot: login_error.png). Add id='submit-btn'
                        to the form submit element in auth_form.jsx line 42."
    Low score  (0.20 ): "The button might not be rendering correctly."

  When diagnostics.success is True, the verifier typically outputs VERIFIED
  with concrete evidence → high SMARC composite for verifier.

  When diagnostics.success is False, a good verifier cites the exact errors
  from console_errors → still high SMARC (Actionable, Measurable) because it
  gives the developer precise instructions based on real data.
  A bad verifier ignores the diagnostics → low SMARC → gap detected →
  patch appended: "CRITICAL: Always cite {{diagnostics.console_errors}} and
  {{diagnostics.screenshots}} in your verification report."
""")

    # ── Step 3: Developer efficiency scoring with 10 retries ──────────────
    section("Step 3 — Developer efficiency scoring with up to 10 retries")

    print("""
  composite = accuracy × 0.40 + efficiency × 0.35 + adaptability × 0.25
  efficiency = max(0.0, 1.0 - retries × 0.20)

  Developer retry scenarios:
""")
    RETRY_SCENARIOS = [
        (0, "Passed on first browser test attempt"),
        (1, "Failed once — minor selector fix"),
        (2, "Failed twice — CORS + missing endpoint"),
        (3, "Failed three times — meta-analysis fires"),
        (5, "Failed 5x — emergency patch trigger likely"),
        (9, "Failed 9x — worst case before final attempt"),
    ]
    print(f"  {'Retries':>8}  {'Efficiency':>11}  {'Composite(smarc=0.75)':>22}  Notes")
    print(f"  {'─' * 72}")
    for retries, note in RETRY_SCENARIOS:
        eff = max(0.0, 1.0 - retries * 0.20)
        comp = 0.75 * 0.40 + eff * 0.35 + 1.0 * 0.25
        threshold_flag = "  ← BELOW 0.85 → emergency patch" if comp < 0.85 else ""
        print(f"  {retries:>8}  {eff:>11.2f}  {comp:>22.3f}  {note}{threshold_flag}")

    print("""
  Key point: even with a perfect SMARC score (1.0), a developer that uses
  2+ retries drops below the 0.85 quality threshold:
    2 retries → composite = 1.0×0.40 + 0.60×0.35 + 1.0×0.25 = 0.86  (just above)
    3 retries → composite = 1.0×0.40 + 0.40×0.35 + 1.0×0.25 = 0.79  (below)
  → Emergency patch fires immediately after that run.
""")

    # ── Step 4: Performance optimizer with 6 agents ───────────────────────
    section("Step 4 — Performance tracking across all 6 agents")

    print("""
  MultiAgentPerformanceOptimizer maintains a composite score per agent.
  quality_threshold = 0.85.  Below it → _on_agent_below_threshold() fires.

  Baseline simulation: 5 runs, browser tests often failing 2–3 times.
""")

    perf = MultiAgentPerformanceOptimizer(quality_threshold=0.85)
    perf_ids: dict[str, str] = {}

    for agent_id in AGENT_ORDER:
        pid = perf.register_agent(
            {"name": agent_id, "role": agents_raw[agent_id]["role"]}
        )
        perf_ids[agent_id] = pid

    # Simulated baseline (smarc, retries, success)
    # Developer suffers most from retries in the browser loop
    BASELINE = {
        "criteria_builder": (0.58, 0, True),
        "planner": (0.52, 0, True),
        "developer": (0.65, 3, True),  # 3 browser retries
        "verifier": (0.61, 0, True),  # low: ignoring diagnostics data
        "tester": (0.55, 1, True),
        "reviewer": (0.60, 0, True),
    }
    IMPROVED = {
        "criteria_builder": (0.85, 0, True),  # patch: add measurable criteria template
        "planner": (0.80, 0, True),  # patch: address build_criteria explicitly
        "developer": (0.82, 1, True),  # patch: cite browser errors in response
        "verifier": (0.87, 0, True),  # patch: always cite diagnostics.* fields
        "tester": (0.83, 0, True),  # patch: derive tests from success criteria
        "reviewer": (0.88, 0, True),  # patch: cite iterations_total in review
    }

    def composite(smarc: float, retries: int, success: bool) -> float:
        acc = smarc
        eff = max(0.0, 1.0 - retries * 0.2)
        ada = 1.0 if success else 0.3
        return acc * 0.40 + eff * 0.35 + ada * 0.25

    sub("Baseline run performance (runs 1–5 average, browser retries included)")
    print(f"  {'Agent':<20} {'SMARC':>7} {'Retries':>8} {'Composite':>10}  Score bar")
    print(f"  {'─' * 68}")

    baseline_composites: dict[str, float] = {}
    for agent_id, (smarc, retries, success) in BASELINE.items():
        c = composite(smarc, retries, success)
        baseline_composites[agent_id] = c
        below = "  ← below 0.85" if c < 0.85 else ""
        print(
            f"  {agent_id:<20} {smarc:>7.2f} {retries:>8} {c:>10.3f}  {bar(c)}{below}"
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

    # ── Step 5: Capability map ────────────────────────────────────────────
    section("Step 5 — Capability map: what gaps look like with diagnostics data")

    print("""
  The same SMARC→capability mapping applies (criterion → named capability),
  but with 6 agents instead of 5, the gap table is richer.

  Gap signals unique to this workflow:

  Agent              Failing dimension   Root cause
  ─────────────────────────────────────────────────────────────────────
  criteria_builder   measurable          Criteria lack numeric thresholds
  developer          efficiency          3+ browser retries per run average
  verifier           actionable          Does not cite console_errors or screenshots
  reviewer           compoundable        Approval ignores iterations_total signal
""")

    protocol = RecursiveSelfImprovementProtocol(
        ethical_constraints={
            "do_no_harm": True,
            "human_alignment": True,
            "transparency": True,
            "reversibility": True,
        }
    )

    # Feed 5 baseline runs
    for _ in range(5):
        for agent_id, (smarc, _, _) in BASELINE.items():
            smarc_r = {
                "specific": True,
                "measurable": smarc > 0.6,
                "actionable": smarc > 0.65,
                "reusable": True,
                "compoundable": smarc > 0.75,
            }
            caps = CapabilityMapper.smarc_to_capabilities(agent_id, smarc_r)
            protocol.update_capability_map(caps)

    sub("Capability map snapshot after 5 runs (sample — criteria_builder + verifier)")
    for cap_name, cap_data in sorted(protocol.capability_map.items()):
        if "criteria_builder" in cap_name or "verifier" in cap_name:
            prof = cap_data.get("proficiency", 0.0)
            level = "LOW ← gap!" if prof < 0.5 else "ok "
            print(f"      {cap_name:<52}  proficiency={prof:.1f}  {level}")

    # ── Step 6: Gap detection ─────────────────────────────────────────────
    section("Step 6 — Gap detection output (every N runs)")

    gaps = protocol._identify_capability_gaps()

    sub("_identify_capability_gaps() output")
    print(
        f"      low_performance_areas  ({len(gaps['low_performance_areas'])} entries):"
    )
    for g in gaps["low_performance_areas"][:8]:
        print(f"        • {g}")
    if len(gaps["low_performance_areas"]) > 8:
        print(f"        … ({len(gaps['low_performance_areas']) - 8} more)")

    # ── Step 7: Anti-idling ───────────────────────────────────────────────
    section("Step 7 — Anti-idling: stagnation with a noisy browser signal")

    print("""
  AntiIdlingSystem tracks whether the improvement_delta is moving.
  In feature-dev-with-diagnostics, improvement_delta can be NOISY:
    Run 1: browser fails 3 times → low delta
    Run 2: same code, browser passes 1st try  → high delta
    Run 3: new feature breaks earlier test → low delta again

  This oscillation means the raw idle_rate might look "active" even when
  the underlying SMARC content quality is stagnant.

  The improvement loop handles this by using the 5-run rolling average
  SMARC composite (from MultiAgentPerformanceOptimizer) as the primary
  stagnation signal, not just the single-run improvement_delta.
""")

    anti_idling = AntiIdlingSystem(idle_threshold=0.05)
    # Simulate noisy deltas from browser tests
    noisy_deltas = [0.02, 0.08, 0.01, 0.07, 0.02]  # oscillating
    for delta in noisy_deltas:
        anti_idling.log_activity({"improvement_delta": delta, "agent": "team"})

    idle_rate = anti_idling.calculate_idle_rate()
    print(f"      noisy deltas (5 runs): {noisy_deltas}")
    print(f"      idle_rate            : {idle_rate:.3f}")
    print(f"      stagnation threshold : {anti_idling.idle_threshold}")
    status = (
        "STAGNANT — triggers emergency patch"
        if idle_rate > anti_idling.idle_threshold
        else "active — oscillation is OK, content SMARC is primary signal"
    )
    print(f"      system status        : {status}")

    # ── Step 8: Patch proposals ───────────────────────────────────────────
    section("Step 8 — Prompt patch proposals for each agent")

    print("""
  PromptEvolver proposes ONE patch per agent per gap-analysis cycle.
  Here are the patches generated for this workflow at run 5.

  Note how each patch is specific to the diagnostics context:
""")

    PATCHES = [
        (
            "criteria_builder",
            "output_measurability",
            "CRITICAL: Always include quantified metrics, numbers, or measurable "
            "criteria.\n\nCRITICAL: Each success criterion MUST include either:\n"
            "  (a) A numeric threshold (e.g. '< 200ms', 'HTTP 200', '15 minutes'), OR\n"
            "  (b) A concrete boolean test (e.g. 'JWT contains exp claim', "
            "'element #login-btn visible').",
        ),
        (
            "developer",
            "output_actionability",
            "CRITICAL: End every response with 'Next step:' and 'Recommendation:'.\n\n"
            "CRITICAL: When the automated browser test fails, explicitly state:\n"
            "  • Which selector or URL caused the failure\n"
            "  • What change you made to fix it in this attempt\n"
            "  • What the Playwright test should find different now",
        ),
        (
            "verifier",
            "output_actionability",
            "CRITICAL: End every response with 'Next step:' and 'Recommendation:'.\n\n"
            "CRITICAL: You MUST cite the automated test results in your verification:\n"
            "  • State 'Test Success: True/False' explicitly\n"
            "  • If console errors exist, quote them verbatim\n"
            "  • Reference the screenshot filename for any visual issue\n"
            "  • Do NOT mark VERIFIED unless diagnostics.success == True",
        ),
        (
            "reviewer",
            "knowledge_compoundability",
            "CRITICAL: Include structured lists or sub-components in your response.\n\n"
            "CRITICAL: Your review MUST reference:\n"
            "  • Total browser test iterations ({{iterations_total}}) and explain\n"
            "    whether that number is acceptable for production code\n"
            "  • Any console_errors from the diagnostics data\n"
            "  • Whether the implementation will remain stable across future runs",
        ),
    ]

    evolver = PromptEvolver(improvement_protocol=protocol, llm_executor=None)

    for agent_id, gap_cap, _expected_suffix in PATCHES:
        persona = agents_raw[agent_id]["prompt"].strip()
        gap_dicts = [
            {
                "capability": f"{agent_id}_{gap_cap}",
                "source": "low_performance_areas",
            }
        ]
        proposed, justification, confidence = evolver._heuristic_propose(
            agent_role=agent_id,
            current_persona=persona,
            capability_gaps=gap_dicts,
        )
        added = proposed[len(persona) :]

        print(f"  ┌─ {agent_id.upper()} patch {'─' * (WIDTH - len(agent_id) - 9)}┐")
        print(f"  │  Gap addressed : {gap_cap}")
        print(f"  │  Confidence    : {confidence:.2f}")
        print("  │  Generated by  : heuristic")
        print("  │")
        print("  │  Suffix appended to existing persona:")
        for line in added.strip().splitlines():
            print(f"  │    {line}")
        print("  └" + "─" * 70 + "┘")
        print()

    # ── Step 9: Meta-analysis vs improvement loop — the two channels ──────
    section("Step 9 — Two feedback channels: meta-analysis vs improvement loop")

    print("""
  This workflow has TWO separate improvement mechanisms.  They operate at
  different time scales and do not interfere with each other.

  ┌───────────────────┬──────────────────────┬────────────────────────────┐
  │                   │  Browser             │  Self-Improvement          │
  │                   │  Meta-Analysis       │  Loop (SMARC patches)      │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ When it fires     │ After 3 consecutive  │ Every N runs (default: 5)  │
  │                   │ browser failures     │ + immediately if composite │
  │                   │ IN THE SAME RUN      │ drops below 0.85           │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ What it analyzes  │ Screenshots, console │ SMARC dimension scores     │
  │                   │ logs, network traces │ across the last N runs     │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ Output            │ Natural-language     │ PromptPatch: new persona   │
  │                   │ hypothesis injected  │ text (persisted to SQLite) │
  │                   │ into next attempt    │ that persists to all runs  │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ Scope             │ Current run only.    │ All future runs of the     │
  │                   │ Ephemeral.           │ workflow. Permanent.       │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ Requires LLM?     │ Yes (MetaAnalyzer)   │ No (heuristic) / Yes (LLM) │
  ├───────────────────┼──────────────────────┼────────────────────────────┤
  │ Human approval?   │ Never (auto-inject)  │ Optional (auto_approve or  │
  │                   │                      │ human via CLI)             │
  └───────────────────┴──────────────────────┴────────────────────────────┘

  Example — developer fails browser test 3 times:

  Attempt 1-3:  Browser returns "TypeError: Cannot read properties of null"
                screenshot: login_form_blank.png
                console_error: "App component not mounted"

  Meta-analysis fires → injects into attempt 4:
    META-ANALYSIS PATTERN: React app takes ~800ms to mount.
    Root cause: Playwright clicks #submit before React finishes mounting.
    Suggested approach: Add await page.waitForSelector('#app-root', {state:'visible'})
    before any interaction. Increase timeout from 5000ms to 8000ms.

  Attempt 4 uses this hint → passes browser test.

  Run record shows: developer retries=3, SMARC efficiency=0.40 → below 0.85
  → improvement loop proposes PATCH after this run:
    "CRITICAL: When browser automation reports 'element not mounted', always
    add an explicit wait_for_selector on the root container before any interaction."
  → Developer persona version 2 active for all future runs.
  → Run 6 onward: developer naturally adds wait logic upfront → 0 retries.
""")

    # ── Step 10: Before vs after comparison ──────────────────────────────
    section("Step 10 — Before vs After (5 baseline runs vs 5 post-patch runs)")

    print(f"\n  {'Agent':<20} {'Baseline':>10} {'Post-patch':>11} {'Δ':>8}   Trend")
    print(f"  {'─' * 68}")

    all_deltas = []
    for agent_id in AGENT_ORDER:
        b_smarc, b_retries, b_success = BASELINE[agent_id]
        p_smarc, p_retries, p_success = IMPROVED[agent_id]
        b_comp = composite(b_smarc, b_retries, b_success)
        p_comp = composite(p_smarc, p_retries, p_success)
        delta = p_comp - b_comp
        all_deltas.append(delta)
        trend = "▲" if delta > 0.02 else ("▼" if delta < -0.02 else "─")
        print(
            f"  {agent_id:<20} {b_comp:>10.3f} {p_comp:>11.3f} {delta:>+8.3f}   "
            f"{trend} {bar(p_comp)}"
        )

    avg_delta = sum(all_deltas) / len(all_deltas)
    print(
        f"\n  Team average improvement: {avg_delta:+.3f}  over {len(AGENT_ORDER)} agents"
    )
    print("""
  The improvements are NOT uniform:
    criteria_builder and verifier gain the most because their patches are
    most specific — the criteria_builder now writes numeric thresholds,
    and the verifier now cites concrete diagnostics data.

    developer gains from reduced retries (patch teaches it to add React
    mount waits upfront) — efficiency goes from 0.40 → 0.80.

    planner gains indirectly — the improved criteria_builder gives it
    richer context, so its plan is more specific and measurable.
""")

    # ── Step 11: Version chain ────────────────────────────────────────────
    section("Step 11 — PromptVersionStore: version history across 6 agents")

    print("""
  Each agent maintains an independent version chain.
  After 15 runs with auto_approve_patches=True, a typical history:

  criteria_builder
    v1  (from YAML) — baseline, vague criteria
    v2  (heuristic) — added: "Each criterion MUST include numeric threshold"
    v3  (llm)       — full rewrite: includes template per criterion type

  planner
    v1  (from YAML) — baseline
    v2  (heuristic) — added actionability suffix (Next step / Recommendation)

  developer
    v1  (from YAML) — baseline
    v2  (heuristic) — added: "When browser test fails, state which selector..."
    v3  (llm)       — added: browser-specific debugging pattern from approved lessons

  verifier
    v1  (from YAML) — baseline
    v2  (heuristic) — added: "MUST cite diagnostics.success, console_errors, screenshots"
    v3  (llm)       — rewrite: structured verification report template with browser section

  tester
    v1  (from YAML) — baseline
    v2  (heuristic) — added: "Derive test cases directly from success_criteria"

  reviewer
    v1  (from YAML) — baseline
    v2  (heuristic) — added: "Reference iterations_total in final review"

  CLI commands:
    agenticom feedback list-patches --workflow feature-dev-with-diagnostics
    agenticom feedback approve-patch <patch-id>
    agenticom feedback rollback feature-dev-with-diagnostics verifier  # → back to v2
    agenticom feedback report feature-dev-with-diagnostics
""")

    # ── Step 12: Putting it all together ──────────────────────────────────
    section("Step 12 — Full lifecycle: one improved run vs one baseline run")

    print("""
  BASELINE RUN (no patches, run 1):

    build_criteria  "Login should work securely"
                    SMARC: specific✓ measurable✗ actionable✓ reusable✓ compoundable✗
                    → criteria_builder composite: 0.56

    plan            Uses vague criteria → plan lacks measurable acceptance targets
                    SMARC composite: 0.52

    implement       Browser fails 3 times (React mount timing issue)
                    efficiency = 0.40  → composite: 0.66  ← below 0.85
                    Emergency patch queued

    verify          Outputs "code looks correct based on review"
                    (ignores console_errors and screenshots)
                    SMARC actionable✗: verifier is not helpful to developer
                    composite: 0.57

    test            Derives test cases from vague intuition
                    SMARC compoundable✗: tests won't catch criterion violations
                    composite: 0.60

    reviewer        Approves code that required 3 browser retries without noting it
                    SMARC compoundable✗: review does not signal future risk
                    composite: 0.60

  ─────────────────────────────────────────────────────────────────────

  POST-PATCH RUN (after run 5 patches + 5 more runs, run 10):

    build_criteria  "1. Login at /login renders < 2s. 2. POST /auth/token 200 + JWT.
                    3. Invalid creds → 401. 4. exp = iat+900. 5. 5 fails → 429"
                    SMARC: all 5 criteria pass
                    → criteria_builder composite: 0.88

    plan            References each success criterion by number
                    "Task 1 addresses criterion 1 (< 2s render)..."
                    SMARC composite: 0.83

    implement       Browser passes on attempt 1 (wait_for_selector added upfront)
                    retries=0  efficiency=1.0  composite: 0.88

    verify          "Test Success: True. 0 console errors. Criteria 1-5 all met.
                    Screenshot: login_loaded.png shows form in 1.8s (< 2s ✓)"
                    SMARC composite: 0.91

    test            "Tests derived from criteria: test_login_render_time < 2s,
                    test_jwt_expiry == 900..."
                    SMARC composite: 0.85

    reviewer        "Approved. 1 iteration required. Execution time 1.8s (< 2s ✓).
                    JWT exp correct. Rate limiting verified. Production ready."
                    SMARC composite: 0.90

  Team composite improved from 0.59 → 0.87 (↑ +0.28) across 10 runs.
  Zero YAML changes. Zero restarts. Zero manual prompt edits.
""")

    # ── Step 13: Using it in your code ────────────────────────────────────
    section("Step 13 — Using it in your own code (identical API to feature-dev)")

    print("""
  from orchestration import load_ready_workflow
  from orchestration.self_improvement import ImprovementLoop

  # feature-dev-with-diagnostics has  self_improve: true  in its metadata
  team = load_ready_workflow(
      "agenticom/bundled_workflows/feature-dev-with-diagnostics.yaml"
  )

  loop = ImprovementLoop(
      auto_approve_patches=True,    # False → human reviews via CLI
      pattern_trigger_n=5,          # gap analysis every 5 runs
  )
  team.attach_improvement_loop(
      loop,
      workflow_id="feature-dev-with-diagnostics",
      self_improve=True,
  )

  # Every call to team.run() automatically:
  #   • Runs browser automation after the developer step (Playwright)
  #   • Captures screenshots, console errors, network requests
  #   • Fires MetaAnalyzer after 3 failures (within-run)
  #   • SMARC-scores each step output (cross-run)
  #   • Updates per-agent performance metrics
  #   • Detects capability gaps every 5 runs
  #   • Proposes (and optionally applies) prompt patches
  result = await team.run("Build a login page with JWT authentication")

  # Inspect improvements:
  #   agenticom feedback report feature-dev-with-diagnostics
  #   agenticom feedback list-patches --workflow feature-dev-with-diagnostics
  #   agenticom feedback rollback feature-dev-with-diagnostics verifier
""")

    banner("END OF CASE STUDY 2")
    print("""
  What you saw:
    ✓  All 6 agents defined (persona, step contract, retry policy, loopbacks)
    ✓  diagnostics_config block: browser type, capture settings, retry ceiling
    ✓  criteria_builder as the flywheel seed: criteria compound through 5 steps
    ✓  How diagnostics.success + console_errors feed SMARC Measurable & Actionable
    ✓  Developer efficiency scoring with 10-retry budget (each retry = −0.20)
    ✓  The TWO feedback channels: meta-analysis (per-run) vs self-improvement (cross-run)
    ✓  Gap analysis output for 6 agents with diagnostics-specific failing dimensions
    ✓  Targeted heuristic patches for criteria_builder, developer, verifier, reviewer
    ✓  Version chains for all 6 agents (heuristic v2 → LLM v3 progression)
    ✓  Full before/after lifecycle: team composite 0.59 → 0.87 over 10 runs

  Next:
    python scripts/demo_self_improvement.py --workflow feature-dev-with-diagnostics --runs 12
      → Run the full loop with a real LLM (set ANTHROPIC_API_KEY first).

    agenticom feedback report feature-dev-with-diagnostics
      → Show the before/after table from real historical runs.

    agenticom workflow run feature-dev-with-diagnostics "Build a login page"
      → Trigger a real run with browser automation active.
    """)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    wf_data = part_a_agent_anatomy()
    part_b_self_optimization(wf_data["agents"], wf_data["workflow"])


if __name__ == "__main__":
    main()
