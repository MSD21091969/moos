"""Tests for event service."""

import pytest

from src.services.event_service import EventService
from src.models.events import EventType, EventSource, EventStatus
from src.core.exceptions import NotFoundError


@pytest.fixture
def event_service(mock_firestore):
    """Create event service with mock Firestore."""
    return EventService(mock_firestore)


class TestCreateEvent:
    """Tests for creating events."""

    async def test_create_root_event(self, event_service):
        """Test creating root event (depth=0)."""
        event = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={"message": "Hello"},
        )

        assert event.event_id.startswith("evt_")
        assert event.session_id == "sess_test123"
        assert event.parent_event_id is None
        assert event.depth == 0
        assert event.event_path.startswith("/evt_")
        assert event.event_type == EventType.AGENT_INVOKED
        assert event.source == EventSource.USER
        assert event.status == EventStatus.PENDING
        assert event.data == {"message": "Hello"}

    async def test_create_child_event(self, event_service):
        """Test creating child event (depth=1)."""
        # Create root event
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={"message": "Hello"},
        )

        # Create child event
        child = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={"tool": "calculator"},
            parent_event_id=root.event_id,
        )

        assert child.parent_event_id == root.event_id
        assert child.depth == 1
        assert child.event_path == f"{root.event_path}/{child.event_id}"

    async def test_create_grandchild_event(self, event_service):
        """Test creating grandchild event (depth=2)."""
        # Create root
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )

        # Create child
        child = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=root.event_id,
        )

        # Create grandchild
        grandchild = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=child.event_id,
        )

        assert grandchild.parent_event_id == child.event_id
        assert grandchild.depth == 2
        assert grandchild.event_path == f"{child.event_path}/{grandchild.event_id}"

    async def test_create_event_parent_not_found(self, event_service):
        """Test creating event with non-existent parent fails."""
        with pytest.raises(NotFoundError):
            await event_service.create_event(
                session_id="sess_test123",
                event_type=EventType.TOOL_EXECUTED,
                source=EventSource.TOOL,
                data={},
                parent_event_id="evt_nonexistent",
            )


class TestGetEvent:
    """Tests for retrieving events."""

    async def test_get_event(self, event_service):
        """Test getting event by ID."""
        # Create event
        created = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={"key": "value"},
        )

        # Get event
        retrieved = await event_service.get_event("sess_test123", created.event_id)

        assert retrieved is not None
        assert retrieved.event_id == created.event_id
        assert retrieved.data == {"key": "value"}

    async def test_get_event_not_found(self, event_service):
        """Test getting non-existent event returns None."""
        result = await event_service.get_event("sess_test123", "evt_nonexistent")
        assert result is None


class TestUpdateEventStatus:
    """Tests for updating event status."""

    async def test_update_event_status_completed(self, event_service):
        """Test updating event to COMPLETED status."""
        # Create event
        event = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )

        # Update to COMPLETED
        updated = await event_service.update_event_status(
            session_id="sess_test123",
            event_id=event.event_id,
            status=EventStatus.COMPLETED,
            result={"answer": "42"},
        )

        assert updated.status == EventStatus.COMPLETED
        assert updated.result == {"answer": "42"}
        assert updated.completed_at is not None
        assert updated.duration_ms is not None

    async def test_update_event_status_failed(self, event_service):
        """Test updating event to FAILED status."""
        # Create event
        event = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )

        # Update to FAILED
        updated = await event_service.update_event_status(
            session_id="sess_test123",
            event_id=event.event_id,
            status=EventStatus.FAILED,
            error="Something went wrong",
        )

        assert updated.status == EventStatus.FAILED
        assert updated.error == "Something went wrong"


class TestEventTree:
    """Tests for event tree operations."""

    async def test_get_event_tree_single_level(self, event_service):
        """Test getting event tree with single level (no children)."""
        # Create root event
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )

        # Get tree
        tree = await event_service.get_event_tree("sess_test123", root.event_id)

        assert tree is not None
        assert tree.event.event_id == root.event_id
        assert tree.children == []
        assert tree.total_descendants == 0

    async def test_get_event_tree_multi_level(self, event_service):
        """Test getting event tree with multiple levels."""
        # Create root
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )

        # Create 2 children
        child1 = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=root.event_id,
        )

        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=root.event_id,
        )

        # Create grandchild
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=child1.event_id,
        )

        # Get tree
        tree = await event_service.get_event_tree("sess_test123", root.event_id)

        assert tree is not None
        assert tree.event.event_id == root.event_id
        assert len(tree.children) == 2
        assert tree.total_descendants == 3

        # Check child1 has grandchild
        child1_tree = next(c for c in tree.children if c.event.event_id == child1.event_id)
        assert len(child1_tree.children) == 1
        assert child1_tree.total_descendants == 1


class TestListEvents:
    """Tests for listing events."""

    async def test_list_events_all(self, event_service):
        """Test listing all events in session."""
        # Create multiple events
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )

        events, total = await event_service.list_events("sess_test123")

        assert len(events) == 2
        assert total == 2

    async def test_list_events_filter_by_depth(self, event_service):
        """Test filtering events by depth."""
        # Create root and child
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=root.event_id,
        )

        # Filter by depth=0
        events, total = await event_service.list_events("sess_test123", depth=0)

        assert len(events) == 1
        assert events[0].depth == 0

    async def test_list_events_filter_by_source(self, event_service):
        """Test filtering events by source."""
        # Create events with different sources
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )

        # Filter by source=TOOL
        events, total = await event_service.list_events("sess_test123", source=EventSource.TOOL)

        assert len(events) == 1
        assert events[0].source == EventSource.TOOL

    async def test_list_events_filter_by_status(self, event_service):
        """Test filtering events by status."""
        # Create event and complete it
        event = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )
        await event_service.update_event_status(
            "sess_test123", event.event_id, EventStatus.COMPLETED
        )

        # Create another pending event
        await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
        )

        # Filter by status=COMPLETED
        events, total = await event_service.list_events(
            "sess_test123", status=EventStatus.COMPLETED
        )

        assert len(events) == 1
        assert events[0].status == EventStatus.COMPLETED


class TestDeleteEvent:
    """Tests for deleting events."""

    async def test_delete_event_with_descendants(self, event_service):
        """Test deleting event deletes all descendants."""
        # Create root with children
        root = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.AGENT_INVOKED,
            source=EventSource.USER,
            data={},
        )
        child = await event_service.create_event(
            session_id="sess_test123",
            event_type=EventType.TOOL_EXECUTED,
            source=EventSource.TOOL,
            data={},
            parent_event_id=root.event_id,
        )

        # Delete root
        await event_service.delete_event("sess_test123", root.event_id)

        # Verify both deleted
        assert await event_service.get_event("sess_test123", root.event_id) is None
        assert await event_service.get_event("sess_test123", child.event_id) is None


class TestGenerateEventId:
    """Tests for event ID generation."""

    def test_generate_event_id_format(self, event_service):
        """Test event ID has correct format."""
        event_id = event_service._generate_event_id()

        assert event_id.startswith("evt_")
        assert len(event_id) == 16  # evt_ + 12 hex chars
