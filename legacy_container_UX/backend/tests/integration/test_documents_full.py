"""Full integration tests for document management endpoints.

Tests all 4 document API endpoints with real/mock Firestore:
1. POST /sessions/{id}/documents - Upload document
2. GET /sessions/{id}/documents - List documents
3. GET /sessions/{id}/documents/{doc_id} - Get document
4. DELETE /sessions/{id}/documents/{doc_id} - Delete document
"""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_upload_document(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test POST /sessions/{id}/documents - Upload document."""
    # Create session first
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Document Test Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Upload document
    file_content = b"Test document content for integration testing"
    response = enterprise_client.post(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
        data={"filename": "test.txt"},
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )

    assert response.status_code == 201, f"Failed to upload document: {response.text}"
    doc_data = response.json()

    # Validate response
    assert "document_id" in doc_data
    assert doc_data["filename"] == "test.txt"
    assert doc_data["content_type"] == "text/plain"
    assert doc_data["size_bytes"] > 0


@pytest.mark.integration
def test_list_documents(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/documents - List documents."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Document List Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Upload a document
    file_content = b"Test content"
    upload_response = enterprise_client.post(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
        data={"filename": "list_test.txt"},
        files={"file": ("list_test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_response.status_code == 201

    # List documents
    response = enterprise_client.get(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to list documents: {response.text}"
    doc_list = response.json()

    # Validate response
    assert "documents" in doc_list
    assert isinstance(doc_list["documents"], list)
    assert len(doc_list["documents"]) >= 1


@pytest.mark.integration
def test_get_document(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/documents/{doc_id} - Get document details."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Document Get Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Upload document
    file_content = b"Get test content"
    upload_response = enterprise_client.post(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
        data={"filename": "get_test.txt"},
        files={"file": ("get_test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["document_id"]

    # Get document
    response = enterprise_client.get(
        f"/sessions/{session_id}/documents/{doc_id}",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to get document: {response.text}"
    doc_data = response.json()

    # Validate response
    assert doc_data["document_id"] == doc_id
    assert doc_data["filename"] == "get_test.txt"


@pytest.mark.integration
def test_delete_document(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test DELETE /sessions/{id}/documents/{doc_id} - Delete document."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Document Delete Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Upload document
    file_content = b"Delete test content"
    upload_response = enterprise_client.post(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
        data={"filename": "delete_test.txt"},
        files={"file": ("delete_test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["document_id"]

    # Delete document
    response = enterprise_client.delete(
        f"/sessions/{session_id}/documents/{doc_id}",
        headers=enterprise_headers,
    )

    assert response.status_code == 204, f"Failed to delete document: {response.text}"

    # Verify deletion
    get_response = enterprise_client.get(
        f"/sessions/{session_id}/documents/{doc_id}",
        headers=enterprise_headers,
    )
    assert get_response.status_code == 404, "Deleted document should return 404"


@pytest.mark.integration
def test_upload_empty_file(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test error handling for empty file upload."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Empty File Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Upload empty file
    response = enterprise_client.post(
        f"/sessions/{session_id}/documents",
        headers=enterprise_headers,
        data={"filename": "empty.txt"},
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )

    assert response.status_code == 400, "Should return 400 for empty file"
