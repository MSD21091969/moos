"""Unit tests for src/persistence/mock_firestore.py

TEST: MockFirestoreClient for testing
PURPOSE: Validate mock Firestore implementation for tests
VALIDATES: In-memory storage, collection/document operations
EXPECTED: Mock behaves like real Firestore client
"""

import pytest

from src.persistence.mock_firestore import MockFirestoreClient


class TestMockFirestoreClient:
    """Test MockFirestoreClient basic operations."""

    def test_client_initialization(self):
        """
        TEST: Initialize mock client
        PURPOSE: Verify client creates successfully
        VALIDATES: Client instance created
        EXPECTED: MockFirestoreClient instance
        """
        client = MockFirestoreClient()

        assert client is not None
        assert hasattr(client, "collection")

    def test_collection_access(self):
        """
        TEST: Access collection
        PURPOSE: Verify collection method
        VALIDATES: Collection reference returned
        EXPECTED: Collection object
        """
        client = MockFirestoreClient()

        collection = client.collection("test_collection")

        assert collection is not None

    @pytest.mark.asyncio
    async def test_set_and_get_document(self):
        """
        TEST: Set and retrieve document
        PURPOSE: Verify document storage
        VALIDATES: Data persistence in memory
        EXPECTED: Same data retrieved
        """
        client = MockFirestoreClient()

        doc_data = {"name": "Test", "value": 123}
        await client.collection("test").document("doc1").set(doc_data)

        doc = await client.collection("test").document("doc1").get()

        assert doc.exists
        assert doc.to_dict()["name"] == "Test"
        assert doc.to_dict()["value"] == 123

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self):
        """
        TEST: Get non-existent document
        PURPOSE: Verify missing document handling
        VALIDATES: exists = False
        EXPECTED: Document with exists=False
        """
        client = MockFirestoreClient()

        doc = await client.collection("test").document("missing").get()

        assert not doc.exists

    @pytest.mark.asyncio
    async def test_delete_document(self):
        """
        TEST: Delete document
        PURPOSE: Verify deletion
        VALIDATES: Document removed
        EXPECTED: Document no longer exists
        """
        client = MockFirestoreClient()

        await client.collection("test").document("doc1").set({"data": "value"})
        await client.collection("test").document("doc1").delete()

        doc = await client.collection("test").document("doc1").get()

        assert not doc.exists

    @pytest.mark.asyncio
    async def test_update_document(self):
        """
        TEST: Update existing document
        PURPOSE: Verify partial updates
        VALIDATES: Fields updated, others preserved
        EXPECTED: Updated document
        """
        client = MockFirestoreClient()

        await client.collection("test").document("doc1").set({"field1": "a", "field2": "b"})
        await client.collection("test").document("doc1").update({"field1": "updated"})

        doc = await client.collection("test").document("doc1").get()

        assert doc.to_dict()["field1"] == "updated"
        assert doc.to_dict()["field2"] == "b"

    @pytest.mark.asyncio
    async def test_query_where_clause(self):
        """
        TEST: Query with where clause
        PURPOSE: Verify filtering
        VALIDATES: Where clause filters results
        EXPECTED: Only matching documents
        """
        client = MockFirestoreClient()

        await client.collection("users").document("user1").set({"tier": "FREE", "name": "User1"})
        await client.collection("users").document("user2").set({"tier": "PRO", "name": "User2"})

        query = client.collection("users").where("tier", "==", "PRO")
        docs = []
        async for doc in query.stream():
            docs.append(doc)

        assert len(docs) == 1
        assert docs[0].to_dict()["name"] == "User2"

    @pytest.mark.asyncio
    async def test_subcollection_access(self):
        """
        TEST: Access subcollection
        PURPOSE: Verify nested collections
        VALIDATES: Document subcollection path
        EXPECTED: Subcollection accessible
        """
        client = MockFirestoreClient()

        await (
            client.collection("sessions")
            .document("sess1")
            .collection("events")
            .document("evt1")
            .set({"data": "test"})
        )

        doc = (
            await client.collection("sessions")
            .document("sess1")
            .collection("events")
            .document("evt1")
            .get()
        )

        assert doc.exists
        assert doc.to_dict()["data"] == "test"
