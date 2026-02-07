"""Unit tests for src/api/routes/sessions.py - FIXED VERSION

TEST: Session CRUD API endpoints with proper dependency overrides
PURPOSE: Validate session management HTTP endpoints
VALIDATES: Request/response, authentication, ACL, pagination
PATTERN: Use app.dependency_overrides instead of direct patching

KEY CHANGES:
1. Override FastAPI dependencies using app.dependency_overrides
2. Use AsyncMock for service methods instead of patching module-level functions
3. Create isolated app instance per test class
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_app_container,
    get_session_service,
    get_user_context,
)
from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.main import app as main_app
from src.models.context import UserContext
from src.models.permissions import Tier
from src.models.sessions import Session, SessionMetadata, SessionStatus, SessionType
from src.services.session_service import SessionService

# Fixtures


@pytest.fixture
def mock_session():
    """Sample session for testing."""
    now = datetime.now(UTC)
    return Session(
        session_id="sess_abc123def456",
        user_id="user_test",
        metadata=SessionMetadata(
            title="Test Session",
            description="Test description",
            tags=["test"],
            session_type=SessionType.CHAT,
            ttl_hours=24,
        ),
        status=SessionStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(hours=24),
        event_count=5,
        is_active=True,
        is_shared=False,
        shared_with_users=[],
        created_by="user_test",
        acl={"user_test": "owner"},
        collection_schemas={},
        session_tools=[],
        active_agent_id=None,
        source_session_id=None,
    )


@pytest.fixture
def test_user_context():
    """UserContext for testing."""
    return UserContext(
        user_id="user_test",
        email="test@example.com",
        permissions=("read_data", "write_data", "execute_tools"),
        quota_remaining=1000,
        tier=Tier.PRO,
    )


@pytest.fixture
def mock_session_service():
    """Mock SessionService for dependency override."""
    service = AsyncMock(spec=SessionService)
    return service


@pytest.fixture
def client(test_user_context, mock_session_service):
    """TestClient with overridden dependencies."""
    # Create fresh app for isolation
    test_app = FastAPI()

    # Copy routes from main app
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    async def override_session_service():
        return mock_session_service

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_session_service] = override_session_service
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestCreateSession:
    """Test POST /sessions endpoint."""

    def test_create_session_success(self, client, mock_session_service, mock_session):
        """
        TEST: Create new session
        PURPOSE: Verify session creation endpoint
        VALIDATES: Request validation, service integration
        EXPECTED: 201 with session data
        """
        # Setup mock
        mock_session_service.create.return_value = mock_session

        # Make request
        response = client.post(
            "/sessions",
            json={
                "title": "Test Session",
                "description": "Test description",
                "session_type": "chat",
                "tags": ["test"],
                "ttl_hours": 24,
            },
        )

        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "sess_abc123def456"
        assert data["title"] == "Test Session"
        assert data["status"] == "active"

        # Verify service called
        mock_session_service.create.assert_called_once()

    def test_create_session_invalid_title_fails(self, client, mock_session_service):
        """
        TEST: Create session with invalid title
        PURPOSE: Verify request validation
        VALIDATES: Pydantic validation
        EXPECTED: 422 validation error
        """
        response = client.post(
            "/sessions",
            json={
                "title": "",  # Empty title
                "session_type": "chat",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_session_tier_limit_exceeded(self, client, mock_session_service):
        """
        TEST: Create session when tier limit reached
        PURPOSE: Verify tier limit enforcement
        VALIDATES: Service raises ValidationError
        EXPECTED: 400 bad request
        """
        # Setup mock to raise ValidationError
        mock_session_service.create.side_effect = ValidationError(
            "Session limit reached. Tier 'PRO' allows max 10 active sessions."
        )

        response = client.post(
            "/sessions",
            json={
                "title": "Test Session",
                "session_type": "chat",
            },
        )

        assert response.status_code == 400
        assert "Session limit reached" in response.json()["detail"]


class TestGetSession:
    """Test GET /sessions/{session_id} endpoint."""

    def test_get_session_success(self, client, mock_session_service, mock_session):
        """
        TEST: Get session by ID
        PURPOSE: Verify session retrieval
        VALIDATES: Service integration, response model
        EXPECTED: 200 with session data
        """
        mock_session_service.get.return_value = mock_session

        response = client.get("/sessions/sess_abc123def456")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess_abc123def456"
        assert data["title"] == "Test Session"

    def test_get_nonexistent_session_fails(self, client, mock_session_service):
        """
        TEST: Get non-existent session
        PURPOSE: Verify error handling
        VALIDATES: NotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_session_service.get.side_effect = NotFoundError("Session not found")

        response = client.get("/sessions/sess_nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_permission_denied(self, client, mock_session_service):
        """
        TEST: Get session owned by another user
        PURPOSE: Verify ACL enforcement
        VALIDATES: PermissionDeniedError → 403
        EXPECTED: 403 forbidden
        """
        mock_session_service.get.side_effect = PermissionDeniedError(
            "User does not have access to session"
        )

        response = client.get("/sessions/sess_other_user")

        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()


class TestListSessions:
    """Test GET /sessions endpoint."""

    def test_list_sessions_success(self, client, mock_session_service, mock_session):
        """
        TEST: List user sessions
        PURPOSE: Verify session listing with pagination
        VALIDATES: Pagination, response structure
        EXPECTED: 200 with sessions array
        """
        mock_session_service.list_user_sessions.return_value = (
            [mock_session],
            1,
        )

        response = client.get("/sessions?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 1
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["has_more"] is False

    def test_list_sessions_pagination(self, client, mock_session_service, mock_session):
        """
        TEST: Pagination with has_more flag
        PURPOSE: Verify pagination logic
        VALIDATES: has_more calculation
        EXPECTED: has_more=True when total > page*page_size
        """
        mock_session_service.list_user_sessions.return_value = (
            [mock_session] * 20,
            50,  # More than one page
        )

        response = client.get("/sessions?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True  # 50 total > 20 per page

    def test_list_sessions_filter_by_status(self, client, mock_session_service, mock_session):
        """
        TEST: Filter sessions by status
        PURPOSE: Verify status filtering
        VALIDATES: Query parameter handling
        EXPECTED: Service called with status filter
        """
        mock_session_service.list_user_sessions.return_value = (
            [mock_session],
            1,
        )

        response = client.get("/sessions?status=active")

        assert response.status_code == 200
        # Verify service called with status filter
        mock_session_service.list_user_sessions.assert_called_once()
        call_kwargs = mock_session_service.list_user_sessions.call_args.kwargs
        assert call_kwargs["status"] == SessionStatus.ACTIVE


class TestUpdateSession:
    """Test PATCH /sessions/{session_id} endpoint."""

    def test_update_session_title(self, client, mock_session_service, mock_session):
        """
        TEST: Update session title
        PURPOSE: Verify partial update
        VALIDATES: PATCH semantics
        EXPECTED: 200 with updated session
        """
        # Create updated session with new title
        updated_session = mock_session.model_copy(deep=True)
        updated_session.metadata.title = "Updated Title"

        # Mock the update method
        mock_session_service.update.return_value = updated_session

        response = client.patch(
            "/sessions/sess_abc123def456",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_session_status(self, client, mock_session_service, mock_session):
        """
        TEST: Update session status
        PURPOSE: Verify status transition
        VALIDATES: Status update handling
        EXPECTED: 200 with new status
        """
        updated_session = mock_session.model_copy(deep=True)
        updated_session.status = SessionStatus.COMPLETED

        mock_session_service.update.return_value = updated_session

        response = client.patch(
            "/sessions/sess_abc123def456",
            json={"status": "completed"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


class TestDeleteSession:
    """Test DELETE /sessions/{session_id} endpoint."""

    def test_delete_session_success(self, client, mock_session_service):
        """
        TEST: Delete session
        PURPOSE: Verify soft delete
        VALIDATES: Service integration
        EXPECTED: 204 no content
        """
        mock_session_service.delete.return_value = None

        response = client.delete("/sessions/sess_abc123def456")

        assert response.status_code == 204
        mock_session_service.delete.assert_called_once_with(
            session_id="sess_abc123def456",
            user_id="user_test",
            cascade=False,
        )

    def test_delete_nonexistent_session_fails(self, client, mock_session_service):
        """
        TEST: Delete non-existent session
        PURPOSE: Verify error handling
        VALIDATES: NotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_session_service.delete.side_effect = NotFoundError("Session not found")

        response = client.delete("/sessions/sess_nonexistent")

        assert response.status_code == 404


# NOTE: Message history tests removed - use events API instead:
# GET /sessions/{id}/events?event_type=user_message,agent_message


class TestShareSession:
    """Test POST /sessions/{session_id}/share endpoint."""

    def test_share_session_success(self, client, mock_session_service, mock_session):
        """
        TEST: Share session with users
        PURPOSE: Verify ACL modification
        VALIDATES: Service integration
        EXPECTED: 200 with updated session
        """
        shared_session = mock_session.model_copy(deep=True)
        shared_session.is_shared = True
        shared_session.shared_with_users = ["user_friend"]

        mock_session_service.share_session.return_value = shared_session

        response = client.post(
            "/sessions/sess_abc123def456/share?user_ids=user_friend",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_shared"] is True
        assert "user_friend" in data["shared_with_users"]

    def test_share_session_permission_denied(self, client, mock_session_service):
        """
        TEST: Non-owner tries to share session
        PURPOSE: Verify ownership check
        VALIDATES: PermissionDeniedError → 403
        EXPECTED: 403 forbidden
        """
        mock_session_service.share_session.side_effect = PermissionDeniedError(
            "Only owner can share session"
        )

        response = client.post(
            "/sessions/sess_other_user/share?user_ids=user_friend",
        )

        assert response.status_code == 403


class TestUnshareSession:
    """Test POST /sessions/{session_id}/unshare endpoint."""

    def test_unshare_session_success(self, client, mock_session_service, mock_session):
        """
        TEST: Revoke session access
        PURPOSE: Verify ACL modification
        VALIDATES: Service integration
        EXPECTED: 200 with updated ACL
        """
        unshared_session = mock_session.model_copy(deep=True)
        unshared_session.is_shared = False
        unshared_session.shared_with_users = []

        mock_session_service.unshare_session.return_value = unshared_session

        response = client.post(
            "/sessions/sess_abc123def456/unshare?user_ids=user_friend",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_shared"] is False
        assert len(data["shared_with_users"]) == 0
