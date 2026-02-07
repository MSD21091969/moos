"""Redis client for caching and session management.

Provides connection pooling, async operations, and automatic serialization.
"""

import json
import logging
from typing import Any, Optional
from contextlib import asynccontextmanager

import redis.asyncio as redis  # type: ignore[import-untyped]
from redis.asyncio.connection import ConnectionPool  # type: ignore[import-untyped]
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and JSON serialization."""

    def __init__(self):
        """Initialize Redis client with connection pool."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Create Redis connection pool and client."""
        if self._client:
            return

        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            logger.info("Redis connection established")

        except Exception as e:
            logger.error("Failed to connect to Redis", extra={"error": str(e)})
            raise

    async def disconnect(self):
        """Close Redis connection pool."""
        if self._client:
            await self._client.aclose()
            logger.info("Redis connection closed")
        if self._pool:
            await self._pool.aclose()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis and deserialize JSON.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found
        """
        if self._client is None:
            return None
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON for key", extra={"key": key})
            return value
        except Exception as e:
            logger.error("Redis GET error", extra={"key": key, "error": str(e)})
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in Redis with JSON serialization.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: from settings)

        Returns:
            True if successful
        """
        if self._client is None:
            return False
        try:
            # Serialize Pydantic models and dicts to JSON
            if isinstance(value, BaseModel):
                serialized = value.model_dump_json()
            else:
                serialized = json.dumps(value)

            ttl = ttl or settings.REDIS_DEFAULT_TTL
            return await self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error("Redis SET error", extra={"key": key, "error": str(e)})
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            return 0
        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.error("Redis DELETE error", extra={"error": str(e)})
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        if self._client is None:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error("Redis EXISTS error", extra={"key": key, "error": str(e)})
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time on a key.

        Args:
            key: Key to expire
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if self._client is None:
            return False
        try:
            return await self._client.expire(key, ttl)
        except Exception as e:
            logger.error("Redis EXPIRE error", extra={"key": key, "error": str(e)})
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment integer value at key.

        Args:
            key: Key to increment
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        if self._client is None:
            return 0
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error("Redis INCR error", extra={"key": key, "error": str(e)})
            return 0

    async def get_many(self, *keys: str) -> list[Optional[Any]]:
        """Get multiple values from Redis.

        Args:
            *keys: Keys to retrieve

        Returns:
            List of deserialized values (None for missing keys)
        """
        if self._client is None:
            return [None] * len(keys)
        try:
            values = await self._client.mget(*keys)
            return [json.loads(v) if v else None for v in values]
        except Exception as e:
            logger.error("Redis MGET error", extra={"error": str(e)})
            return [None] * len(keys)

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set multiple key-value pairs in Redis.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds (applied to all keys)

        Returns:
            True if successful
        """
        if self._client is None:
            return False
        try:
            # Serialize all values
            serialized = {
                k: (v.model_dump_json() if isinstance(v, BaseModel) else json.dumps(v))
                for k, v in mapping.items()
            }

            # Use pipeline for atomic operation
            async with self._client.pipeline() as pipe:
                await pipe.mset(serialized)
                if ttl:
                    for key in serialized.keys():
                        await pipe.expire(key, ttl)
                await pipe.execute()

            return True
        except Exception as e:
            logger.error("Redis MSET error", extra={"error": str(e)})
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*", "session:*")

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            return 0
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Redis CLEAR PATTERN error", extra={"pattern": pattern, "error": str(e)})
            return 0

    @asynccontextmanager
    async def pipeline(self):
        """Context manager for Redis pipeline operations.

        Yields:
            Redis pipeline for batched operations
        """
        if self._client is None:
            # Return a dummy pipeline that does nothing
            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def dummy_pipeline():
                yield None

            async with dummy_pipeline():
                yield None
            return
        async with self._client.pipeline() as pipe:
            yield pipe


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency injection for Redis client.

    Returns:
        Configured Redis client instance
    """
    return redis_client
