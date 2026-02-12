# Smart Refiner: LLM-Based Interview → Coherent Prompt Synthesis

## The Problem

Previous approaches produced **mechanical, template-filled outputs**:

```
## Role
You are a B2B Marketing Strategy Assistant...

## Key Details Extracted:
- **Business Type**: B2B SaaS company
- **Challenge**: Lead generation struggles
...
```

**Issues:**
- Looks like a form was filled out
- Mechanical bullet points stacking extracted info
- No strategic depth or domain wisdom
- Generic instructions that could apply to anything

## The Solution: Smart Refiner

The Smart Refiner takes a fundamentally different approach:

1. **LLM conducts thoughtful interview** - Asks contextually relevant questions, not generic ones
2. **LLM synthesizes coherent prompt** - Writes natural prose like a human expert would
3. **Output reads like expert-written brief** - No templates, no mechanical bullet points

### Example Output

```
You are a B2B growth strategist who has helped dozens of SaaS companies break
through their lead generation plateaus. You combine deep expertise in demand
generation with a practical, results-focused mindset.

Your client is a B2B SaaS company that's hit a wall with their current marketing
approach. They've invested in content marketing and LinkedIn outreach, but the
results have been disappointing—low engagement on their content and poor quality
leads from their outreach efforts...

First, understand that low engagement usually signals a targeting or messaging
problem, not just a distribution problem...

When you provide recommendations, be specific enough to act on. Don't just say
"improve your content strategy"—tell them exactly what kind of content works...
```

**Notice:**
- Natural prose flow (no ## sections)
- Specific persona with depth ("helped dozens of SaaS companies")
- Strategic insights woven in ("low engagement usually signals...")
- Actionable guidance integrated ("tell them exactly what kind of...")
- Reads like a thoughtful brief, not a filled form

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SMART REFINER FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

User Input: "I need help with marketing"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INTERVIEWER LLM                                                     │
│  ─────────────────                                                   │
│  • Analyzes conversation context                                     │
│  • Assesses understanding confidence                                 │
│  • Identifies critical gaps                                          │
│  • Generates contextual follow-up questions                         │
│  • Decides when enough info gathered                                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MULTI-TURN CONVERSATION                                             │
│  ─────────────────────────                                           │
│  Turn 1: "What type of business? Who's your audience?"              │
│  Turn 2: "What have you tried? What's not working?"                 │
│  Turn 3: "Got it, I understand. Ready to proceed?"                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ User confirms
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SYNTHESIZER LLM                                                     │
│  ────────────────                                                    │
│  • Reviews full conversation                                         │
│  • Sets appropriate expert persona (not generic "assistant")         │
│  • Weaves context into natural narrative                             │
│  • Embeds domain-specific wisdom                                     │
│  • Writes coherent, human-quality prompt                            │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
               COHERENT SYNTHESIZED PROMPT
```

## Usage

### Async API

```python
import anthropic
from orchestration.tools import SmartRefiner

client = anthropic.AsyncAnthropic()

async def call_claude(system: str, user: str) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text

# Create refiner
refiner = SmartRefiner(llm_call=call_claude, max_questions=4)
session_id = refiner.create_session()

# Multi-turn conversation
result = await refiner.process(session_id, "I need help with marketing")
print(result["response"])  # Follow-up question

result = await refiner.process(session_id, "B2B SaaS, struggling with lead gen")
print(result["response"])  # Another question or ready to proceed

result = await refiner.process(session_id, "yes, proceed")
print(result["final_prompt"])  # Coherent, synthesized prompt!
```

### Sync API

```python
from orchestration.tools import SyncSmartRefiner

def call_llm(system: str, user: str) -> str:
    # Your sync LLM call here
    pass

refiner = SyncSmartRefiner(llm_call=call_llm)
session_id = refiner.create_session()
result = refiner.process(session_id, "I need help with marketing")
```

## Key Components

### Interview System Prompt

The `get_interviewer_prompt()` function returns a prompt that instructs the LLM to:
- Understand what the user REALLY wants
- Identify critical vs helpful gaps
- Ask ONE question at a time (not a list)
- Max 3-4 questions total
- Be ready at 70%+ confidence with no critical gaps

### Synthesizer System Prompt

The `SYNTHESIZER_PROMPT` instructs the LLM to write a system prompt that:
1. Sets a **specific expert persona** (not generic "assistant")
2. Establishes context as **natural narrative** (not bullet points)
3. Defines **clear objectives** in order of priority
4. Specifies the **approach** with domain wisdom
5. Sets **success criteria**
6. Adds **appropriate guardrails**

**Critical rules enforced:**
- Write naturally, as if a human expert wrote it
- NO template sections like "## Key Details Extracted:"
- NO mechanical bullet points listing extracted fields
- Make it feel like a thoughtful brief, not a filled form

## Quality Comparison

| Aspect | Old (Template) | New (Smart Synthesis) |
|--------|----------------|----------------------|
| Structure | ## Headers, bullet points | Natural prose paragraphs |
| Persona | Generic "assistant" | Specific expert with depth |
| Context | Extracted bullet list | Woven into narrative |
| Insights | None | Domain-specific wisdom |
| Guidance | Generic instructions | Actionable specifics |
| Feel | Form that was filled | Expert-written brief |
| Coherence | LOW | HIGH |

## Files

- `orchestration/tools/smart_refiner.py` - Main implementation
- `experiments/smart_refiner_demo.py` - Demo with mock LLM
- `experiments/prompt_quality_comparison.py` - Quality comparison
- `docs/SMART_REFINER.md` - This documentation

## Design Principles

1. **Interview, don't interrogate** - Ask thoughtful questions, not a checklist
2. **Synthesize, don't stack** - Create coherent prose, not bullet point lists
3. **Expert persona, not generic** - "B2B growth strategist" not "assistant"
4. **Weave context naturally** - "Your client is a..." not "- **Client**: ..."
5. **Embed wisdom** - Include strategic insights, not just extracted facts
6. **Respect their time** - Max 3-4 questions, then proceed with what you have
