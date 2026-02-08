"""Unit tests for src/api/routes/rate_limit.py - FIXED VERSION

TEST: Rate limiting endpoints with proper dependency overrides
PURPOSE: Validate rate limit info and reset endpoints
VALIDATES: Tier-based limits, usage tracking
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.main import app as main_app
from src.api.dependencies import get_user_context, get_rate_limiter_instance, get_app_container
from src.models.context import UserContext
from src.models.permissions import Tier
from src.core.rate_limiter import RateLimiter


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
def mock_rate_limiter():
    """Mock RateLimiter for dependency override."""
    limiter = MagicMock(spec=RateLimiter)
    return limiter


@pytest.fixture
def client(test_user_context, mock_rate_limiter):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    def override_rate_limiter():
        return mock_rate_limiter

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_rate_limiter_instance] = override_rate_limiter
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestGetRateLimitInfo:
    """Test GET /rate-limit/info endpoint."""

    def test_get_rate_limit_info_success(self, client, mock_rate_limiter):
        """
        TEST: Get rate limit information
        PURPOSE: Verify rate limit status retrieval
        VALIDATES: Service integration, response structure
        EXPECTED: 200 with limit info
        """
        mock_rate_limiter.get_limit_info.return_value = {
            "limit": 60,
            "used": 23,
            "remaining": 37,
            "reset_at": datetime.now(UTC).isoformat(),
            "tier": "pro",
        }

        response = client.get("/rate-limit/info")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 60
        assert data["used"] == 23
        assert data["remaining"] == 37
        assert "tier" in data

    def test_get_rate_limit_includes_tier_info(self, client, mock_rate_limiter):
        """
        TEST: Rate limit info includes tier
        PURPOSE: Verify tier information in response
        VALIDATES: Tier-based limits
        EXPECTED: Tier field present
        """
        mock_rate_limiter.get_limit_info.return_value = {
            "limit": 120,
            "used": 5,
            "remaining": 115,
            "reset_at": datetime.now(UTC).isoformat(),
            "tier": "pro",
        }

        response = client.get("/rate-limit/info")

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["limit"] == 120  # PRO tier has higher limit


class TestResetRateLimit:
    """Test POST /rate-limit/reset endpoint."""

    def test_reset_rate_limit_success(self, client, mock_rate_limiter):
        """
        TEST: Reset rate limit
        PURPOSE: Verify rate limit reset
        VALIDATES: Admin operation (MVP - no auth check)
        EXPECTED: 204 no content
        """
        mock_rate_limiter.reset_user.return_value = None

        response = client.post("/rate-limit/reset")

        assert response.status_code == 204

        # Verify service called
        mock_rate_limiter.reset_user.assert_called_once_with("user_test")
