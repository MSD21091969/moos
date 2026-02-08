"""User preferences service for cross-device state synchronization."""

from datetime import UTC, datetime

from src.models.users import UserPreferences, UserPreferencesUpdate
from src.persistence.firestore_client import get_firestore_client


class UserPreferencesService:
    """Service layer for managing user preferences and session context."""

    async def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences, creating default if not exists.

        Args:
            user_id: User ID to fetch preferences for

        Returns:
            UserPreferences object
        """
        client = await get_firestore_client()
        doc_ref = client.collection("user_preferences").document(user_id)
        doc = await doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return UserPreferences(
                user_id=data.get("user_id", user_id),
                active_session_id=data.get("active_session_id"),
                draft_messages=data.get("draft_messages", {}),
                active_tabs=data.get("active_tabs", {}),
                ui_preferences=data.get("ui_preferences", {}),
                created_at=data.get("created_at", datetime.now(UTC)),
                updated_at=data.get("updated_at", datetime.now(UTC)),
            )

        # Create default preferences for new user
        return await self._create_default_preferences(user_id)

    async def _create_default_preferences(self, user_id: str) -> UserPreferences:
        """Create default preferences for a user.

        Args:
            user_id: User ID

        Returns:
            Newly created UserPreferences
        """
        now = datetime.now(UTC)

        prefs = UserPreferences(
            user_id=user_id,
            active_session_id=None,
            draft_messages={},
            active_tabs={},
            ui_preferences={},
            created_at=now,
            updated_at=now,
        )

        client = await get_firestore_client()
        doc_ref = client.collection("user_preferences").document(user_id)
        await doc_ref.set(
            {
                "user_id": user_id,
                "active_session_id": None,
                "draft_messages": {},
                "active_tabs": {},
                "ui_preferences": {},
                "created_at": now,
                "updated_at": now,
            }
        )

        return prefs

    async def update_preferences(
        self,
        user_id: str,
        update: UserPreferencesUpdate,
    ) -> UserPreferences:
        """Update user preferences (partial update with merge).

        Args:
            user_id: User ID
            update: Fields to update

        Returns:
            Updated UserPreferences
        """
        # Get current preferences
        current = await self.get_preferences(user_id)

        # Merge updates
        update_data: dict = {"updated_at": datetime.now(UTC)}

        if update.active_session_id is not None:
            update_data["active_session_id"] = update.active_session_id

        if update.draft_messages is not None:
            # Merge with existing draft_messages
            merged_drafts = {**current.draft_messages, **update.draft_messages}
            update_data["draft_messages"] = merged_drafts

        if update.active_tabs is not None:
            # Merge with existing active_tabs
            merged_tabs = {**current.active_tabs, **update.active_tabs}
            update_data["active_tabs"] = merged_tabs

        if update.ui_preferences is not None:
            # Merge with existing ui_preferences
            merged_prefs = {**current.ui_preferences, **update.ui_preferences}
            update_data["ui_preferences"] = merged_prefs

        # Update Firestore
        client = await get_firestore_client()
        doc_ref = client.collection("user_preferences").document(user_id)
        await doc_ref.update(update_data)

        # Return updated preferences
        return await self.get_preferences(user_id)

    async def clear_draft(self, user_id: str, session_id: str) -> UserPreferences:
        """Clear draft message for a specific session.

        Args:
            user_id: User ID
            session_id: Session ID to clear draft for

        Returns:
            Updated UserPreferences
        """
        current = await self.get_preferences(user_id)

        # Remove the draft for this session
        if session_id in current.draft_messages:
            updated_drafts = {**current.draft_messages}
            del updated_drafts[session_id]

            client = await get_firestore_client()
            doc_ref = client.collection("user_preferences").document(user_id)
            await doc_ref.update(
                {
                    "draft_messages": updated_drafts,
                    "updated_at": datetime.now(UTC),
                }
            )

        return await self.get_preferences(user_id)

    async def reset_preferences(self, user_id: str) -> UserPreferences:
        """Reset user preferences to defaults.

        Args:
            user_id: User ID

        Returns:
            Reset UserPreferences
        """
        now = datetime.now(UTC)

        client = await get_firestore_client()
        doc_ref = client.collection("user_preferences").document(user_id)
        await doc_ref.update(
            {
                "active_session_id": None,
                "draft_messages": {},
                "active_tabs": {},
                "ui_preferences": {},
                "updated_at": now,
            }
        )

        return await self.get_preferences(user_id)


# Singleton instance
user_preferences_service = UserPreferencesService()
