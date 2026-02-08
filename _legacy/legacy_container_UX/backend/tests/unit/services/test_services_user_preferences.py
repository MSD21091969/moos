"""Unit tests for UserPreferencesService.

Tests user preferences and cross-device state sync in src/services/user_preferences_service.py.
"""

import pytest

from src.models.users import UserPreferencesUpdate
from src.services.user_preferences_service import UserPreferencesService


@pytest.fixture
def service():
    """UserPreferencesService."""
    return UserPreferencesService()


class TestGetPreferences:
    """Tests for get_preferences()"""

    @pytest.mark.asyncio
    async def test_get_preferences_creates_default(self, service):
        """
        TEST: Get preferences creates default when none exist
        PURPOSE: Verify default initialization
        VALIDATES: Default preferences structure
        EXPECTED: Empty drafts, tabs, empty UI settings
        """
        user_id = "test_user_new_prefs"

        prefs = await service.get_preferences(user_id)

        assert prefs.user_id == user_id
        assert prefs.draft_messages == {}
        assert prefs.active_tabs == {}
        assert prefs.active_session_id is None
        # Default UI preferences is empty dict
        assert isinstance(prefs.ui_preferences, dict)

    @pytest.mark.asyncio
    async def test_get_preferences_returns_existing(self, service):
        """
        TEST: Get preferences returns existing data
        PURPOSE: Verify retrieval of saved preferences
        VALIDATES: Preserved user data
        EXPECTED: Exact match with stored preferences
        """
        user_id = "test_user_existing_prefs"

        # Create preferences first via update
        update = UserPreferencesUpdate(
            active_session_id="sess_123",
            draft_messages={"sess_123": "test draft"},
            active_tabs={"sess_123": "chat"},
            ui_preferences={"theme": "light", "fontSize": 14},
        )
        await service.update_preferences(user_id, update)

        prefs = await service.get_preferences(user_id)

        assert prefs.user_id == user_id
        assert prefs.active_session_id == "sess_123"
        assert prefs.draft_messages["sess_123"] == "test draft"
        assert prefs.active_tabs["sess_123"] == "chat"
        assert prefs.ui_preferences["theme"] == "light"


class TestUpdatePreferences:
    """Tests for update_preferences()"""

    @pytest.mark.asyncio
    async def test_update_preferences_merge_strategy(self, service):
        """
        TEST: Update preferences merges with existing
        PURPOSE: Verify merge behavior (not replace)
        VALIDATES: Old data preserved + new data added
        EXPECTED: Both old and new drafts exist
        """
        user_id = "test_user_merge_prefs"

        # Create initial draft
        update1 = UserPreferencesUpdate(draft_messages={"sess_old": "old draft"})
        await service.update_preferences(user_id, update1)

        # Update with new draft
        update2 = UserPreferencesUpdate(draft_messages={"sess_new": "new draft"})
        result = await service.update_preferences(user_id, update2)

        # Both drafts should exist
        assert "sess_old" in result.draft_messages
        assert "sess_new" in result.draft_messages
        assert result.draft_messages["sess_old"] == "old draft"
        assert result.draft_messages["sess_new"] == "new draft"

    @pytest.mark.asyncio
    async def test_update_preferences_active_session(self, service):
        """
        TEST: Update active session ID
        PURPOSE: Verify session tracking
        VALIDATES: active_session_id updated
        EXPECTED: New session ID stored
        """
        user_id = "test_user_session_prefs"

        update = UserPreferencesUpdate(active_session_id="sess_active_123")
        result = await service.update_preferences(user_id, update)

        assert result.active_session_id == "sess_active_123"

    @pytest.mark.asyncio
    async def test_update_preferences_ui_settings(self, service):
        """
        TEST: Update UI preferences (theme, sidebar)
        PURPOSE: Verify UI state persistence
        VALIDATES: ui_preferences merged
        EXPECTED: Theme and sidebar saved
        """
        user_id = "test_user_ui_prefs"

        update = UserPreferencesUpdate(
            ui_preferences={
                "theme": "light",
                "sidebarCollapsed": True,
                "fontSize": 16,
            }
        )
        result = await service.update_preferences(user_id, update)

        assert result.ui_preferences["theme"] == "light"
        assert result.ui_preferences["sidebarCollapsed"] is True
        assert result.ui_preferences["fontSize"] == 16


class TestClearDraft:
    """Tests for clear_draft()"""

    @pytest.mark.asyncio
    async def test_clear_draft_removes_specific(self, service):
        """
        TEST: Clear draft removes specific session draft
        PURPOSE: Verify selective draft deletion
        VALIDATES: Target draft removed, others preserved
        EXPECTED: Only specified draft deleted
        """
        user_id = "test_user_clear_prefs"

        # Create multiple drafts
        update = UserPreferencesUpdate(
            draft_messages={
                "sess_keep": "keep this",
                "sess_delete": "delete this",
            }
        )
        await service.update_preferences(user_id, update)

        # Clear one draft
        result = await service.clear_draft(user_id, "sess_delete")

        assert "sess_keep" in result.draft_messages
        assert "sess_delete" not in result.draft_messages
        assert result.draft_messages["sess_keep"] == "keep this"


class TestResetPreferences:
    """Tests for reset_preferences()"""

    @pytest.mark.asyncio
    async def test_reset_preferences_to_defaults(self, service):
        """
        TEST: Reset preferences clears all user data
        PURPOSE: Verify full reset to defaults
        VALIDATES: All custom data removed
        EXPECTED: Default empty state
        """
        user_id = "test_user_reset_prefs"

        # Create custom preferences
        update = UserPreferencesUpdate(
            draft_messages={"sess_1": "draft 1", "sess_2": "draft 2"},
            active_tabs={"sess_1": "chat"},
            active_session_id="sess_1",
            ui_preferences={"theme": "light"},
        )
        await service.update_preferences(user_id, update)

        # Reset to defaults
        result = await service.reset_preferences(user_id)

        assert result.draft_messages == {}
        assert result.active_tabs == {}
        assert result.active_session_id is None
        assert result.ui_preferences == {}  # Empty after reset
