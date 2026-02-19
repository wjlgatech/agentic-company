# Memory Management & Ticket System Architecture

## Executive Summary

This document proposes a comprehensive ticket management system with intelligent memory management to accumulate lessons learned without context bloat.

**Key Question:** How to keep lessons learned active but NOT bloated for next tasks?

---

## 🎯 Current State

### What We Have:
- ✅ **WorkflowRun**: Tracks overall run state (id, workflow_id, status, timestamps)
- ✅ **StepResult**: Tracks individual step execution (step_id, agent, output, timestamps)
- ✅ **SQLite Storage**: Persistent state at `~/.agenticom/state.db`
- ✅ **Artifact Storage**: Generated files at `./outputs/{run_id}/`

### What's Missing:
- ❌ **Stage Timestamps**: No separate timestamps for PLAN/IMPLEMENT/VERIFY/TEST/REVIEW
- ❌ **Documentation Links**: No structured way to attach docs to stages
- ❌ **Automatic Stage Transitions**: Manual, not automatic
- ❌ **Archive System**: No way to move completed tickets
- ❌ **Memory Management**: No intelligent lesson-learned extraction
- ❌ **Context Summarization**: No way to condense past learnings

---

## 🏗️ Proposed Architecture

### 1. Enhanced Ticket/Card Model

```python
@dataclass
class TicketCard:
    """Enhanced workflow run with stage tracking."""
    id: str                    # ticket-abc123
    workflow_id: str           # feature-dev
    task: str                  # User's original request
    status: TicketStatus       # active, completed, archived

    # Stage tracking
    stages: Dict[str, StageInfo]  # {stage_name: StageInfo}
    current_stage: str         # plan, implement, verify, test, review

    # Timestamps
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    # Documentation & Artifacts
    documentation: Dict[str, List[str]]  # {stage: [doc_paths]}
    artifacts: List[str]       # [file_paths]

    # Memory/Learning
    lessons_learned: List[Lesson]
    tags: List[str]            # For retrieval

@dataclass
class StageInfo:
    """Information about a specific stage."""
    name: str                  # plan, implement, verify, test, review
    status: StepStatus         # pending, running, completed, failed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]

    # Agent that executed this stage
    agent: str

    # Stage outputs
    input_context: str
    output: str

    # Attached documentation
    documentation: List[DocumentLink]

@dataclass
class DocumentLink:
    """Link to documentation for a stage."""
    type: str                  # plan, code, test, review_feedback
    path: str                  # File path or URL
    description: str
    created_at: datetime
```

### 2. Automatic Stage Transitions

```python
class TicketManager:
    """Manages ticket lifecycle and transitions."""

    STAGE_SEQUENCE = ["plan", "implement", "verify", "test", "review"]

    def transition_stage(self, ticket_id: str) -> None:
        """Automatically move ticket to next stage."""
        ticket = self.get_ticket(ticket_id)
        current_idx = self.STAGE_SEQUENCE.index(ticket.current_stage)

        # Complete current stage
        ticket.stages[ticket.current_stage].completed_at = datetime.now()
        ticket.stages[ticket.current_stage].status = StepStatus.COMPLETED

        # Move to next stage
        if current_idx < len(self.STAGE_SEQUENCE) - 1:
            next_stage = self.STAGE_SEQUENCE[current_idx + 1]
            ticket.current_stage = next_stage
            ticket.stages[next_stage].started_at = datetime.now()
            ticket.stages[next_stage].status = StepStatus.RUNNING
        else:
            # All stages complete
            ticket.status = TicketStatus.COMPLETED
            self.extract_lessons(ticket)  # Extract before archiving

    def archive_ticket(self, ticket_id: str) -> None:
        """Move completed ticket to archive."""
        ticket = self.get_ticket(ticket_id)
        if ticket.status != TicketStatus.COMPLETED:
            raise ValueError("Can only archive completed tickets")

        ticket.status = TicketStatus.ARCHIVED
        ticket.archived_at = datetime.now()

        # Move to archive storage
        self._move_to_archive(ticket)
```

---

## 🧠 Memory Management: The Core Challenge

### The Problem:
**How do we accumulate knowledge without context explosion?**

Every workflow generates:
- 1,000-10,000 words of output per run
- Multiple artifacts (code, docs, tests)
- Implicit learnings (what worked, what failed)

After 100 runs → 1,000,000+ words of context (impossible to pass to LLM)

### Three Approaches to Consider:

---

### Approach 1: **Hierarchical Summarization** (Recommended)

**Concept:** Multi-level memory pyramid

```
Level 0 (Full Context):     Individual ticket details (archived after use)
Level 1 (Tactical Memory):  Per-workflow summaries (last 10-20 tickets)
Level 2 (Strategic Memory): Cross-workflow patterns (500-1000 words)
Level 3 (Core Principles):  Distilled best practices (100-200 words)
```

**Implementation:**

```python
class HierarchicalMemory:
    """Multi-level memory system."""

    def extract_lessons(self, ticket: TicketCard) -> List[Lesson]:
        """Extract lessons from completed ticket."""
        lessons = []

        # Analyze what worked well
        successes = self._analyze_successes(ticket)
        # Analyze what failed
        failures = self._analyze_failures(ticket)
        # Extract patterns
        patterns = self._extract_patterns(ticket)

        for insight in successes + failures + patterns:
            lesson = Lesson(
                ticket_id=ticket.id,
                workflow_id=ticket.workflow_id,
                type=insight.type,  # success, failure, pattern
                content=insight.content,
                confidence=insight.confidence,
                tags=insight.tags,
                created_at=datetime.now()
            )
            lessons.append(lesson)

        return lessons

    def get_relevant_memory(self, task: str, workflow_id: str) -> str:
        """Get relevant memory for new task."""
        # Level 3: Core principles (always included)
        core = self.get_core_principles(workflow_id)

        # Level 2: Strategic patterns (relevant to task)
        strategic = self.get_strategic_patterns(task, workflow_id)

        # Level 1: Tactical lessons (from recent similar tasks)
        tactical = self.get_tactical_lessons(task, workflow_id, limit=5)

        # Compose memory context (total ~1500 words)
        return self._compose_memory(core, strategic, tactical)

    def periodic_consolidation(self) -> None:
        """Periodically consolidate memories (run weekly)."""
        # Level 1 → Level 2: Summarize tactical to strategic
        self._consolidate_tactical_to_strategic()

        # Level 2 → Level 3: Distill strategic to core principles
        self._consolidate_strategic_to_core()

        # Archive old Level 1 memories (keep only recent)
        self._archive_old_tactical()
```

**Pros:**
- ✅ Bounded context size (always ~1500 words)
- ✅ Maintains both recent and long-term knowledge
- ✅ Automatic consolidation prevents bloat
- ✅ Retrieval is fast (indexed by tags/embeddings)

**Cons:**
- ⚠️ Requires periodic consolidation jobs
- ⚠️ May lose some nuanced details
- ⚠️ Need good summarization prompts

---

### Approach 2: **Vector Search + Retrieval**

**Concept:** Store all memories, retrieve only relevant ones

```python
class VectorMemory:
    """Embedding-based memory retrieval."""

    def __init__(self):
        self.vector_store = VectorDB()  # Chroma, Pinecone, etc.

    def store_lesson(self, lesson: Lesson) -> None:
        """Store lesson with vector embedding."""
        embedding = self.embed(lesson.content)
        self.vector_store.add(
            id=lesson.id,
            embedding=embedding,
            metadata={
                'workflow_id': lesson.workflow_id,
                'type': lesson.type,
                'tags': lesson.tags,
                'created_at': lesson.created_at
            },
            content=lesson.content
        )

    def retrieve_relevant(self, task: str, k: int = 10) -> List[Lesson]:
        """Retrieve k most relevant lessons for task."""
        query_embedding = self.embed(task)
        results = self.vector_store.similarity_search(
            query=query_embedding,
            k=k,
            filter={'archived': False}  # Only active memories
        )
        return [self._to_lesson(r) for r in results]
```

**Pros:**
- ✅ Preserves all details (nothing lost)
- ✅ Highly relevant retrieval
- ✅ Scales well (millions of memories)

**Cons:**
- ⚠️ Requires vector DB (infrastructure)
- ⚠️ Embedding costs (API calls)
- ⚠️ No automatic consolidation (memories never merge)

---

### Approach 3: **Time-Decay + Manual Curation**

**Concept:** Recent memories are detailed, old memories fade

```python
class DecayingMemory:
    """Time-based memory decay with curator."""

    def get_memory_weight(self, lesson: Lesson) -> float:
        """Calculate relevance weight with time decay."""
        age_days = (datetime.now() - lesson.created_at).days

        # Exponential decay (half-life = 30 days)
        time_weight = 0.5 ** (age_days / 30)

        # Importance boost (manual curation)
        importance_weight = lesson.importance  # 0.0 to 1.0

        # Usage boost (frequently retrieved = more important)
        usage_weight = min(lesson.retrieval_count / 10, 1.0)

        return time_weight * 0.4 + importance_weight * 0.4 + usage_weight * 0.2

    def curate_memories(self) -> None:
        """Human curator marks important lessons."""
        # Show recent lessons to user
        recent_lessons = self.get_recent_lessons(limit=20)

        # User marks importance (0-10 scale)
        # High importance lessons never decay
        # Low importance lessons decay faster
```

**Pros:**
- ✅ Simple to understand
- ✅ Recent information prioritized
- ✅ Human judgment incorporated

**Cons:**
- ⚠️ Requires manual curation (human in loop)
- ⚠️ Good insights may be lost if not curated
- ⚠️ No automatic pattern extraction

---

## 🤔 How Does OpenClaw (Claude) Remember?

### Reality Check: Claude Doesn't "Remember Everything"

**What Claude Actually Does:**

1. **Extended Context Window** (200K tokens ≈ 150,000 words)
   - Can hold ~100 full tickets in single context
   - But performance degrades with very long contexts
   - Not true "memory" - just long attention span

2. **Projects** (claude.ai feature)
   - Store documents/context per project
   - Injected into every conversation
   - Still limited by context window

3. **Conversation History**
   - Recent messages kept in context
   - Old messages truncated/summarized
   - Not persistent across sessions (in API)

4. **No Long-Term Memory** (currently)
   - No learning across conversations
   - No automatic pattern extraction
   - Each session starts fresh (except Projects)

**Key Insight:**
> Claude's "memory" is actually just a VERY LONG context window, not true learning/consolidation.

### What We Can Learn:

1. **Don't Mimic Claude's Approach**
   - We can't afford 200K token context per workflow
   - We need smarter consolidation, not just more context

2. **Use Hierarchical Memory Instead**
   - Claude uses flat context (everything included)
   - We need levels (recent detailed, old summarized)

3. **Explicit Retrieval Over Implicit Context**
   - Don't dump everything into prompt
   - Retrieve only what's relevant for current task

---

## 🎯 Recommended Architecture

### **Hybrid: Hierarchical + Vector Retrieval**

Combine the best of both worlds:

```python
class SmartMemory:
    """Intelligent memory management system."""

    def __init__(self):
        # Hierarchical storage
        self.core_principles = CoreMemory()      # ~200 words
        self.strategic_patterns = StrategyMemory()  # ~800 words

        # Vector retrieval for details
        self.vector_store = VectorMemory()       # Unlimited lessons

        # Active working memory
        self.working_memory = WorkingMemory()    # Current task context

    def prepare_context(self, task: str, workflow_id: str) -> str:
        """Prepare memory context for new task (budget: 2000 words)."""

        # 1. Core principles (always included) - 200 words
        core = self.core_principles.get(workflow_id)

        # 2. Vector search for relevant lessons - 800 words
        similar_tickets = self.vector_store.retrieve_relevant(task, k=5)
        relevant_lessons = self._extract_lessons(similar_tickets)

        # 3. Strategic patterns (for this workflow type) - 500 words
        patterns = self.strategic_patterns.get(workflow_id)

        # 4. Recent failures/warnings - 500 words
        recent_issues = self.get_recent_issues(workflow_id, days=7)

        return self._compose_context(
            core=core,
            relevant=relevant_lessons,
            patterns=patterns,
            warnings=recent_issues
        )

    def learn_from_ticket(self, ticket: TicketCard) -> None:
        """Extract and store lessons from completed ticket."""

        # Extract lessons using LLM
        lessons = self._extract_lessons_llm(ticket)

        # Store in vector DB (for retrieval)
        for lesson in lessons:
            self.vector_store.store_lesson(lesson)

        # Update strategic patterns (if significant)
        if self._is_significant(ticket):
            self.strategic_patterns.update(ticket)

        # Update core principles (if fundamental)
        if self._is_fundamental(ticket):
            self.core_principles.update(ticket)

    def _extract_lessons_llm(self, ticket: TicketCard) -> List[Lesson]:
        """Use LLM to extract lessons from ticket."""
        prompt = f"""
        Analyze this completed workflow and extract 3-5 key lessons:

        Task: {ticket.task}
        Workflow: {ticket.workflow_id}

        Stages:
        {self._format_stages(ticket.stages)}

        Extract lessons in these categories:
        1. What worked well (to repeat)
        2. What failed (to avoid)
        3. Patterns discovered (for future tasks)
        4. Best practices (general principles)

        Format: Brief, actionable statements (1-2 sentences each)
        """

        response = self.llm_call(prompt)
        return self._parse_lessons(response)
```

### Memory Budget Example:

```
Total Context Budget: 2000 words

Allocation:
├─ Core Principles:        200 words (10%)   [Always included]
├─ Relevant Lessons:       800 words (40%)   [Vector search]
├─ Strategic Patterns:     500 words (25%)   [Workflow-specific]
├─ Recent Issues:          500 words (25%)   [Last 7 days]
└─ Total:                  2000 words (100%)
```

---

## 📋 Implementation Roadmap

### Phase 1: Enhanced Ticket System (1-2 days)
- [ ] Add stage timestamps to WorkflowRun
- [ ] Create TicketCard model with stage tracking
- [ ] Implement automatic stage transitions
- [ ] Add documentation attachment system
- [ ] Create archive mechanism

### Phase 2: Basic Memory (2-3 days)
- [ ] Create Lesson model
- [ ] Implement lesson extraction (manual first)
- [ ] Build simple retrieval (SQL queries)
- [ ] Add tags for categorization
- [ ] Display relevant lessons in UI

### Phase 3: Hierarchical Memory (3-4 days)
- [ ] Implement CoreMemory (principles)
- [ ] Implement StrategyMemory (patterns)
- [ ] Build consolidation jobs
- [ ] Add time-based archiving
- [ ] Create memory dashboard

### Phase 4: Vector Search (2-3 days)
- [ ] Integrate vector DB (Chroma/Pinecone)
- [ ] Generate embeddings for lessons
- [ ] Implement similarity search
- [ ] Add relevance scoring
- [ ] Optimize retrieval performance

### Phase 5: LLM-Powered Learning (2-3 days)
- [ ] Automated lesson extraction
- [ ] Pattern detection across tickets
- [ ] Principle distillation
- [ ] Anomaly detection (unusual failures)
- [ ] Continuous learning loop

**Total Estimated Time:** 10-15 days

---

## 🎨 Dashboard UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Active Tickets                            [Archive]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ticket-abc123   "Create todo app"         [✓ 80%]     │
│ ├─ Plan        ✓ 2min  📄 plan.md                      │
│ ├─ Implement   ✓ 8min  💾 todo.py, test_todo.py       │
│ ├─ Verify      ✓ 1min  📝 verification.md              │
│ ├─ Test        🔄 ...   (running)                       │
│ └─ Review      ⏳       (pending)                        │
│                                                          │
│ ticket-def456   "Marketing campaign"      [✓ 100%]    │
│ ├─ Plan        ✓ 3min  📄 campaign_plan.md             │
│ ├─ Implement   ✓ 12min 💾 content_strategy.md          │
│ ├─ Verify      ✓ 2min  ✓ Verified                      │
│ ├─ Test        ✓ 1min  📊 metrics.csv                  │
│ └─ Review      ✓ 2min  ✅ Approved                      │
│                         [Move to Archive]                │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ 🧠 Lessons Learned                      [View All]      │
├─────────────────────────────────────────────────────────┤
│ • feature-dev: Always include type hints (4 successes) │
│ • marketing: Start with audience research (3 patterns) │
│ • testing: Run tests before review (2 failures avoided)│
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Key Recommendations

### DO:
1. ✅ **Implement Hierarchical Memory** - Best balance of detail and efficiency
2. ✅ **Use Vector Search** - For precise retrieval when needed
3. ✅ **Automate Lesson Extraction** - LLM analyzes completed tickets
4. ✅ **Set Memory Budgets** - Hard limits prevent context bloat (2000 words)
5. ✅ **Consolidate Periodically** - Weekly/monthly consolidation jobs
6. ✅ **Archive Aggressively** - Move old tickets to archive after 30 days
7. ✅ **Tag Everything** - Enable efficient retrieval

### DON'T:
1. ❌ **Don't Keep Full Histories** - Summarize after 30 days
2. ❌ **Don't Mimic Claude** - We need smarter consolidation
3. ❌ **Don't Manual Curation Only** - Must be mostly automatic
4. ❌ **Don't Store Everything in Context** - Retrieve on demand
5. ❌ **Don't Ignore Time Decay** - Old info becomes less relevant

---

## 🔬 Research Questions

### For Discussion:

1. **Memory Granularity**
   - Should lessons be per-step or per-workflow?
   - How do we handle conflicting lessons?

2. **Consolidation Frequency**
   - Daily? Weekly? Monthly?
   - Triggered by ticket count or time?

3. **Retrieval Strategy**
   - Semantic similarity (embeddings)?
   - Tag-based filtering?
   - Hybrid approach?

4. **User Involvement**
   - Should users curate important lessons?
   - Or fully automated?

5. **Cross-Workflow Learning**
   - Should feature-dev learn from marketing-campaign?
   - Or keep workflow memories separate?

6. **Memory Lifecycle**
   - When do memories "expire"?
   - Can they be "revived" if suddenly relevant?

---

## 🎯 Proposed Next Steps

1. **Discussion** (Now)
   - Review this proposal
   - Discuss memory management approach
   - Decide on architecture

2. **Prototype Phase 1** (2-3 days)
   - Implement enhanced TicketCard model
   - Add stage timestamps
   - Test automatic transitions

3. **Research Vector DBs** (1 day)
   - Evaluate Chroma vs Pinecone vs SQLite-VSS
   - Test embedding performance
   - Estimate costs

4. **Design Memory Schema** (1 day)
   - Finalize Lesson model
   - Design consolidation logic
   - Plan retrieval API

5. **Build MVP** (1 week)
   - Basic hierarchical memory
   - Simple lesson extraction
   - UI for viewing lessons

---

**Let's discuss:** Which memory approach resonates most with your vision? Any concerns or alternative ideas?
