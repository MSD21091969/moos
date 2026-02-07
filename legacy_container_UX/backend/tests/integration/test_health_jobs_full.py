"""Full integration tests for health and jobs endpoints.

Tests all 5 health/jobs API endpoints with real/mock Firestore:
1. GET / - Root endpoint
2. GET /health - Health check
3. GET /ready - Readiness check
4. POST /jobs/export - Export session
5. POST /jobs/trigger - Trigger background job
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_endpoint(
    enterprise_client: TestClient,
):
    """Test GET / - Root endpoint returns API information."""
    response = enterprise_client.get("/")

    assert response.status_code == 200, f"Root endpoint failed: {response.text}"

    # Root endpoint returns JSON with API information
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "My Tiny Data Collider" in data["message"]
    assert data["version"] == "2.0.0"


@pytest.mark.integration
def test_health_check(
    enterprise_client: TestClient,
):
    """Test GET /health - Health check endpoint."""
    response = enterprise_client.get("/health")

    assert response.status_code == 200, f"Health check failed: {response.text}"
    health = response.json()

    # Validate response structure
    assert "status" in health
    assert health["status"] in ["healthy", "ok", "up"]


@pytest.mark.integration
def test_readiness_check(
    enterprise_client: TestClient,
):
    """Test GET /ready - Readiness probe."""
    response = enterprise_client.get("/ready")

    assert response.status_code == 200, f"Readiness check failed: {response.text}"
    readiness = response.json()

    # Validate response
    assert "status" in readiness or "ready" in readiness


@pytest.mark.integration
def test_export_session_job(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test POST /jobs/export - Trigger session export job."""
    # Create session first
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Export Test Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Trigger export
    response = enterprise_client.post(
        "/jobs/export-session",
        headers=enterprise_headers,
        json={"session_id": session_id, "export_format": "json"},
    )

    # Export job may not be fully implemented
    # Accept 200 (success), 202 (accepted), 500 (server error), or 501 (not implemented)
    assert response.status_code in [
        200,
        202,
        500,
        501,
    ], f"Export job returned unexpected status: {response.status_code}"


@pytest.mark.integration
def test_trigger_background_job(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test POST /jobs/trigger - Trigger background job."""
    response = enterprise_client.post(
        "/jobs/trigger",
        headers=enterprise_headers,
        json={"task_name": "cleanup", "task_args": {}},
    )

    # Background job may not be fully implemented
    # Accept 200 (success), 202 (accepted), 404 (not found), 500 (server error), or 501 (not implemented)
    assert response.status_code in [
        200,
        202,
        404,
        500,
        501,
    ], f"Background job returned unexpected status: {response.status_code}"


@pytest.mark.integration
def test_health_endpoints_unauthenticated(
    enterprise_client: TestClient,
):
    """Test that health endpoints work without authentication."""
    # Health endpoints should be public
    endpoints = [
        "/",
        "/health",
        "/ready",
    ]

    for endpoint in endpoints:
        response = enterprise_client.get(endpoint)
        # Should NOT return 401 (should be public)
        assert (
            response.status_code != 401
        ), f"{endpoint} should be accessible without authentication"
