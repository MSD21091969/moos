"""Unit tests for src/core/redis_client.py

TEST: Redis client for caching
PURPOSE: Validate async Redis operations
VALIDATES: RedisClient, connect, get, set, delete
EXPECTED: All Redis operations work correctly
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.core.redis_client import RedisClient


class TestRedisClient:
    """Test RedisClient class."""

    @pytest.mark.asyncio
    async def test_redis_client_initialization(self):
        """
        TEST: Initialize Redis client
        PURPOSE: Verify client creation
        VALIDATES: Client attributes set
        EXPECTED: Client ready
        """
        client = RedisClient()

        assert client._pool is None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_connect_creates_pool(self):
        """
        TEST: Connect to Redis
        PURPOSE: Verify connection setup
        VALIDATES: Pool and client created
        EXPECTED: Connection established
        """
        with patch("src.core.redis_client.ConnectionPool"):
            with patch("src.core.redis_client.redis.Redis") as MockRedis:
                mock_client = AsyncMock()
                mock_client.ping = AsyncMock()
                MockRedis.return_value = mock_client

                client = RedisClient()
                await client.connect()

                assert mock_client.ping.called

    @pytest.mark.asyncio
    async def test_disconnect_closes_connections(self):
        """
        TEST: Disconnect from Redis
        PURPOSE: Verify cleanup
        VALIDATES: Pool and client closed
        EXPECTED: Connections closed
        """
        client = RedisClient()
        client._client = AsyncMock()
        client._pool = AsyncMock()

        await client.disconnect()

        client._client.aclose.assert_called_once()
        client._pool.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_deserializes_json(self):
        """
        TEST: Get value from Redis
        PURPOSE: Verify JSON deserialization
        VALIDATES: Value retrieved and parsed
        EXPECTED: Python object returned
        """
        client = RedisClient()
        client._client = AsyncMock()
        client._client.get.return_value = '{"key": "value"}'

        result = await client.get("test_key")

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_set_serializes_json(self):
        """
        TEST: Set value in Redis
        PURPOSE: Verify JSON serialization
        VALIDATES: Value serialized and stored
        EXPECTED: Redis setex called
        """
        client = RedisClient()
        client._client = AsyncMock()
        client._client.setex = AsyncMock(return_value=True)

        await client.set("test_key", {"data": "test"}, ttl=300)

        client._client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        """
        TEST: Delete key from Redis
        PURPOSE: Verify key deletion
        VALIDATES: Redis delete called
        EXPECTED: Key removed
        """
        client = RedisClient()
        client._client = AsyncMock()

        await client.delete("test_key")

        client._client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_increment_increases_counter(self):
        """
        TEST: Increment counter
        PURPOSE: Verify counter operation
        VALIDATES: Redis incrby called
        EXPECTED: Counter incremented
        """
        client = RedisClient()
        client._client = AsyncMock()
        client._client.incrby = AsyncMock(return_value=5)

        result = await client.increment("counter_key")

        assert result == 5
        client._client.incrby.assert_called_once()

    @pytest.mark.asyncio
    async def test_expire_sets_ttl(self):
        """
        TEST: Set key expiration
        PURPOSE: Verify TTL setting
        VALIDATES: Redis expire called
        EXPECTED: TTL set
        """
        client = RedisClient()
        client._client = AsyncMock()

        await client.expire("test_key", 600)

        client._client.expire.assert_called_once_with("test_key", 600)
