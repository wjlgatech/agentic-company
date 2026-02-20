#!/usr/bin/env python3
"""
Agenticom Self-Improvement Demo
================================
Runs a workflow N times with a real LLM backend, lets the improvement loop
detect capability gaps and auto-apply prompt patches, then prints a
before-vs-after comparison showing the measured score delta.

Usage:
    python scripts/demo_self_improvement.py
    python scripts/demo_self_improvement.py --workflow due-diligence --runs 15
    python scripts/demo_self_improvement.py --workflow feature-dev \
        --task "Add OAuth2 login endpoint" --runs 12

Requirements:
    - ANTHROPIC_API_KEY or OPENAI_API_KEY set in environment  (or Ollama running)
    - The package installed:  pip install -e .

What happens:
    1. The workflow team is loaded with real agents and a real LLM executor.
    2. An ImprovementLoop is attached with auto_approve_patches=True and
       pattern_trigger_n set to runs//3 (so gap analysis fires twice).
    3. The workflow runs N times against the same task description.
    4. After every 5th run the loop analyses capability gaps, proposes targeted
       prompt patches, and immediately applies them — without any human action.
    5. Subsequent runs use the improved agent personas.
    6. At the end a before/after table shows the measured score delta.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

# ── Make sure the project root is on sys.path ────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BUNDLED = PROJECT_ROOT / "agenticom" / "bundled_workflows"
DEFAULT_DB = Path.home() / ".agenticom" / "self_improve.db"

WIDTH = 65


def hr(char: str = "─", width: int = WIDTH) -> str:
    return char * width


def banner(text: str) -> None:
    print()
    print("═" * WIDTH)
    print(f"  {text}")
    print("═" * WIDTH)


def section(text: str) -> None:
    print()
    print(f"── {text} {'─' * max(0, WIDTH - len(text) - 4)}")


def info(text: str) -> None:
    print(f"  {text}")


# ── Score helpers ─────────────────────────────────────────────────────────────


def fetch_latest_run(workflow_id: str, db_path: Path) -> dict | None:
    """Return the most recent si_run_records row for this workflow (or None)."""
    if not db_path.exists():
        return None
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM si_run_records WHERE workflow_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (workflow_id,),
        ).fetchone()
    return dict(row) if row else None


def fetch_all_runs(workflow_id: str, db_path: Path) -> list[dict]:
    """Return all si_run_records rows for this workflow, oldest first."""
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM si_run_records WHERE workflow_id = ? "
            "ORDER BY created_at ASC",
            (workflow_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_applied_patches(workflow_id: str, db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM si_prompt_patches "
            "WHERE workflow_id = ? AND status = 'applied' ORDER BY approved_at ASC",
            (workflow_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def avg_scores(runs: list[dict]) -> dict[str, float]:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for r in runs:
        for agent, score in json.loads(r.get("agent_scores") or "{}").items():
            sums[agent] = sums.get(agent, 0.0) + float(score)
            counts[agent] = counts.get(agent, 0) + 1
    return {a: sums[a] / counts[a] for a in sums}


def score_bar(score: float, width: int = 10) -> str:
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


# ── Main demo ─────────────────────────────────────────────────────────────────


async def run_demo(
    workflow_id: str,
    task: str,
    n_runs: int,
    db_path: Path,
) -> None:
    from orchestration.self_improvement import ImprovementLoop
    from orchestration.workflows import load_ready_workflow

    # Gap analysis fires at runs 1/3 and 2/3 of the total run count so the
    # audience sees improvement happen during the demo, not only at the end.
    pattern_n = max(3, n_runs // 3)

    banner(
        f"Agenticom Self-Improvement Demo\n"
        f"  Workflow : {workflow_id}\n"
        f"  Task     : {task[:55]}{'…' if len(task) > 55 else ''}\n"
        f"  Runs     : {n_runs}  "
        f"(auto-approve patches, gap-check every {pattern_n} runs)"
    )

    # ── Load workflow ─────────────────────────────────────────────────────
    yaml_path = BUNDLED / f"{workflow_id}.yaml"
    if not yaml_path.exists():
        print(f"❌  Workflow YAML not found: {yaml_path}")
        sys.exit(1)

    try:
        team = load_ready_workflow(yaml_path)
    except RuntimeError as exc:
        print(f"\n❌  {exc}")
        sys.exit(1)

    # ── Set up improvement loop ───────────────────────────────────────────
    # Grab the same executor the team uses so the PromptEvolver can rewrite
    # personas with the LLM (falls back to heuristics if unavailable).
    first_agent = next(iter(team.agents.values()))
    llm_executor = getattr(first_agent, "_executor", None)

    loop = ImprovementLoop(
        db_path=db_path,
        llm_executor=llm_executor,
        auto_approve_patches=True,
        ab_test_enabled=False,  # keep demo clean: no A/B split
        pattern_trigger_n=pattern_n,
        stagnation_threshold=0.05,
    )
    team.attach_improvement_loop(loop, workflow_id, self_improve=True)

    # Detect which LLM backend is active
    from orchestration.integrations.unified import get_ready_backends

    backends = get_ready_backends()
    backend_label = backends[0].value if backends else "unknown"
    info(f"\n  LLM backend : {backend_label}")

    # ── Run loop ──────────────────────────────────────────────────────────
    phase_boundary = n_runs // 2
    recorded_run_ids: list[str] = []

    for run_num in range(1, n_runs + 1):
        if run_num == 1:
            section(f"PHASE 1: Baseline (runs 1–{phase_boundary})")
        elif run_num == phase_boundary + 1:
            section(f"PHASE 2: Post-improvement (runs {phase_boundary + 1}–{n_runs})")

        t0 = time.perf_counter()
        result = await team.run(task)
        elapsed = time.perf_counter() - t0

        # Give the background asyncio.create_task time to write to SQLite.
        await asyncio.sleep(1.5)

        latest = fetch_latest_run(workflow_id, db_path)
        if latest:
            recorded_run_ids.append(latest["id"])
            agent_scores = json.loads(latest.get("agent_scores") or "{}")
            score_parts = "  ".join(
                f"{a}={v:.2f}" for a, v in list(agent_scores.items())[:4]
            )
        else:
            score_parts = "(scores not yet recorded)"

        status = "✓" if result.success else "✗"
        print(f"  Run {run_num:>2}/{n_runs}  {status}  {elapsed:5.1f}s  {score_parts}")

        # Show any patches that were just applied
        applied = fetch_applied_patches(workflow_id, db_path)
        # Only print newly applied patches (those we haven't announced yet)
        for p in applied:
            if p["id"] not in getattr(run_demo, "_announced_patches", set()):
                if not hasattr(run_demo, "_announced_patches"):
                    run_demo._announced_patches = set()
                run_demo._announced_patches.add(p["id"])
                gaps = json.loads(p.get("capability_gaps") or "[]")
                gap_str = ", ".join(g.replace("_", " ") for g in gaps[:3])
                print(
                    f"    ↳ Patch applied [{p['id'][:8]}] {p['agent_id']} "
                    f"({p['generated_by']}): {gap_str}"
                )

    # ── Final comparison ──────────────────────────────────────────────────
    all_runs = fetch_all_runs(workflow_id, db_path)
    # Restrict to runs recorded during THIS demo session
    session_run_ids = set(recorded_run_ids)
    session_runs = [r for r in all_runs if r["id"] in session_run_ids]

    if len(session_runs) < 2:
        print("\n  Not enough recorded runs to compute a comparison.")
        return

    n_base = max(1, len(session_runs) // 2)
    base_runs = session_runs[:n_base]
    post_runs = session_runs[n_base:]

    base_scores = avg_scores(base_runs)
    post_scores = avg_scores(post_runs)
    all_agents = sorted(set(base_scores) | set(post_scores))

    applied_patches = fetch_applied_patches(workflow_id, db_path)
    session_patches = [
        p
        for p in applied_patches
        if p["id"] in getattr(run_demo, "_announced_patches", set())
    ]

    banner(
        f"BEFORE → AFTER COMPARISON\n"
        f"  Baseline : first {n_base} run(s) of this session\n"
        f"  Current  : last {len(post_runs)} run(s) of this session\n"
        f"  Patches  : {len(session_patches)} applied"
    )

    col_w = max((len(a) for a in all_agents), default=10) + 2
    print(f"  {'Agent':<{col_w}} {'Baseline':>10} {'Current':>10} " f"{'Δ':>8}   Trend")
    print(f"  {hr('─', col_w + 44)}")

    deltas = []
    for agent in all_agents:
        b = base_scores.get(agent, 0.0)
        c = post_scores.get(agent, 0.0)
        d = c - b
        deltas.append(d)
        bar = score_bar(c)
        trend = "▲" if d > 0.02 else ("▼" if d < -0.02 else "─")
        print(
            f"  {agent:<{col_w}} {b:>10.3f} {c:>10.3f} {d:>+8.3f}   " f"{trend} {bar}"
        )

    if deltas:
        avg_d = sum(deltas) / len(deltas)
        direction = "improved" if avg_d > 0 else "declined"
        print()
        print(
            f"  Overall score {direction} by {avg_d:+.3f} "
            f"across {len(all_agents)} agent(s)"
        )

    if session_patches:
        print()
        print("  Applied patches:")
        for p in session_patches:
            gaps = json.loads(p.get("capability_gaps") or "[]")
            gap_str = ", ".join(g.replace("_", " ") for g in gaps[:3])
            ts = (p.get("approved_at") or "")[:10]
            print(
                f"    [{p['id'][:8]}]  {p['agent_id']:<18} {p['generated_by']:<12} {ts}"
            )
            print(f"             {gap_str}")

    print()
    print(
        f"  Run `agenticom feedback report {workflow_id}` to see the full "
        "history any time."
    )
    print()
    print("═" * WIDTH)
    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a workflow N times and watch the self-improvement loop work.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--workflow",
        "-w",
        default="feature-dev",
        help="Workflow ID (default: feature-dev)",
    )
    parser.add_argument(
        "--task",
        "-t",
        default=(
            "Add a user authentication endpoint with JWT tokens, "
            "input validation, rate limiting, and unit tests."
        ),
        help="Task description passed to the workflow on every run",
    )
    parser.add_argument(
        "--runs",
        "-n",
        type=int,
        default=12,
        help="Total number of workflow runs (default: 12; minimum: 6)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite database path (default: {DEFAULT_DB})",
    )
    args = parser.parse_args()

    if args.runs < 6:
        print(
            "❌  --runs must be at least 6 (need enough runs to trigger gap analysis twice)"
        )
        sys.exit(1)

    # Ensure the DB directory exists
    args.db.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(
        run_demo(
            workflow_id=args.workflow,
            task=args.task,
            n_runs=args.runs,
            db_path=args.db,
        )
    )


if __name__ == "__main__":
    main()
