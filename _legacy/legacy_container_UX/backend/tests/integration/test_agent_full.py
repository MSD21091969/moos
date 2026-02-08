"""Full integration tests for agent execution endpoints.

Tests all 2 agent API endpoints with real/mock Firestore:
1. POST /agent/run - Execute agent with message
2. GET /agent/capabilities - Get agent capabilities
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_agent_run_with_session(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test POST /agent/run - Execute agent with session."""
    # Create session first
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={
            "title": "Agent Test Session",
            "session_type": "chat",
            "ttl_hours": 24,
        },
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Run agent
    response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={
            "message": "Hello, what is 2+2?",
            "session_id": session_id,
        },
    )

    assert response.status_code == 200, f"Failed to run agent: {response.text}"
    agent_response = response.json()

    # Validate response structure
    assert "session_id" in agent_response
    assert "message_id" in agent_response
    assert "response" in agent_response
    assert "tools_used" in agent_response
    assert "quota_used" in agent_response
    assert "quota_remaining" in agent_response

    # Validate values
    assert agent_response["session_id"] == session_id
    assert isinstance(agent_response["response"], str)
    assert len(agent_response["response"]) > 0
    assert agent_response["quota_used"] >= 0


@pytest.mark.integration
def test_agent_run_without_session(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test POST /agent/run - Execute agent without session (ephemeral)."""
    response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={
            "message": "Quick question: What is the capital of France?",
            # No session_id - should auto-create ephemeral session
        },
    )

    assert response.status_code == 200, f"Failed to run agent: {response.text}"
    agent_response = response.json()

    # Validate ephemeral session created
    assert "session_id" in agent_response
    assert agent_response["session_id"].startswith("sess_")

    # Track for cleanup
    created_session_ids.append(agent_response["session_id"])

    # Validate response
    assert "response" in agent_response
    assert isinstance(agent_response["response"], str)
    assert len(agent_response["response"]) > 0


@pytest.mark.integration
def test_agent_run_invalid_session(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test POST /agent/run - Error on invalid session ID."""
    response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={
            "message": "Test message",
            "session_id": "invalid_session_id",  # Invalid format
        },
    )

    assert response.status_code == 400, "Should return 400 for invalid session ID"


@pytest.mark.integration
def test_agent_run_nonexistent_session(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test POST /agent/run - Error on non-existent session."""
    response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={
            "message": "Test message",
            "session_id": "sess_000000000000",  # Valid format but doesn't exist
        },
    )

    assert response.status_code == 404, "Should return 404 for non-existent session"


@pytest.mark.integration
def test_agent_capabilities(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /agent/capabilities - Get agent capabilities."""
    response = enterprise_client.get(
        "/agent/capabilities",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to get capabilities: {response.text}"
    capabilities = response.json()

    # Validate capabilities structure
    # Note: Structure depends on implementation, adjust as needed
    assert isinstance(capabilities, dict)


@pytest.mark.integration
def test_agent_run_validation(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test POST /agent/run - Validation errors."""
    # Empty message
    response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={
            "message": "",  # Empty message
        },
    )

    # Should either succeed with empty message or return 400/422
    # 422 = Unprocessable Entity (Pydantic validation error)
    assert response.status_code in [
        200,
        400,
        422,
    ], f"Unexpected status for empty message: {response.status_code}"
