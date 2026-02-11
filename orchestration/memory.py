"""
Memory system for storing and retrieving workflow context.

Supports local, Redis, PostgreSQL, and Supabase backends.
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            tags=data.get("tags", []),
        )


class MemoryStore(ABC):
    """Abstract base class for memory stores."""

    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry and return its ID."""
        pass

    @abstractmethod
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for memory entries matching query."""
        pass

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> list[MemoryEntry]:
        """List all memory entries."""
        pass

    def recall(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Alias for search - recall memories matching query."""
        return self.search(query, limit)

    def remember(self, content: str, metadata: Optional[dict] = None, tags: Optional[list[str]] = None) -> str:
        """Store content as a memory entry."""
        entry_id = hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:16]
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
        )
        return self.store(entry)


class LocalMemoryStore(MemoryStore):
    """In-memory storage backend."""

    def __init__(self, max_entries: int = 1000):
        self.entries: dict[str, MemoryEntry] = {}
        self.max_entries = max_entries

    def store(self, entry: MemoryEntry) -> str:
        """Store entry in memory."""
        # Evict oldest if at capacity
        if len(self.entries) >= self.max_entries:
            oldest_id = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].created_at
            )
            del self.entries[oldest_id]

        self.entries[entry.id] = entry
        return entry.id

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry by ID."""
        return self.entries.get(entry_id)

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search entries by content similarity."""
        query_lower = query.lower()
        results = []

        # Copy values to avoid "dictionary changed size during iteration" in concurrent access
        for entry in list(self.entries.values()):
            # Check if expired
            if entry.expires_at and entry.expires_at < datetime.now():
                continue

            # Simple text matching
            score = 0
            content_lower = entry.content.lower()

            # Word overlap scoring
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = query_words & content_words

            if overlap:
                score = len(overlap) / len(query_words)
                results.append((entry, score))

            # Also check tags
            for tag in entry.tags:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    results.append((entry, 0.5))
                    break

        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]

    def delete(self, entry_id: str) -> bool:
        """Delete entry by ID."""
        if entry_id in self.entries:
            del self.entries[entry_id]
            return True
        return False

    def list_all(self, limit: int = 100, offset: int = 0) -> list[MemoryEntry]:
        """List all entries."""
        entries = sorted(
            self.entries.values(),
            key=lambda e: e.created_at,
            reverse=True
        )
        return entries[offset:offset + limit]

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()

    def count(self) -> int:
        """Count total entries."""
        return len(self.entries)


class RedisMemoryStore(MemoryStore):
    """Redis-backed memory store."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "agentic:memory:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._client = None

    @property
    def client(self):
        """Lazy load Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self.redis_url, decode_responses=True)
            except ImportError:
                raise ImportError("Redis support requires: pip install redis")
        return self._client

    def _key(self, entry_id: str) -> str:
        return f"{self.prefix}{entry_id}"

    def store(self, entry: MemoryEntry) -> str:
        """Store entry in Redis."""
        key = self._key(entry.id)
        data = json.dumps(entry.to_dict())

        if entry.expires_at:
            ttl = int((entry.expires_at - datetime.now()).total_seconds())
            if ttl > 0:
                self.client.setex(key, ttl, data)
            else:
                return entry.id  # Already expired
        else:
            self.client.set(key, data)

        # Add to index set
        self.client.sadd(f"{self.prefix}index", entry.id)
        return entry.id

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from Redis."""
        key = self._key(entry_id)
        data = self.client.get(key)
        if data:
            return MemoryEntry.from_dict(json.loads(data))
        return None

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search entries (basic implementation)."""
        results = []
        query_lower = query.lower()

        # Get all entry IDs
        entry_ids = self.client.smembers(f"{self.prefix}index")

        for entry_id in entry_ids:
            entry = self.retrieve(entry_id)
            if entry and query_lower in entry.content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def delete(self, entry_id: str) -> bool:
        """Delete entry from Redis."""
        key = self._key(entry_id)
        deleted = self.client.delete(key)
        self.client.srem(f"{self.prefix}index", entry_id)
        return deleted > 0

    def list_all(self, limit: int = 100, offset: int = 0) -> list[MemoryEntry]:
        """List all entries."""
        entry_ids = list(self.client.smembers(f"{self.prefix}index"))
        entry_ids = entry_ids[offset:offset + limit]

        entries = []
        for entry_id in entry_ids:
            entry = self.retrieve(entry_id)
            if entry:
                entries.append(entry)

        return sorted(entries, key=lambda e: e.created_at, reverse=True)


class PostgresMemoryStore(MemoryStore):
    """PostgreSQL-backed memory store with vector search support."""

    def __init__(self, database_url: str, table_name: str = "memories"):
        self.database_url = database_url
        self.table_name = table_name
        self._engine = None
        self._initialized = False

    async def _ensure_table(self):
        """Ensure the memories table exists."""
        if self._initialized:
            return

        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            self._engine = create_async_engine(self.database_url)

            async with self._engine.begin() as conn:
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id VARCHAR(64) PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{{}}',
                        embedding VECTOR(1536),
                        tags TEXT[] DEFAULT '{{}}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """))
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tags
                    ON {self.table_name} USING GIN(tags)
                """))

            self._initialized = True
        except ImportError:
            raise ImportError("PostgreSQL support requires: pip install asyncpg sqlalchemy[asyncio]")

    def store(self, entry: MemoryEntry) -> str:
        """Store entry (sync wrapper)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._async_store(entry))

    async def _async_store(self, entry: MemoryEntry) -> str:
        """Store entry asynchronously."""
        await self._ensure_table()
        from sqlalchemy import text

        async with self._engine.begin() as conn:
            await conn.execute(
                text(f"""
                    INSERT INTO {self.table_name} (id, content, metadata, tags, expires_at)
                    VALUES (:id, :content, :metadata, :tags, :expires_at)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        tags = EXCLUDED.tags,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": entry.id,
                    "content": entry.content,
                    "metadata": json.dumps(entry.metadata),
                    "tags": entry.tags,
                    "expires_at": entry.expires_at,
                }
            )
        return entry.id

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry (sync wrapper)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._async_retrieve(entry_id))

    async def _async_retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry asynchronously."""
        await self._ensure_table()
        from sqlalchemy import text

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT * FROM {self.table_name} WHERE id = :id"),
                {"id": entry_id}
            )
            row = result.fetchone()
            if row:
                return MemoryEntry(
                    id=row.id,
                    content=row.content,
                    metadata=row.metadata or {},
                    tags=row.tags or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    expires_at=row.expires_at,
                )
        return None

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search entries (sync wrapper)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._async_search(query, limit))

    async def _async_search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search entries using full-text search."""
        await self._ensure_table()
        from sqlalchemy import text

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                    SELECT * FROM {self.table_name}
                    WHERE content ILIKE :pattern
                    OR :query = ANY(tags)
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"pattern": f"%{query}%", "query": query, "limit": limit}
            )
            entries = []
            for row in result.fetchall():
                entries.append(MemoryEntry(
                    id=row.id,
                    content=row.content,
                    metadata=row.metadata or {},
                    tags=row.tags or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    expires_at=row.expires_at,
                ))
            return entries

    def delete(self, entry_id: str) -> bool:
        """Delete entry (sync wrapper)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._async_delete(entry_id))

    async def _async_delete(self, entry_id: str) -> bool:
        """Delete entry asynchronously."""
        await self._ensure_table()
        from sqlalchemy import text

        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(f"DELETE FROM {self.table_name} WHERE id = :id"),
                {"id": entry_id}
            )
            return result.rowcount > 0

    def list_all(self, limit: int = 100, offset: int = 0) -> list[MemoryEntry]:
        """List all entries (sync wrapper)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._async_list_all(limit, offset))

    async def _async_list_all(self, limit: int = 100, offset: int = 0) -> list[MemoryEntry]:
        """List all entries asynchronously."""
        await self._ensure_table()
        from sqlalchemy import text

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                    SELECT * FROM {self.table_name}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"limit": limit, "offset": offset}
            )
            entries = []
            for row in result.fetchall():
                entries.append(MemoryEntry(
                    id=row.id,
                    content=row.content,
                    metadata=row.metadata or {},
                    tags=row.tags or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    expires_at=row.expires_at,
                ))
            return entries


def create_memory_store(backend: str = "local", **kwargs) -> MemoryStore:
    """Factory function to create memory stores."""
    if backend == "local":
        return LocalMemoryStore(**kwargs)
    elif backend == "redis":
        return RedisMemoryStore(**kwargs)
    elif backend == "postgres":
        return PostgresMemoryStore(**kwargs)
    else:
        raise ValueError(f"Unknown memory backend: {backend}")
