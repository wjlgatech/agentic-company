"""
Lesson Learning System - Extract and manage lessons from workflow executions.

Phase 2: Basic lesson extraction with LLM proposals and human curation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import uuid


class LessonType(str, Enum):
    """Types of lessons that can be learned."""
    SUCCESS_PATTERN = "success_pattern"      # What worked well
    FAILURE_PATTERN = "failure_pattern"      # What went wrong
    OPTIMIZATION = "optimization"            # How to do it better/faster
    EDGE_CASE = "edge_case"                 # Unusual situation handling
    ANTI_PATTERN = "anti_pattern"           # What to avoid
    BEST_PRACTICE = "best_practice"         # Recommended approach


class LessonStatus(str, Enum):
    """Lesson approval status."""
    PROPOSED = "proposed"        # LLM proposed, awaiting review
    APPROVED = "approved"        # Human approved, active in memory
    REJECTED = "rejected"        # Human rejected
    ARCHIVED = "archived"        # Superseded or outdated


@dataclass
class LessonMetadata:
    """Metadata about a lesson's context and applicability."""
    workflow_id: str                          # Which workflow this came from
    workflow_cluster: str = "general"         # code, content, analysis, etc.
    domain_tags: List[str] = field(default_factory=list)  # e.g., ["auth", "api", "python"]
    complexity: str = "medium"                # simple, medium, complex
    confidence_score: float = 0.0             # LLM's confidence (0-1)
    evidence_run_ids: List[str] = field(default_factory=list)  # Runs that support this lesson


@dataclass
class Lesson:
    """A learned insight from workflow execution."""
    id: str
    type: LessonType
    title: str                                # Short summary (1 line)
    content: str                              # Detailed lesson content
    situation: str                            # When/where this applies
    recommendation: str                       # What to do about it

    status: LessonStatus
    metadata: LessonMetadata

    created_at: str
    created_by: str                           # "llm" or user ID
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None

    usage_count: int = 0                      # How many times retrieved
    last_used_at: Optional[str] = None
    effectiveness_score: Optional[float] = None  # Human feedback (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, LessonType) else self.type,
            "title": self.title,
            "content": self.content,
            "situation": self.situation,
            "recommendation": self.recommendation,
            "status": self.status.value if isinstance(self.status, LessonStatus) else self.status,
            "metadata": {
                "workflow_id": self.metadata.workflow_id,
                "workflow_cluster": self.metadata.workflow_cluster,
                "domain_tags": self.metadata.domain_tags,
                "complexity": self.metadata.complexity,
                "confidence_score": self.metadata.confidence_score,
                "evidence_run_ids": self.metadata.evidence_run_ids,
            },
            "created_at": self.created_at,
            "created_by": self.created_by,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at,
            "effectiveness_score": self.effectiveness_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lesson":
        """Deserialize from dictionary."""
        metadata = LessonMetadata(
            workflow_id=data["metadata"]["workflow_id"],
            workflow_cluster=data["metadata"].get("workflow_cluster", "general"),
            domain_tags=data["metadata"].get("domain_tags", []),
            complexity=data["metadata"].get("complexity", "medium"),
            confidence_score=data["metadata"].get("confidence_score", 0.0),
            evidence_run_ids=data["metadata"].get("evidence_run_ids", []),
        )

        return cls(
            id=data["id"],
            type=LessonType(data["type"]),
            title=data["title"],
            content=data["content"],
            situation=data["situation"],
            recommendation=data["recommendation"],
            status=LessonStatus(data["status"]),
            metadata=metadata,
            created_at=data["created_at"],
            created_by=data["created_by"],
            reviewed_at=data.get("reviewed_at"),
            reviewed_by=data.get("reviewed_by"),
            review_notes=data.get("review_notes"),
            usage_count=data.get("usage_count", 0),
            last_used_at=data.get("last_used_at"),
            effectiveness_score=data.get("effectiveness_score"),
        )


class LessonExtractor:
    """
    Extract lessons from completed workflow runs using LLM analysis.

    Phase 2 approach: LLM proposes lessons, human curates.
    """

    EXTRACTION_PROMPT = """You are a lesson extraction expert analyzing a completed workflow execution.

Your task is to identify 1-3 high-value lessons that future workflows can learn from.

WORKFLOW CONTEXT:
- Workflow ID: {workflow_id}
- Task: {task}
- Status: {status}
- Duration: {duration}s

EXECUTION DETAILS:
{execution_summary}

STAGE PERFORMANCE:
{stage_summary}

ANALYSIS GUIDELINES:

1. **Focus on actionable insights** - Not just "it worked" but WHY it worked
2. **Look for patterns** - What made this succeed or fail?
3. **Consider transferability** - Will this help other similar tasks?
4. **Be specific** - Avoid generic advice like "test your code"

LESSON TYPES TO CONSIDER:
- Success Pattern: An approach that worked particularly well
- Failure Pattern: A mistake or issue that occurred
- Optimization: A way to make this faster/better next time
- Edge Case: An unusual situation that was handled (or not)
- Anti-Pattern: Something that should be avoided
- Best Practice: A recommended approach worth following

For each lesson, provide:
1. **Type**: One of the lesson types above
2. **Title**: One-line summary (max 80 chars)
3. **Content**: Detailed explanation (2-4 sentences)
4. **Situation**: When/where this applies (1-2 sentences)
5. **Recommendation**: What to do about it (1-2 sentences)
6. **Confidence**: Your confidence in this lesson (0.0-1.0)
7. **Domain Tags**: Relevant tags (e.g., ["authentication", "api", "python"])

Return valid JSON in this format:
{{
  "lessons": [
    {{
      "type": "success_pattern",
      "title": "...",
      "content": "...",
      "situation": "...",
      "recommendation": "...",
      "confidence": 0.85,
      "domain_tags": ["tag1", "tag2"]
    }}
  ]
}}

IMPORTANT: Only propose lessons with confidence >= 0.7. Quality over quantity."""

    def __init__(self, llm_call):
        """
        Initialize lesson extractor.

        Args:
            llm_call: Function(prompt: str) -> str that calls LLM
        """
        self.llm_call = llm_call

    def extract_from_run(
        self,
        run_id: str,
        workflow_id: str,
        task: str,
        status: str,
        duration: float,
        stages: Dict[str, Any],
        steps: List[Dict[str, Any]],
    ) -> List[Lesson]:
        """
        Extract lessons from a completed workflow run.

        Args:
            run_id: Workflow run identifier
            workflow_id: Workflow template ID
            task: User's task description
            status: Final run status
            duration: Total execution time in seconds
            stages: Stage execution data
            steps: Step execution data

        Returns:
            List of proposed lessons (status=PROPOSED)
        """
        # Build execution summary
        execution_summary = self._summarize_execution(steps)
        stage_summary = self._summarize_stages(stages)

        # Build prompt
        prompt = self.EXTRACTION_PROMPT.format(
            workflow_id=workflow_id,
            task=task,
            status=status,
            duration=duration,
            execution_summary=execution_summary,
            stage_summary=stage_summary,
        )

        # Call LLM
        try:
            response = self.llm_call(prompt)

            # Parse JSON response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            # Convert to Lesson objects
            lessons = []
            for lesson_data in data.get("lessons", []):
                lesson = Lesson(
                    id=str(uuid.uuid4())[:8],
                    type=LessonType(lesson_data["type"]),
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    situation=lesson_data["situation"],
                    recommendation=lesson_data["recommendation"],
                    status=LessonStatus.PROPOSED,
                    metadata=LessonMetadata(
                        workflow_id=workflow_id,
                        workflow_cluster=self._detect_cluster(workflow_id),
                        domain_tags=lesson_data.get("domain_tags", []),
                        confidence_score=lesson_data.get("confidence", 0.8),
                        evidence_run_ids=[run_id],
                    ),
                    created_at=datetime.now().isoformat(),
                    created_by="llm",
                )
                lessons.append(lesson)

            return lessons

        except Exception as e:
            # If extraction fails, return empty list (don't block workflow)
            print(f"Lesson extraction failed: {e}")
            return []

    def _summarize_execution(self, steps: List[Dict[str, Any]]) -> str:
        """Summarize step execution for LLM context."""
        summary_lines = []
        for step in steps:
            status_emoji = {"completed": "✓", "failed": "✗", "pending": "○"}.get(step.get("status"), "?")
            summary_lines.append(
                f"{status_emoji} {step.get('step_id', 'unknown')}: {step.get('agent', 'unknown')} "
                f"({step.get('status', 'unknown')})"
            )
            if step.get("error"):
                summary_lines.append(f"  Error: {step['error'][:100]}")

        return "\n".join(summary_lines)

    def _summarize_stages(self, stages: Dict[str, Any]) -> str:
        """Summarize stage performance for LLM context."""
        if not stages:
            return "No stage data available"

        summary_lines = []
        for stage_name, stage_info in stages.items():
            if not stage_info.get("started_at"):
                continue

            duration = "?"
            if stage_info.get("started_at") and stage_info.get("completed_at"):
                start = datetime.fromisoformat(stage_info["started_at"])
                end = datetime.fromisoformat(stage_info["completed_at"])
                duration = f"{(end - start).total_seconds():.1f}s"

            artifact_count = len(stage_info.get("artifacts", []))
            status = "✓" if stage_info.get("completed_at") else "●"

            summary_lines.append(
                f"{status} {stage_name.upper()}: {duration} | {artifact_count} artifacts"
            )

        return "\n".join(summary_lines)

    def _detect_cluster(self, workflow_id: str) -> str:
        """Detect workflow cluster from ID."""
        workflow_id_lower = workflow_id.lower()

        if any(kw in workflow_id_lower for kw in ["dev", "feature", "code", "implement", "build"]):
            return "code"
        elif any(kw in workflow_id_lower for kw in ["market", "content", "campaign", "social"]):
            return "content"
        elif any(kw in workflow_id_lower for kw in ["analysis", "research", "due-diligence", "audit"]):
            return "analysis"
        else:
            return "general"


class LessonManager:
    """
    Manage lesson storage and retrieval with human curation.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize lesson manager.

        Args:
            storage_path: Path to JSON file for lesson storage (None = in-memory)
        """
        from pathlib import Path

        if storage_path is None:
            storage_path = str(Path.home() / ".agenticom" / "lessons.json")

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.lessons: Dict[str, Lesson] = {}
        self._load()

    def _load(self):
        """Load lessons from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for lesson_data in data.get("lessons", []):
                        lesson = Lesson.from_dict(lesson_data)
                        self.lessons[lesson.id] = lesson
            except Exception as e:
                print(f"Failed to load lessons: {e}")

    def _save(self):
        """Save lessons to storage."""
        try:
            data = {
                "lessons": [lesson.to_dict() for lesson in self.lessons.values()],
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save lessons: {e}")

    def add_proposed(self, lesson: Lesson) -> str:
        """Add a proposed lesson awaiting review."""
        self.lessons[lesson.id] = lesson
        self._save()
        return lesson.id

    def approve(
        self,
        lesson_id: str,
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Approve a proposed lesson."""
        if lesson_id not in self.lessons:
            return False

        lesson = self.lessons[lesson_id]
        lesson.status = LessonStatus.APPROVED
        lesson.reviewed_at = datetime.now().isoformat()
        lesson.reviewed_by = reviewer_id
        lesson.review_notes = notes

        self._save()
        return True

    def reject(
        self,
        lesson_id: str,
        reviewer_id: str,
        reason: str
    ) -> bool:
        """Reject a proposed lesson."""
        if lesson_id not in self.lessons:
            return False

        lesson = self.lessons[lesson_id]
        lesson.status = LessonStatus.REJECTED
        lesson.reviewed_at = datetime.now().isoformat()
        lesson.reviewed_by = reviewer_id
        lesson.review_notes = reason

        self._save()
        return True

    def get_pending_review(self) -> List[Lesson]:
        """Get all lessons awaiting review."""
        return [
            lesson for lesson in self.lessons.values()
            if lesson.status == LessonStatus.PROPOSED
        ]

    def get_approved(
        self,
        workflow_cluster: Optional[str] = None,
        domain_tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Lesson]:
        """
        Get approved lessons, optionally filtered.

        Args:
            workflow_cluster: Filter by cluster (code, content, analysis)
            domain_tags: Filter by domain tags
            limit: Maximum number to return

        Returns:
            List of approved lessons, sorted by usage_count (most used first)
        """
        lessons = [
            lesson for lesson in self.lessons.values()
            if lesson.status == LessonStatus.APPROVED
        ]

        # Filter by cluster
        if workflow_cluster:
            lessons = [
                l for l in lessons
                if l.metadata.workflow_cluster == workflow_cluster
            ]

        # Filter by domain tags
        if domain_tags:
            lessons = [
                l for l in lessons
                if any(tag in l.metadata.domain_tags for tag in domain_tags)
            ]

        # Sort by usage count (most used first)
        lessons.sort(key=lambda l: l.usage_count, reverse=True)

        return lessons[:limit]

    def record_usage(self, lesson_id: str):
        """Record that a lesson was used."""
        if lesson_id in self.lessons:
            lesson = self.lessons[lesson_id]
            lesson.usage_count += 1
            lesson.last_used_at = datetime.now().isoformat()
            self._save()

    def record_feedback(self, lesson_id: str, effectiveness: float):
        """
        Record human feedback on lesson effectiveness.

        Args:
            lesson_id: Lesson identifier
            effectiveness: Score from 0.0 (not helpful) to 1.0 (very helpful)
        """
        if lesson_id in self.lessons:
            lesson = self.lessons[lesson_id]
            # Simple averaging for now
            if lesson.effectiveness_score is None:
                lesson.effectiveness_score = effectiveness
            else:
                # Weighted average (new feedback has 30% weight)
                lesson.effectiveness_score = (
                    0.7 * lesson.effectiveness_score + 0.3 * effectiveness
                )
            self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get lesson statistics."""
        total = len(self.lessons)
        by_status = {}
        for status in LessonStatus:
            by_status[status.value] = len([
                l for l in self.lessons.values()
                if l.status == status
            ])

        by_type = {}
        for lesson_type in LessonType:
            by_type[lesson_type.value] = len([
                l for l in self.lessons.values()
                if l.type == lesson_type and l.status == LessonStatus.APPROVED
            ])

        return {
            "total_lessons": total,
            "by_status": by_status,
            "by_type": by_type,
            "storage_path": str(self.storage_path),
        }
