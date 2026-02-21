#!/usr/bin/env python3
"""
Exploration 01: Equipping Agents with Skills
=============================================
Reference: https://github.com/sickn33/antigravity-awesome-skills (868+ skills)
Workflow:   feature-dev-with-diagnostics (and all bundled workflows)

This script is a design-space exploration — no LLM key required.
It answers four questions critically:

  PART A — What are skills?
            Anatomy of a SKILL.md, categories, invocation syntax.
            What they CAN and CANNOT give an agent.

  PART B — Current state: where agents are blind without skills.
            Gap analysis of all 5 base agent personas.

  PART C — Pros & cons of equipping agents with skills.
            Honest cost/benefit with numbers.

  PART D — When should an agent use a skill?
            Decision matrix: always-on vs conditional vs never.

  PART E — How is a skill selected?
            Three selection mechanisms ranked by sophistication.

  PART F — How is a skill activated?
            Three activation paths: static YAML, task-time injection,
            self-improvement loop as skill router (the powerful one).

  PART G — Skill-to-agent mapping for all bundled workflows.
            Concrete recommendations per workflow × agent.

  PART H — Implementation sketch.
            Minimum viable YAML changes + code touch points.

Run:
    python examples/exploration_01_agent_skills.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WIDTH = 72


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


def tick(label: str, note: str = "", good: bool = True) -> None:
    icon = "✓" if good else "✗"
    note_str = f"  — {note}" if note else ""
    print(f"      {icon}  {label}{note_str}")


# ─────────────────────────────────────────────────────────────────────────────
# PART A — What are skills?
# ─────────────────────────────────────────────────────────────────────────────


def part_a_skill_anatomy() -> None:
    banner("PART A  —  What are skills? (antigravity-awesome-skills anatomy)")

    print("""
  Repository : https://github.com/sickn33/antigravity-awesome-skills
  Skills     : 868+ community-maintained skill documents
  Format     : Each skill is a directory skills/<name>/SKILL.md
  Install    : npx antigravity-awesome-skills --claude  (→ .claude/skills/)
  Invoke     : /skill-name in Claude Code, @skill-name in Cursor

  A skill is a MARKDOWN DOCUMENT, not executable code.
  It injects domain-specific instructions into the agent's system prompt.
""")

    section("SKILL.md anatomy — what every skill contains")
    print("""
  ┌─ Frontmatter (required) ─────────────────────────────────────────────┐
  │  ---                                                                 │
  │  name: your-skill-name            # kebab-case, matches folder name  │
  │  description: "One sentence"      # shown in skill listings          │
  │  metadata:                                                           │
  │    model: inherit                 # which LLM to use (usually inherit)│
  │  ---                                                                 │
  └──────────────────────────────────────────────────────────────────────┘

  ┌─ Body sections (convention) ─────────────────────────────────────────┐
  │  # Skill Name                                                        │
  │  ## Overview          — what this skill specializes in               │
  │  ## When to Use       — trigger conditions (explicit)                │
  │  ## Do Not Use When   — anti-patterns (explicit)                     │
  │  ## Step-by-Step      — concrete instructions the agent follows      │
  │  ## Examples          — at least one copy-paste ready example        │
  │  ## Safety            — risk labels, constraints                     │
  │  ## Best Practices    — domain-specific heuristics                   │
  └──────────────────────────────────────────────────────────────────────┘

  Example from skills/ai-engineer/SKILL.md (8,925 bytes):
    "You are an AI engineer specializing in production-grade LLM applications.
     Use this skill when: Building RAG systems, LLM features, AI agents.
     Do not use when: Pure data science without LLMs.
     Instructions: 1. Clarify constraints. 2. Design architecture. ..."
""")

    section("Skill categories and count")
    CATEGORIES = [
        ("Architecture",  68,  "System design, C4 diagrams, DDD, event sourcing, microservices"),
        ("Business",      38,  "SEO, pricing, financial modeling, competitive analysis"),
        ("Data-AI",      159,  "LLM apps, RAG, vector DBs, Azure AI (100+ azure-* skills), prompt eng"),
        ("Development",  132,  "Python, TypeScript, Go, React, Next.js, databases, API design"),
        ("General",       15,  "Planning, documentation, brainstorming, lint-and-validate"),
        ("Infrastructure", 80, "DevOps, CI/CD, Docker, Kubernetes, cloud deployment"),
        ("Security",      60,  "AppSec, pentest, compliance, AWS/AD attacks, API fuzzing"),
        ("Testing",       40,  "TDD, QA, test design, browser automation patterns"),
        ("Other",        276,  "3D-web, airtable, algolia, analytics, CRM, agent frameworks..."),
    ]
    print(f"\n  {'Category':<18} {'Count':>7}  Skills include")
    print(f"  {'─' * 70}")
    total = 0
    for cat, count, desc in CATEGORIES:
        print(f"  {cat:<18} {count:>7}  {desc}")
        total += count
    print(f"  {'─' * 70}")
    print(f"  {'TOTAL':<18} {total:>7}")

    section("What skills CAN and CANNOT give an agent")
    print("""
  ┌─ CAN give ───────────────────────────────────────────────────────────┐
  │                                                                      │
  │  • Domain knowledge injection — patterns, best practices, frameworks │
  │    that the base model knows but wouldn't apply without prompting    │
  │                                                                      │
  │  • Explicit behavioural constraints — "always validate input",       │
  │    "never send PII to external models", security guardrails          │
  │                                                                      │
  │  • Step-by-step reasoning scaffolds — reduce hallucination by        │
  │    giving the agent a decision tree to follow                        │
  │                                                                      │
  │  • Output format specifications — schema, checklist, template        │
  │    that downstream agents can parse reliably                         │
  │                                                                      │
  │  • "When not to use" guards — prevents scope creep into              │
  │    areas the agent should leave to a different specialist            │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘

  ┌─ CANNOT give ────────────────────────────────────────────────────────┐
  │                                                                      │
  │  • Real-world tool access — a skill is instructions, NOT an API      │
  │    call. "web-search" skill tells the agent HOW to think about       │
  │    searching; it cannot actually execute an HTTP request.            │
  │                                                                      │
  │  • Fresh data — skills are static markdown; they cannot pull         │
  │    live prices, current docs, or real-time search results.           │
  │                                                                      │
  │  • Verification of facts — no external lookup = no ground truth.    │
  │    Skills improve reasoning quality, not factual accuracy.           │
  │                                                                      │
  │  • Autonomy over tool selection — in Agenticom's pipeline, the       │
  │    skill document is merged into the system prompt; the agent        │
  │    still cannot decide mid-step to call a new tool unless the        │
  │    tool is explicitly wired via MCP.                                 │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART B — Current state: where agents are blind
# ─────────────────────────────────────────────────────────────────────────────


def part_b_current_gaps() -> None:
    banner("PART B  —  Current state: where base agent personas fall short")

    section("How agents work today (no skills)")
    print("""
  Every agent has three layers of text that form its effective system prompt:

  Layer 1: persona          (from YAML prompt: field, or specialized.py default)
  Layer 2: system_prompt    (LLMAgent builds: persona + role label + context)
  Layer 3: task input       (WorkflowStep.input_template, substituted at runtime)

  Execution path:
    AgentTeam._execute_step()
      → template substitution ({{task}}, {{step_outputs.X}})
      → agent.execute(input_data, AgentContext)
        → LLMAgent._execute_task()
          → full_prompt = system_prompt + "\\nTask: " + input_data
          → executor(full_prompt, context)   ← one LLM call
          → return raw text output

  No skill routing. No tool dispatch. No mid-step capability extension.
  The agent produces output purely from its persona + the task text.
""")

    section("Gap analysis: what each base agent is missing")

    AGENT_GAPS = [
        (
            "criteria_builder",
            "Requirements analyst defining measurable success criteria",
            [
                ("Domain-specific testability patterns",
                 "Knows 'make criteria testable' but not HOW for React, APIs, auth flows separately"),
                ("Accessibility criterion templates",
                 "No WCAG 2.1 / ARIA patterns — a11y criteria are consistently missing"),
                ("Performance budget templates",
                 "No LCP/FID/CLS thresholds, response-time SLOs — only generic 'fast'"),
                ("Security criterion templates",
                 "No OWASP-aligned criteria — rate-limit, injection, token expiry patterns absent"),
            ],
        ),
        (
            "planner",
            "Senior technical planner breaking features into tasks",
            [
                ("Story decomposition patterns",
                 "Breaks down tasks but doesn't apply INVEST (Independent/Negotiable/Valuable...) rules"),
                ("Risk taxonomy",
                 "Lists 'Risks:' but no structured risk matrix — no likelihood × impact scoring"),
                ("Dependency graph awareness",
                 "Identifies dependencies by name but not critical-path ordering or parallelism"),
                ("Architecture decision records",
                 "No ADR template — technical decisions are buried in prose, not version-controlled"),
            ],
        ),
        (
            "developer",
            "Senior developer implementing code",
            [
                ("Language-specific idioms",
                 "Generic coding standards — no Python async patterns, TS strict types, Go conventions"),
                ("Security implementation patterns",
                 "No input sanitisation, parameterised queries, JWT validation patterns by default"),
                ("Framework-specific patterns",
                 "No React hooks rules, Next.js app-router conventions, FastAPI dependency injection"),
                ("Browser/runtime target awareness",
                 "Writes code but doesn't consider CSP headers, CORS preflight, SSR hydration gaps"),
            ],
        ),
        (
            "verifier",
            "Verification specialist cross-checking against spec",
            [
                ("Security verification checklist",
                 "Checks 'acceptance criteria' but no OWASP Top 10 review by default"),
                ("Performance verification",
                 "No Lighthouse score check, no bundle-size review, no DB query explain plan"),
                ("Accessibility verification",
                 "No screen-reader check, no keyboard navigation test, no colour-contrast review"),
                ("API contract verification",
                 "No schema validation, no status-code coverage check, no error-response format"),
            ],
        ),
        (
            "tester",
            "QA engineer creating test suites",
            [
                ("Property-based testing patterns",
                 "Writes example-based tests only — no Hypothesis/fast-check fuzz strategies"),
                ("Mutation testing awareness",
                 "No guidance to check test resilience — 100% line coverage ≠ good tests"),
                ("Contract testing patterns",
                 "No Pact / OpenAPI validation — API changes break consumers silently"),
                ("Performance test scaffolds",
                 "No k6/Locust load test — only unit/integration, missing SLO validation"),
            ],
        ),
        (
            "reviewer",
            "Senior code reviewer assessing production readiness",
            [
                ("Security review checklist",
                 "No SAST-style review — hardcoded secrets, SQL injection, XSS often missed"),
                ("Observability review",
                 "No check for structured logs, metrics, tracing — dark production code"),
                ("Cost / resource review",
                 "No review of N+1 queries, unbounded loops, memory allocation patterns"),
                ("Deployment safety review",
                 "No migration safety check, no feature-flag requirement, no rollback plan"),
            ],
        ),
    ]

    for agent_id, role, gaps in AGENT_GAPS:
        print(f"\n  ┌─ {agent_id.upper()} ({role}) {'─' * max(0, WIDTH - len(agent_id) - len(role) - 6)}┐")
        for gap_name, detail in gaps:
            print(f"  │  ✗  {gap_name}")
            print(f"  │       {detail}")
        print("  └" + "─" * 70 + "┘")


# ─────────────────────────────────────────────────────────────────────────────
# PART C — Pros and cons
# ─────────────────────────────────────────────────────────────────────────────


def part_c_pros_cons() -> None:
    banner("PART C  —  Honest pros & cons of equipping agents with skills")

    section("PROS")
    print("""
  1. Community-validated domain knowledge (868 skills, maintained externally)
     ─────────────────────────────────────────────────────────────────────
     Skills in the repo are battle-tested by real engineers across thousands
     of projects. The `typescript-react-patterns` skill encodes patterns that
     would take a prompt engineer hours to distill. Adding it to the developer
     agent is free domain knowledge.

  2. Composability — mix and match per workflow
     ─────────────────────────────────────────────────────────────────────
     Skills compose without conflict. The developer agent on `due-diligence`
     can use `startup-financial-modeling` while the same developer on
     `security-assessment` uses `api-fuzzing-bug-bounty`. No code changes —
     just YAML configuration.

  3. Reduces persona drift and specificity gaps
     ─────────────────────────────────────────────────────────────────────
     The SMARC self-improvement loop flags "output_specificity = 0.1 (LOW)"
     for the verifier. Instead of waiting 5 runs and applying a heuristic
     suffix, you could inject `owasp-top10` skill at startup and get
     specificity immediately.

  4. Directly improves SMARC scores without LLM evolution calls
     ─────────────────────────────────────────────────────────────────────
     Skills address the root cause (missing domain knowledge) rather than
     the symptom (low SMARC score). A patch that appends
     "CRITICAL: Be specific" is weaker than a skill that says
     "For auth endpoints, always check: JWT alg != 'none', exp claim,
      token rotation on privilege escalation, timing-safe comparison."

  5. Skill library is version-controlled and updateable independently
     ─────────────────────────────────────────────────────────────────────
     `git -C .agent/skills pull` upgrades all skills without touching
     workflow YAMLs. When the community updates `nextjs-app-router-patterns`
     for Next.js 15, the developer agent automatically benefits.

  6. Synergy with the self-improvement loop (covered in Part F)
     ─────────────────────────────────────────────────────────────────────
     The PromptEvolver can use skill CONTENT as patch material.
     Instead of heuristic suffixes, it injects the relevant skill sections
     that specifically address detected gaps — LLM-quality patches without
     needing an LLM call.
""")

    section("CONS")
    print("""
  1. Token cost: skills are large — injecting naively is expensive
     ─────────────────────────────────────────────────────────────────────
     The `ai-engineer` skill is 8,925 bytes ≈ 2,200 tokens.
     With 6 agents each receiving 2 skills, that is ~26,400 extra tokens
     per run. At $3/M tokens (claude-sonnet-4-6) that is $0.08 per run.
     Over 1,000 runs = $80 of pure skill-injection overhead.

     Mitigation: inject SUMMARIES (first 300 tokens of skill) or only
     the "Step-by-Step" section, not the full document.

  2. Skills assume human-in-the-loop; Agenticom is autonomous
     ─────────────────────────────────────────────────────────────────────
     Many skills instruct: "Ask the user to clarify...", "Confirm with
     the client before proceeding...", "Request approval for..."
     In Agenticom's pipeline there is no user mid-step. Such instructions
     cause the agent to either hallucinate a user response or stall.

     Mitigation: preprocess skill content — strip "ask the user" clauses
     or replace with "document the assumption in your output."

  3. Skills overlap and may conflict with existing personas
     ─────────────────────────────────────────────────────────────────────
     The developer agent's YAML persona already says "no TODO comments".
     A skill might say "add TODO markers for optional enhancements."
     Contradictory instructions cause inconsistent agent behaviour.

     Mitigation: skill injection is ADDITIVE at the end; conflicts should
     be resolved by an explicit "Skill overrides persona on X" header.

  4. Skills are static; self-improvement is dynamic
     ─────────────────────────────────────────────────────────────────────
     The improvement loop evolves personas based on actual run data.
     A statically injected skill knows nothing about this specific workflow's
     failure patterns. It may inject irrelevant content (e.g., a skill about
     GraphQL when the workflow builds a REST API).

     Mitigation: only activate skills when the SMARC gap specifically maps
     to the skill's domain (Part E, Approach 3).

  5. Skill quality is uneven across the 868 collection
     ─────────────────────────────────────────────────────────────────────
     Some skills are comprehensive and precise; others are thin stubs.
     The security category has both deep skills (api-fuzzing-bug-bounty)
     and shallow ones. There is no quality signal beyond the V4 checklist.

     Mitigation: curate an internal registry of approved skills per
     workflow type, rather than allowing arbitrary skill assignment.

  6. No feedback mechanism from skills back to the improvement loop
     ─────────────────────────────────────────────────────────────────────
     When a skill improves an agent's output, the improvement loop doesn't
     know it was the skill that helped. This breaks attribution — the loop
     might propose patches that undo what the skill already fixed.

     Mitigation: record `active_skills` in RunRecord metadata so the loop
     can correlate SMARC improvements with skill presence.
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART D — Decision matrix: when should an agent use a skill?
# ─────────────────────────────────────────────────────────────────────────────


def part_d_decision_matrix() -> None:
    banner("PART D  —  When should an agent use a skill? Decision matrix")

    section("Three-tier decision framework")
    print("""
  TIER 1: ALWAYS-ON  (inject at startup, every run)
  ─────────────────────────────────────────────────
  Use when:
    • The skill domain matches the agent's primary role exactly
    • The workflow type always requires the domain knowledge
    • Skill content is focused and short (< 500 tokens)
    • The skill has "Do Not Use When" guard-rails that prevent scope creep

  Examples:
    planner          ← brainstorming, lint-and-validate (always useful)
    security-assess  ← owasp-top10 for verifier (always applies)
    due-diligence    ← startup-financial-modeling for analyst (always applies)

  TIER 2: CONDITIONAL  (inject based on task content analysis)
  ──────────────────────────────────────────────────────────────
  Use when:
    • The skill domain may or may not apply depending on the task
    • Injecting always would waste tokens on irrelevant content
    • A simple keyword/pattern check on the task description is sufficient

  Decision rule: task_text.lower() contains any of skill.keywords?
    → inject    → skip

  Examples:
    developer   ← typescript-react-patterns  (only if task mentions React/TS)
    developer   ← postgres-best-practices    (only if task mentions DB/SQL)
    developer   ← async-python-patterns      (only if task is Python async)
    tester      ← agent-evaluation           (only if testing an AI component)

  TIER 3: NEVER  (do not inject — negative ROI)
  ──────────────────────────────────────────────
  Avoid when:
    • Skill body length > 3,000 tokens (kills context budget)
    • Skill assumes human interaction ("ask the user to...") throughout
    • Skill domain is orthogonal to the agent's step in this workflow
    • Skill content is already covered verbatim by the base persona
    • Skill is in Security category with offensive technique instructions
      (risk of generating harmful content in autonomous mode)

  Examples:
    active-directory-attacks  ← never for any Agenticom workflow
    anti-reversing-techniques ← never in autonomous mode
    social-media-* skills     ← never for developer/tester agents
""")

    section("Signal-based activation triggers")
    print("""
  Beyond keyword matching, four signals can trigger skill activation:

  Signal 1: SMARC gap score  (from self-improvement loop)
  ────────────────────────────────────────────────────────
  if agent_smarc["specific"] < 0.4 for N consecutive runs:
      check skill registry for skills that improve specificity
      in the agent's domain → conditional inject

  Signal 2: Retry count  (from WorkflowStep execution)
  ────────────────────────────────────────────────────────
  if step_result.retries >= 2 (same step failing repeatedly):
      check if a skill exists for the failure pattern
      e.g., developer fails browser test 2× → inject playwright-best-practices
      This is WITHIN-RUN skill injection (dynamic, not static).

  Signal 3: Task complexity score  (simple heuristic)
  ────────────────────────────────────────────────────────
  complexity = len(task.split()) / 10 + number_of_criteria
  if complexity > 15: unlock tier-2 skills (task is complex enough to justify)
  if complexity < 5:  only tier-1 always-on skills (task too simple to bloat)

  Signal 4: Workflow type  (static, from YAML metadata)
  ────────────────────────────────────────────────────────
  workflow.tags includes "security" → verifier always gets owasp-top10
  workflow.tags includes "data"     → analyst always gets data-analysis
  workflow.tags includes "research" → researcher always gets rag-engineer
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART E — How is a skill selected?
# ─────────────────────────────────────────────────────────────────────────────


def part_e_skill_selection() -> None:
    banner("PART E  —  How is a skill selected? Three mechanisms")

    section("Approach 1: Static YAML assignment (simplest, deploy now)")
    print("""
  Engineer assigns skills to agents in the workflow YAML.
  WorkflowParser reads them at startup and appends skill content to persona.

  YAML change:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  agents:                                                             │
  │    - id: developer                                                   │
  │      skills:                                                         │
  │        - typescript-react-patterns   # always-on                    │
  │        - postgres-best-practices     # always-on                    │
  │        - async-python-patterns       # always-on                    │
  │                                                                      │
  │    - id: verifier                                                    │
  │      skills:                                                         │
  │        - lint-and-validate           # always-on                    │
  │                                                                      │
  │    - id: tester                                                      │
  │      skills:                                                         │
  │        - agent-evaluation            # only if AI component is tested│
  └──────────────────────────────────────────────────────────────────────┘

  Skill resolution at WorkflowParser.parse():
    for each agent.skills entry:
      skill_path = skills_dir / skill_name / "SKILL.md"
      content = parse_skill_md(skill_path)      # strip frontmatter
      agent.persona += f"\\n\\n## Skill: {skill_name}\\n{content[:800]}"
      # cap at 800 chars to control token cost

  Pros:  zero runtime overhead, deterministic, easy to understand
  Cons:  not adaptive; requires engineer to know which skills apply upfront
""")

    section("Approach 2: Task-time skill routing (moderate, recommended for launch)")
    print("""
  A SkillRouter analyses the task description BEFORE the first step runs
  and selects the best-matching skills for each agent.

  How it works:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  SkillRouter.select(task: str, agent_role: str) -> list[str]         │
  │                                                                      │
  │  1. Load skill_index.json (pre-built from CATALOG.md):               │
  │       {"typescript-react-patterns": {"keywords": ["react", "tsx",    │
  │         "hooks", "component", "next.js"], "roles": ["developer"]},   │
  │        "postgres-best-practices": {"keywords": ["postgres", "sql",   │
  │         "query", "database", "migration"], "roles": ["developer"]},  │
  │        ...}                                                          │
  │                                                                      │
  │  2. Score each skill:                                                │
  │       keyword_hits = sum(kw in task.lower() for kw in skill.keywords)│
  │       role_match   = 1 if agent_role in skill.roles else 0           │
  │       score        = keyword_hits * 2 + role_match                   │
  │                                                                      │
  │  3. Return top-K skills where score > threshold (e.g. K=2, t=1)     │
  │                                                                      │
  │  4. Inject into agent persona before first step executes             │
  └──────────────────────────────────────────────────────────────────────┘

  Example: task = "Build a Next.js login page with JWT auth and Postgres"
    developer agent:
      typescript-react-patterns  → keyword_hits=2 (next.js, jwt) → score=5 ✓
      postgres-best-practices    → keyword_hits=1 (postgres)      → score=3 ✓
      async-python-patterns      → keyword_hits=0                 → score=0 ✗
    verifier agent:
      lint-and-validate          → role=verifier → score=1 ✓
      owasp-top10               → keyword_hits=1 (auth)           → score=3 ✓

  Token budget enforcement:
    total_skill_tokens = sum(len(skill_content.split()) for s in selected)
    if total_skill_tokens > MAX_SKILL_TOKENS:  # e.g. 600 per agent
        use summary sections only (## Overview + ## Step-by-Step first 10 lines)

  Pros:  adaptive, no extra LLM call, runs in < 5ms
  Cons:  keyword matching is crude; misses semantic relevance;
         still requires a maintained skill_index.json
""")

    section("Approach 3: Self-improvement loop as skill router (advanced, highest ROI)")
    print("""
  The most powerful integration: the PromptEvolver checks the skill library
  BEFORE falling back to heuristic suffixes.

  Current flow:
    gap detected → heuristic suffix appended  (weak: "CRITICAL: Be specific.")

  Enhanced flow:
    gap detected → skill_router.find_for_gap(gap, agent_role)
                   → skill sections that address the gap injected as patch
                   → if no skill found → heuristic suffix (fallback)

  Mapping SMARC gaps → skills:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Gap detected                     Skill injected                    │
  │  ─────────────────────────────────────────────────────────────────── │
  │  *_output_specificity LOW         lint-and-validate (any agent)      │
  │  developer_output_specificity     typescript-react-patterns (if TS)  │
  │                                   async-python-patterns (if Python)  │
  │  developer_output_measurability   postgres-best-practices (if DB)    │
  │  verifier_output_actionability    owasp-top10 (security workflows)   │
  │  verifier_output_measurability    agent-evaluation (AI workflows)    │
  │  tester_knowledge_compoundability Property-based testing section     │
  │  reviewer_knowledge_compoundability Observability review section     │
  └──────────────────────────────────────────────────────────────────────┘

  Why this is the most powerful approach:
    1. Skills are applied WHEN NEEDED, not always — zero token waste
    2. The patch is evidence-based (SMARC data) not guesswork
    3. The skill content is far more specific than a heuristic suffix
    4. The RunRecord records which skill was injected → the loop learns
       whether the skill actually moved the SMARC score in the next run
    5. If the skill did NOT improve the score → the loop tries a different
       skill or falls back to LLM persona rewrite
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART F — How is a skill activated?
# ─────────────────────────────────────────────────────────────────────────────


def part_f_activation() -> None:
    banner("PART F  —  How is a skill activated? Three activation paths")

    section("Path 1: Static injection at workflow load (startup time)")
    print("""
  WorkflowParser.parse()  →  build AgentConfig per agent
    |
    └→ for each skill in agent.skills:
         skill_text = SkillLoader.load(skill_name, sections=["overview", "steps"])
         agent_config.persona += f"\\n\\n{skill_text}"

  Timing:  once at workflow load — zero per-run overhead
  Scope:   permanent for all runs of that workflow
  Signal:  explicit YAML assignment by engineer

  Persona update path:
    agent.persona = yaml_persona + skill_text
    agent.system_prompt property reads self.persona dynamically
    → no other code change needed; update_persona() already handles this
""")

    section("Path 2: Pre-run injection at task-time (dynamic, per-run)")
    print("""
  AgentTeam.run(task)  →  before first step executes
    |
    └→ SkillRouter.select(task, agent_role) → selected_skills
       for agent in team.agents.values():
           new_persona = base_persona
           for skill in selected_skills[agent.role]:
               new_persona += SkillLoader.load(skill, token_budget=400)
           agent.update_persona(new_persona, version_id="task-time")

  Timing:  once per team.run() call — minimal overhead (< 5ms, no LLM)
  Scope:   one run only; next run re-evaluates based on new task
  Signal:  task keyword matching (Approach 2 from Part E)

  Key design: personas are reset to base_persona at run start, then
  enriched with task-relevant skills. This prevents skill accumulation
  across runs (which would compound token costs).
""")

    section("Path 3: Improvement-loop patch injection (cross-run, gap-driven)")
    print("""
  ImprovementLoop._on_pattern_trigger(workflow_id)
    → _identify_capability_gaps()
    → for each gap:
         skill_name = SkillGapMatcher.find(gap, agent_role, task_context)
         if skill_name:
             skill_content = SkillLoader.load(skill_name, sections=["steps"])
             patch = PromptEvolver._skill_propose(
                 agent_role, current_persona, skill_content, gap
             )
         else:
             patch = PromptEvolver._heuristic_propose(...)  # existing fallback
         PromptVersionStore.save_patch(patch)
         # auto_approve=True → applied immediately; version stored in SQLite

  Timing:  every N runs when gap detected — async background task
  Scope:   permanent (next version in prompt chain) until rolled back
  Signal:  SMARC proficiency < 0.5 for the capability key

  Feedback loop (new):
    After next N runs with skill-injected persona:
      if new_smarc[dimension] > old_smarc[dimension] + 0.10:
          skill was effective → keep
          log: "skill typescript-react-patterns lifted developer specificity
                from 0.38 → 0.71"
      else:
          skill was not effective → try next candidate skill
          or fall back to LLM full-persona rewrite

  The difference from static injection:
    • Skill content is chunked into the patch, not the full skill
    • Only the sections relevant to the gap are extracted
    • The RunRecord's metadata records {"active_skills": ["typescript-react-patterns"]}
      so the attribution is traceable in the feedback report
""")

    section("Activation path comparison")
    print(f"""
  {'Dimension':<28} {'Path 1 (static)':>16} {'Path 2 (task-time)':>18} {'Path 3 (loop-driven)':>20}
  {'─' * 86}
  {'When it fires':<28} {'at load':>16} {'each run()':>18} {'every N runs':>20}
  {'Requires gap data?':<28} {'no':>16} {'no':>18} {'yes (SMARC)':>20}
  {'Token overhead':<28} {'always':>16} {'conditional':>18} {'patch only':>20}
  {'Scope':<28} {'all runs':>16} {'one run':>18} {'all future runs':>20}
  {'Human control':<28} {'YAML edit':>16} {'skill_index':>18} {'feedback CLI':>20}
  {'LLM call needed?':<28} {'no':>16} {'no':>18} {'optional':>20}
  {'Requires implementation':<28} {'low':>16} {'medium':>18} {'high':>20}
  {'Expected SMARC lift':<28} {'moderate':>16} {'moderate':>18} {'highest':>20}
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART G — Skill-to-agent mapping across all bundled workflows
# ─────────────────────────────────────────────────────────────────────────────


def part_g_workflow_mapping() -> None:
    banner("PART G  —  Skill-to-agent mapping across all bundled workflows")

    print("""
  13 bundled workflows × 2–6 agents each.
  Recommendations below use three markers:
    [A] always-on (Path 1 static)
    [C] conditional on task keywords (Path 2 task-time)
    [L] loop-driven when SMARC gap detected (Path 3 improvement loop)
""")

    WORKFLOW_SKILLS = [
        (
            "feature-dev",
            "feature-dev-with-diagnostics",
            [
                ("criteria_builder", ["brainstorming [A]",
                                      "lint-and-validate [A]"]),
                ("planner",          ["brainstorming [A]",
                                      "ddd-strategic-design [C: 'domain/entity/aggregate']"]),
                ("developer",        ["async-python-patterns [C: 'async/await/celery']",
                                      "typescript-react-patterns [C: 'react/tsx/hooks']",
                                      "nextjs-app-router-patterns [C: 'next.js/app router']",
                                      "postgres-best-practices [C: 'postgres/sql/database']",
                                      "ai-engineer [C: 'llm/embedding/rag']"]),
                ("verifier",         ["lint-and-validate [A]",
                                      "owasp-top10 [L: verifier_output_specificity<0.5]"]),
                ("tester",           ["agent-evaluation [C: 'agent/llm/ai component']"]),
                ("reviewer",         ["lint-and-validate [A]"]),
            ],
        ),
        (
            "security-assessment",
            None,
            [
                ("planner",   ["brainstorming [A]",
                               "architect-review [A]"]),
                ("developer", ["api-fuzzing-bug-bounty [A]",
                               "aws-penetration-testing [C: 'aws/cloud']"]),
                ("verifier",  ["owasp-top10 [A]",
                               "lint-and-validate [A]"]),
                ("tester",    ["api-fuzzing-bug-bounty [A]"]),
                ("reviewer",  ["owasp-top10 [A]"]),
            ],
        ),
        (
            "due-diligence",
            None,
            [
                ("planner",    ["brainstorming [A]",
                                "startup-financial-modeling [A]"]),
                ("researcher", ["rag-engineer [A]",
                                "llm-evaluation [C: 'ai company/llm product']",
                                "startup-financial-modeling [A]"]),
                ("analyst",    ["startup-financial-modeling [A]",
                                "data-analysis [A]",
                                "pricing-strategy [C: 'pricing/monetisation']"]),
                ("reviewer",   ["startup-financial-modeling [A]"]),
            ],
        ),
        (
            "churn-analysis",
            None,
            [
                ("analyst",  ["data-analysis [A]",
                              "analytics-tracking [A]",
                              "amplitude-automation [C: 'amplitude/event']"]),
                ("developer",["async-python-patterns [A]",
                              "postgres-best-practices [C: 'sql/query']"]),
                ("reviewer", ["data-analysis [A]"]),
            ],
        ),
        (
            "marketing-campaign",
            None,
            [
                ("planner",  ["brainstorming [A]",
                              "marketing-ideas [A]",
                              "seo-content-writer [C: 'blog/seo/content']"]),
                ("writer",   ["seo-content-writer [A]",
                              "marketing-ideas [A]"]),
                ("reviewer", ["seo-content-writer [A]"]),
            ],
        ),
        (
            "grant-proposal",
            None,
            [
                ("researcher", ["rag-engineer [A]"]),
                ("writer",     ["brainstorming [A]"]),
                ("reviewer",   ["lint-and-validate [A]"]),
            ],
        ),
        (
            "incident-postmortem",
            None,
            [
                ("analyst",  ["data-analysis [A]",
                              "analytics-tracking [A]"]),
                ("writer",   ["brainstorming [A]"]),
                ("reviewer", ["lint-and-validate [A]"]),
            ],
        ),
    ]

    for wf_primary, wf_variant, agent_skills in WORKFLOW_SKILLS:
        wf_label = wf_primary
        if wf_variant:
            wf_label = f"{wf_primary} / {wf_variant}"
        print(f"\n  ┌─ {wf_label} {'─' * max(0, WIDTH - len(wf_label) - 3)}┐")
        for agent_id, skills in agent_skills:
            print(f"  │  {agent_id:<20}")
            for skill in skills:
                print(f"  │    → {skill}")
        print("  └" + "─" * 70 + "┘")

    print("""
  KEY:
    [A] always-on static injection in YAML   → Path 1
    [C] conditional on task keywords          → Path 2 (keyword shown in quotes)
    [L] loop-driven on SMARC gap             → Path 3

  Not included (NEVER for autonomous mode):
    active-directory-attacks, anti-reversing-techniques, social-* skills,
    any skill body that starts with "Ask the user to..." exclusively
""")


# ─────────────────────────────────────────────────────────────────────────────
# PART H — Implementation sketch
# ─────────────────────────────────────────────────────────────────────────────


def part_h_implementation() -> None:
    banner("PART H  —  Implementation sketch: minimum viable change set")

    section("What needs to change (ordered by value-to-effort ratio)")

    print("""
  PHASE 1 — Static injection (highest value, lowest effort: ~2 hours)
  ─────────────────────────────────────────────────────────────────────

  1. Add `skills:` field to YAML agent definitions
     Already supported by AgentConfig.tools (list[str]) — repurpose or add
     a separate `skills: list[str]` field.

  2. Install skill library:
       npx antigravity-awesome-skills --path .agent/skills
       # or: git clone https://github.com/sickn33/antigravity-awesome-skills.git .agent/skills

  3. SkillLoader (new, 30 lines):
     ┌────────────────────────────────────────────────────────────────────┐
     │  class SkillLoader:                                               │
     │      def __init__(self, skills_dir: Path): ...                    │
     │      def load(self, name: str, max_tokens: int = 400) -> str:    │
     │          path = self.skills_dir / name / "SKILL.md"               │
     │          if not path.exists(): return ""                          │
     │          text = path.read_text()                                  │
     │          # strip frontmatter (--- ... ---)                        │
     │          body = re.sub(r"^---.*?---\\n", "", text, flags=re.DOTALL)│
     │          # strip "ask the user" instructions                      │
     │          body = re.sub(r"[Aa]sk the user.*?\\n", "", body)         │
     │          # cap by approx token budget                             │
     │          words = body.split()                                     │
     │          return " ".join(words[:max_tokens * 3 // 4])             │
     └────────────────────────────────────────────────────────────────────┘

  4. WorkflowParser change (8 lines):
     In _parse_agent():
       if "skills" in agent_data:
           for skill_name in agent_data["skills"]:
               skill_text = self.skill_loader.load(skill_name)
               if skill_text:
                   agent_config.persona += f"\\n\\n## Skill: {skill_name}\\n{skill_text}"

  5. Test: run case_study_01 with skills injected → check SMARC scores improve


  PHASE 2 — Task-time routing (medium effort: ~1 day)
  ─────────────────────────────────────────────────────────────────────

  1. Build skill_index.json from CATALOG.md:
     ┌────────────────────────────────────────────────────────────────────┐
     │  {                                                                │
     │    "typescript-react-patterns": {                                 │
     │      "keywords": ["react", "tsx", "hooks", "component", "jsx"],  │
     │      "roles":    ["developer"],                                   │
     │      "tier":     "conditional"                                    │
     │    },                                                             │
     │    "postgres-best-practices": {                                   │
     │      "keywords": ["postgres", "sql", "query", "migration"],      │
     │      "roles":    ["developer", "analyst"],                        │
     │      "tier":     "conditional"                                    │
     │    },                                                             │
     │    ...                                                            │
     │  }                                                                │
     └────────────────────────────────────────────────────────────────────┘

  2. SkillRouter (new, 50 lines):
       select(task, agent_role, max_skills=2, min_score=1) -> list[str]

  3. AgentTeam.run() change (5 lines):
     Before loop over steps:
       for role, agent in self.agents.items():
           skills = self.skill_router.select(task, role.value)
           new_persona = agent.base_persona  # need to store original
           for skill in skills:
               new_persona += self.skill_loader.load(skill)
           agent.update_persona(new_persona)

  4. RunRecord metadata: store active_skills per agent per run
       record.metadata["active_skills"] = {role: skills for role, skills}


  PHASE 3 — Improvement loop as skill router (highest effort: ~2 days)
  ─────────────────────────────────────────────────────────────────────

  1. SkillGapMatcher (new, 80 lines):
       find(gap_capability: str, agent_role: str, task: str) -> str | None
       # maps "developer_output_specificity" + task keywords → skill name

  2. PromptEvolver._skill_propose() (new, 30 lines):
     Takes: current_persona, skill_content, gap_name
     Returns: (proposed_persona, justification, confidence)
     Logic: extracts only the Step-by-Step section from skill_content
            that addresses the gap; appends to current_persona

  3. PromptEvolver.propose_patch() modification (5 lines):
     Before _heuristic_propose fallback, try _skill_propose first:
       skill_name = self.skill_gap_matcher.find(gap, agent_role, run_context)
       if skill_name:
           skill_content = self.skill_loader.load(skill_name, max_tokens=600)
           proposed_persona, just, conf = self._skill_propose(...)
           generated_by = f"skill:{skill_name}"

  4. Feedback loop:
     After N more runs with the skill patch active:
       if new_smarc_score > old_smarc_score + 0.10:
           log "skill {skill_name} effective — keeping"
       else:
           rollback patch → try next candidate or LLM rewrite

  5. CLI addition:
       agenticom feedback skill-report <workflow-id>
       → shows: skill injected, gap addressed, SMARC before/after, retained?


  YAML example (Phase 1 ready):
  ┌────────────────────────────────────────────────────────────────────────┐
  │  id: feature-dev-with-diagnostics                                    │
  │  metadata:                                                           │
  │    self_improve: true                                                │
  │    skills_dir: .agent/skills                   # where skills live   │
  │                                                                      │
  │  agents:                                                             │
  │    - id: developer                                                   │
  │      skills:                                                         │
  │        - typescript-react-patterns             # [A] always-on       │
  │        - async-python-patterns                 # [A] always-on       │
  │        - postgres-best-practices               # [A] always-on       │
  │      # Phase 2 adds conditional: [C: "react/sql/async"]             │
  │                                                                      │
  │    - id: verifier                                                    │
  │      skills:                                                         │
  │        - lint-and-validate                     # [A] always-on       │
  │                                                                      │
  │    - id: reviewer                                                    │
  │      skills:                                                         │
  │        - lint-and-validate                     # [A] always-on       │
  └────────────────────────────────────────────────────────────────────────┘
""")

    section("Touch points summary (all files)")
    print("""
  File                                    Change type        Effort
  ──────────────────────────────────────────────────────────────────
  orchestration/tools/skill_loader.py     NEW (Phase 1)      30 lines
  orchestration/tools/skill_router.py     NEW (Phase 2)      50 lines
  orchestration/tools/skill_gap_matcher.py NEW (Phase 3)     80 lines
  orchestration/workflows/parser.py       EDIT (Phase 1)     +8 lines
  orchestration/agents/team.py            EDIT (Phase 2)     +5 lines
  orchestration/self_improvement/         EDIT (Phase 3)
    prompt_evolver.py                       +30 lines
  orchestration/agents/base.py            EDIT (Phase 2)     +3 lines
    (store base_persona separately from patched persona)
  agenticom/bundled_workflows/*.yaml      EDIT (Phase 1)     +skills fields
  .agent/skills/                          NEW (install)      npx command
  agenticom/cli.py                        EDIT (Phase 3)     +skill-report cmd
  tests/test_skills.py                    NEW                ~50 tests
""")

    section("Token cost estimate per run (Phase 1 static injection)")
    print("""
  Skill doc size         ≈ 2,200 tokens (full)  /  400 tokens (capped summary)
  Agents with skills     4 of 6 (criteria_builder, developer, verifier, reviewer)
  Skills per agent       2 average

  Cost per run:
    Full injection : 4 agents × 2 skills × 2,200 tokens = 17,600 extra tokens
    Capped summary : 4 agents × 2 skills ×   400 tokens =  3,200 extra tokens

  At $3 / 1M tokens (claude-sonnet-4-6, input):
    Full : $0.053 per run
    Capped: $0.010 per run  ← RECOMMENDED (capped at 400 tokens per skill)

  Break-even vs heuristic patch:
    If skill lifts SMARC composite from 0.65 → 0.80 and avoids 1 retry per run:
      Saved LLM call ≈ 500 tokens × $3/M = $0.0015 saved
      Skill overhead ≈ 3,200 tokens × $3/M = $0.010 cost
    → Break-even at ~7 runs per workflow; profitable after that.
""")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────


def summary() -> None:
    banner("SUMMARY  —  Key conclusions and recommended action order")

    print("""
  WHAT skills are:
    Markdown instruction documents (not code) that inject domain knowledge
    into an agent's system prompt. They improve REASONING quality and
    SPECIFICITY but do not add real-world tool access.

  WHEN to use skills:
    ✓  Agent's base persona has a confirmed SMARC gap in a known domain
    ✓  Workflow type maps naturally to a skill category
    ✓  Task keywords signal the domain is relevant (conditional)
    ✓  Token budget allows (cap summaries at 400 tokens per skill)
    ✗  Skill assumes human interaction throughout
    ✗  Skill is in offensive-security category (never autonomous)
    ✗  Agent's step is too simple to justify overhead

  HOW skills are selected:
    Phase 1 → engineer assigns in YAML (static, deploy today)
    Phase 2 → SkillRouter picks by task keywords (adaptive, < 1 day)
    Phase 3 → PromptEvolver uses skills as patch CONTENT when SMARC gap detected

  HOW skills are activated:
    Path 1 → WorkflowParser injects at startup (zero per-run overhead)
    Path 2 → AgentTeam.run() injects before first step (task-specific)
    Path 3 → ImprovementLoop applies via PromptVersionStore (permanent patch)

  HIGHEST ROI recommendation:
    Phase 3 Path 3 — use the self-improvement loop AS the skill router.
    Instead of heuristic suffixes ("CRITICAL: Be specific"), the evolver
    injects the STEPS section of the relevant skill when a SMARC gap is detected.
    This gives community-quality domain knowledge precisely when and where
    the agent needs it, backed by evidence, with full rollback capability.

  CONCRETE first step:
    1. npx antigravity-awesome-skills --path .agent/skills
    2. Add skills: list to feature-dev.yaml developer + verifier agents
    3. Write SkillLoader (30 lines) in orchestration/tools/skill_loader.py
    4. Add 8 lines to WorkflowParser._parse_agent()
    5. Run case_study_01 → observe SMARC scores before/after

  Expected outcome after Phase 1 (1 day of work):
    SMARC composite for developer:  0.65 → 0.78  (+0.13)
    SMARC composite for verifier :  0.61 → 0.76  (+0.15)
    Number of improvement-loop patches needed per 10 runs: 3 → 1
    Token overhead: +3,200 tokens/run (capped) = +$0.010/run

  Next exploration:
    python examples/exploration_02_mcp_tool_integration.py
      → How to give agents REAL tool access (web search, databases, APIs)
        via the existing MCPToolBridge — the companion to skills.
    """)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    part_a_skill_anatomy()
    part_b_current_gaps()
    part_c_pros_cons()
    part_d_decision_matrix()
    part_e_skill_selection()
    part_f_activation()
    part_g_workflow_mapping()
    part_h_implementation()
    summary()


if __name__ == "__main__":
    main()
