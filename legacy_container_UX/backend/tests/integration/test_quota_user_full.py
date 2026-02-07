"""Full integration tests for quota and user endpoints.

Tests all 3 user/quota API endpoints with real/mock Firestore:
1. GET /user/info - Get current user info
2. GET /user/usage - Get usage statistics
3. GET /rate-limit/info - Get rate limit info
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_get_user_info(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /user/info - Get current user information."""
    response = enterprise_client.get(
        "/user/info",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to get user info: {response.text}"
    user_info = response.json()

    # Validate response structure
    assert "user_id" in user_info
    assert "email" in user_info
    assert "tier" in user_info
    assert "quota_remaining" in user_info
    assert "permissions" in user_info

    # Validate values
    assert user_info["email"] == "enterprise@test.com"
    assert user_info["tier"] in ["free", "pro", "enterprise"]
    assert isinstance(user_info["permissions"], list)


@pytest.mark.integration
def test_get_usage_statistics(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /user/usage - Get usage statistics."""
    response = enterprise_client.get(
        "/user/usage",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to get usage stats: {response.text}"
    usage_stats = response.json()

    # Validate response structure
    assert "quota" in usage_stats
    quota = usage_stats["quota"]

    assert "total" in quota
    assert "used" in quota
    assert "remaining" in quota
    assert "reset_at" in quota

    # Validate quota values are numeric
    assert isinstance(quota["total"], (int, float))
    assert isinstance(quota["used"], (int, float))
    assert isinstance(quota["remaining"], (int, float))


@pytest.mark.integration
def test_get_rate_limit_info(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /rate-limit/info - Get rate limit information."""
    response = enterprise_client.get(
        "/rate-limit/info",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to get rate limit info: {response.text}"
    rate_limit = response.json()

    # Validate response structure
    assert "limit" in rate_limit
    assert "used" in rate_limit
    assert "remaining" in rate_limit
    assert "reset_at" in rate_limit
    assert "tier" in rate_limit

    # Validate values
    assert isinstance(rate_limit["limit"], (int, float))
    assert isinstance(rate_limit["used"], (int, float))
    assert isinstance(rate_limit["remaining"], (int, float))
    assert rate_limit["tier"] in ["free", "pro", "enterprise"]


@pytest.mark.integration
def test_user_endpoints_unauthenticated(
    enterprise_client: TestClient,
):
    """Test that user endpoints require authentication."""
    # Test without auth headers
    endpoints = [
        "/user/info",
        "/user/usage",
        "/rate-limit/info",
    ]

    for endpoint in endpoints:
        response = enterprise_client.get(endpoint)
        assert response.status_code == 401, f"{endpoint} should return 401 without authentication"
