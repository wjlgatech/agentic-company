"""
PostgreSQL database models and connection management.

Provides async database operations with SQLAlchemy.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from orchestration.config import get_config

Base = declarative_base()


# ============== Models ==============


class WorkflowRun(Base):
    """Workflow execution record."""

    __tablename__ = "workflow_runs"

    id = Column(String(64), primary_key=True)
    workflow_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    input_data = Column(Text)
    output_data = Column(Text)
    config = Column(JSON, default={})
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)
    created_by = Column(String(255))

    # Relationships
    steps = relationship(
        "WorkflowStep", back_populates="workflow_run", cascade="all, delete-orphan"
    )
    approvals = relationship("ApprovalRecord", back_populates="workflow_run")

    __table_args__ = (
        Index("idx_workflow_runs_created", "started_at"),
        Index("idx_workflow_runs_status_name", "status", "workflow_name"),
    )


class WorkflowStep(Base):
    """Individual step within a workflow."""

    __tablename__ = "workflow_steps"

    id = Column(String(64), primary_key=True)
    workflow_run_id = Column(String(64), ForeignKey("workflow_runs.id"), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_order = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    input_data = Column(Text)
    output_data = Column(Text)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)
    guardrail_results = Column(JSON, default=[])
    evaluation_result = Column(JSON)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="steps")


class MemoryEntry(Base):
    """Persistent memory entry."""

    __tablename__ = "memory_entries"

    id = Column(String(64), primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON)  # Vector stored as JSON array
    metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    created_by = Column(String(255))

    __table_args__ = (
        Index("idx_memory_entries_created", "created_at"),
        Index("idx_memory_entries_expires", "expires_at"),
    )


class ApprovalRecord(Base):
    """Approval request record."""

    __tablename__ = "approval_records"

    id = Column(String(64), primary_key=True)
    workflow_run_id = Column(String(64), ForeignKey("workflow_runs.id"))
    step_name = Column(String(255), nullable=False)
    content = Column(Text)
    status = Column(String(50), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    decided_at = Column(DateTime)
    decided_by = Column(String(255))
    reason = Column(Text)
    metadata = Column(JSON, default={})

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="approvals")

    __table_args__ = (
        Index("idx_approval_records_status", "status"),
        Index("idx_approval_records_created", "created_at"),
    )


class MetricSnapshot(Base):
    """Metric snapshot for historical tracking."""

    __tablename__ = "metric_snapshots"

    id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    labels = Column(JSON, default={})


class AuditLog(Base):
    """Audit log for tracking changes."""

    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(64))
    user_id = Column(String(255))
    details = Column(JSON, default={})
    ip_address = Column(String(45))


# ============== Database Connection ==============

_engine = None
_session_factory = None


def get_database_url() -> str:
    """Get database URL from config."""
    config = get_config()
    url = config.memory.database_url or os.getenv("DATABASE_URL")
    if url and url.startswith("postgresql://"):
        # Convert to async URL
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url or "postgresql+asyncpg://agentic:agentic@localhost:5432/agentic"


async def init_db() -> None:
    """Initialize database connection and create tables."""
    global _engine, _session_factory

    database_url = get_database_url()
    _engine = create_async_engine(
        database_url,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        pool_size=5,
        max_overflow=10,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connection."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def get_session():
    """Get database session."""
    if _session_factory is None:
        await init_db()

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============== Repository Classes ==============


class WorkflowRepository:
    """Repository for workflow operations."""

    @staticmethod
    async def create(
        id: str,
        workflow_name: str,
        input_data: str,
        config: dict | None = None,
    ) -> WorkflowRun:
        """Create a new workflow run."""
        async with get_session() as session:
            run = WorkflowRun(
                id=id,
                workflow_name=workflow_name,
                input_data=input_data,
                config=config or {},
            )
            session.add(run)
            return run

    @staticmethod
    async def get(id: str) -> WorkflowRun | None:
        """Get workflow run by ID."""
        async with get_session() as session:
            return await session.get(WorkflowRun, id)

    @staticmethod
    async def update_status(
        id: str,
        status: str,
        output_data: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update workflow run status."""
        async with get_session() as session:
            run = await session.get(WorkflowRun, id)
            if run:
                run.status = status
                run.output_data = output_data
                run.error_message = error_message
                if status in ["completed", "failed"]:
                    run.completed_at = datetime.utcnow()
                    if run.started_at:
                        run.duration_ms = (
                            run.completed_at - run.started_at
                        ).total_seconds() * 1000


class MemoryRepository:
    """Repository for memory operations."""

    @staticmethod
    async def store(
        id: str,
        content: str,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        """Store a memory entry."""
        async with get_session() as session:
            entry = MemoryEntry(
                id=id,
                content=content,
                tags=tags or [],
                metadata=metadata or {},
            )
            session.add(entry)
            return entry

    @staticmethod
    async def search(query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search memory entries."""
        from sqlalchemy import or_, select

        async with get_session() as session:
            stmt = (
                select(MemoryEntry)
                .where(
                    or_(
                        MemoryEntry.content.ilike(f"%{query}%"),
                        MemoryEntry.tags.contains([query]),
                    )
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()


class ApprovalRepository:
    """Repository for approval operations."""

    @staticmethod
    async def create(
        id: str,
        workflow_run_id: str | None,
        step_name: str,
        content: str,
        expires_at: datetime | None = None,
    ) -> ApprovalRecord:
        """Create an approval request."""
        async with get_session() as session:
            record = ApprovalRecord(
                id=id,
                workflow_run_id=workflow_run_id,
                step_name=step_name,
                content=content,
                expires_at=expires_at,
            )
            session.add(record)
            return record

    @staticmethod
    async def list_pending() -> list[ApprovalRecord]:
        """List pending approval requests."""
        from sqlalchemy import select

        async with get_session() as session:
            stmt = (
                select(ApprovalRecord)
                .where(ApprovalRecord.status == "pending")
                .order_by(ApprovalRecord.created_at.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def decide(
        id: str,
        approved: bool,
        decided_by: str,
        reason: str = "",
    ) -> ApprovalRecord | None:
        """Record approval decision."""
        async with get_session() as session:
            record = await session.get(ApprovalRecord, id)
            if record and record.status == "pending":
                record.status = "approved" if approved else "rejected"
                record.decided_at = datetime.utcnow()
                record.decided_by = decided_by
                record.reason = reason
                return record
            return None
