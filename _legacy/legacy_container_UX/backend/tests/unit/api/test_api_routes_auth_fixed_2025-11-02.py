"""Unit tests for src/api/routes/auth.py - FIXED VERSION

TEST: Authentication endpoints with proper dependency overrides
PURPOSE: Validate login/token endpoints
VALIDATES: OAuth2 flow, password verification, token generation
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app as main_app
from src.api.dependencies import get_auth_service, get_app_container
from src.services.auth_service import AuthService
from src.models.users import User
from src.models.permissions import Tier


# Fixtures


@pytest.fixture
def mock_auth_service():
    """Mock AuthService for dependency override."""
    service = AsyncMock(spec=AuthService)
    service.create_access_token = MagicMock()  # Synchronous method
    return service


@pytest.fixture
def mock_user():
    """Sample user for testing."""
    return User(
        user_id="user_test123",
        email="test@example.com",
        tier=Tier.PRO,
        created_at="2025-01-01T00:00:00Z",
        is_active=True,
    )


@pytest.fixture
def client(mock_auth_service):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    def override_auth_service():
        return mock_auth_service

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_auth_service] = override_auth_service
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestLogin:
    """Test POST /auth/login endpoint."""

    def test_login_success(self, client, mock_auth_service, mock_user):
        """
        TEST: Login with valid credentials
        PURPOSE: Verify authentication flow
        VALIDATES: User authentication, token generation
        EXPECTED: 200 with access token
        """
        mock_auth_service.authenticate_user.return_value = mock_user
        mock_auth_service.create_access_token.return_value = "mock_jwt_token_abc123"

        response = client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock_jwt_token_abc123"
        assert data["token_type"] == "bearer"

        # Verify service called
        mock_auth_service.authenticate_user.assert_called_once_with(
            "test@example.com", "SecurePass123!"
        )

    def test_login_invalid_credentials_fails(self, client, mock_auth_service):
        """
        TEST: Login with wrong password
        PURPOSE: Verify credential validation
        VALIDATES: Authentication rejection
        EXPECTED: 401 Unauthorized
        """
        mock_auth_service.authenticate_user.return_value = None  # Auth failed

        response = client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "WrongPassword",
            },
        )

        assert response.status_code == 401
        assert "username or password" in response.json()["detail"].lower()

    def test_login_missing_fields_fails(self, client):
        """
        TEST: Login without required fields
        PURPOSE: Verify request validation
        VALIDATES: OAuth2PasswordRequestForm validation
        EXPECTED: 422 validation error
        """
        response = client.post("/auth/login", data={})

        assert response.status_code == 422  # Pydantic validation
