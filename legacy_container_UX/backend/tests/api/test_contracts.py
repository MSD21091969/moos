"""
API Contract Testing

Tests critical Firestore queries and backend functionality to ensure:
1. order_by() calls work correctly (no invalid direction parameter)
2. Session listing, quota tracking work in production
3. Firestore queries return correct data structures

Run with: pytest tests/api/test_contracts.py -v
"""

import pytest

from src.models.events import EventSource, EventType


@pytest.mark.asyncio
async def test_all_firestore_queries():
    """
    Validate all Firestore queries work with correct API (not mocks).

    Tests critical paths that use order_by, where, limit, etc.
    This validates the Firestore API compatibility fixes.
    """
    from src.models.sessions import SessionCreate, SessionMetadata, SessionType
    from src.persistence.firestore_client import get_firestore_client
    from src.services.event_service import EventService
    from src.services.quota_service import QuotaService
    from src.services.session_service import SessionService

    db = await get_firestore_client()
    session_service = SessionService(db)
    quota_service = QuotaService(db)
    event_service = EventService(db, session_service)

    test_user = "contract_test_user"

    # Test 1: Session listing (uses order_by) - returns tuple (sessions, total)
    sessions, total = await session_service.list_user_sessions(test_user, page_size=10)
    assert isinstance(sessions, list)
    assert isinstance(total, int)

    # Test 2: Quota usage history (uses order_by with date)
    usage = await quota_service.get_usage_history(test_user, days=7)
    assert isinstance(usage, list)

    # Test 3: Create session and event to test event listing with order_by
    metadata = SessionMetadata(title="Firestore Contract Test", session_type=SessionType.CHAT)
    session = await session_service.create(
        user_id=test_user, user_tier="free", request=SessionCreate(metadata=metadata)
    )

    # Create test event
    await event_service.create_event(
        session_id=session.session_id,
        event_type=EventType.USER_MESSAGE,
        source=EventSource.USER,
        data={"content": "test message"},
        metadata={},
    )

    # Test 4: List events (uses order_by on timestamp) - returns tuple (events, total)
    events_result = await event_service.list_events(session.session_id)
    assert isinstance(events_result, tuple)
    events, total = events_result
    assert isinstance(events, list)
    assert len(events) > 0
    assert total >= 1

    # Cleanup
    await session_service.delete(session.session_id, test_user)
