"""
Caching module for performance optimization.

Provides in-memory and Redis-backed caching with TTL support.
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any


@dataclass
class CacheEntry:
    """A cached value with metadata."""

    value: Any
    created_at: float
    expires_at: float | None = None
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheBackend(ABC):
    """Abstract cache backend."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class LocalCache(CacheBackend):
    """In-memory cache implementation."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self._cache.get(key)

        if entry is None:
            self._stats["misses"] += 1
            return None

        if entry.is_expired:
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        entry.hits += 1
        self._stats["hits"] += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl
        elif self.default_ttl:
            expires_at = time.time() + self.default_ttl

        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
        )

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return False
        if entry.is_expired:
            del self._cache[key]
            return False
        return True

    def _evict_oldest(self) -> None:
        """Evict the oldest entry."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": hit_rate,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


class RedisCache(CacheBackend):
    """Redis-backed cache implementation."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "agentic:cache:",
        default_ttl: int = 300,
    ):
        self.redis_url = redis_url
        self.prefix = prefix
        self.default_ttl = default_ttl
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

    def _key(self, key: str) -> str:
        """Prefix the key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        data = self.client.get(self._key(key))
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        data = json.dumps(value)
        if ttl:
            self.client.setex(self._key(key), ttl, data)
        else:
            self.client.set(self._key(key), data)

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return self.client.delete(self._key(key)) > 0

    def clear(self) -> None:
        """Clear all cache entries with prefix."""
        pattern = f"{self.prefix}*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.client.exists(self._key(key)) > 0


# Global cache instance
_cache: CacheBackend | None = None


def get_cache() -> CacheBackend:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = LocalCache()
    return _cache


def set_cache(cache: CacheBackend) -> None:
    """Set the global cache instance."""
    global _cache
    _cache = cache


# ============== Caching Decorators ==============


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Callable[..., str] | None = None,
):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Hash long keys
            if len(cache_key) > 200:
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def cached_async(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Callable[..., str] | None = None,
):
    """Decorator to cache async function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Hash long keys
            if len(cache_key) > 200:
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache entries matching pattern."""
    cache = get_cache()
    if isinstance(cache, LocalCache):
        keys_to_delete = [key for key in cache._cache.keys() if pattern in key]
        for key in keys_to_delete:
            cache.delete(key)
        return len(keys_to_delete)
    elif isinstance(cache, RedisCache):
        full_pattern = f"{cache.prefix}{pattern}*"
        keys = cache.client.keys(full_pattern)
        if keys:
            cache.client.delete(*keys)
            return len(keys)
    return 0


# ============== Response Caching for FastAPI ==============


class CacheMiddleware:
    """Middleware for caching API responses."""

    def __init__(
        self,
        cache: CacheBackend,
        ttl: int = 60,
        cacheable_methods: set = None,
        cacheable_status_codes: set = None,
    ):
        self.cache = cache
        self.ttl = ttl
        self.cacheable_methods = cacheable_methods or {"GET"}
        self.cacheable_status_codes = cacheable_status_codes or {200}

    def should_cache(self, request, response) -> bool:
        """Determine if response should be cached."""
        if request.method not in self.cacheable_methods:
            return False
        if response.status_code not in self.cacheable_status_codes:
            return False
        # Don't cache if Cache-Control: no-store
        if "no-store" in request.headers.get("Cache-Control", ""):
            return False
        return True

    def get_cache_key(self, request) -> str:
        """Generate cache key for request."""
        return f"response:{request.method}:{request.url.path}:{request.url.query}"
