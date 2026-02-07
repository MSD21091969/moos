"""Caching decorators and utilities for API endpoints."""

import functools
import hashlib
import logging
from typing import Any, Callable, Optional

from src.core.redis_client import redis_client

logger = logging.getLogger(__name__)


def cache_key(*args, prefix: str = "", **kwargs) -> str:
    """Generate cache key from function arguments.

    Args:
        *args: Positional arguments
        prefix: Key prefix (e.g., "user", "session")
        **kwargs: Keyword arguments

    Returns:
        SHA256 hash-based cache key
    """
    # Create deterministic string from args
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # Hash for consistent key length
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

    return f"{prefix}:{key_hash}" if prefix else key_hash


def cached(
    ttl: int = 300,
    prefix: str = "",
    key_builder: Optional[Callable] = None,
):
    """Decorator to cache function results in Redis.

    Args:
        ttl: Cache time-to-live in seconds (default: 5 minutes)
        prefix: Cache key prefix
        key_builder: Custom function to build cache key

    Example:
        @cached(ttl=600, prefix="user")
        async def get_user(user_id: str):
            return await db.get_user(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Skip 'self' or 'cls' for methods
                cache_args = args[1:] if args and hasattr(args[0], "__dict__") else args
                key = cache_key(*cache_args, prefix=prefix, **kwargs)

            # Try to get from cache
            try:
                cached_value = await redis_client.get(key)
                if cached_value is not None:
                    logger.debug("Cache HIT", extra={"key": key})
                    return cached_value
            except Exception as e:
                logger.warning("Cache GET error", extra={"error": str(e)})

            # Cache miss - call function
            logger.debug("Cache MISS", extra={"key": key})
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                await redis_client.set(key, result, ttl=ttl)
            except Exception as e:
                logger.warning("Cache SET error", extra={"error": str(e)})

            return result

        return wrapper

    return decorator


def invalidate_cache(*keys: str):
    """Decorator to invalidate cache keys after function execution.

    Args:
        *keys: Cache key patterns to invalidate

    Example:
        @invalidate_cache("user:*", "session:*")
        async def update_user(user_id: str, data: dict):
            return await db.update_user(user_id, data)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Execute function
            result = await func(*args, **kwargs)

            # Invalidate cache keys
            try:
                for pattern in keys:
                    deleted = await redis_client.clear_pattern(pattern)
                    if deleted:
                        logger.info(
                            "Invalidated cache keys",
                            extra={"deleted_count": deleted, "pattern": pattern},
                        )
            except Exception as e:
                logger.warning("Cache invalidation error", extra={"error": str(e)})

            return result

        return wrapper

    return decorator


class CacheManager:
    """Helper class for manual cache management."""

    @staticmethod
    async def get_user(user_id: str) -> Optional[dict]:
        """Get user from cache."""
        return await redis_client.get(f"user:{user_id}")

    @staticmethod
    async def set_user(user_id: str, user_data: dict, ttl: int = 3600):
        """Cache user data (1 hour default)."""
        return await redis_client.set(f"user:{user_id}", user_data, ttl=ttl)

    @staticmethod
    async def invalidate_user(user_id: str):
        """Invalidate user cache."""
        return await redis_client.delete(f"user:{user_id}")

    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        """Get session from cache."""
        return await redis_client.get(f"session:{session_id}")

    @staticmethod
    async def set_session(session_id: str, session_data: dict, ttl: int = 1800):
        """Cache session data (30 minutes default)."""
        return await redis_client.set(f"session:{session_id}", session_data, ttl=ttl)

    @staticmethod
    async def invalidate_session(session_id: str):
        """Invalidate session cache."""
        return await redis_client.delete(f"session:{session_id}")

    @staticmethod
    async def get_rate_limit(key: str) -> Optional[int]:
        """Get rate limit counter."""
        value = await redis_client.get(f"rate_limit:{key}")
        return int(value) if value else 0

    @staticmethod
    async def increment_rate_limit(key: str, window: int = 60) -> int:
        """Increment rate limit counter with expiration."""
        full_key = f"rate_limit:{key}"
        count = await redis_client.increment(full_key)
        if count == 1:  # First increment, set expiration
            await redis_client.expire(full_key, window)
        return count
