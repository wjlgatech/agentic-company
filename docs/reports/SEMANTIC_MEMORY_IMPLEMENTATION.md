# Semantic-First, Traffic-Adaptive Memory: Implementation Plan

## Executive Summary

Implementing an intelligent memory system that:
- ✅ Prioritizes semantic relevance over traffic volume
- ✅ Uses gradient shift (not hard cutover)
- ✅ Pulls from similar-cluster workflows
- ✅ LLM judges cross-workflow relevance
- ✅ **Learns optimal parameters from usage**

---

## 🎓 Learning Gradient Parameters: The Strategy

### The Question:
**"Where do we learn the gradient threshold parameters?"**

### Three-Stage Learning Approach:

```
Stage 1: Heuristic Bootstrap    (Week 1-4)    → Start with reasonable defaults
Stage 2: Feedback-Driven        (Month 2-3)   → Learn from user corrections
Stage 3: Meta-Learning          (Month 4+)    → Optimize across all workflows
```

---

## 📊 Stage 1: Heuristic Bootstrap (Weeks 1-4)

### Initial Parameters (Research-Based Defaults)

```python
class MemoryParameters:
    """Gradient parameters with research-based defaults."""

    # Similarity thresholds (how similar must cross-workflow lesson be?)
    SIMILARITY_SPARSE = 0.50    # <10 tickets: accept moderately similar
    SIMILARITY_GROWING = 0.65   # 10-50 tickets: prefer more similar
    SIMILARITY_MATURE = 0.80    # 50+ tickets: only highly similar

    # Same-workflow weights (how much to favor same-workflow?)
    WEIGHT_SPARSE = 0.60        # <10 tickets: 60% same, 40% cross
    WEIGHT_GROWING = 0.75       # 10-50 tickets: 75% same, 25% cross
    WEIGHT_MATURE = 0.90        # 50+ tickets: 90% same, 10% cross

    # Traffic thresholds (when to shift gradients?)
    THRESHOLD_SPARSE = 10       # Below this: sparse mode
    THRESHOLD_GROWING = 50      # Below this: growing mode
    # Above 50: mature mode

    # Relevance scoring
    MIN_LLM_RELEVANCE = 0.70    # LLM must rate ≥7/10 for inclusion

@dataclass
class ParameterRationale:
    """Why we chose these defaults."""

    SIMILARITY_SPARSE_RATIONALE = """
    0.50 threshold for sparse data because:
    - With <10 tickets, we need more data
    - Accept moderately similar lessons (50%+ similarity)
    - Research: Users prefer some info over no info
    - Can always filter out bad lessons later
    """

    WEIGHT_SPARSE_RATIONALE = """
    60/40 split (same/cross) for sparse because:
    - Still favor same-workflow (60%)
    - But give cross-workflow meaningful weight (40%)
    - Research: Cold start needs diverse examples
    """

    THRESHOLD_10_RATIONALE = """
    10 tickets = sparse threshold because:
    - Statistical significance: n≥10 shows patterns
    - Practical: 10 tickets ≈ 1-2 weeks of active use
    - Below 10: not enough data to establish workflow identity
    """

    THRESHOLD_50_RATIONALE = """
    50 tickets = mature threshold because:
    - Sufficient data: 50 tickets cover most common patterns
    - Practical: 50 tickets ≈ 1-2 months of active use
    - Above 50: workflow-specific patterns are clear
    """
```

### Implementation:

```python
class AdaptiveMemory:
    """Memory system with adaptive parameters."""

    def __init__(self):
        self.params = MemoryParameters()
        self.usage_tracker = UsageTracker()  # Track what works

    def get_adaptive_config(self, workflow_id: str) -> dict:
        """Get current adaptive configuration."""
        ticket_count = self.count_tickets(workflow_id)

        if ticket_count < self.params.THRESHOLD_SPARSE:
            return {
                'mode': 'sparse',
                'same_weight': self.params.WEIGHT_SPARSE,
                'cross_threshold': self.params.SIMILARITY_SPARSE,
                'reason': f'Only {ticket_count} tickets, need more data'
            }

        elif ticket_count < self.params.THRESHOLD_GROWING:
            # Interpolate between sparse and mature
            progress = (ticket_count - self.params.THRESHOLD_SPARSE) / \
                      (self.params.THRESHOLD_GROWING - self.params.THRESHOLD_SPARSE)

            return {
                'mode': 'growing',
                'same_weight': self._interpolate(
                    self.params.WEIGHT_SPARSE,
                    self.params.WEIGHT_MATURE,
                    progress
                ),
                'cross_threshold': self._interpolate(
                    self.params.SIMILARITY_SPARSE,
                    self.params.SIMILARITY_MATURE,
                    progress
                ),
                'reason': f'{ticket_count} tickets, transitioning to mature'
            }

        else:
            return {
                'mode': 'mature',
                'same_weight': self.params.WEIGHT_MATURE,
                'cross_threshold': self.params.SIMILARITY_MATURE,
                'reason': f'{ticket_count} tickets, workflow established'
            }

    def _interpolate(self, start: float, end: float, progress: float) -> float:
        """Smooth interpolation between start and end."""
        return start + (end - start) * progress
```

**Rationale for defaults:**
- Based on research: "10-50-rule" (statistical significance thresholds)
- Similarity scores: 0.5=moderate, 0.65=good, 0.8=excellent (standard)
- Weights: 60/40 → 75/25 → 90/10 (gradual shift, never 100/0)

---

## 📈 Stage 2: Feedback-Driven Learning (Months 2-3)

### Capture Feedback Signals

Users give implicit feedback through actions:

```python
class FeedbackSignal(Enum):
    """Types of feedback we can capture."""

    # Explicit signals (user actions)
    LESSON_UPVOTE = "upvote"           # User marks lesson as helpful
    LESSON_DOWNVOTE = "downvote"       # User marks lesson as unhelpful
    LESSON_DISMISSED = "dismissed"     # User dismisses suggestion
    LESSON_APPLIED = "applied"         # User copies/uses lesson

    # Implicit signals (workflow outcomes)
    TICKET_SUCCESS = "success"         # Ticket completed successfully
    TICKET_FAILED = "failed"           # Ticket failed/needed retry
    STEP_FAST = "fast"                 # Step completed faster than average
    STEP_SLOW = "slow"                 # Step took longer than average
    REVISION_NEEDED = "revision"       # User had to revise output

@dataclass
class FeedbackEvent:
    """A single feedback event."""
    workflow_id: str
    ticket_id: str
    lesson_id: Optional[str]           # Which lesson was shown
    signal: FeedbackSignal
    context: dict                      # What parameters were used
    timestamp: datetime

class FeedbackTracker:
    """Tracks and analyzes feedback."""

    def record_feedback(self, event: FeedbackEvent) -> None:
        """Record a feedback event."""
        self.db.store(event)

        # Track success rate for parameter combinations
        if event.signal in [FeedbackSignal.LESSON_APPLIED,
                           FeedbackSignal.TICKET_SUCCESS]:
            self._increment_success(event.context)
        elif event.signal in [FeedbackSignal.LESSON_DOWNVOTE,
                             FeedbackSignal.TICKET_FAILED]:
            self._increment_failure(event.context)

    def analyze_parameter_effectiveness(self) -> dict:
        """Which parameter values lead to best outcomes?"""

        # Group by parameter values
        results = defaultdict(lambda: {'success': 0, 'total': 0})

        for event in self.db.query_all():
            params = event.context['params']
            key = (
                params['same_weight'],
                params['cross_threshold'],
                params['ticket_count_bucket']  # 0-10, 10-50, 50+
            )

            results[key]['total'] += 1
            if event.signal in [FeedbackSignal.LESSON_APPLIED,
                               FeedbackSignal.TICKET_SUCCESS]:
                results[key]['success'] += 1

        # Calculate success rates
        effectiveness = {}
        for key, counts in results.items():
            effectiveness[key] = counts['success'] / counts['total']

        return effectiveness
```

### Adjust Parameters Based on Feedback

```python
class ParameterOptimizer:
    """Learns optimal parameters from feedback."""

    def __init__(self):
        self.feedback_tracker = FeedbackTracker()
        self.params = MemoryParameters()

    def optimize_parameters(self) -> None:
        """Run weekly to adjust parameters based on feedback."""

        # Analyze last week's feedback
        effectiveness = self.feedback_tracker.analyze_parameter_effectiveness()

        # For each ticket-count bucket, find best-performing parameters
        for bucket in ['sparse', 'growing', 'mature']:
            best_params = self._find_best_params(effectiveness, bucket)

            # Gradually adjust toward best-performing values
            if bucket == 'sparse':
                self.params.WEIGHT_SPARSE = self._adjust_toward(
                    current=self.params.WEIGHT_SPARSE,
                    target=best_params['same_weight'],
                    step=0.05  # Move 5% per week
                )
                self.params.SIMILARITY_SPARSE = self._adjust_toward(
                    current=self.params.SIMILARITY_SPARSE,
                    target=best_params['cross_threshold'],
                    step=0.05
                )
            # ... similar for growing and mature

        # Log adjustments for transparency
        self._log_parameter_changes()

    def _adjust_toward(self, current: float, target: float, step: float) -> float:
        """Gradually move current toward target."""
        if abs(current - target) < step:
            return target
        return current + step if target > current else current - step
```

**Example learning:**
```
Week 1: WEIGHT_SPARSE = 0.60 (default)
        → Success rate: 65%

Week 4: WEIGHT_SPARSE = 0.55 (adjusted down)
        → Success rate: 72% (better!)

Week 8: WEIGHT_SPARSE = 0.50 (adjusted down more)
        → Success rate: 68% (worse)

Week 12: WEIGHT_SPARSE = 0.55 (adjusted back up)
         → Converged to optimal: 0.55
```

---

## 🧠 Stage 3: Meta-Learning (Months 4+)

### Learn Patterns Across All Workflows

```python
class MetaLearner:
    """Learns optimal parameters across all workflows."""

    def discover_workflow_archetypes(self) -> dict:
        """Find common workflow patterns."""

        # Cluster workflows by behavior
        workflows = self.get_all_workflows()

        # Features for clustering
        features = []
        for wf in workflows:
            features.append({
                'avg_ticket_duration': wf.avg_duration(),
                'step_count': wf.step_count,
                'code_generation': wf.generates_code(),  # Boolean
                'human_review': wf.requires_review(),    # Boolean
                'failure_rate': wf.failure_rate(),
                'cross_workflow_success': wf.cross_workflow_lesson_success_rate()
            })

        # Cluster into archetypes
        archetypes = cluster_workflows(features, n_clusters=3)

        # Example archetypes discovered:
        # 1. "Code-Heavy" (feature-dev, security)
        #    → Benefits from cross-learning (shared code patterns)
        #    → Optimal: WEIGHT_SPARSE=0.55, SIMILARITY=0.55
        #
        # 2. "Content-Heavy" (marketing, grant-proposal)
        #    → Less benefit from cross-learning (domain-specific)
        #    → Optimal: WEIGHT_SPARSE=0.70, SIMILARITY=0.70
        #
        # 3. "Analysis-Heavy" (churn-analysis, due-diligence)
        #    → Moderate cross-learning benefit
        #    → Optimal: WEIGHT_SPARSE=0.60, SIMILARITY=0.60

        return archetypes

    def predict_optimal_params(self, workflow_id: str) -> dict:
        """Predict best parameters for a workflow."""

        # Get workflow features
        features = self._extract_features(workflow_id)

        # Find closest archetype
        archetype = self._match_archetype(features)

        # Return archetype's optimal parameters
        return archetype.optimal_params
```

### Continuous Improvement Loop

```
Every Week:
  1. Collect feedback signals
  2. Analyze parameter effectiveness
  3. Adjust parameters (5% step)

Every Month:
  1. Re-cluster workflow archetypes
  2. Update archetype-specific parameters
  3. Predict params for new workflows

Every Quarter:
  1. Evaluate overall system performance
  2. Consider major parameter restructuring
  3. A/B test new strategies
```

---

## 🏗️ Workflow Clustering: Implementation

### Pre-Defined Clusters (Cold Start)

```python
WORKFLOW_CLUSTERS = {
    "code": {
        "workflows": [
            "feature-dev",
            "security-assessment",
            "incident-postmortem"
        ],
        "params": {
            "same_weight": 0.55,      # More cross-learning (shared code patterns)
            "similarity_threshold": 0.55,
            "description": "Code-focused workflows share implementation patterns"
        }
    },

    "content": {
        "workflows": [
            "marketing-campaign",
            "grant-proposal"
        ],
        "params": {
            "same_weight": 0.70,      # Less cross-learning (domain-specific)
            "similarity_threshold": 0.70,
            "description": "Content workflows are more domain-specific"
        }
    },

    "analysis": {
        "workflows": [
            "churn-analysis",
            "due-diligence",
            "patent-landscape",
            "compliance-audit"
        ],
        "params": {
            "same_weight": 0.60,      # Moderate cross-learning
            "similarity_threshold": 0.60,
            "description": "Analysis workflows share research methodologies"
        }
    }
}

class ClusterManager:
    """Manages workflow clusters."""

    def get_cluster_for_workflow(self, workflow_id: str) -> Optional[str]:
        """Find which cluster a workflow belongs to."""
        for cluster_name, cluster_info in WORKFLOW_CLUSTERS.items():
            if workflow_id in cluster_info["workflows"]:
                return cluster_name
        return None

    def get_similar_workflows(self, workflow_id: str) -> List[str]:
        """Get workflows in the same cluster."""
        cluster = self.get_cluster_for_workflow(workflow_id)
        if cluster:
            return WORKFLOW_CLUSTERS[cluster]["workflows"]
        return []

    def get_cluster_params(self, workflow_id: str) -> dict:
        """Get cluster-specific parameters."""
        cluster = self.get_cluster_for_workflow(workflow_id)
        if cluster:
            return WORKFLOW_CLUSTERS[cluster]["params"]
        return self._get_default_params()
```

---

## 🤖 LLM-Based Relevance Judging

### Cross-Workflow Lesson Evaluation

```python
class LLMRelevanceJudge:
    """Uses LLM to judge if cross-workflow lesson is relevant."""

    async def judge_relevance(
        self,
        lesson: Lesson,
        target_workflow: str,
        target_task: str
    ) -> float:
        """
        Judge if a lesson from one workflow is relevant to another.

        Returns: 0.0-1.0 relevance score
        """

        prompt = f"""
You are a relevance judge for a multi-workflow AI system.

LESSON (from {lesson.workflow_id}):
{lesson.content}

Context: {lesson.context}
Original task: {lesson.original_task}

TARGET WORKFLOW: {target_workflow}
TARGET TASK: {target_task}

QUESTION: Is this lesson relevant to the target task?

Consider:
1. Domain similarity (same type of work?)
2. Pattern transferability (does the lesson's principle apply?)
3. Actionability (can the target agent actually use this?)

Rate relevance: 0-10 scale
- 0-3: Not relevant (different domains, won't help)
- 4-6: Somewhat relevant (tangential connection)
- 7-8: Relevant (clear applicability)
- 9-10: Highly relevant (directly applicable)

Respond with JSON:
{{
  "score": <0-10>,
  "reasoning": "<brief explanation>",
  "applicable": <true/false>
}}
"""

        response = await self.llm_call(prompt)
        result = json.loads(response)

        # Store judgment for meta-learning
        self._record_judgment(lesson, target_workflow, result)

        return result["score"] / 10.0  # Normalize to 0.0-1.0

    async def batch_judge(
        self,
        lessons: List[Lesson],
        target_workflow: str,
        target_task: str
    ) -> List[Tuple[Lesson, float]]:
        """Judge multiple lessons in parallel."""

        # Batch for efficiency
        judgments = await asyncio.gather(*[
            self.judge_relevance(lesson, target_workflow, target_task)
            for lesson in lessons
        ])

        # Return lessons with scores
        return [(lesson, score) for lesson, score in zip(lessons, judgments)]
```

### Caching Judgments

```python
class JudgmentCache:
    """Cache LLM relevance judgments to save API calls."""

    def get_cached_judgment(
        self,
        lesson_id: str,
        target_workflow: str
    ) -> Optional[float]:
        """Check if we've judged this combination before."""

        cache_key = f"{lesson_id}:{target_workflow}"
        return self.cache.get(cache_key)

    def cache_judgment(
        self,
        lesson_id: str,
        target_workflow: str,
        score: float,
        ttl: int = 30 * 86400  # 30 days
    ) -> None:
        """Cache a judgment."""

        cache_key = f"{lesson_id}:{target_workflow}"
        self.cache.set(cache_key, score, ttl=ttl)
```

---

## 📊 Complete Memory Retrieval Flow

```python
class SemanticMemory:
    """Complete semantic-first, traffic-adaptive memory system."""

    def __init__(self):
        self.chroma = ChromaDB()
        self.params = MemoryParameters()
        self.cluster_manager = ClusterManager()
        self.llm_judge = LLMRelevanceJudge()
        self.feedback_tracker = FeedbackTracker()
        self.optimizer = ParameterOptimizer()

    async def get_memory_for_task(
        self,
        workflow_id: str,
        task: str
    ) -> MemoryContext:
        """Get relevant memory for a new task."""

        # 1. Get adaptive configuration
        config = self.get_adaptive_config(workflow_id)
        ticket_count = self.count_tickets(workflow_id)

        # 2. Get same-workflow lessons
        same_workflow_lessons = self.chroma.query(
            collection=f"lessons_{workflow_id}",
            query_text=task,
            n_results=10
        )

        # 3. Get cross-workflow lessons (from cluster)
        similar_workflows = self.cluster_manager.get_similar_workflows(workflow_id)
        cross_workflow_lessons = []

        for other_workflow in similar_workflows:
            if other_workflow == workflow_id:
                continue

            # Query other workflow's lessons
            candidates = self.chroma.query(
                collection=f"lessons_{other_workflow}",
                query_text=task,
                n_results=5
            )

            # Filter by similarity threshold
            for lesson, similarity in candidates:
                if similarity >= config['cross_threshold']:
                    cross_workflow_lessons.append((lesson, similarity))

        # 4. LLM judges cross-workflow lessons
        if cross_workflow_lessons:
            judged_lessons = await self.llm_judge.batch_judge(
                lessons=[l for l, s in cross_workflow_lessons],
                target_workflow=workflow_id,
                target_task=task
            )

            # Filter by LLM relevance
            cross_workflow_lessons = [
                (lesson, score)
                for lesson, score in judged_lessons
                if score >= self.params.MIN_LLM_RELEVANCE
            ]

        # 5. Combine with adaptive weighting
        memory = self._combine_memories(
            same_workflow=same_workflow_lessons,
            cross_workflow=cross_workflow_lessons,
            same_weight=config['same_weight']
        )

        # 6. Track usage for feedback loop
        self.feedback_tracker.record_memory_retrieval(
            workflow_id=workflow_id,
            task=task,
            config=config,
            lessons_used=memory.lessons
        )

        return memory
```

---

## 🎯 Implementation Priority Order

### Phase 1: Enhanced Ticket Tracking (Days 1-3)

**Goal:** Add stage timestamps and automatic transitions

```python
# New fields in WorkflowRun
@dataclass
class WorkflowRun:
    id: str
    workflow_id: str
    task: str
    status: StepStatus

    # NEW: Stage tracking
    current_stage: str  # plan, implement, verify, test, review
    stages: Dict[str, StageInfo]  # {stage_name: StageInfo}

    # NEW: Documentation
    documentation: Dict[str, List[str]]  # {stage: [doc_paths]}

    # Existing fields
    current_step: int
    total_steps: int
    context: dict
    created_at: str
    updated_at: str
    error: Optional[str] = None
```

**Tasks:**
- [ ] Add stage tracking to WorkflowRun model
- [ ] Create StageInfo dataclass
- [ ] Implement automatic stage transitions
- [ ] Add stage timestamps (started_at, completed_at)
- [ ] Update dashboard to show stage progress

---

### Phase 2: Basic Lesson Extraction (Days 4-7)

**Goal:** LLM extracts lessons, human curates

```python
class LessonExtractor:
    """Extracts lessons from completed tickets."""

    async def extract_lessons(self, ticket: WorkflowRun) -> List[Lesson]:
        """LLM proposes lessons from ticket."""

        prompt = f"""
Analyze this completed workflow and extract key lessons:

Task: {ticket.task}
Workflow: {ticket.workflow_id}
Status: {ticket.status}

Stages:
{self._format_stages(ticket.stages)}

Extract 3-5 lessons in these categories:
1. SUCCESS: What worked well (to repeat)
2. FAILURE: What didn't work (to avoid)
3. PATTERN: Patterns discovered (for similar tasks)
4. PRINCIPLE: Best practices (general wisdom)

Format each lesson as:
- Category: [SUCCESS/FAILURE/PATTERN/PRINCIPLE]
- Content: [1-2 sentence description]
- Confidence: [LOW/MEDIUM/HIGH]
- Tags: [relevant, keywords]

Return JSON array of lessons.
"""

        response = await self.llm_call(prompt)
        raw_lessons = json.loads(response)

        # Convert to Lesson objects
        lessons = [self._to_lesson(l, ticket) for l in raw_lessons]

        # Present to user for curation
        return lessons

class LessonCurator:
    """UI for human curation of lessons."""

    def present_for_curation(self, lessons: List[Lesson]) -> None:
        """Show lessons to user for approval/editing."""

        print("\n📚 Lessons extracted from workflow:")
        print("=" * 60)

        for i, lesson in enumerate(lessons, 1):
            print(f"\n{i}. [{lesson.category}] {lesson.content}")
            print(f"   Confidence: {lesson.confidence}")
            print(f"   Tags: {', '.join(lesson.tags)}")

            action = input("   [A]pprove / [E]dit / [D]ismiss / [S]kip: ").lower()

            if action == 'a':
                self._save_lesson(lesson)
            elif action == 'e':
                edited = self._edit_lesson(lesson)
                self._save_lesson(edited)
            elif action == 'd':
                continue
            else:
                continue
```

**Tasks:**
- [ ] Create Lesson model
- [ ] Implement LLM extraction
- [ ] Build curation UI
- [ ] Add lesson storage (SQLite + Chroma)
- [ ] Create lesson dashboard

---

### Phase 3: Hierarchical Memory (Days 8-12)

**Goal:** Multi-level memory consolidation

```python
class HierarchicalMemory:
    """Three-level memory system."""

    def __init__(self):
        self.tactical = TacticalMemory()      # Recent 10-20 tickets
        self.strategic = StrategicMemory()    # Workflow patterns
        self.core = CoreMemory()              # Best practices

    async def consolidate_weekly(self) -> None:
        """Weekly consolidation job."""

        # Level 1 → Level 2: Tactical to Strategic
        recent_lessons = self.tactical.get_last_week()
        patterns = await self._extract_patterns(recent_lessons)
        self.strategic.add_patterns(patterns)

        # Level 2 → Level 3: Strategic to Core
        if self.strategic.lesson_count() > 100:
            principles = await self._distill_principles(
                self.strategic.get_all()
            )
            self.core.update_principles(principles)

        # Archive old tactical lessons
        self.tactical.archive_older_than(days=30)
```

**Tasks:**
- [ ] Implement three memory levels
- [ ] Build consolidation logic
- [ ] Create weekly consolidation job
- [ ] Add archiving mechanism
- [ ] Build memory dashboard

---

### Phase 4: Vector Search Integration (Days 13-17)

**Goal:** Semantic retrieval with Chroma

```python
class ChromaMemory:
    """Vector-based memory with Chroma."""

    def __init__(self):
        self.client = chromadb.Client()
        self._setup_collections()

    def _setup_collections(self):
        """Create collection per workflow."""
        for workflow_id in self.get_all_workflows():
            self.client.create_collection(
                name=f"lessons_{workflow_id}",
                metadata={"workflow": workflow_id}
            )

    def add_lesson(self, lesson: Lesson) -> None:
        """Add lesson with embedding."""
        collection = self.client.get_collection(
            name=f"lessons_{lesson.workflow_id}"
        )

        collection.add(
            ids=[lesson.id],
            documents=[lesson.content],
            metadatas=[{
                "category": lesson.category,
                "confidence": lesson.confidence,
                "tags": json.dumps(lesson.tags),
                "created_at": lesson.created_at.isoformat()
            }]
        )

    def query_similar(
        self,
        workflow_id: str,
        task: str,
        n_results: int = 10
    ) -> List[Tuple[Lesson, float]]:
        """Query similar lessons."""
        collection = self.client.get_collection(
            name=f"lessons_{workflow_id}"
        )

        results = collection.query(
            query_texts=[task],
            n_results=n_results
        )

        return self._parse_results(results)
```

**Tasks:**
- [ ] Install and configure Chroma
- [ ] Create collections per workflow
- [ ] Implement lesson indexing
- [ ] Build similarity search
- [ ] Add LLM relevance judging
- [ ] Implement caching

---

## 📈 Success Metrics

### How we'll know it's working:

1. **Memory Efficiency**
   - Average context size: <2000 words ✅
   - Retrieval time: <500ms ✅
   - Relevant lessons: >80% ✅

2. **Workflow Quality**
   - Success rate: Increase from 60% → 80%+ ✅
   - Retry rate: Decrease from 30% → <15% ✅
   - User satisfaction: >8/10 ✅

3. **Parameter Learning**
   - Convergence time: <3 months ✅
   - Stability: Parameters don't oscillate ✅
   - Improvement: Better than defaults ✅

---

## 🎯 Timeline

```
Week 1-2:   Enhanced ticket tracking
Week 2-3:   Basic lesson extraction + curation
Week 3-4:   Hierarchical memory system
Week 4-5:   Vector search with Chroma
Week 5-6:   LLM relevance judging
Week 6-8:   Parameter learning (feedback loop)
Week 8-12:  Optimization and meta-learning
```

**Total: 12 weeks to fully operational semantic memory system**

---

## 🎓 Open Questions for Discussion

1. **Curation frequency:** Should users curate after every ticket or batch weekly?
2. **Lesson quality bar:** Better to have 100 curated lessons or 1000 auto-extracted?
3. **Cross-cluster learning:** Should "code" cluster ever learn from "content" cluster?
4. **Parameter visibility:** Should users see/adjust the gradient parameters?
5. **Archiving strategy:** Hard delete after 90 days or move to cold storage?

---

**Ready to start Phase 1? Let's build enhanced ticket tracking!**
