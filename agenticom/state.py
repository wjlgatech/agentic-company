"""
State Management - SQLite-based persistence for workflow state.

Following antfarm pattern: "YAML + SQLite + cron. That's it."
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStage(str, Enum):
    """Workflow stages matching the 5-agent pattern."""

    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    TEST = "test"
    REVIEW = "review"


@dataclass
class StageInfo:
    """Information about a workflow stage execution."""

    stage: WorkflowStage
    started_at: str | None = None
    completed_at: str | None = None
    step_id: str | None = None  # The step that triggered this stage
    artifacts: list[str] = None  # Paths to artifacts/documentation

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage": (
                self.stage.value
                if isinstance(self.stage, WorkflowStage)
                else self.stage
            ),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "step_id": self.step_id,
            "artifacts": self.artifacts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StageInfo":
        """Create from dictionary."""
        return cls(
            stage=WorkflowStage(data["stage"]),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            step_id=data.get("step_id"),
            artifacts=data.get("artifacts", []),
        )


@dataclass
class WorkflowRun:
    """A single workflow execution."""

    id: str
    workflow_id: str
    task: str
    status: StepStatus
    current_step: int
    total_steps: int
    context: dict
    created_at: str
    updated_at: str
    error: str | None = None
    stages: dict[str, StageInfo] = None  # Map of stage name -> StageInfo
    current_stage: WorkflowStage | None = None
    loop_counts: dict[str, int] = None  # Track loops per step
    feedback_history: list[dict] = None  # Store failure feedback

    def __post_init__(self):
        if self.stages is None:
            # Initialize all stages as not started
            self.stages = {
                stage.value: StageInfo(stage=stage) for stage in WorkflowStage
            }
        if self.loop_counts is None:
            self.loop_counts = {}
        if self.feedback_history is None:
            self.feedback_history = []

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "task": self.task,
            "status": (
                self.status.value
                if isinstance(self.status, StepStatus)
                else self.status
            ),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "stages": {k: v.to_dict() for k, v in (self.stages or {}).items()},
            "current_stage": self.current_stage.value if self.current_stage else None,
        }

    def start_stage(self, stage: WorkflowStage, step_id: str) -> None:
        """Mark a stage as started."""
        if self.stages is None:
            self.__post_init__()

        stage_key = stage.value
        if stage_key in self.stages:
            self.stages[stage_key].started_at = datetime.now().isoformat()
            self.stages[stage_key].step_id = step_id
        self.current_stage = stage

    def complete_stage(self, stage: WorkflowStage) -> None:
        """Mark a stage as completed."""
        if self.stages is None:
            self.__post_init__()

        stage_key = stage.value
        if stage_key in self.stages:
            self.stages[stage_key].completed_at = datetime.now().isoformat()

    def add_artifact(self, stage: WorkflowStage, artifact_path: str) -> None:
        """Add an artifact to a stage."""
        if self.stages is None:
            self.__post_init__()

        stage_key = stage.value
        if stage_key in self.stages:
            if artifact_path not in self.stages[stage_key].artifacts:
                self.stages[stage_key].artifacts.append(artifact_path)


@dataclass
class StepResult:
    """Result of a single step execution."""

    run_id: str
    step_id: str
    agent: str
    status: StepStatus
    input_context: str
    output: str
    started_at: str
    completed_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "agent": self.agent,
            "status": (
                self.status.value
                if isinstance(self.status, StepStatus)
                else self.status
            ),
            "input_context": self.input_context,
            "output": self.output,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class StateManager:
    """SQLite-based state persistence for workflow runs."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".agenticom" / "state.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    total_steps INTEGER NOT NULL,
                    context TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    stages TEXT DEFAULT '{}',
                    current_stage TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS step_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_context TEXT,
                    output TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error TEXT,
                    FOREIGN KEY (run_id) REFERENCES workflow_runs(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_status ON workflow_runs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_run ON step_results(run_id)
            """)

            # Migration: Add stages and current_stage columns if they don't exist
            try:
                conn.execute(
                    "ALTER TABLE workflow_runs ADD COLUMN stages TEXT DEFAULT '{}'"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE workflow_runs ADD COLUMN current_stage TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    def create_run(self, run: WorkflowRun) -> str:
        """Create a new workflow run."""
        # Ensure stages are initialized
        if run.stages is None:
            run.__post_init__()

        stages_json = json.dumps({k: v.to_dict() for k, v in run.stages.items()})
        current_stage_val = run.current_stage.value if run.current_stage else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs
                (id, workflow_id, task, status, current_step, total_steps, context, created_at, updated_at, error, stages, current_stage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run.id,
                    run.workflow_id,
                    run.task,
                    run.status.value,
                    run.current_step,
                    run.total_steps,
                    json.dumps(run.context),
                    run.created_at,
                    run.updated_at,
                    run.error,
                    stages_json,
                    current_stage_val,
                ),
            )
            conn.commit()
        return run.id

    def get_run(self, run_id: str) -> WorkflowRun | None:
        """Get a workflow run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE id = ?", (run_id,)
            ).fetchone()

            if row:
                # Deserialize stages
                stages_data = json.loads(row["stages"] or "{}")
                stages = (
                    {k: StageInfo.from_dict(v) for k, v in stages_data.items()}
                    if stages_data
                    else None
                )

                # Deserialize current_stage
                current_stage_str = row["current_stage"]
                current_stage = (
                    WorkflowStage(current_stage_str) if current_stage_str else None
                )

                return WorkflowRun(
                    id=row["id"],
                    workflow_id=row["workflow_id"],
                    task=row["task"],
                    status=StepStatus(row["status"]),
                    current_step=row["current_step"],
                    total_steps=row["total_steps"],
                    context=json.loads(row["context"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    error=row["error"],
                    stages=stages,
                    current_stage=current_stage,
                )
        return None

    def update_run(self, run_id: str, **updates) -> bool:
        """Update a workflow run."""
        if "context" in updates and isinstance(updates["context"], dict):
            updates["context"] = json.dumps(updates["context"])
        if "status" in updates and isinstance(updates["status"], StepStatus):
            updates["status"] = updates["status"].value
        if "stages" in updates and isinstance(updates["stages"], dict):
            # Convert StageInfo objects to dict
            stages_dict = {}
            for k, v in updates["stages"].items():
                if isinstance(v, StageInfo):
                    stages_dict[k] = v.to_dict()
                else:
                    stages_dict[k] = v
            updates["stages"] = json.dumps(stages_dict)
        if "current_stage" in updates and isinstance(
            updates["current_stage"], WorkflowStage
        ):
            updates["current_stage"] = updates["current_stage"].value

        updates["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [run_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"UPDATE workflow_runs SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
            return cursor.rowcount > 0

    def save_step_result(self, result: StepResult) -> int:
        """Save a step execution result."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO step_results
                (run_id, step_id, agent, status, input_context, output, started_at, completed_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.run_id,
                    result.step_id,
                    result.agent,
                    result.status.value,
                    result.input_context,
                    result.output,
                    result.started_at,
                    result.completed_at,
                    result.error,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def archive_run(self, run_id: str) -> bool:
        """Archive a workflow run (soft delete)."""
        with sqlite3.connect(self.db_path) as conn:
            # Add is_archived column if it doesn't exist
            try:
                conn.execute(
                    "ALTER TABLE runs ADD COLUMN is_archived INTEGER DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Mark as archived
            conn.execute("UPDATE runs SET is_archived = 1 WHERE id = ?", (run_id,))
            conn.commit()
            return True

    def unarchive_run(self, run_id: str) -> bool:
        """Unarchive a workflow run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE runs SET is_archived = 0 WHERE id = ?", (run_id,))
            conn.commit()
            return True

    def delete_run(self, run_id: str, permanent: bool = False) -> bool:
        """Delete a workflow run.

        Args:
            run_id: Run ID to delete
            permanent: If True, permanently delete. If False, archive instead.
        """
        if permanent:
            with sqlite3.connect(self.db_path) as conn:
                # Delete step results first (foreign key)
                conn.execute("DELETE FROM step_results WHERE run_id = ?", (run_id,))
                # Delete artifacts
                conn.execute("DELETE FROM artifacts WHERE run_id = ?", (run_id,))
                # Delete run
                conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                conn.commit()
                return True
        else:
            # Soft delete = archive
            return self.archive_run(run_id)

    def get_step_results(self, run_id: str) -> list[StepResult]:
        """Get all step results for a run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM step_results WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()

            return [
                StepResult(
                    run_id=row["run_id"],
                    step_id=row["step_id"],
                    agent=row["agent"],
                    status=StepStatus(row["status"]),
                    input_context=row["input_context"],
                    output=row["output"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    error=row["error"],
                )
                for row in rows
            ]

    def list_runs(
        self,
        status: StepStatus | None = None,
        workflow_id: str | None = None,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[WorkflowRun]:
        """List workflow runs with optional filters.

        Args:
            status: Filter by status
            workflow_id: Filter by workflow ID
            limit: Maximum number of runs
            include_archived: If True, include archived runs. Default False.
        """
        query = "SELECT * FROM workflow_runs WHERE 1=1"
        params = []

        # Exclude archived by default
        if not include_archived:
            query += " AND (is_archived IS NULL OR is_archived = 0)"

        if status:
            query += " AND status = ?"
            params.append(status.value)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

            runs = []
            for row in rows:
                # Deserialize stages
                stages_data = json.loads(row["stages"] or "{}")
                stages = (
                    {k: StageInfo.from_dict(v) for k, v in stages_data.items()}
                    if stages_data
                    else None
                )

                # Deserialize current_stage
                current_stage_str = row["current_stage"]
                current_stage = (
                    WorkflowStage(current_stage_str) if current_stage_str else None
                )

                runs.append(
                    WorkflowRun(
                        id=row["id"],
                        workflow_id=row["workflow_id"],
                        task=row["task"],
                        status=StepStatus(row["status"]),
                        current_step=row["current_step"],
                        total_steps=row["total_steps"],
                        context=json.loads(row["context"]),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        error=row["error"],
                        stages=stages,
                        current_stage=current_stage,
                    )
                )

            return runs

    def get_stats(self) -> dict[str, Any]:
        """Get workflow execution statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0]
            by_status = {}
            for status in StepStatus:
                count = conn.execute(
                    "SELECT COUNT(*) FROM workflow_runs WHERE status = ?",
                    (status.value,),
                ).fetchone()[0]
                by_status[status.value] = count

            return {
                "total_runs": total,
                "by_status": by_status,
                "db_path": str(self.db_path),
            }
