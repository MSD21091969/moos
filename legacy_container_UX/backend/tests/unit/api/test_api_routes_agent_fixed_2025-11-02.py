"""Unit tests for src/api/routes/agent.py - FIXED VERSION

TEST: Agent execution API endpoints with proper dependency overrides
PURPOSE: Validate agent run, streaming, and capabilities endpoints
VALIDATES: Request/response, quota enforcement, session integration
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app as main_app
from src.api.dependencies import get_user_context, get_app_container
from src.api.routes.agent import get_agent_service as get_agent_service_route
from src.models.context import UserContext
from src.models.permissions import Tier
from src.core.exceptions import (
    NotFoundError,
    InsufficientQuotaError,
)
from src.services.agent_service import AgentService, AgentExecutionResult


# Fixtures


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
def mock_agent_service():
    """Mock AgentService for dependency override."""
    service = AsyncMock(spec=AgentService)
    return service


@pytest.fixture
def mock_execution_result():
    """Sample execution result."""
    return AgentExecutionResult(
        session_id="sess_abc123def456",
        message_id="msg_xyz789",
        response="This is the agent response",
        tools_used=["calculate_expression"],
        new_messages_count=2,
        quota_used=3,  # int, not float
        quota_remaining=997,  # int, not float
        model_used="gpt-4",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    )


@pytest.fixture
def client(test_user_context, mock_agent_service):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    def override_agent_service():
        return mock_agent_service

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_agent_service_route] = override_agent_service
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestRunAgent:
    """Test POST /agent/run endpoint."""

    def test_run_agent_success(self, client, mock_agent_service, mock_execution_result):
        """
        TEST: Run agent with valid request
        PURPOSE: Verify agent execution
        VALIDATES: Service integration, response structure
        EXPECTED: 200 with execution result
        """
        mock_agent_service.execute.return_value = mock_execution_result

        response = client.post(
            "/agent/run",
            json={
                "message": "What is 2 + 2?",
                "session_id": "sess_abc123def456",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess_abc123def456"
        assert data["message_id"] == "msg_xyz789"
        assert data["response"] == "This is the agent response"
        assert data["tools_used"] == ["calculate_expression"]
        assert data["quota_used"] == 3

        # Verify service called
        mock_agent_service.execute.assert_called_once()

    def test_run_agent_without_session(self, client, mock_agent_service, mock_execution_result):
        """
        TEST: Run agent without session_id (ephemeral)
        PURPOSE: Verify auto-session creation
        VALIDATES: Session-less execution
        EXPECTED: 200 with new session_id
        """
        # Agent creates ephemeral session
        ephemeral_result = mock_execution_result
        ephemeral_result.session_id = "sess_ephemeral99"
        mock_agent_service.execute.return_value = ephemeral_result

        response = client.post(
            "/agent/run",
            json={"message": "Quick question"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["response"] == "This is the agent response"

    def test_run_agent_quota_exceeded(self, client, mock_agent_service):
        """
        TEST: Run agent when quota exhausted
        PURPOSE: Verify quota enforcement
        VALIDATES: InsufficientQuotaError → 429
        EXPECTED: 429 Too Many Requests
        """
        mock_agent_service.execute.side_effect = InsufficientQuotaError("Daily quota exceeded")

        response = client.post(
            "/agent/run",
            json={"message": "Test"},
        )

        assert response.status_code == 429
        assert "quota" in response.json()["detail"].lower()

    def test_run_agent_session_not_found(self, client, mock_agent_service):
        """
        TEST: Run agent with non-existent session
        PURPOSE: Verify session validation
        VALIDATES: NotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_agent_service.execute.side_effect = NotFoundError("Session not found")

        response = client.post(
            "/agent/run",
            json={
                "message": "Test",
                "session_id": "sess_000000000000",  # Valid format but non-existent
            },
        )

        assert response.status_code == 404

    def test_run_agent_invalid_session_format(self, client, mock_agent_service):
        """
        TEST: Run agent with invalid session_id format
        PURPOSE: Verify session_id regex validation
        VALIDATES: Session ID pattern matching
        EXPECTED: 400 bad request
        """
        response = client.post(
            "/agent/run",
            json={
                "message": "Test",
                "session_id": "invalid-format",  # Wrong format
            },
        )

        assert response.status_code == 400
        assert "Invalid session_id format" in response.json()["detail"]

    def test_run_agent_empty_message_fails(self, client):
        """
        TEST: Run agent with empty message
        PURPOSE: Verify message validation
        VALIDATES: Pydantic validation
        EXPECTED: 422 validation error
        """
        response = client.post(
            "/agent/run",
            json={
                "message": "",  # Empty message
            },
        )

        assert response.status_code == 422  # Pydantic validation


class TestGetCapabilities:
    """Test GET /agent/capabilities endpoint."""

    def test_get_capabilities_success(self, client, mock_agent_service):
        """
        TEST: Get agent capabilities
        PURPOSE: Verify capabilities retrieval
        VALIDATES: Service integration
        EXPECTED: 200 with capabilities dict
        """
        mock_agent_service.get_capabilities.return_value = {
            "available_models": ["gpt-4", "gpt-3.5-turbo"],
            "available_tools": ["search", "calculate", "export"],
            "max_messages_per_session": 100,
            "max_concurrent_sessions": 10,
            "features": {
                "streaming": True,
                "file_upload": True,
                "tool_execution": True,
                "session_sharing": True,
            },
        }

        response = client.get("/agent/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert "available_models" in data
        assert "available_tools" in data
        assert "gpt-4" in data["available_models"]


class TestStreamAgent:
    """Test POST /agent/stream endpoint."""

    async def test_stream_agent_success(self, client, mock_agent_service):
        """
        TEST: Stream agent response
        PURPOSE: Verify SSE streaming
        VALIDATES: StreamingResponse
        EXPECTED: 200 with text/event-stream
        """

        async def mock_stream():
            yield b'data: {"type": "token", "token": "Hello"}\n\n'
            yield b'data: {"type": "done"}\n\n'

        mock_agent_service.stream_agent.return_value = mock_stream()

        response = client.post(
            "/agent/stream",
            json={"message": "Test"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    async def test_stream_agent_quota_exceeded(self, client, mock_agent_service):
        """
        TEST: Stream agent when quota exhausted
        PURPOSE: Verify quota enforcement
        VALIDATES: InsufficientQuotaError → 402
        EXPECTED: 402 Payment Required
        """
        mock_agent_service.stream_agent.side_effect = InsufficientQuotaError("Daily quota exceeded")

        response = client.post(
            "/agent/stream",
            json={"message": "Test"},
        )

        assert response.status_code == 402
