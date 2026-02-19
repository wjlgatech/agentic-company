"""
Tests for orchestration/memory.py — MemoryEntry, LocalMemoryStore, RedisMemoryStore,
create_memory_store factory.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from orchestration.memory import (
    LocalMemoryStore,
    MemoryEntry,
    RedisMemoryStore,
    create_memory_store,
)

# ---------------------------------------------------------------------------
# MemoryEntry — to_dict / from_dict round-trip
# ---------------------------------------------------------------------------


class TestMemoryEntry:
    def _make_entry(self, **kwargs) -> MemoryEntry:
        defaults = dict(
            id="test-id",
            content="Test content",
            metadata={"key": "val"},
            tags=["tag1", "tag2"],
        )
        defaults.update(kwargs)
        return MemoryEntry(**defaults)

    def test_to_dict_has_required_keys(self):
        entry = self._make_entry()
        d = entry.to_dict()
        for key in ("id", "content", "metadata", "tags", "created_at", "updated_at"):
            assert key in d

    def test_to_dict_iso_timestamps(self):
        entry = self._make_entry()
        d = entry.to_dict()
        # Should be parseable ISO strings
        datetime.fromisoformat(d["created_at"])
        datetime.fromisoformat(d["updated_at"])

    def test_to_dict_expires_at_none_when_not_set(self):
        entry = self._make_entry()
        d = entry.to_dict()
        assert d["expires_at"] is None

    def test_to_dict_expires_at_iso_when_set(self):
        entry = self._make_entry(expires_at=datetime(2099, 1, 1))
        d = entry.to_dict()
        assert d["expires_at"] is not None
        datetime.fromisoformat(d["expires_at"])

    def test_from_dict_round_trip(self):
        entry = self._make_entry()
        d = entry.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.id == entry.id
        assert restored.content == entry.content
        assert restored.metadata == entry.metadata
        assert restored.tags == entry.tags

    def test_from_dict_missing_dates_uses_now(self):
        d = {"id": "x", "content": "hello"}
        entry = MemoryEntry.from_dict(d)
        assert entry.id == "x"
        assert entry.content == "hello"

    def test_from_dict_with_expires_at(self):
        expiry = datetime(2099, 6, 15, 12, 0, 0)
        d = {"id": "x", "content": "c", "expires_at": expiry.isoformat()}
        entry = MemoryEntry.from_dict(d)
        assert entry.expires_at == expiry


# ---------------------------------------------------------------------------
# LocalMemoryStore
# ---------------------------------------------------------------------------


class TestLocalMemoryStore:
    def setup_method(self):
        self.store = LocalMemoryStore(max_entries=100)

    def _make_entry(self, eid="e1", content="hello world") -> MemoryEntry:
        return MemoryEntry(id=eid, content=content)

    def test_store_and_retrieve(self):
        entry = self._make_entry()
        self.store.store(entry)
        retrieved = self.store.retrieve("e1")
        assert retrieved is not None
        assert retrieved.content == "hello world"

    def test_retrieve_missing_returns_none(self):
        assert self.store.retrieve("nope") is None

    def test_delete_existing_returns_true(self):
        self.store.store(self._make_entry())
        assert self.store.delete("e1") is True
        assert self.store.retrieve("e1") is None

    def test_delete_missing_returns_false(self):
        assert self.store.delete("nope") is False

    def test_count(self):
        self.store.store(self._make_entry("a"))
        self.store.store(self._make_entry("b"))
        assert self.store.count() == 2

    def test_clear(self):
        self.store.store(self._make_entry("a"))
        self.store.clear()
        assert self.store.count() == 0

    def test_get_recent(self):
        self.store.store(self._make_entry("a"))
        self.store.store(self._make_entry("b"))
        recent = self.store.get_recent(limit=1)
        assert len(recent) == 1

    def test_list_all_ordering(self):
        self.store.store(self._make_entry("a"))
        self.store.store(self._make_entry("b"))
        entries = self.store.list_all()
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# LocalMemoryStore — eviction
# ---------------------------------------------------------------------------


class TestLocalMemoryStoreEviction:
    def test_eviction_at_max_entries(self):
        store = LocalMemoryStore(max_entries=2)
        store.store(MemoryEntry(id="first", content="first"))
        store.store(MemoryEntry(id="second", content="second"))
        store.store(MemoryEntry(id="third", content="third"))
        # One entry should have been evicted
        assert store.count() == 2
        # "third" should still be there
        assert store.retrieve("third") is not None


# ---------------------------------------------------------------------------
# LocalMemoryStore — search
# ---------------------------------------------------------------------------


class TestLocalMemoryStoreSearch:
    def setup_method(self):
        self.store = LocalMemoryStore()

    def test_search_word_overlap(self):
        self.store.store(MemoryEntry(id="e1", content="python programming language"))
        self.store.store(MemoryEntry(id="e2", content="java enterprise beans"))
        results = self.store.search("python language")
        ids = [e.id for e in results]
        assert "e1" in ids

    def test_search_tag_boost(self):
        self.store.store(
            MemoryEntry(id="e1", content="nothing relevant", tags=["python"])
        )
        results = self.store.search("python")
        ids = [e.id for e in results]
        assert "e1" in ids

    def test_search_excludes_expired(self):
        expired_entry = MemoryEntry(
            id="expired",
            content="hello world",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        self.store.store(expired_entry)
        results = self.store.search("hello")
        ids = [e.id for e in results]
        assert "expired" not in ids

    def test_search_no_match_returns_empty(self):
        self.store.store(MemoryEntry(id="e1", content="completely unrelated stuff"))
        results = self.store.search("xyz_nonexistent_term")
        assert results == []


# ---------------------------------------------------------------------------
# LocalMemoryStore — remember shortcut
# ---------------------------------------------------------------------------


class TestRemember:
    def test_remember_stores_entry(self):
        store = LocalMemoryStore()
        eid = store.remember("Some important fact", tags=["fact"])
        assert eid is not None
        entry = store.retrieve(eid)
        assert entry is not None
        assert entry.content == "Some important fact"


# ---------------------------------------------------------------------------
# RedisMemoryStore (mocked)
# ---------------------------------------------------------------------------


class TestRedisMemoryStoreMocked:
    def _make_store(self):
        mock_redis = MagicMock()
        store = RedisMemoryStore(
            redis_url="redis://localhost:6379/0", prefix="test:mem:"
        )
        store._client = mock_redis
        return store, mock_redis

    def test_store_without_ttl_calls_set(self):
        store, mock_redis = self._make_store()
        entry = MemoryEntry(id="e1", content="hello")
        store.store(entry)
        mock_redis.set.assert_called_once()
        # index add
        mock_redis.sadd.assert_called_once()

    def test_store_with_ttl_calls_setex(self):
        store, mock_redis = self._make_store()
        entry = MemoryEntry(
            id="e2",
            content="expiring",
            expires_at=datetime.now() + timedelta(seconds=60),
        )
        store.store(entry)
        mock_redis.setex.assert_called_once()

    def test_store_already_expired_skips(self):
        store, mock_redis = self._make_store()
        entry = MemoryEntry(
            id="old",
            content="gone",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        result = store.store(entry)
        # Should return entry.id without calling set
        assert result == "old"
        mock_redis.set.assert_not_called()
        mock_redis.setex.assert_not_called()

    def test_retrieve_returns_entry(self):
        store, mock_redis = self._make_store()
        entry = MemoryEntry(id="e3", content="data")
        mock_redis.get.return_value = json.dumps(entry.to_dict())
        retrieved = store.retrieve("e3")
        assert retrieved is not None
        assert retrieved.content == "data"

    def test_retrieve_missing_returns_none(self):
        store, mock_redis = self._make_store()
        mock_redis.get.return_value = None
        assert store.retrieve("nope") is None

    def test_delete_removes_from_index(self):
        store, mock_redis = self._make_store()
        mock_redis.delete.return_value = 1
        result = store.delete("e1")
        assert result is True
        mock_redis.srem.assert_called_once()

    def test_search_returns_matching_entries(self):
        store, mock_redis = self._make_store()
        entry = MemoryEntry(id="e1", content="python rocks")
        mock_redis.smembers.return_value = {"e1"}
        mock_redis.get.return_value = json.dumps(entry.to_dict())
        results = store.search("python")
        assert len(results) == 1

    def test_client_lazy_load_raises_import_error(self):
        store = RedisMemoryStore()
        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError):
                _ = store.client


# ---------------------------------------------------------------------------
# create_memory_store factory
# ---------------------------------------------------------------------------


class TestCreateMemoryStore:
    def test_local_backend(self):
        store = create_memory_store("local")
        assert isinstance(store, LocalMemoryStore)

    def test_redis_backend(self):
        store = create_memory_store("redis", redis_url="redis://localhost:6379/0")
        assert isinstance(store, RedisMemoryStore)

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            create_memory_store("unknown_backend")
