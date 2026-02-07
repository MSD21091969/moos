"""Unit tests for src/api/routes/documents.py - FIXED VERSION

TEST: Document management endpoints with proper dependency overrides
PURPOSE: Validate document upload, listing, retrieval, deletion
VALIDATES: File handling, session ownership, pagination
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from io import BytesIO

from src.main import app as main_app
from src.api.dependencies import get_user_context, get_document_service, get_app_container
from src.models.context import UserContext
from src.models.permissions import Tier
from src.models.documents import Document
from src.services.document_service import DocumentService
from src.core.exceptions import NotFoundError, PermissionDeniedError


# Fixtures


@pytest.fixture
def test_user_context():
    """UserContext for testing."""
    return UserContext(
        user_id="user_test",
        email="test@example.com",
        permissions=("read_data", "write_data"),
        quota_remaining=1000,
        tier=Tier.PRO,
    )


@pytest.fixture
def mock_document_service():
    """Mock DocumentService for dependency override."""
    service = AsyncMock(spec=DocumentService)
    return service


@pytest.fixture
def sample_document():
    """Sample document."""
    return Document(
        document_id="doc_abc123",
        session_id="sess_xyz789",
        filename="report.txt",
        content_type="text/plain",
        content="This is test content",
        size_bytes=20,
        created_at=datetime.now(UTC),
        user_id="user_test",
        tags=["test"],
        metadata={"original_name": "report.txt"},
    )


@pytest.fixture
def client(test_user_context, mock_document_service):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    async def override_document_service():
        return mock_document_service

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_document_service] = override_document_service
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestUploadDocument:
    """Test POST /sessions/{session_id}/documents endpoint."""

    def test_upload_document_success(self, client, mock_document_service, sample_document):
        """
        TEST: Upload document to session
        PURPOSE: Verify file upload handling
        VALIDATES: Multipart form-data, file content reading
        EXPECTED: 201 with document info
        """
        mock_document_service.upload_document.return_value = sample_document

        file_content = b"This is test content"
        files = {"file": ("report.txt", BytesIO(file_content), "text/plain")}
        data = {"filename": "report.txt"}

        response = client.post(
            "/sessions/sess_xyz789/documents",
            files=files,
            data=data,
        )

        assert response.status_code == 201
        result = response.json()
        assert result["document_id"] == "doc_abc123"
        assert result["filename"] == "report.txt"
        assert result["size_bytes"] == 20

    def test_upload_document_empty_file_fails(self, client, mock_document_service):
        """
        TEST: Upload empty file
        PURPOSE: Verify file validation
        VALIDATES: Empty file rejection
        EXPECTED: 400 bad request
        """
        files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
        data = {"filename": "empty.txt"}

        response = client.post(
            "/sessions/sess_xyz789/documents",
            files=files,
            data=data,
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_document_permission_denied(self, client, mock_document_service):
        """
        TEST: Upload to session user doesn't own
        PURPOSE: Verify ownership check
        VALIDATES: PermissionDeniedError → 403
        EXPECTED: 403 forbidden
        """
        mock_document_service.upload_document.side_effect = PermissionDeniedError(
            "User does not own session"
        )

        file_content = b"Test content"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        data = {"filename": "test.txt"}

        response = client.post(
            "/sessions/sess_other_user/documents",
            files=files,
            data=data,
        )

        assert response.status_code == 403


class TestListDocuments:
    """Test GET /sessions/{session_id}/documents endpoint."""

    def test_list_documents_success(self, client, mock_document_service, sample_document):
        """
        TEST: List session documents
        PURPOSE: Verify document listing
        VALIDATES: Pagination, response structure
        EXPECTED: 200 with documents array
        """
        mock_document_service.list_documents.return_value = ([sample_document], 1)

        response = client.get("/sessions/sess_xyz789/documents?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 1
        assert data["total"] == 1

    def test_list_documents_pagination(self, client, mock_document_service, sample_document):
        """
        TEST: Paginate document list
        PURPOSE: Verify pagination logic
        VALIDATES: has_more calculation
        EXPECTED: Correct pagination metadata
        """
        docs = [sample_document] * 20
        mock_document_service.list_documents.return_value = (docs, 50)

        response = client.get("/sessions/sess_xyz789/documents?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True  # 50 total > 20 per page

    def test_list_documents_empty_session(self, client, mock_document_service):
        """
        TEST: List documents for session with no documents
        PURPOSE: Verify empty result handling
        VALIDATES: Empty array response
        EXPECTED: 200 with empty documents array
        """
        mock_document_service.list_documents.return_value = ([], 0)

        response = client.get("/sessions/sess_empty/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0


class TestGetDocument:
    """Test GET /sessions/{session_id}/documents/{document_id} endpoint."""

    def test_get_document_success(self, client, mock_document_service, sample_document):
        """
        TEST: Get document details
        PURPOSE: Verify document retrieval
        VALIDATES: Service integration
        EXPECTED: 200 with document data
        """
        mock_document_service.get_document.return_value = sample_document

        response = client.get("/sessions/sess_xyz789/documents/doc_abc123")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc_abc123"
        assert data["filename"] == "report.txt"

    def test_get_document_not_found(self, client, mock_document_service):
        """
        TEST: Get non-existent document
        PURPOSE: Verify error handling
        VALIDATES: NotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_document_service.get_document.side_effect = NotFoundError("Document not found")

        response = client.get("/sessions/sess_xyz789/documents/doc_nonexistent")

        assert response.status_code == 404


class TestDeleteDocument:
    """Test DELETE /sessions/{session_id}/documents/{document_id} endpoint."""

    def test_delete_document_success(self, client, mock_document_service):
        """
        TEST: Delete document
        PURPOSE: Verify document deletion
        VALIDATES: Service integration
        EXPECTED: 204 no content
        """
        mock_document_service.delete_document.return_value = None

        response = client.delete("/sessions/sess_xyz789/documents/doc_abc123")

        assert response.status_code == 204

    def test_delete_document_permission_denied(self, client, mock_document_service):
        """
        TEST: Delete document user doesn't own
        PURPOSE: Verify ownership check
        VALIDATES: PermissionDeniedError → 403
        EXPECTED: 403 forbidden
        """
        mock_document_service.delete_document.side_effect = PermissionDeniedError(
            "User does not own document"
        )

        response = client.delete("/sessions/sess_other/documents/doc_abc123")

        assert response.status_code == 403

    def test_delete_document_not_found(self, client, mock_document_service):
        """
        TEST: Delete non-existent document
        PURPOSE: Verify error handling
        VALIDATES: NotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_document_service.delete_document.side_effect = NotFoundError("Document not found")

        response = client.delete("/sessions/sess_xyz789/documents/doc_nonexistent")

        assert response.status_code == 404
