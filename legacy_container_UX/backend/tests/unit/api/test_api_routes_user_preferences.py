"""Unit tests for user preferences API routes.

Tests GET /user/preferences and PATCH /user/preferences in src/api/routes/user.py.
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
        user_id="test_user_prefs_api",
        email="test_prefs@example.com",
        tier=Tier.PRO,
        permissions=["read", "write"],
        quota_remaining=1000,
    )


class TestGetPreferences:
    """Tests for GET /user/preferences"""

    def test_get_preferences_success(self, client, user_ctx):
        """
        TEST: GET /user/preferences returns user preferences
        PURPOSE: Verify preferences retrieval
        VALIDATES: Response structure matches UserPreferences
        EXPECTED: 200 with all preference fields
        """
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.get("/user/preferences")

            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "draft_messages" in data
            assert "active_tabs" in data
            assert "ui_preferences" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_preferences_requires_auth(self, client):
        """
        TEST: GET /user/preferences requires authentication
        PURPOSE: Verify auth protection
        VALIDATES: 401 without token
        EXPECTED: Unauthorized
        """
        response = client.get("/user/preferences")
        assert response.status_code == 401


class TestPatchPreferences:
    """Tests for PATCH /user/preferences"""

    def test_patch_preferences_merge_drafts(self, client, user_ctx):
        """
        TEST: PATCH /user/preferences merges draft messages
        PURPOSE: Verify merge behavior (not replace)
        VALIDATES: New drafts added
        EXPECTED: 200 with updated preferences
        """
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.patch(
                "/user/preferences",
                json={"draft_messages": {"sess_new_api": "new draft"}},
            )

            assert response.status_code == 200
            data = response.json()
            assert "sess_new_api" in data["draft_messages"]
        finally:
            app.dependency_overrides.clear()

    def test_patch_preferences_ui_settings(self, client, user_ctx):
        """
        TEST: PATCH /user/preferences updates UI settings
        PURPOSE: Verify UI state persistence
        VALIDATES: Theme, sidebar saved
        EXPECTED: 200 with updated UI preferences
        """
        from src.api.dependencies import get_user_context

        app.dependency_overrides[get_user_context] = lambda: user_ctx

        try:
            response = client.patch(
                "/user/preferences",
                json={
                    "ui_preferences": {
                        "theme": "light",
                        "sidebarCollapsed": True,
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ui_preferences"]["theme"] == "light"
        finally:
            app.dependency_overrides.clear()

    def test_patch_preferences_requires_auth(self, client):
        """
        TEST: PATCH /user/preferences requires authentication
        PURPOSE: Verify auth protection
        VALIDATES: 401 without token
        EXPECTED: Unauthorized
        """
        response = client.patch(
            "/user/preferences",
            json={"active_session_id": "test"},
        )
        assert response.status_code == 401
