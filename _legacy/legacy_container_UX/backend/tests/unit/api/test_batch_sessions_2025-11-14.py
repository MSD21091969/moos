"""Unit tests for batch session creation (2025-11-14).

Tests POST /sessions/batch endpoint for frontend staging queue support.
PATTERN: Use app.dependency_overrides instead of patching
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_session_service, get_user_context
from src.core.exceptions import ValidationError
from src.main import app
from src.models.context import UserContext
from src.models.permissions import Tier
from src.models.sessions import Session, SessionMetadata, SessionStatus, SessionType


@pytest.fixture
def test_user_context():
    """Mock user context dependency."""
    return UserContext(
        user_id="user_test123",
        email="test@example.com",
        tier=Tier.PRO,
        permissions=["read", "write"],
        remaining_quota=1000,
    )


@pytest.fixture
def mock_session_service():
    """Mock session service for testing."""
    service = AsyncMock()
    return service


@pytest.fixture
def client(test_user_context, mock_session_service):
    """TestClient with overridden dependencies."""

    async def override_user_context():
        return test_user_context

    async def override_session_service():
        return mock_session_service

    app.dependency_overrides[get_user_context] = override_user_context
    app.dependency_overrides[get_session_service] = override_session_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_sessions():
    """Sample sessions for testing."""
    now = datetime.now(UTC)
    # Create sessions with proper parent_session_id reference
    sessions = []
    for i in range(3):
        sessions.append(
            Session(
                session_id=f"sess_{i:012x}",  # Use valid hex format
                user_id="user_test123",
                metadata=SessionMetadata(
                    title=f"Test Session {i}",
                    description=f"Test description {i}",
                    tags=["test"],
                    session_type=SessionType.CHAT,
                    ttl_hours=24,
                ),
                status=SessionStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                expires_at=now,
                created_by="user_test123",
                acl={"user_test123": "owner"},
                parent_session_id="sess_000000000000" if i > 0 else None,  # Reference first session
                child_sessions=[],
            )
        )
    return sessions


class TestBatchSessionCreation:
    """Test suite for POST /sessions/batch endpoint."""

    def test_batch_create_success_all(self, client, mock_session_service, sample_sessions):
        """Test successful batch creation of all sessions."""
        # Arrange
        mock_session_service.create_batch.return_value = (sample_sessions, [])

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [
                    {
                        "title": f"Test Session {i}",
                        "session_type": "chat",
                        "parent_session_id": "sess_000000000000" if i > 0 else None,
                    }
                    for i in range(3)
                ]
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 3
        assert data["success_count"] == 3
        assert data["failed_count"] == 0
        assert len(data["sessions"]) == 3
        assert len(data["errors"]) == 0

    def test_batch_create_partial_success(self, client, mock_session_service, sample_sessions):
        """Test batch creation with partial success (some failures)."""
        # Arrange
        errors = [{"index": 1, "title": "Test Session 1", "error": "Title too long"}]
        mock_session_service.create_batch.return_value = (sample_sessions[:2], errors)

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [
                    {"title": f"Test Session {i}", "session_type": "chat"} for i in range(3)
                ]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 3
        assert data["success_count"] == 2
        assert data["failed_count"] == 1
        assert len(data["sessions"]) == 2
        assert len(data["errors"]) == 1
        assert data["errors"][0]["index"] == 1

    def test_batch_create_exceeds_limit(self, client, mock_session_service):
        """Test batch creation fails when exceeding 25 session limit."""
        # Arrange
        client = TestClient(app)

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [{"title": f"Session {i}", "session_type": "chat"} for i in range(26)]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 422  # FastAPI validation error
        assert "max_length" in response.text.lower() or "25" in response.text

    def test_batch_create_tier_quota_exceeded(self, client, mock_session_service):
        """Test batch creation fails when user tier quota would be exceeded."""
        # Arrange
        mock_session_service.create_batch.side_effect = ValidationError(
            "Batch creation would exceed session limit"
        )

        client = TestClient(app)

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [{"title": f"Session {i}", "session_type": "chat"} for i in range(5)]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 400
        assert "exceed" in response.text.lower()

    def test_batch_create_with_parent_sessions(
        self, client, mock_session_service, sample_sessions
    ):
        """Test batch creation of child sessions with parent_session_id."""
        # Arrange
        mock_session_service.create_batch.return_value = (sample_sessions[1:], [])

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [
                    {
                        "title": f"Child {i}",
                        "session_type": "chat",
                        "parent_session_id": "sess_000000000000",
                    }
                    for i in range(2)
                ]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 2
        for session in data["sessions"]:
            assert session["parent_session_id"] == "sess_000000000000"

    def test_batch_create_with_visual_metadata(
        self, client, mock_session_service, sample_sessions
    ):
        """Test batch creation with frontend visual metadata."""
        # Arrange
        mock_session_service.create_batch.return_value = (sample_sessions[:1], [])

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [
                    {
                        "title": "Visual Session",
                        "session_type": "chat",
                        "visual_metadata": {
                            "color": "#FF5733",
                            "position": {"x": 100, "y": 200},
                            "collapsed": False,
                        },
                    }
                ]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 1

    def test_batch_create_container_sessions(
        self, client, mock_session_service, sample_sessions
    ):
        """Test batch creation of container sessions with is_container flag."""
        # Arrange
        mock_session_service.create_batch.return_value = (sample_sessions[:1], [])

        # Act
        response = client.post(
            "/sessions/batch",
            json={
                "sessions": [
                    {
                        "title": "Container Session",
                        "session_type": "workflow",
                        "is_container": True,
                        "child_node_ids": ["node_123", "node_456"],
                    }
                ]
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 1

    def test_batch_create_no_sessions(self, client, mock_session_service):
        """Test batch creation fails with empty session list."""
        # Act
        response = client.post(
            "/sessions/batch",
            json={"sessions": []},
        )

        # Assert
        assert response.status_code == 422  # FastAPI validation error
        assert "min_length" in response.text.lower() or "at least 1 item" in response.text.lower()

    def test_batch_create_invalid_session_type(self, client, mock_session_service):
        """Test batch creation fails with invalid session_type."""
        # Act
        response = client.post(
            "/sessions/batch",
            json={"sessions": [{"title": "Invalid Session", "session_type": "invalid_type"}]},
        )

        # Assert
        # Currently returns 500 because ValueError raised in route handler
        # TODO: Move session_type validation to Pydantic request model to get proper 422
        assert response.status_code == 500
        assert "invalid" in response.text.lower() or "sessiontype" in response.text.lower()


class TestSessionHierarchyFiltering:
    """Test suite for parent_session_id filtering."""

    def test_list_sessions_with_parent_filter(self, client, mock_session_service, sample_sessions):
        """Test listing sessions filtered by parent_session_id."""
        # Arrange
        child_sessions = sample_sessions[1:]  # Sessions with parent
        mock_session_service.list_user_sessions.return_value = (child_sessions, 2)

        # Act
        response = client.get(
            "/sessions?parent_session_id=sess_000000000000",
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["sessions"]) == 2
        for session in data["sessions"]:
            assert session["parent_session_id"] == "sess_000000000000"

        # Verify service was called with parent_session_id parameter
        mock_session_service.list_user_sessions.assert_called_once()
        call_kwargs = mock_session_service.list_user_sessions.call_args.kwargs
        assert call_kwargs["parent_session_id"] == "sess_000000000000"


class TestCascadeDelete:
    """Test suite for cascade delete functionality."""

    def test_delete_session_with_cascade(self, client, mock_session_service):
        """Test deleting session with cascade deletes children."""
        # Arrange
        mock_session_service.delete.return_value = None

        # Act
        response = client.delete(
            "/sessions/sess_000000000000?cascade=true",
        )

        # Assert
        assert response.status_code == 204

        # Verify service was called with cascade=True
        mock_session_service.delete.assert_called_once_with(
            session_id="sess_000000000000", user_id="user_test123", cascade=True
        )

    def test_delete_session_without_cascade(self, client, mock_session_service):
        """Test deleting session without cascade (default behavior)."""
        # Arrange
        mock_session_service.delete.return_value = None

        # Act
        response = client.delete(
            "/sessions/sess_test123",
        )

        # Assert
        assert response.status_code == 204

        # Verify service was called with cascade=False (default)
        mock_session_service.delete.assert_called_once_with(
            session_id="sess_test123", user_id="user_test123", cascade=False
        )
