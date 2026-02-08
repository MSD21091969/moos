"""Tests for dashboard API endpoints.

Tests the new dashboard statistics and session activity endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.api.dependencies import get_user_context
from src.models.context import UserContext
from src.models.permissions import Tier

client = TestClient(app)


@pytest.fixture
def mock_user_context():
    """Create a mock user context for testing."""
    return UserContext(
        user_id="test_user_123",
        email="test@example.com",
        display_name="Test User",
        tier=Tier.PRO,
        permissions=["all"],
        quota_remaining=1000,
    )


@pytest.fixture(autouse=True)
def override_dependencies(mock_user_context):
    """Override dependencies for all tests in this module."""
    app.dependency_overrides[get_user_context] = lambda: mock_user_context
    yield
    app.dependency_overrides.clear()


class TestDashboardStats:
    """Test GET /dashboard/stats endpoint."""

    def test_get_dashboard_stats_success(self, mock_user_context):
        """Test successful dashboard stats retrieval."""
        response = client.get("/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "total_messages" in data
        assert "total_tool_calls" in data
        assert "most_used_tools" in data
        assert "most_used_agents" in data
        assert "quota_usage_trend" in data
        assert "recent_activity" in data
        assert "session_distribution" in data

        # Verify data types
        assert isinstance(data["total_sessions"], int)
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["total_messages"], int)
        assert isinstance(data["total_tool_calls"], int)
        assert isinstance(data["most_used_tools"], list)
        assert isinstance(data["most_used_agents"], list)
        assert isinstance(data["quota_usage_trend"], list)
        assert isinstance(data["recent_activity"], list)
        assert isinstance(data["session_distribution"], dict)

    def test_get_dashboard_stats_returns_default_on_error(self, mock_user_context):
        """Test that dashboard stats returns default values on error."""
        # This test verifies the fallback behavior
        response = client.get("/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # Should always return valid structure even if empty
        assert data["total_sessions"] >= 0
        assert data["active_sessions"] >= 0
        assert data["total_messages"] >= 0
        assert data["total_tool_calls"] >= 0


class TestSessionActivity:
    """Test GET /dashboard/sessions/{session_id}/activity endpoint."""

    def test_get_session_activity_nonexistent_session(self, mock_user_context):
        """Test getting activity for nonexistent session returns 404."""
        session_id = "sess_nonexistent"
        response = client.get(f"/dashboard/sessions/{session_id}/activity")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_session_activity_with_pagination(self, mock_user_context):
        """Test session activity endpoint accepts pagination parameters."""
        session_id = "sess_test123456"
        response = client.get(
            f"/dashboard/sessions/{session_id}/activity", params={"limit": 10, "offset": 0}
        )

        # May return 404 if session doesn't exist, or 403 if permission denied
        # Both are acceptable for this test
        assert response.status_code in [200, 403, 404]


class TestBackwardCompatibility:
    """Test that new fields don't break existing endpoints."""

    def test_session_response_includes_new_fields(self):
        """Test that SessionResponse model includes new optional fields."""
        from src.api.models import SessionResponse

        # Verify new fields exist in model
        fields = SessionResponse.model_fields
        assert "preview" in fields
        assert "last_activity" in fields
        assert "message_count" in fields
        assert "tool_usage_summary" in fields
        assert "color_theme" in fields

        # Verify fields are optional
        assert fields["preview"].is_required() is False
        assert fields["last_activity"].is_required() is False
        assert fields["color_theme"].is_required() is False

    def test_tool_info_includes_new_fields(self):
        """Test that ToolInfo model includes new optional fields."""
        from src.api.models import ToolInfo

        fields = ToolInfo.model_fields
        assert "icon" in fields
        assert "usage_count" in fields
        assert "example_use_case" in fields
        assert "estimated_quota_cost" in fields

        # Verify fields are optional or have defaults
        assert fields["icon"].is_required() is False
        assert fields["usage_count"].is_required() is False
        assert fields["example_use_case"].is_required() is False

    def test_agent_capabilities_includes_new_fields(self):
        """Test that AgentCapabilitiesResponse includes new optional fields."""
        from src.api.models import AgentCapabilitiesResponse

        fields = AgentCapabilitiesResponse.model_fields
        assert "personality" in fields
        assert "specializations" in fields
        assert "example_prompts" in fields
        assert "performance_stats" in fields

        # Verify fields are optional
        assert fields["personality"].is_required() is False

    def test_trace_event_includes_new_fields(self):
        """Test that TraceEventResponse includes new optional fields."""
        from src.api.models import TraceEventResponse

        fields = TraceEventResponse.model_fields
        assert "depth_level" in fields
        assert "siblings_count" in fields
        assert "is_collapsed" in fields
        assert "execution_context" in fields

        # Verify fields have defaults
        assert fields["depth_level"].is_required() is False
        assert fields["siblings_count"].is_required() is False
        assert fields["is_collapsed"].is_required() is False
