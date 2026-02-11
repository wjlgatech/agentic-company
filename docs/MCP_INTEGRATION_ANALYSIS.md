# Critical Analysis: MCP Tool Integration for Agenticom

**Date:** 2026-02-11
**Question:** Can Claude Code / OpenClaw / Nanobot recommend and provide the right MCP tools for Agenticom?

---

## Executive Summary

**Answer: YES, but with integration work required.**

| Platform | MCP Capability | Tool Discovery | Tool Provision | Integration Effort |
|----------|---------------|----------------|----------------|-------------------|
| **Claude Code** | ✅ Native MCP support | ✅ `mcp-registry` search | ✅ Direct tool calls | Low |
| **OpenClaw** | ✅ `mcporter` skill | ⚠️ Manual config | ✅ Via mcporter CLI | Medium |
| **Nanobot** | ❓ Unknown | ❓ Unknown | ❓ Unknown | Unknown |

---

## Part 1: The Gap Analysis

### What Agenticom Declares vs What Exists

| Agenticom Placeholder | MCP Equivalent | Status |
|----------------------|----------------|--------|
| `web_search` | Ahrefs, Similarweb, WebSearch | ✅ Available |
| `social_api` | LunarCrush, Twitter API | ✅ Available |
| `data_analysis` | S&P Global, Amplitude | ✅ Available |
| `text_generation` | Native LLM | ✅ Built-in |
| `image_generation` | DALL-E, Gamma | ✅ Available |
| `analytics` | Amplitude, Windsor.ai | ✅ Available |
| `reporting` | Gamma, Custom | ⚠️ Partial |
| `messaging` | Slack, Discord connectors | ✅ Available |

### Example: Biomedical Research Workflow

```yaml
# What Agenticom needs
agent: researcher
task: "Research CAR-T therapy resistance"
tools: [literature_search, citation_manager]

# What MCP provides
- PubMed MCP: search_articles, get_article_metadata, find_related_articles
- bioRxiv MCP: search_biorxiv_publications, get_preprint
- Consensus MCP: search (scientific papers)
- Scholar Gateway: Semantic Search
```

### Example: Marketing Campaign Workflow

```yaml
# What Agenticom needs
agent: social-intel
task: "Find pain points on social media"
tools: [web_search, social_api]

# What MCP provides
- LunarCrush: Topic, Topic_Posts, Topic_Time_Series (social data)
- Similarweb: get-websites-traffic-and-engagement, get-websites-similar-sites-agg
- Ahrefs: brand-radar-mentions-overview, keyword-suggestions
```

### Example: Startup Validation Workflow

```yaml
# What Agenticom needs
agent: analyst
task: "Analyze market and competitors"
tools: [market_research, competitor_analysis]

# What MCP provides
- Harmonic: enrich_company, get_saved_search_companies_results
- S&P Global: get_company_summary_from_identifiers, get_info_from_identifiers
- Vibe Prospecting: fetch-businesses-events, enrich-business
- HubSpot: search_crm_objects
```

---

## Part 2: Platform Capabilities

### Claude Code (This Environment)

**Strengths:**
- ✅ Native MCP tool calling via `mcp__*` functions
- ✅ `mcp-registry` for dynamic tool discovery
- ✅ `suggest_connectors` for user connection prompts
- ✅ Direct execution without intermediate layers

**How It Works:**
```python
# 1. Search for relevant tools
mcp__mcp-registry__search_mcp_registry(keywords=["pubmed", "research"])

# 2. Suggest connection to user
mcp__mcp-registry__suggest_connectors(directoryUuids=[...])

# 3. Once connected, call tools directly
mcp__PubMed__search_articles(query="CAR-T resistance solid tumors")
```

**Limitation:** User must manually connect each MCP service (OAuth/API key).

---

### OpenClaw

**Strengths:**
- ✅ `mcporter` CLI for MCP server management
- ✅ Multi-channel delivery (WhatsApp, Telegram, etc.)
- ✅ Background process management for long-running tools
- ✅ Skills system for tool instructions

**How It Works:**
```bash
# List available MCP servers
mcporter list

# Call a tool directly
mcporter call pubmed.search_articles query="CAR-T resistance"

# Or via OpenClaw skill
"Use mcporter to search PubMed for CAR-T therapy papers"
```

**Limitation:** Requires `mcporter` installation and manual server configuration.

---

### Nanobot

**Status:** Unable to evaluate - no public repository found. May be:
- An alias for OpenClaw
- A different project entirely
- A private/internal tool

---

## Part 3: Critical Evaluation

### Can They RECOMMEND Tools?

| Platform | Auto-Recommendation | How |
|----------|---------------------|-----|
| Claude Code | ✅ Yes | `search_mcp_registry` + semantic matching |
| OpenClaw | ⚠️ Partial | Skills can describe tools, but no auto-discovery |
| Agenticom | ❌ No | Just declares placeholder strings |

### Can They PROVIDE Tools?

| Platform | Tool Provision | How |
|----------|---------------|-----|
| Claude Code | ✅ Yes | Direct MCP function calls |
| OpenClaw | ✅ Yes | Via mcporter or native extensions |
| Agenticom | ❌ No | Needs executor with tool bindings |

### The Missing Link

**Agenticom currently has no mechanism to:**
1. Parse `tools: [web_search]` from YAML
2. Query an MCP registry for matching tools
3. Bind those tools to the agent's executor
4. Execute tool calls during workflow steps

---

## Part 4: Proposed Integration Architecture

### Option A: Claude Code as Orchestrator

```
┌──────────────────────────────────────────────────────────┐
│                    Claude Code                            │
│  (Has MCP registry access + direct tool calling)         │
└─────────────────────────┬────────────────────────────────┘
                          │ Reads workflow YAML
                          ▼
┌──────────────────────────────────────────────────────────┐
│                 Agenticom Workflow                        │
│  tools: [web_search, social_api, literature_search]      │
└─────────────────────────┬────────────────────────────────┘
                          │ Claude Code maps to MCP
                          ▼
┌──────────────────────────────────────────────────────────┐
│  web_search → Ahrefs MCP                                 │
│  social_api → LunarCrush MCP                             │
│  literature_search → PubMed MCP                          │
└──────────────────────────────────────────────────────────┘
```

**Pros:** No code changes to Agenticom needed
**Cons:** Claude Code becomes the executor, not Agenticom

---

### Option B: Agenticom MCP Integration

```python
# New file: orchestration/tools/mcp_bridge.py

class MCPToolBridge:
    """Bridge between Agenticom tool declarations and MCP servers."""

    TOOL_MAPPING = {
        "web_search": ["ahrefs", "similarweb"],
        "social_api": ["lunarcrush", "twitter"],
        "literature_search": ["pubmed", "biorxiv", "consensus"],
        "market_research": ["harmonic", "spglobal"],
        "data_analysis": ["amplitude", "windsor"],
    }

    def resolve_tools(self, declared_tools: list[str]) -> list[MCPTool]:
        """Map Agenticom tool names to actual MCP servers."""
        resolved = []
        for tool in declared_tools:
            if tool in self.TOOL_MAPPING:
                for mcp_server in self.TOOL_MAPPING[tool]:
                    if self.is_connected(mcp_server):
                        resolved.append(self.get_tool(mcp_server))
        return resolved

    async def execute_tool(self, tool_name: str, **kwargs):
        """Execute an MCP tool call."""
        # Use mcporter or direct MCP client
        pass
```

**Pros:** Agenticom becomes self-sufficient
**Cons:** Significant development effort

---

### Option C: OpenClaw as Tool Provider

```
┌──────────────────────────────────────────────────────────┐
│                      OpenClaw                             │
│  (Multi-channel + mcporter + skill system)               │
└─────────────────────────┬────────────────────────────────┘
                          │ Receives: "Use agenticom marketing-campaign"
                          ▼
┌──────────────────────────────────────────────────────────┐
│              Agenticom Skill (SKILL.md)                   │
│  + Enhanced with MCP tool recommendations                │
└─────────────────────────┬────────────────────────────────┘
                          │ Before execution, OpenClaw:
                          │ 1. Reads workflow YAML
                          │ 2. Identifies needed tools
                          │ 3. Connects via mcporter
                          ▼
┌──────────────────────────────────────────────────────────┐
│  mcporter call pubmed.search_articles ...                │
│  mcporter call lunarcrush.Topic ...                      │
└──────────────────────────────────────────────────────────┘
```

**Pros:** Leverages existing OpenClaw infrastructure
**Cons:** OpenClaw must understand Agenticom workflows

---

## Part 5: Test Results

### Test 1: MCP Registry Discovery

```python
# Searched: ["web", "search", "scrape", "browser"]
# Found: Similarweb, Ahrefs, Day AI, Harmonic...

# Searched: ["research", "academic", "literature", "pubmed"]
# Found: PubMed, Consensus, bioRxiv, Scholar Gateway...

# Searched: ["social", "media", "twitter", "analytics"]
# Found: LunarCrush, Amplitude, Windsor.ai...
```

**Result:** ✅ MCP registry has tools for ALL Agenticom placeholder categories.

### Test 2: Tool Mapping Feasibility

| Agenticom Tool | MCP Match | Confidence |
|----------------|-----------|------------|
| `web_search` | Ahrefs `batch-analysis` | ⭐⭐⭐⭐⭐ |
| `social_api` | LunarCrush `Topic_Posts` | ⭐⭐⭐⭐⭐ |
| `literature_search` | PubMed `search_articles` | ⭐⭐⭐⭐⭐ |
| `competitor_analysis` | Similarweb `get-websites-similar-sites-agg` | ⭐⭐⭐⭐ |
| `market_research` | Harmonic `enrich_company` | ⭐⭐⭐⭐ |
| `data_analysis` | S&P Global, Amplitude | ⭐⭐⭐⭐ |

**Result:** ✅ High-confidence mappings exist for all categories.

### Test 3: Current Integration Status

```bash
# Agenticom workflow run with tools
$ agenticom workflow run marketing-campaign -i "Miami real estate"

# Current behavior:
# - Reads tools: [web_search, social_api]
# - Does NOTHING with them
# - LLM hallucinates data instead

# Desired behavior:
# - Reads tools: [web_search, social_api]
# - Queries MCP registry
# - Connects to Ahrefs, LunarCrush
# - Executes real API calls
# - Returns actual data to agent
```

**Result:** ❌ No integration exists today.

---

## Part 6: Recommendations

### Immediate (No Code)

Use Claude Code directly as the orchestrator:

```
User: "Research CAR-T therapy resistance mechanisms"

Claude Code:
1. Calls mcp__PubMed__search_articles(query="CAR-T resistance solid tumors 2020-2024")
2. Gets real papers with citations
3. Synthesizes findings
4. No Agenticom needed for research tasks
```

**When to use:** Research tasks, one-off analyses

### Short-Term (Light Integration)

Create an MCP tool mapping file for Agenticom:

```yaml
# mcp_tools.yaml
tool_mappings:
  web_search:
    primary: ahrefs
    fallback: similarweb

  literature_search:
    primary: pubmed
    fallback: [biorxiv, consensus]

  social_api:
    primary: lunarcrush
```

**Effort:** 1-2 days

### Medium-Term (Full Integration)

Build `MCPToolBridge` class in Agenticom that:
1. Reads tool declarations from workflow YAML
2. Queries available MCP servers (via mcporter or direct)
3. Binds tools to agent executors
4. Handles tool results in workflow context

**Effort:** 1-2 weeks

---

## Part 7: Verdict

### Does MCP Solve Agenticom's Tool Problem?

**YES** - The tools exist. The gap is integration.

### Can Claude Code Recommend and Provide Tools?

**YES** - It has `mcp-registry` search and direct tool calling.

### Can OpenClaw Recommend and Provide Tools?

**PARTIALLY** - Has `mcporter` for execution, but no auto-recommendation.

### What's Missing?

1. **Tool Resolution Layer** - Map Agenticom placeholders → MCP servers
2. **Connection Management** - Handle OAuth/API keys for MCP services
3. **Result Injection** - Feed MCP results into agent context
4. **Workflow Awareness** - Know which tools each step needs

---

## Appendix: Available MCP Tools by Category

### Research & Literature
- PubMed: `search_articles`, `get_article_metadata`, `find_related_articles`
- bioRxiv: `search_biorxiv_publications`, `get_preprint`
- Consensus: `search`
- Scholar Gateway: `Semantic Search`

### Web & SEO
- Ahrefs: 61+ tools including `batch-analysis`, `keyword-suggestions`
- Similarweb: 22+ tools for traffic, engagement, competitors

### Social & Analytics
- LunarCrush: `Topic`, `Topic_Posts`, `Topic_Time_Series`
- Amplitude: `query_dataset`, `query_charts`, `query_metric`

### Business Intelligence
- S&P Global: Company data, financials, relationships
- Harmonic: Company enrichment, people search
- HubSpot: CRM data access

### Content Creation
- Gamma: `generate` presentations, docs, sites
- BioRender: Scientific icons and templates

---

*Analysis completed 2026-02-11*
