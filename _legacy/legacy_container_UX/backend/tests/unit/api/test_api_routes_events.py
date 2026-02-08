"""Unit tests for src/api/routes/events.py

TEST: Event querying API endpoints
PURPOSE: Validate event listing, retrieval, and tree operations
VALIDATES: Event filtering, hierarchical tree retrieval, permissions
PATTERN: Use app.dependency_overrides for service mocking
"""

import pytest
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from src.main import app as main_app
from src.api.dependencies import get_user_context
from src.api.routes.events import get_event_service
from src.models.context import UserContext
from src.models.permissions import Tier
from src.models.events import SessionEvent, SessionEventTree, EventSource, EventStatus, EventType
from src.services.event_service import EventService


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
def sample_event():
    """Sample session event."""
    return SessionEvent(
        event_id="evt_abc123",
        session_id="sess_abc123def456",
        parent_event_id=None,
        event_path="/evt_abc123",
        depth=0,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        status=EventStatus.COMPLETED,
        data={"message": "Test"},
        timestamp=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_event_tree(sample_event):
    """Sample event tree."""
    return SessionEventTree(
        event=sample_event,
        children=[],
    )


@pytest.fixture
def mock_event_service():
    """Mock EventService."""
    return AsyncMock(spec=EventService)


@pytest.fixture
def client(test_user_context, mock_event_service):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    async def override_user_context():
        return test_user_context

    async def override_event_service():
        return mock_event_service

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_event_service] = override_event_service

    return TestClient(test_app)


# Tests


class TestListEvents:
    """Tests for GET /sessions/{id}/events"""

    def test_list_events_all(self, client, mock_event_service, sample_event):
        """Test listing all events in a session."""
        mock_event_service.list_events.return_value = ([sample_event], 1)

        response = client.get("/sessions/sess_abc123def456/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["event_id"] == "evt_abc123"

    def test_list_events_filter_by_depth(self, client, mock_event_service, sample_event):
        """Test filtering events by depth."""
        mock_event_service.list_events.return_value = ([sample_event], 1)

        response = client.get("/sessions/sess_abc123def456/events?depth=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["depth"] == 0

    def test_list_events_filter_by_source(self, client, mock_event_service, sample_event):
        """Test filtering events by source."""
        mock_event_service.list_events.return_value = ([sample_event], 1)

        response = client.get("/sessions/sess_abc123def456/events?source=user")

        assert response.status_code == 200

    def test_list_events_filter_by_status(self, client, mock_event_service, sample_event):
        """Test filtering events by status."""
        mock_event_service.list_events.return_value = ([sample_event], 1)

        response = client.get("/sessions/sess_abc123def456/events?status=completed")

        assert response.status_code == 200


class TestGetEventDetails:
    """Tests for GET /sessions/{id}/events/{event_id}"""

    def test_get_event_details_success(self, client, mock_event_service, sample_event):
        """Test getting event details."""
        mock_event_service.get_event.return_value = sample_event

        response = client.get("/sessions/sess_abc123def456/events/evt_abc123")

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "evt_abc123"
        assert data["source"] == "user"  # EventSource enum serializes to lowercase

    def test_get_event_details_not_found(self, client, mock_event_service):
        """Test getting non-existent event."""
        mock_event_service.get_event.return_value = None

        response = client.get("/sessions/sess_abc123def456/events/nonexistent")

        assert response.status_code == 404


class TestGetEventTree:
    """Tests for GET /sessions/{id}/events/{event_id}/tree"""

    def test_get_event_tree_success(self, client, mock_event_service, sample_event_tree):
        """Test getting event tree."""
        mock_event_service.get_event_tree.return_value = sample_event_tree

        response = client.get("/sessions/sess_abc123def456/events/evt_abc123/tree")

        assert response.status_code == 200
        data = response.json()
        assert data["event"]["event_id"] == "evt_abc123"
        assert "children" in data

    def test_get_event_tree_not_found(self, client, mock_event_service):
        """Test getting tree for non-existent event."""
        mock_event_service.get_event_tree.return_value = None

        response = client.get("/sessions/sess_abc123def456/events/nonexistent/tree")

        assert response.status_code == 404
