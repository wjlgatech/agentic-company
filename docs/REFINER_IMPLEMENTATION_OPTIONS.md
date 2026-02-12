# Intent Refiner Implementation Options

## Three Approaches Compared

| Aspect | Rule-Based | LLM-Based | Hybrid (Recommended) |
|--------|------------|-----------|----------------------|
| **Speed** | ⚡ ~1ms | 🐢 ~1-3s | ⚡ Fast for simple, LLM for complex |
| **Cost** | 💰 Free | 💸 $0.01-0.10/call | 💵 Minimal |
| **Accuracy** | 📊 70-80% | 📊 90-95% | 📊 90%+ |
| **Nuance** | ❌ Poor | ✅ Excellent | ✅ Good |
| **Consistency** | ✅ 100% | ⚠️ 80-90% | ✅ High |
| **Maintenance** | 🔧 High (manual rules) | 🔧 Low | 🔧 Medium |

## Architecture Comparison

### Option 1: Pure Rule-Based (Current)

```
User Input → Regex/Keywords → Classification → Template Response
```

**Pros:**
- Instant response
- No API costs
- Deterministic

**Cons:**
- Can't understand nuance ("I guess maybe we could try marketing?")
- Requires manual keyword updates
- Limited entity extraction

### Option 2: Pure LLM

```
User Input → LLM Analysis → LLM Response Generation → Output
```

**Pros:**
- Excellent understanding
- Handles novel phrasings
- Extracts complex entities

**Cons:**
- Slow (1-3 seconds per turn)
- Expensive at scale
- Can be inconsistent

### Option 3: Hybrid (Recommended)

```
User Input
    │
    ▼
┌─────────────────┐
│ Quick Patterns  │ ← "yes", "proceed", "change" - NO LLM needed
│ (Rules)         │
└────────┬────────┘
         │ Complex input
         ▼
┌─────────────────┐
│ LLM Analysis    │ ← Extract entities, classify, assess readiness
│ (Structured)    │    JSON output for reliability
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Response    │ ← Generate natural, conversational response
│ (Natural)       │    OR use templates for common cases
└─────────────────┘
```

**Pros:**
- Fast for simple interactions (acceptance, refinement)
- Accurate for complex understanding
- Cost-efficient (LLM only when needed)
- Natural responses

## When to Use LLM vs Rules

### Use Rules (Fast, Free):

| Scenario | Pattern | Action |
|----------|---------|--------|
| User accepts | "yes", "proceed", "looks good" | → Complete session |
| User refines | "change", "actually", "add" | → Enter refine mode |
| Simple greeting | "hi", "hello" | → Greeting response |
| Help request | "help", "?" | → Show help |

### Use LLM (Accurate, Paid):

| Scenario | Why LLM | Output |
|----------|---------|--------|
| Initial analysis | Understand nuance, context | JSON structure |
| Entity extraction | "Our B2B SaaS startup" → ["B2B", "SaaS", "startup"] | Structured data |
| Readiness assessment | Is there enough info? | Score + missing items |
| Question generation | Natural, relevant questions | Conversational text |
| Final prompt | Preserve ALL specifics | Optimized prompt |

## LLM System Prompts

### Analysis Prompt (Structured Output)

```
You are an Intent Analysis AI. Analyze the user's request and return JSON:

{
  "task_type": "analysis|creation|...",
  "domain": "business|technical|...",
  "entities": ["specific things mentioned"],
  "goals": ["what they want to achieve"],
  "readiness_score": 0.0-1.0,
  "suggested_questions": [...],
  "understanding_summary": "one sentence"
}

RULES:
1. Extract SPECIFIC details - don't generalize
2. readiness_score >= 0.8 means ready to proceed
3. Max 2-3 suggested questions
```

### Response Generation Prompt (Natural Output)

```
Generate a natural, conversational response based on analysis.

If readiness < 0.8:
"I can help with [understanding]. To get this right:
• [Question]?
• [Question]?
Or just tell me more!"

If readiness >= 0.8:
"Got it! Here's my approach:
1. [Step]
2. [Step]
Ready to proceed?"
```

### Prompt Engineering Prompt

```
Generate an optimized system prompt that:
1. Sets appropriate role for {domain}
2. Includes ALL specific details from user
3. Defines clear success criteria
4. Adds domain-appropriate guardrails

User request: {full_context}
Entities: {entities}
Goals: {goals}
Constraints: {constraints}
```

## Cost Optimization Strategies

### 1. Caching

```python
# Cache analysis results by input hash
cache_key = hashlib.md5(user_input.encode()).hexdigest()
if cache_key in self._cache:
    return self._cache[cache_key]
```

### 2. Tiered Models

```python
# Use cheaper model for simple tasks
if is_simple_classification(input):
    model = "gpt-3.5-turbo"  # $0.002/1K tokens
else:
    model = "gpt-4"           # $0.03/1K tokens
```

### 3. Batch Analysis

```python
# Combine multiple small analyses into one call
if len(pending_analyses) >= 3:
    batch_result = await llm_batch_analyze(pending_analyses)
```

### 4. Progressive Disclosure

```python
# Start with rules, escalate to LLM only if needed
if rule_confidence > 0.9:
    return rule_based_response()
else:
    return await llm_analysis()
```

## Implementation Recommendation

For production, use the **Hybrid Approach**:

```python
class HybridRefiner:
    def process_input(self, session_id: str, user_input: str):
        # 1. Quick pattern matching (FREE, INSTANT)
        if self._is_acceptance(user_input):
            return self._handle_acceptance(session)

        if self._is_refinement(user_input):
            return self._handle_refinement(session)

        # 2. Check cache (FREE, INSTANT)
        cached = self._get_cached_analysis(user_input)
        if cached:
            return self._generate_response(cached)

        # 3. LLM analysis (PAID, 1-2s)
        analysis = await self._llm_analyze(user_input)

        # 4. Cache result
        self._cache_analysis(user_input, analysis)

        # 5. Generate response (template or LLM)
        if analysis.readiness >= 0.8:
            return self._template_draft_response(analysis)
        else:
            return await self._llm_generate_response(analysis)
```

This gives you:
- **<100ms** for simple interactions (acceptance, refinement)
- **~1-2s** for complex analysis (only when needed)
- **$0.01-0.05** per complex interaction (cached for repeat)
- **90%+ accuracy** on understanding user intent
