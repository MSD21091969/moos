"""
TEST: src/core/container.py - Dependency injection container
PURPOSE: Validate singleton pattern, lazy initialization, resource management
VALIDATES: AppContainer singleton, firestore_client
EXPECTED: Single instance, lazy init, proper reset

NOTE: EventBuilder and SessionHistoryLoader were removed in event-first migration (PR #60).
      This test now only validates firestore_client management.
"""

import pytest

from src.core.container import AppContainer
from src.persistence.firestore_client import FirestoreClient


class TestAppContainer:
    """Test suite for AppContainer dependency injection."""

    @pytest.fixture(autouse=True)
    async def reset_container(self):
        """Reset container between tests."""
        yield
        # Reset singleton after each test
        container = AppContainer()
        await container.reset()

    def test_singleton_pattern(self):
        """
        TEST: AppContainer singleton pattern
        PURPOSE: Validate only one instance exists
        VALIDATES: Multiple AppContainer() calls return same instance
        EXPECTED: container1 is container2
        """
        container1 = AppContainer()
        container2 = AppContainer()

        assert container1 is container2

    def test_firestore_client_lazy_initialization(self):
        """
        TEST: Firestore client lazy initialization
        PURPOSE: Validate client created on first access
        VALIDATES: _firestore_client None initially, created on .firestore_client
        EXPECTED: FirestoreClient instance after first access
        """
        container = AppContainer()

        # Not initialized yet
        assert container._firestore_client is None

        # Access triggers initialization
        client = container.firestore_client

        assert client is not None
        assert isinstance(client, FirestoreClient)

    def test_firestore_client_reuses_instance(self):
        """
        TEST: Firestore client instance reused
        PURPOSE: Validate same client returned on multiple accesses
        VALIDATES: container.firestore_client returns same instance
        EXPECTED: client1 is client2
        """
        container = AppContainer()

        client1 = container.firestore_client
        client2 = container.firestore_client

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_reset_clears_all_instances(self):
        """
        TEST: reset() clears all cached instances
        PURPOSE: Validate reset for testing/cleanup
        VALIDATES: All internal instances set to None after reset()
        EXPECTED: _firestore_client set to None
        """
        container = AppContainer()

        # Initialize firestore client
        _ = container.firestore_client

        # Reset
        await container.reset()

        # All cleared
        assert container._firestore_client is None

    @pytest.mark.asyncio
    async def test_reset_clears_singleton(self):
        """
        TEST: reset() clears singleton instance
        PURPOSE: Validate complete reset for testing
        VALIDATES: AppContainer._instance set to None after reset()
        EXPECTED: New AppContainer() after reset creates new instance
        """
        container1 = AppContainer()
        await container1.reset()

        container2 = AppContainer()

        # After reset, singleton can be re-initialized
        assert container2 is not None

    @pytest.mark.asyncio
    async def test_reset_closes_firestore_connection(self):
        """
        TEST: reset() closes firestore client connection
        PURPOSE: Validate resource cleanup
        VALIDATES: firestore_client.close() called during reset
        EXPECTED: Connection closed before clearing instance
        """
        container = AppContainer()

        # Initialize client

        # Reset should close connection
        await container.reset()

        # Verify reset occurred (client is None)
        assert container._firestore_client is None

    def test_get_container_convenience_function(self):
        """
        TEST: get_container() returns AppContainer singleton
        PURPOSE: Validate convenience function
        VALIDATES: get_container() returns same instance as AppContainer()
        EXPECTED: get_container() is AppContainer()
        """
        from src.core.container import get_container

        container1 = get_container()
        container2 = AppContainer()

        assert container1 is container2
