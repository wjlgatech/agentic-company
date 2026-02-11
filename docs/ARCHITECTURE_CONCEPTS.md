# Agent Architecture: Concepts & Connections

## The Core Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW                                        │
│  "A sequence of steps to accomplish a complex task"                         │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Step 1  │───▶│ Step 2  │───▶│ Step 3  │───▶│ Step 4  │───▶│ Step 5  │  │
│  │ (plan)  │    │ (build) │    │(verify) │    │ (test)  │    │(review) │  │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ AGENT   │    │ AGENT   │    │ AGENT   │    │ AGENT   │    │ AGENT   │  │
│  │(planner)│    │(developer)   │(verifier)│   │(tester) │    │(reviewer)│  │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼────────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │                            SKILLS                                    │
   │  "Knowledge that teaches agents HOW to do things"                   │
   │                                                                      │
   │  • Prompts & personas        • Best practices                       │
   │  • Domain knowledge          • Output formats                       │
   │  • Decision frameworks       • Error handling                       │
   └──────────────────────────────────┬──────────────────────────────────┘
                                      │
                                      ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │                            TOOLS                                     │
   │  "Capabilities that let agents DO things in the real world"         │
   │                                                                      │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
   │  │ PubMed   │  │ Ahrefs   │  │ GitHub   │  │ Slack    │            │
   │  │ search   │  │ SEO data │  │ PR/Issue │  │ message  │            │
   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
   │                                                                      │
   │  Provided via MCP (Model Context Protocol) servers                  │
   └─────────────────────────────────────────────────────────────────────┘
```

---

## Concept Definitions

### 1. AGENT
**What:** An AI entity with a specific role, persona, and capabilities.

**Characteristics:**
- Has a **role** (planner, developer, researcher, etc.)
- Has a **prompt/persona** that defines behavior
- Has access to **tools** (or should have)
- Can **execute** tasks via an LLM

**Example:**
```yaml
agent:
  id: researcher
  name: "Research Specialist"
  role: "Deep research and literature review"
  prompt: |
    You are an expert researcher. Your job is to find
    and synthesize information from multiple sources.
  tools: [web_search, literature_search]
```

**Analogy:** An employee with a job title and skills.

---

### 2. SKILL
**What:** Packaged knowledge/instructions that teach agents HOW to do something.

**Characteristics:**
- **Declarative** - describes what to do, not how to execute
- **Reusable** - can be applied to multiple agents
- **Domain-specific** - contains expertise in a particular area
- **Instructions** - tells the LLM how to behave

**Example:**
```markdown
# SKILL.md - Research Skill
When researching a topic:
1. Start with broad searches
2. Identify key papers/sources
3. Cross-reference claims
4. Synthesize findings
5. Cite all sources
```

**Analogy:** A training manual or playbook.

---

### 3. TOOL
**What:** An executable capability that performs real-world actions.

**Characteristics:**
- **Executable** - actually runs code/API calls
- **Has inputs/outputs** - defined schema
- **External** - connects to real services
- **Provided by MCP** - standardized protocol

**Example:**
```python
# PubMed MCP Tool
tool: search_articles
inputs:
  query: "CAR-T therapy resistance"
  max_results: 10
outputs:
  articles: [{title, authors, abstract, pmid, doi}]
```

**Analogy:** A power tool or software application.

---

### 4. WORKFLOW
**What:** A sequence of steps that accomplishes a complex task.

**Characteristics:**
- **Sequential** - steps execute in order
- **Context passing** - each step gets previous outputs
- **Multi-agent** - different agents handle different steps
- **Stateful** - tracks progress, can resume

**Example:**
```yaml
workflow: feature-dev
steps:
  - step: plan
    agent: planner
    input: "{{task}}"
    output: plan_document

  - step: implement
    agent: developer
    input: "{{plan_document}}"
    output: code_changes
```

**Analogy:** An assembly line or business process.

---

### 5. EXECUTOR
**What:** The runtime component that actually runs agents.

**Characteristics:**
- **Makes LLM calls** - sends prompts, receives responses
- **Handles tools** - executes tool calls
- **Manages context** - tracks conversation history
- **Multi-backend** - can use Claude, GPT, Ollama

**Example:**
```python
executor = UnifiedExecutor(backend="claude")
result = await executor.execute(
    prompt="Research CAR-T therapy",
    tools=[pubmed_tool, web_search_tool]
)
```

**Analogy:** The engine that powers the car.

---

### 6. MCP (Model Context Protocol)
**What:** A standard protocol for connecting LLMs to external tools.

**Characteristics:**
- **Standardized** - common interface for all tools
- **Discoverable** - registry of available tools
- **Authenticated** - handles OAuth/API keys
- **Real-time** - live data, not training data

**Example:**
```
MCP Server: pubmed.mcp.claude.com
Tools:
  - search_articles
  - get_article_metadata
  - find_related_articles
```

**Analogy:** USB standard for connecting peripherals.

---

## How They Connect

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                 │
│  "Research CAR-T therapy resistance and write a review"            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          WORKFLOW                                    │
│  Parses request → Creates execution plan → Manages state            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  STEP 1  │      │  STEP 2  │      │  STEP 3  │
        │ Research │      │ Analyze  │      │  Write   │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  AGENT   │      │  AGENT   │      │  AGENT   │
        │researcher│      │ analyst  │      │  writer  │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             │ Uses SKILL      │ Uses SKILL      │ Uses SKILL
             │ (research       │ (analysis       │ (writing
             │  methodology)   │  framework)     │  guidelines)
             │                 │                 │
             ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ EXECUTOR │      │ EXECUTOR │      │ EXECUTOR │
        │ (Claude) │      │ (Claude) │      │ (Claude) │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             │ Calls TOOLS     │ Calls TOOLS     │ Calls TOOLS
             │ via MCP         │ via MCP         │ via MCP
             │                 │                 │
             ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ PubMed   │      │ Data     │      │ Document │
        │ bioRxiv  │      │ Analysis │      │ Export   │
        │ Scholar  │      │ Tools    │      │ Tools    │
        └──────────┘      └──────────┘      └──────────┘
```

---

## The Key Insight

### Without Tools (Current Agenticom)
```
User: "Research competitors"
Agent: *thinks really hard*
Output: "Based on my training data, competitors might include..."
Reality: HALLUCINATION - no real data
```

### With Tools (via MCP)
```
User: "Research competitors"
Agent: *calls Similarweb MCP tool*
Tool: *fetches real traffic data*
Output: "Competitor A has 2.3M monthly visits, 45% from search..."
Reality: REAL DATA from live API
```

---

## Comparison Table

| Concept | What it IS | What it DOES | Analogy |
|---------|-----------|--------------|---------|
| **Agent** | AI entity with role | Thinks, decides, acts | Employee |
| **Skill** | Packaged knowledge | Teaches how to behave | Training manual |
| **Tool** | Executable capability | Performs real actions | Power tool |
| **Workflow** | Sequence of steps | Orchestrates process | Assembly line |
| **Executor** | Runtime engine | Runs LLM + tools | Car engine |
| **MCP** | Protocol standard | Connects to services | USB standard |

---

## Why MCP Changes Everything

**Before MCP:**
- Each tool had custom integration
- No standardization
- Hard to discover available tools
- Authentication was a mess

**After MCP:**
- Standard protocol for all tools
- Central registry for discovery
- Unified auth handling
- Easy to add new tools

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PubMed    │     │   Ahrefs    │     │   Slack     │
│  (custom)   │     │  (custom)   │     │  (custom)   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────┴──────┐
                    │    MCP      │
                    │  Protocol   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   Agent     │
                    │  Executor   │
                    └─────────────┘
```

Now the agent can use ANY MCP tool with the same interface.
