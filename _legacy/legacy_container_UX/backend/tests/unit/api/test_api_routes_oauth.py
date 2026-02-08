"""Unit tests for OAuth routes.

Tests Google OAuth flow endpoints in src/api/routes/oauth.py.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.context import UserContext
from src.models.permissions import Tier


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def user_ctx():
    """Test user context."""
    return UserContext(
        user_id="test_user_oauth",
        email="test_oauth@example.com",
        tier=Tier.PRO,
        permissions=["read", "write"],
        quota_remaining=1000,
    )


class TestOAuthAuthorize:
    """Tests for GET /oauth/google/authorize"""

    def test_oauth_authorize_redirects_to_google(self, client, user_ctx):
        """
        TEST: OAuth authorize redirects to Google consent
        PURPOSE: Verify OAuth flow initiation
        VALIDATES: 307 redirect with Google URL
        EXPECTED: Redirect to accounts.google.com
        """
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.get(
                "/oauth/google/authorize",
                follow_redirects=False,
            )

            assert response.status_code == 307
            assert "google" in response.headers.get("location", "").lower()
        finally:
            app.dependency_overrides.clear()

    def test_oauth_authorize_requires_auth(self, client):
        """
        TEST: OAuth authorize requires authentication
        PURPOSE: Verify auth protection
        VALIDATES: 401 without token
        EXPECTED: Unauthorized
        """
        response = client.get("/oauth/google/authorize")
        assert response.status_code == 401


class TestOAuthStatus:
    """Tests for GET /oauth/google/status"""

    def test_oauth_status_not_connected(self, client, user_ctx):
        """
        TEST: OAuth status returns not connected
        PURPOSE: Verify status check when no credentials
        VALIDATES: connected=false
        EXPECTED: 200 with connected: false
        """
        # Override dependency
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.get("/oauth/google/status")

            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is False
            # Response has connected_email or no email field when not connected
        finally:
            app.dependency_overrides.clear()

    def test_oauth_status_requires_auth(self, client):
        """
        TEST: OAuth status requires authentication
        PURPOSE: Verify auth protection
        VALIDATES: 401 without token
        EXPECTED: Unauthorized
        """
        response = client.get("/oauth/google/status")
        assert response.status_code == 401


class TestOAuthRevoke:
    """Tests for DELETE /oauth/google/revoke"""

    def test_oauth_revoke_success(self, client, user_ctx):
        """
        TEST: OAuth revoke removes credentials
        PURPOSE: Verify credential revocation
        VALIDATES: 200 with success message
        EXPECTED: Credentials deleted
        """
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.delete("/oauth/google/revoke")

            assert response.status_code == 200
            data = response.json()
            msg = data.get("message", "").lower()
            assert "revoked" in msg or "success" in msg or "disconnected" in msg
        finally:
            app.dependency_overrides.clear()

    def test_oauth_revoke_requires_auth(self, client):
        """
        TEST: OAuth revoke requires authentication
        PURPOSE: Verify auth protection
        VALIDATES: 401 without token
        EXPECTED: Unauthorized
        """
        response = client.delete("/oauth/google/revoke")
        assert response.status_code == 401


class TestOAuthCallback:
    """Tests for GET /oauth/callback"""

    def test_oauth_callback_requires_auth(self, client):
        """
        TEST: OAuth callback requires authentication
        PURPOSE: Verify auth protection on callback
        VALIDATES: 401 without proper auth
        EXPECTED: Unauthorized
        """
        response = client.get(
            "/oauth/callback?code=test_code&state=test_user",
            follow_redirects=False,
        )

        # Should require authentication
        assert response.status_code == 401
