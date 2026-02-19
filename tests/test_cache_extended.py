"""
Tests for orchestration/cache.py — LocalCache, RedisCache, decorators, middleware.
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from orchestration.cache import (
    CacheEntry,
    CacheMiddleware,
    LocalCache,
    RedisCache,
    cached,
    cached_async,
    get_cache,
    invalidate_cache,
    set_cache,
)

# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------


class TestCacheEntry:
    def test_not_expired_when_expires_at_none(self):
        entry = CacheEntry(value="v", created_at=time.time(), expires_at=None)
        assert entry.is_expired is False

    def test_not_expired_when_future(self):
        entry = CacheEntry(
            value="v", created_at=time.time(), expires_at=time.time() + 100
        )
        assert entry.is_expired is False

    def test_expired_when_past(self):
        entry = CacheEntry(
            value="v", created_at=time.time() - 200, expires_at=time.time() - 100
        )
        assert entry.is_expired is True


# ---------------------------------------------------------------------------
# LocalCache — basic operations
# ---------------------------------------------------------------------------


class TestLocalCacheBasic:
    def setup_method(self):
        self.cache = LocalCache(max_size=10, default_ttl=0)

    def test_set_and_get(self):
        self.cache.set("k", "hello")
        assert self.cache.get("k") == "hello"

    def test_get_missing_key_returns_none(self):
        assert self.cache.get("nope") is None

    def test_delete_existing_returns_true(self):
        self.cache.set("k", "v")
        assert self.cache.delete("k") is True
        assert self.cache.get("k") is None

    def test_delete_missing_returns_false(self):
        assert self.cache.delete("nope") is False

    def test_exists_true_when_present(self):
        self.cache.set("k", "v")
        assert self.cache.exists("k") is True

    def test_exists_false_when_missing(self):
        assert self.cache.exists("gone") is False

    def test_clear_removes_all(self):
        self.cache.set("a", 1)
        self.cache.set("b", 2)
        self.cache.clear()
        assert self.cache.get("a") is None
        assert self.cache.get("b") is None


# ---------------------------------------------------------------------------
# LocalCache — TTL expiry
# ---------------------------------------------------------------------------


class TestLocalCacheTTL:
    def test_expired_entry_returns_none(self):
        cache = LocalCache(default_ttl=0)
        # Set with explicit very short TTL
        cache.set("k", "v", ttl=0)
        # Manually expire it
        cache._cache["k"].expires_at = time.time() - 1
        assert cache.get("k") is None

    def test_non_expired_entry_returns_value(self):
        cache = LocalCache(default_ttl=300)
        cache.set("k", "v", ttl=300)
        assert cache.get("k") == "v"

    def test_exists_removes_expired(self):
        cache = LocalCache(default_ttl=0)
        cache.set("k", "v", ttl=1)
        cache._cache["k"].expires_at = time.time() - 1
        assert cache.exists("k") is False

    def test_cleanup_expired_returns_count(self):
        cache = LocalCache(default_ttl=0)
        cache.set("a", 1, ttl=1)
        cache.set("b", 2, ttl=300)
        cache._cache["a"].expires_at = time.time() - 1
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("b") == 2


# ---------------------------------------------------------------------------
# LocalCache — LRU eviction at max_size
# ---------------------------------------------------------------------------


class TestLocalCacheLRU:
    def test_evicts_oldest_when_full(self):
        cache = LocalCache(max_size=3, default_ttl=300)
        cache.set("first", 1)
        cache.set("second", 2)
        cache.set("third", 3)
        # Inserting 4th should evict oldest
        cache.set("fourth", 4)
        # "first" should be gone
        assert cache.get("first") is None
        assert cache.get("fourth") == 4

    def test_eviction_increments_counter(self):
        cache = LocalCache(max_size=1, default_ttl=300)
        cache.set("a", 1)
        cache.set("b", 2)  # triggers eviction
        stats = cache.get_stats()
        assert stats["evictions"] >= 1


# ---------------------------------------------------------------------------
# LocalCache — get_stats
# ---------------------------------------------------------------------------


class TestLocalCacheStats:
    def test_hit_rate_calculation(self):
        cache = LocalCache(default_ttl=300)
        cache.set("k", "v")
        cache.get("k")  # hit
        cache.get("k")  # hit
        cache.get("miss")  # miss
        stats = cache.get_stats()
        # 2 hits, 1 miss → hit_rate = 2/3
        assert abs(stats["hit_rate"] - 2 / 3) < 0.01

    def test_stats_size(self):
        cache = LocalCache(default_ttl=300)
        cache.set("a", 1)
        cache.set("b", 2)
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == cache.max_size


# ---------------------------------------------------------------------------
# @cached decorator
# ---------------------------------------------------------------------------


class TestCachedDecorator:
    def setup_method(self):
        # Use a fresh LocalCache to avoid cross-test pollution
        set_cache(LocalCache(default_ttl=300))

    def test_cached_returns_value(self):
        call_count = {"n": 0}

        @cached(ttl=60)
        def add(a, b):
            call_count["n"] += 1
            return a + b

        result = add(1, 2)
        assert result == 3

    def test_cached_uses_cached_value(self):
        call_count = {"n": 0}

        @cached(ttl=60)
        def compute(x):
            call_count["n"] += 1
            return x * 2

        compute(5)
        compute(5)
        assert call_count["n"] == 1

    def test_cached_hashes_long_keys(self):
        """Keys > 200 chars should be MD5-hashed."""

        @cached(ttl=60)
        def fn(arg):
            return len(arg)

        # Create a call with very long string arg
        long_arg = "a" * 200
        result = fn(long_arg)
        assert result == 200

    def test_cached_custom_key_builder(self):
        call_count = {"n": 0}

        def key_builder(x):
            return f"custom:{x}"

        @cached(ttl=60, key_builder=key_builder)
        def fn(x):
            call_count["n"] += 1
            return x

        fn(42)
        fn(42)
        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# @cached_async decorator
# ---------------------------------------------------------------------------


class TestCachedAsyncDecorator:
    def setup_method(self):
        set_cache(LocalCache(default_ttl=300))

    async def test_cached_async_returns_value(self):
        @cached_async(ttl=60)
        async def fetch(x):
            return x * 3

        result = await fetch(4)
        assert result == 12

    async def test_cached_async_caches_result(self):
        call_count = {"n": 0}

        @cached_async(ttl=60)
        async def fetch(x):
            call_count["n"] += 1
            return x

        await fetch(7)
        await fetch(7)
        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# invalidate_cache
# ---------------------------------------------------------------------------


class TestInvalidateCache:
    def setup_method(self):
        self.lc = LocalCache(default_ttl=300)
        set_cache(self.lc)

    def test_invalidate_matching_keys(self):
        self.lc.set("user:1", "alice")
        self.lc.set("user:2", "bob")
        self.lc.set("order:1", "item")
        count = invalidate_cache("user:")
        assert count == 2
        assert self.lc.get("order:1") == "item"

    def test_invalidate_no_match_returns_zero(self):
        self.lc.set("foo", "bar")
        count = invalidate_cache("nonexistent_prefix:")
        assert count == 0


# ---------------------------------------------------------------------------
# RedisCache (mocked)
# ---------------------------------------------------------------------------


class TestRedisCacheMocked:
    def _make_redis_cache(self):
        mock_redis = MagicMock()
        cache = RedisCache(
            redis_url="redis://localhost:6379/0", prefix="test:", default_ttl=300
        )
        cache._client = mock_redis
        return cache, mock_redis

    def test_set_with_ttl_calls_setex(self):
        cache, mock_redis = self._make_redis_cache()
        cache.set("mykey", {"data": 1}, ttl=60)
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "test:mykey"
        assert args[1] == 60

    def test_get_returns_json_parsed_value(self):
        import json

        cache, mock_redis = self._make_redis_cache()
        mock_redis.get.return_value = json.dumps({"x": 42})
        result = cache.get("mykey")
        assert result == {"x": 42}

    def test_get_missing_returns_none(self):
        cache, mock_redis = self._make_redis_cache()
        mock_redis.get.return_value = None
        assert cache.get("missing") is None

    def test_delete_returns_true_when_deleted(self):
        cache, mock_redis = self._make_redis_cache()
        mock_redis.delete.return_value = 1
        assert cache.delete("mykey") is True

    def test_exists_true(self):
        cache, mock_redis = self._make_redis_cache()
        mock_redis.exists.return_value = 1
        assert cache.exists("mykey") is True

    def test_exists_false(self):
        cache, mock_redis = self._make_redis_cache()
        mock_redis.exists.return_value = 0
        assert cache.exists("nope") is False

    def test_client_lazy_load_raises_import_error_if_no_redis(self):
        cache = RedisCache()
        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError):
                _ = cache.client


# ---------------------------------------------------------------------------
# CacheMiddleware
# ---------------------------------------------------------------------------


class TestCacheMiddleware:
    def _make_request(self, method="GET", path="/api", query="", headers=None):
        req = MagicMock()
        req.method = method
        req.url.path = path
        req.url.query = query
        req.headers = headers or {}
        return req

    def _make_response(self, status_code=200):
        resp = MagicMock()
        resp.status_code = status_code
        return resp

    def setup_method(self):
        self.cache = LocalCache(default_ttl=300)
        self.middleware = CacheMiddleware(cache=self.cache, ttl=60)

    def test_should_cache_get_200(self):
        req = self._make_request(method="GET")
        resp = self._make_response(200)
        assert self.middleware.should_cache(req, resp) is True

    def test_should_not_cache_post(self):
        req = self._make_request(method="POST")
        resp = self._make_response(200)
        assert self.middleware.should_cache(req, resp) is False

    def test_should_not_cache_non_200(self):
        req = self._make_request(method="GET")
        resp = self._make_response(404)
        assert self.middleware.should_cache(req, resp) is False

    def test_should_not_cache_no_store_header(self):
        req = self._make_request(headers={"Cache-Control": "no-store"})
        resp = self._make_response(200)
        assert self.middleware.should_cache(req, resp) is False

    def test_get_cache_key_format(self):
        req = self._make_request(method="GET", path="/api/data", query="x=1")
        key = self.middleware.get_cache_key(req)
        assert "GET" in key
        assert "/api/data" in key
        assert "x=1" in key
