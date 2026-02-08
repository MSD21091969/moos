"""Unit tests for src/api/routes/user.py - FIXED VERSION

TEST: User management endpoints with proper dependency overrides
PURPOSE: Validate user info and usage statistics endpoints
VALIDATES: JWT user context, quota tracking
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import app as main_app
from src.api.dependencies import get_user_context, get_app_container
from src.models.context import UserContext
from src.models.permissions import Tier


# Fixtures


@pytest.fixture
def test_user_context():
    """UserContext for testing."""
    return UserContext(
        user_id="user_test123",
        email="test@example.com",
        display_name="Test User",
        permissions=("read_data", "write_data", "execute_tools"),
        quota_remaining=850,
        tier=Tier.PRO,
    )


@pytest.fixture
def client(test_user_context):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestGetCurrentUserInfo:
    """Test GET /user/info endpoint."""

    def test_get_user_info_success(self, client):
        """
        TEST: Get current user info
        PURPOSE: Verify user context extraction
        VALIDATES: JWT token decoding, user data
        EXPECTED: 200 with user info
        """
        response = client.get("/user/info")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_test123"
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert data["tier"] == "pro"  # Serialized enum value
        assert data["quota_remaining"] == 850
        assert "read_data" in data["permissions"]


class TestGetUsageStatistics:
    """Test GET /user/usage endpoint."""

    @patch("src.api.routes.user.QuotaService")
    def test_get_usage_statistics_success(self, mock_quota_service_class, client):
        """
        TEST: Get user usage statistics
        PURPOSE: Verify usage data retrieval
        VALIDATES: Quota tracking, historical data
        EXPECTED: 200 with usage info
        """
        # Mock the QuotaService instance
        mock_service = AsyncMock()
        mock_service.get_quota_usage.return_value = [
            {
                "date": datetime.now(UTC).date().isoformat(),
                "used": 150,
                "daily_limit": 1000,
            }
        ]
        mock_quota_service_class.return_value = mock_service

        response = client.get("/user/usage")

        assert response.status_code == 200
        data = response.json()
        assert "quota" in data
        assert "usage_history" in data
        assert data["user_id"] == "user_test123"
        assert data["tier"] == "pro"  # Serialized enum value
        assert data["quota"]["total"] == 1000
        assert data["quota"]["used"] == 150
        assert data["quota"]["remaining"] == 850

    @patch("src.api.routes.user.QuotaService")
    def test_get_usage_statistics_error_fallback(self, mock_quota_service_class, client):
        """
        TEST: Usage statistics with service error
        PURPOSE: Verify fallback response
        VALIDATES: Error handling, degraded mode
        EXPECTED: 200 with fallback data
        """
        # Mock service to raise exception
        mock_service = AsyncMock()
        mock_service.get_quota_usage.side_effect = Exception("Database error")
        mock_quota_service_class.return_value = mock_service

        response = client.get("/user/usage")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["quota"]["remaining"] == 850  # From user context
