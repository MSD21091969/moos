"""
TEST: src/persistence/firestore_client.py - Firestore client wrapper
PURPOSE: Validate Firestore client initialization, mock/production switching
VALIDATES: FirestoreClient, collection/document access, close(), singleton pattern
EXPECTED: Mock client in dev, real client in prod, proper cleanup
"""

from unittest.mock import MagicMock, patch

import pytest

from src.persistence.firestore_client import (
    FirestoreClient,
    close_firestore_client,
    get_firestore_client,
)


class TestFirestoreClient:
    """Test suite for FirestoreClient wrapper."""

    @pytest.fixture(autouse=True)
    async def cleanup(self):
        """Clean up global client after each test."""
        yield
        await close_firestore_client()

    def test_initialize_with_mock_firestore(self):
        """
        TEST: Initialize with mock Firestore client
        PURPOSE: Validate mock client used in development
        VALIDATES: use_firestore_mocks=True loads MockFirestoreClient
        EXPECTED: MockFirestoreClient instance, no GCP connection
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            mock_settings.use_firestore_mocks = True
            mock_settings.gcp_project = "test-project"
            mock_settings.firestore_database = "(default)"

            client = FirestoreClient()

            # Mock client used
            from src.persistence.mock_firestore import MockFirestoreClient

            assert isinstance(client._client, MockFirestoreClient)

    def test_initialize_with_real_firestore(self):
        """
        TEST: Initialize with real Firestore client
        PURPOSE: Validate production Firestore connection
        VALIDATES: use_firestore_mocks=False loads firestore.AsyncClient
        EXPECTED: AsyncClient with GCP project/database
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            with patch(
                "src.persistence.firestore_client.firestore.AsyncClient"
            ) as mock_async_client:
                mock_settings.use_firestore_mocks = False
                mock_settings.gcp_project = "prod-project"
                mock_settings.firestore_database = "prod-db"

                FirestoreClient()

                # Real AsyncClient created
                mock_async_client.assert_called_once_with(
                    project="prod-project", database="prod-db"
                )

    def test_collection_access(self):
        """
        TEST: Access Firestore collection
        PURPOSE: Validate collection() method delegates to client
        VALIDATES: client.collection(path) returns collection reference
        EXPECTED: Collection reference for path
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            mock_settings.use_firestore_mocks = True
            mock_settings.gcp_project = "test-project"

            client = FirestoreClient()

            # Access collection
            collection = client.collection("sessions")

            assert collection is not None

    def test_document_access(self):
        """
        TEST: Access Firestore document
        PURPOSE: Validate document() method delegates to client
        VALIDATES: client.document(path) returns document reference
        EXPECTED: Document reference for path
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            mock_settings.use_firestore_mocks = True
            mock_settings.gcp_project = "test-project"

            client = FirestoreClient()

            # Access document
            doc = client.document("sessions/sess_123")

            assert doc is not None

    @pytest.mark.asyncio
    async def test_close_client(self):
        """
        TEST: Close Firestore client connection
        PURPOSE: Validate cleanup on shutdown
        VALIDATES: close() calls _client.close() if exists
        EXPECTED: Connection closed, no errors
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            mock_settings.use_firestore_mocks = True
            mock_settings.gcp_project = "test-project"

            client = FirestoreClient()

            # Mock close method
            client._client.close = MagicMock(return_value=None)

            await client.close()

            # close() called on underlying client
            client._client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_client_without_close_method(self):
        """
        TEST: Close client that doesn't have close() method
        PURPOSE: Validate graceful handling of clients without close
        VALIDATES: No error if _client lacks close() method
        EXPECTED: No exception raised
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            mock_settings.use_firestore_mocks = True
            mock_settings.gcp_project = "test-project"

            client = FirestoreClient()

            # Create a mock object without close method
            from unittest.mock import MagicMock

            mock_client = MagicMock()
            del mock_client.close
            client._client = mock_client

            # Should not raise
            await client.close()

    @pytest.mark.asyncio
    async def test_get_firestore_client_singleton(self):
        """
        TEST: get_firestore_client() returns singleton
        PURPOSE: Validate global client reuse
        VALIDATES: Multiple calls return same instance
        EXPECTED: client1 is client2
        """
        client1 = await get_firestore_client()
        client2 = await get_firestore_client()

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_close_firestore_client_clears_global(self):
        """
        TEST: close_firestore_client() clears global instance
        PURPOSE: Validate cleanup for testing/shutdown
        VALIDATES: Global _firestore_client set to None after close
        EXPECTED: Next get_firestore_client() creates new instance
        """
        client1 = await get_firestore_client()

        await close_firestore_client()

        client2 = await get_firestore_client()

        # New instance created after close
        assert client1 is not client2

    def test_logs_mock_firestore_usage(self):
        """
        TEST: Log message when using mock Firestore
        PURPOSE: Validate development mode visibility
        VALIDATES: Logger called with "Using mock Firestore client"
        EXPECTED: Info log for mock mode
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            with patch("src.persistence.firestore_client.logger") as mock_logger:
                mock_settings.use_firestore_mocks = True
                mock_settings.gcp_project = "test-project"

                FirestoreClient()

                # Logger called
                assert mock_logger.info.called

    def test_logs_real_firestore_connection(self):
        """
        TEST: Log message when connecting to real Firestore
        PURPOSE: Validate production connection visibility
        VALIDATES: Logger called with project/database info
        EXPECTED: Info log with connection details
        """
        with patch("src.persistence.firestore_client.settings") as mock_settings:
            with patch("src.persistence.firestore_client.logger") as mock_logger:
                with patch("src.persistence.firestore_client.firestore.AsyncClient"):
                    mock_settings.use_firestore_mocks = False
                    mock_settings.gcp_project = "prod-project"
                    mock_settings.firestore_database = "prod-db"

                    FirestoreClient()

                    # Logger called with connection info
                    assert mock_logger.info.called
