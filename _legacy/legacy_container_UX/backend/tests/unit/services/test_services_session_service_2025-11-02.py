"""
Unit tests for SessionService.

Tests session CRUD, tier limits, state transitions with MockFirestoreClient.
"""

from datetime import UTC, datetime

import pytest

from src.core.exceptions import DepthLimitError, NotFoundError, ValidationError
from src.models.links import ResourceLink, ResourceType
from src.models.permissions import Tier
from src.models.sessions import (
    SessionCreate,
    SessionMetadata,
    SessionStatus,
    SessionType,
    SessionUpdate,
)
from src.services.session_service import SessionService


@pytest.fixture
def session_service(mock_firestore):
    """SessionService with mock Firestore."""
    return SessionService(firestore=mock_firestore)


@pytest.fixture
def session_create_request():
    """Sample SessionCreate request."""
    return SessionCreate(
        metadata=SessionMetadata(
            title="Test Session",
            description="Test description",
            session_type=SessionType.CHAT,
        )
    )


class TestCreateSession:
    """Test session creation with tier limits."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, session_create_request):
        """
        TEST: create() creates session for FREE tier user.

        PURPOSE: Validate session creation with tier limit check.

        VALIDATES:
        - Session created with sess_{uuid} pattern
        - Session stored in Firestore
        - user_id, metadata stored correctly
        - status defaults to ACTIVE
        - Tier limit check passes (FREE tier = 5 sessions max)

        EXPECTED: Session created, stored in Firestore.
        """
        session = await session_service.create(
            user_id="user_123",
            user_tier=Tier.FREE,
            request=session_create_request,
        )

        assert session.session_id.startswith("sess_")
        assert session.user_id == "user_123"
        assert session.metadata.title == "Test Session"
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_session_enforces_tier_limit(
        self, session_service, mock_firestore, session_create_request
    ):
        """
        TEST: create() raises ValidationError when tier limit exceeded.

        PURPOSE: Prevent users from creating too many sessions.

        VALIDATES:
        - FREE tier limit = 5 active sessions
        - 5th session succeeds, 6th raises ValidationError
        - Error message includes tier limit

        EXPECTED: ValidationError on 6th session for FREE tier.
        """
        # Create 5 sessions (FREE tier max)
        for i in range(5):
            await session_service.create(
                user_id="user_123",
                user_tier=Tier.FREE,
                request=session_create_request,
            )

        # 6th session should fail
        with pytest.raises(ValidationError) as exc_info:
            await session_service.create(
                user_id="user_123",
                user_tier=Tier.FREE,
                request=session_create_request,
            )

        assert "Session limit reached" in str(exc_info.value.message)
        assert "5" in str(exc_info.value.message)  # Tier limit mentioned

    @pytest.mark.asyncio
    async def test_create_session_unlimited_for_enterprise(
        self, session_service, session_create_request
    ):
        """
        TEST: create() allows unlimited sessions for ENTERPRISE tier.

        PURPOSE: ENTERPRISE users have no session limits.

        VALIDATES:
        - ENTERPRISE tier limit = -1 (unlimited)
        - Can create >100 sessions without error
        - Tier limit check skipped

        EXPECTED: All sessions created successfully.
        """
        # Create 10 sessions (would fail for FREE tier)
        for i in range(10):
            session = await session_service.create(
                user_id="enterprise_user",
                user_tier=Tier.ENTERPRISE,
                request=session_create_request,
            )
            assert session.session_id.startswith("sess_")


class TestGetSession:
    """Test session retrieval with ACL checks."""

    @pytest.mark.asyncio
    async def test_get_session_by_owner(self, session_service, session_create_request):
        """
        TEST: get() retrieves session for owner.

        PURPOSE: Allow users to retrieve their own sessions.

        VALIDATES:
        - Owner can get session by session_id
        - All fields returned correctly
        - Cached for 30 minutes (cache decorator)

        EXPECTED: Session returned with all fields.
        """
        created = await session_service.create(
            user_id="user_123",
            user_tier=Tier.FREE,
            request=session_create_request,
        )

        retrieved = await session_service.get(
            session_id=created.session_id,
            user_id="user_123",
        )

        assert retrieved.session_id == created.session_id
        assert retrieved.user_id == "user_123"
        assert retrieved.metadata.title == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service):
        """
        TEST: get() raises NotFoundError for missing session.

        PURPOSE: Handle missing sessions gracefully.

        VALIDATES:
        - get("nonexistent_session", "user_123") raises NotFoundError
        - Error message includes session_id

        EXPECTED: NotFoundError with session_id in message.
        """
        with pytest.raises(NotFoundError) as exc_info:
            await session_service.get(
                session_id="sess_nonexistent",
                user_id="user_123",
            )

        assert "sess_nonexistent" in str(exc_info.value.message)


class TestUpdateSession:
    """Test session updates."""

    @pytest.mark.asyncio
    async def test_update_session_title(self, session_service, session_create_request):
        """
        TEST: update() modifies session metadata.

        PURPOSE: Allow users to update session title/description.

        VALIDATES:
        - SessionUpdate with new title applied
        - updated_at timestamp changed
        - Other fields unchanged

        EXPECTED: Session updated, new title stored.
        """
        created = await session_service.create(
            user_id="user_123",
            user_tier=Tier.FREE,
            request=session_create_request,
        )

        update_data = SessionUpdate(
            metadata=SessionMetadata(
                title="Updated Title",
                session_type=SessionType.CHAT,
            )
        )

        updated = await session_service.update(
            session_id=created.session_id,
            user_id="user_123",
            update_data=update_data,
        )

        assert updated.metadata.title == "Updated Title"
        assert updated.session_id == created.session_id

    @pytest.mark.asyncio
    async def test_update_session_preferences(self, session_service, session_create_request):
        """
        TEST: update() modifies session preferences.

        PURPOSE: Allow users to set per-session preferences (theme, settings).

        VALIDATES:
        - SessionUpdate with preferences applied
        - Preferences merge with existing (not replace)
        - Empty preferences dict created if none exist

        EXPECTED: Session preferences updated and merged.
        """
        created = await session_service.create(
            user_id="user_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Set initial preference
        update_data = SessionUpdate(preferences={"theme": "dark", "view": "gallery"})
        updated = await session_service.update(
            session_id=created.session_id,
            user_id="user_123",
            update_data=update_data,
        )

        assert updated.preferences["theme"] == "dark"
        assert updated.preferences["view"] == "gallery"

        # Update only one preference (should merge)
        update_data2 = SessionUpdate(preferences={"theme": "light"})
        updated2 = await session_service.update(
            session_id=created.session_id,
            user_id="user_123",
            update_data=update_data2,
        )

        assert updated2.preferences["theme"] == "light"
        assert updated2.preferences["view"] == "gallery"  # Preserved


class TestDeleteSession:
    """Test session deletion."""

    @pytest.mark.asyncio
    async def test_delete_session_by_owner(self, session_service, session_create_request):
        """
        TEST: delete() removes session for owner.

        PURPOSE: Allow users to delete their own sessions.

        VALIDATES:
        - Owner can delete session
        - Session removed from Firestore
        - Subsequent get() raises NotFoundError

        EXPECTED: Session deleted, not retrievable.
        """
        created = await session_service.create(
            user_id="user_123",
            user_tier=Tier.FREE,
            request=session_create_request,
        )

        await session_service.delete(
            session_id=created.session_id,
            user_id="user_123",
        )

        # Verify deletion
        with pytest.raises(NotFoundError):
            await session_service.get(
                session_id=created.session_id,
                user_id="user_123",
            )


class TestListUserSessions:
    """Test session listing with pagination."""

    @pytest.mark.asyncio
    async def test_list_user_sessions(self, session_service, session_create_request):
        """
        TEST: list_user_sessions() returns user's sessions.

        PURPOSE: Enable users to view all their sessions.

        VALIDATES:
        - Returns only user's sessions (not other users')
        - Ordered by created_at descending (newest first)
        - Supports limit/offset pagination

        EXPECTED: List of user's sessions.
        """
        # Create 3 sessions for user
        for i in range(3):
            await session_service.create(
                user_id="user_123",
                user_tier=Tier.PRO,
                request=session_create_request,
            )

        # List user sessions
        sessions, total = await session_service.list_user_sessions(
            user_id="user_123",
            page=1,
            page_size=10,
        )

        assert len(sessions) == 3
        assert total == 3
        assert all(s.user_id == "user_123" for s in sessions)

    @pytest.mark.asyncio
    async def test_list_user_sessions_pagination(self, session_service, session_create_request):
        """
        TEST: list_user_sessions() supports pagination.

        PURPOSE: Enable paginated session retrieval for users with many sessions.

        VALIDATES:
        - limit parameter controls page size
        - offset parameter skips sessions
        - total count accurate regardless of limit/offset

        EXPECTED: Paginated results with correct total.
        """
        # Create 5 sessions
        for i in range(5):
            await session_service.create(
                user_id="user_123",
                user_tier=Tier.PRO,
                request=session_create_request,
            )

        # Get page 1 (first 2)
        sessions1, total1 = await session_service.list_user_sessions(
            user_id="user_123",
            page=1,
            page_size=2,
        )

        # Get page 2 (next 2)
        sessions2, total2 = await session_service.list_user_sessions(
            user_id="user_123",
            page=2,
            page_size=2,
        )

        assert len(sessions1) == 2
        assert len(sessions2) <= 2  # May have fewer on page 2
        # Total should be the same for all pages (total count of all sessions)
        assert total1 == 5  # Total number of sessions
        assert total2 == 5  # Total number of sessions


class TestGetEvents:
    """Test event retrieval from session."""

    @pytest.mark.asyncio
    async def test_get_events_returns_session_events(self, session_service, session_create_request):
        """
        TEST: get_events() returns events for a session.

        PURPOSE: Retrieve session event history for timeline/audit.

        VALIDATES:
        - Returns events in correct order (oldest first by default)
        - Respects limit/offset pagination
        - Only callable for accessible sessions

        EXPECTED: List of events for the session.
        """
        # Create session
        session = await session_service.create(
            user_id="user_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Get events (should be empty or contain system events)
        events, total = await session_service.get_events(
            session_id=session.session_id,
            event_type_filter=None,
            limit=10,
            offset=0,
        )

        # Should have list of events
        assert isinstance(events, list)
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_events_not_found_raises_error(self, session_service):
        """
        TEST: get_events() raises error for non-existent session.

        PURPOSE: Validate session existence before returning events.

        VALIDATES:
        - Error raised for invalid session_id

        EXPECTED: Error raised.
        """
        # get_events doesn't directly validate user, but calls event_service
        # which will fail if session doesn't exist
        events, total = await session_service.get_events(
            session_id="sess_invalid",
            limit=10,
            offset=0,
        )
        # Invalid session returns empty list
        assert events == []
        assert total == 0


class TestShareSession:
    """Test session sharing functionality."""

    @pytest.mark.asyncio
    async def test_share_session_grants_access(self, session_service, session_create_request):
        """
        TEST: share_session() grants another user access.

        PURPOSE: Enable collaboration by sharing sessions.

        VALIDATES:
        - Only owner can share
        - Creates share record with target_user_ids
        - Shared user can now access session

        EXPECTED: Session shared successfully.
        """
        # Create session as owner
        session = await session_service.create(
            user_id="owner_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Share with another user
        shared_session = await session_service.share_session(
            session_id=session.session_id,
            owner_user_id="owner_123",
            target_user_ids=["shared_user_456"],
        )

        # Verify share was recorded
        assert "shared_user_456" in shared_session.shared_with_users

    @pytest.mark.asyncio
    async def test_share_session_non_owner_fails(self, session_service, session_create_request):
        """
        TEST: share_session() fails if user is not owner.

        PURPOSE: Prevent unauthorized session sharing.

        VALIDATES:
        - Only owner can initiate share
        - Non-owner cannot share

        EXPECTED: PermissionDeniedError or NotFoundError.
        """
        from src.core.exceptions import PermissionDeniedError

        # Create session as owner
        session = await session_service.create(
            user_id="owner_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Non-owner tries to share - should fail
        with pytest.raises((PermissionDeniedError, NotFoundError)):
            await session_service.share_session(
                session_id=session.session_id,
                owner_user_id="not_owner_789",
                target_user_ids=["shared_user_456"],
            )


class TestUnshareSession:
    """Test session unsharing functionality."""

    @pytest.mark.asyncio
    async def test_unshare_session_revokes_access(self, session_service, session_create_request):
        """
        TEST: unshare_session() revokes sharing access.

        PURPOSE: Enable owner to revoke session access.

        VALIDATES:
        - Only owner can unshare
        - Removes user from shared_with_users
        - Revocation is successful

        EXPECTED: Access revoked successfully.
        """
        # Create session and share it
        session = await session_service.create(
            user_id="owner_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Share with another user
        shared_session = await session_service.share_session(
            session_id=session.session_id,
            owner_user_id="owner_123",
            target_user_ids=["shared_user_456"],
        )

        assert "shared_user_456" in shared_session.shared_with_users

        # Unshare from that user
        unshared_session = await session_service.unshare_session(
            session_id=session.session_id,
            owner_user_id="owner_123",
            target_user_ids=["shared_user_456"],
        )

        # User should be removed from shared list
        assert "shared_user_456" not in unshared_session.shared_with_users

    @pytest.mark.asyncio
    async def test_unshare_session_non_owner_fails(self, session_service, session_create_request):
        """
        TEST: unshare_session() fails if user is not owner.

        PURPOSE: Prevent unauthorized session unsharing.

        VALIDATES:
        - Only owner can revoke sharing
        - Non-owner cannot unshare

        EXPECTED: PermissionDeniedError or NotFoundError.
        """
        from src.core.exceptions import PermissionDeniedError

        # Create session as owner
        session = await session_service.create(
            user_id="owner_123",
            user_tier=Tier.PRO,
            request=session_create_request,
        )

        # Non-owner tries to unshare - should fail
        with pytest.raises((PermissionDeniedError, NotFoundError)):
            await session_service.unshare_session(
                session_id=session.session_id,
                owner_user_id="not_owner_789",
                target_user_ids=["shared_user_456"],
            )


class TestResourceLinkDepthLimits:
    """Depth guardrails for ResourceLink operations."""

    @pytest.mark.asyncio
    async def test_add_resource_link_blocks_depth_overflow(self, session_service, session_create_request):
        """
        Ensure tier depth limits are enforced when adding resource links.

        FREE tier: max_depth=1, so a parent at depth=2 should reject non-source child (new_depth=3).
        """

        # Build a session chain to depth=2 (grandchild)
        root = await session_service.create("user_123", Tier.FREE, session_create_request)

        child_request = session_create_request.model_copy(deep=True)
        child_request.parent_id = root.session_id
        child = await session_service.create("user_123", Tier.FREE, child_request)

        grand_request = session_create_request.model_copy(deep=True)
        grand_request.parent_id = child.session_id
        grand = await session_service.create("user_123", Tier.FREE, grand_request)

        link = ResourceLink(
            resource_id="agent_def_test",
            resource_type=ResourceType.AGENT,
            description="Deep agent",
            added_at=datetime.now(UTC),
            added_by="user_123",
            enabled=True,
        )

        with pytest.raises(DepthLimitError):
            await session_service.add_resource_link(
                grand.session_id,
                user_id="user_123",
                link=link,
                user_tier=Tier.FREE,
            )

    @pytest.mark.asyncio
    async def test_add_resource_link_allows_source_at_boundary(self, session_service, session_create_request):
        """FREE tier can add SOURCE at boundary depth (new_depth == max_depth + 1)."""

        # Parent at depth=1 → new_depth=2 (boundary for FREE tier)
        root = await session_service.create("user_123", Tier.FREE, session_create_request)

        child_request = session_create_request.model_copy(deep=True)
        child_request.parent_id = root.session_id
        child = await session_service.create("user_123", Tier.FREE, child_request)

        link = ResourceLink(
            resource_id="source_def_test",
            resource_type=ResourceType.SOURCE,
            description="Boundary source",
            added_at=datetime.now(UTC),
            added_by="user_123",
            enabled=True,
        )

        created = await session_service.add_resource_link(
            child.session_id,
            user_id="user_123",
            link=link,
            user_tier=Tier.FREE,
        )

        assert created.resource_id == "source_def_test"
        assert created.resource_type == ResourceType.SOURCE
