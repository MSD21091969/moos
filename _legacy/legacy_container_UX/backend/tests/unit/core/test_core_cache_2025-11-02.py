"""Unit tests for src/core/cache.py

TEST: Caching decorators and utilities
PURPOSE: Validate cache operations
VALIDATES: @cached, @invalidate_cache, CacheManager
EXPECTED: All cache functions work correctly
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.core.cache import cache_key, cached, invalidate_cache, CacheManager


class TestCacheKey:
    """Test cache key generation."""

    def test_cache_key_with_args(self):
        """
        TEST: Generate cache key from args
        PURPOSE: Verify key generation
        VALIDATES: Deterministic hash
        EXPECTED: Consistent key for same args
        """
        key1 = cache_key("user_123", "session_456", prefix="test")
        key2 = cache_key("user_123", "session_456", prefix="test")

        assert key1 == key2
        assert "test:" in key1

    def test_cache_key_with_kwargs(self):
        """
        TEST: Generate cache key from kwargs
        PURPOSE: Verify kwargs handling
        VALIDATES: Sorted kwargs
        EXPECTED: Order-independent key
        """
        key1 = cache_key(prefix="user", user_id="123", session_id="456")
        key2 = cache_key(prefix="user", session_id="456", user_id="123")

        assert key1 == key2

    def test_cache_key_without_prefix(self):
        """
        TEST: Generate cache key without prefix
        PURPOSE: Verify optional prefix
        VALIDATES: Hash only
        EXPECTED: No prefix in key
        """
        key = cache_key("test", "data")

        assert ":" not in key or len(key.split(":")) == 1


class TestCachedDecorator:
    """Test @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_miss(self):
        """
        TEST: Cached decorator on cache miss
        PURPOSE: Verify function execution
        VALIDATES: Function called, result cached
        EXPECTED: Function runs, value cached
        """
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("src.core.cache.redis_client", mock_redis):

            @cached(ttl=300, prefix="test")
            async def test_func(arg1: str):
                return f"result_{arg1}"

            result = await test_func("value")

            assert result == "result_value"
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_hit(self):
        """
        TEST: Cached decorator on cache hit
        PURPOSE: Verify cache retrieval
        VALIDATES: Function not called
        EXPECTED: Cached value returned
        """
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "cached_result"

        with patch("src.core.cache.redis_client", mock_redis):
            call_count = 0

            @cached(ttl=300, prefix="test")
            async def test_func(arg1: str):
                nonlocal call_count
                call_count += 1
                return f"result_{arg1}"

            result = await test_func("value")

            assert result == "cached_result"
            assert call_count == 0  # Function not called


class TestInvalidateCacheDecorator:
    """Test @invalidate_cache decorator."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_decorator(self):
        """
        TEST: Invalidate cache after function
        PURPOSE: Verify cache clearing
        VALIDATES: clear_pattern called
        EXPECTED: Cache invalidated
        """
        mock_redis = AsyncMock()
        mock_redis.clear_pattern.return_value = 5

        with patch("src.core.cache.redis_client", mock_redis):

            @invalidate_cache("user:*", "session:*")
            async def test_func():
                return "result"

            result = await test_func()

            assert result == "result"
            assert mock_redis.clear_pattern.call_count == 2


class TestCacheManager:
    """Test CacheManager helper class."""

    @pytest.mark.asyncio
    async def test_get_user(self):
        """
        TEST: CacheManager get_user
        PURPOSE: Verify user cache retrieval
        VALIDATES: Redis get called
        EXPECTED: User data returned
        """
        mock_redis = AsyncMock()
        mock_redis.get.return_value = {"user_id": "123"}

        with patch("src.core.cache.redis_client", mock_redis):
            result = await CacheManager.get_user("123")

            assert result == {"user_id": "123"}
            mock_redis.get.assert_called_once_with("user:123")

    @pytest.mark.asyncio
    async def test_set_session(self):
        """
        TEST: CacheManager set_session
        PURPOSE: Verify session caching
        VALIDATES: Redis set called
        EXPECTED: Session cached with TTL
        """
        mock_redis = AsyncMock()

        with patch("src.core.cache.redis_client", mock_redis):
            await CacheManager.set_session("sess_123", {"data": "test"}, ttl=1800)

            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_rate_limit(self):
        """
        TEST: CacheManager increment rate limit
        PURPOSE: Verify rate limit counter
        VALIDATES: Redis increment called
        EXPECTED: Counter incremented
        """
        mock_redis = AsyncMock()
        mock_redis.increment.return_value = 1

        with patch("src.core.cache.redis_client", mock_redis):
            count = await CacheManager.increment_rate_limit("user_123")

            assert count == 1
            mock_redis.increment.assert_called_once()
