"""
State Management - SQLite-based persistence for workflow state.

Following antfarm pattern: "YAML + SQLite + cron. That's it."
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


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
    error: Optional[str] = None


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
    completed_at: Optional[str] = None
    error: Optional[str] = None


class StateManager:
    """SQLite-based state persistence for workflow runs."""

    def __init__(self, db_path: Optional[Path] = None):
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
                    error TEXT
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
            conn.commit()

    def create_run(self, run: WorkflowRun) -> str:
        """Create a new workflow run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO workflow_runs
                (id, workflow_id, task, status, current_step, total_steps, context, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.id, run.workflow_id, run.task, run.status.value,
                run.current_step, run.total_steps, json.dumps(run.context),
                run.created_at, run.updated_at, run.error
            ))
            conn.commit()
        return run.id

    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Get a workflow run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE id = ?", (run_id,)
            ).fetchone()

            if row:
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
                    error=row["error"]
                )
        return None

    def update_run(self, run_id: str, **updates) -> bool:
        """Update a workflow run."""
        if "context" in updates and isinstance(updates["context"], dict):
            updates["context"] = json.dumps(updates["context"])
        if "status" in updates and isinstance(updates["status"], StepStatus):
            updates["status"] = updates["status"].value

        updates["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [run_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"UPDATE workflow_runs SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0

    def save_step_result(self, result: StepResult) -> int:
        """Save a step execution result."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO step_results
                (run_id, step_id, agent, status, input_context, output, started_at, completed_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.run_id, result.step_id, result.agent, result.status.value,
                result.input_context, result.output, result.started_at,
                result.completed_at, result.error
            ))
            conn.commit()
            return cursor.lastrowid

    def get_step_results(self, run_id: str) -> list[StepResult]:
        """Get all step results for a run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM step_results WHERE run_id = ? ORDER BY id",
                (run_id,)
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
                    error=row["error"]
                )
                for row in rows
            ]

    def list_runs(
        self,
        status: Optional[StepStatus] = None,
        workflow_id: Optional[str] = None,
        limit: int = 50
    ) -> list[WorkflowRun]:
        """List workflow runs with optional filters."""
        query = "SELECT * FROM workflow_runs WHERE 1=1"
        params = []

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

            return [
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
                    error=row["error"]
                )
                for row in rows
            ]

    def get_stats(self) -> dict[str, Any]:
        """Get workflow execution statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0]
            by_status = {}
            for status in StepStatus:
                count = conn.execute(
                    "SELECT COUNT(*) FROM workflow_runs WHERE status = ?",
                    (status.value,)
                ).fetchone()[0]
                by_status[status.value] = count

            return {
                "total_runs": total,
                "by_status": by_status,
                "db_path": str(self.db_path)
            }
