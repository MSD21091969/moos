"""Integration tests for hierarchical event system.

Tests end-to-end scenarios involving:
- Agent execution creating hierarchical event trees
- Direct tool execution with event tracking
- Event tree navigation and retrieval
- Multi-level event hierarchies
- Event filtering by depth, status, and source
- Cascade deletion of event trees
"""

import pytest
from src.models.events import EventSource, EventStatus, EventType
from src.models.context import SessionContext, UserContext
from src.services.event_service import EventService
from src.persistence.mock_firestore import MockFirestoreClient


@pytest.fixture
def mock_firestore():
    """Create mock Firestore client."""
    return MockFirestoreClient()


@pytest.fixture
def event_service(mock_firestore):
    """Create event service with mock Firestore."""
    return EventService(mock_firestore)


@pytest.fixture
def user_ctx():
    """Create user context for tests."""
    return UserContext(
        user_id="user_test",
        email="test@example.com",
        tier="PRO",
        permissions=["execute_tools", "use_agents"],
    )


@pytest.fixture
def session_ctx(user_ctx):
    """Create session context for tests."""
    import uuid

    session_id = f"sess_{uuid.uuid4().hex[:15]}"
    return SessionContext(
        user_id=user_ctx.user_id,
        user_email=user_ctx.email,
        session_id=session_id,
        tier=user_ctx.tier,
        permissions=list(user_ctx.permissions),
        quota_remaining=100.0,
    )


@pytest.mark.asyncio
async def test_agent_execution_creates_event_tree(event_service, session_ctx):
    """Test that agent execution creates a hierarchical event tree."""
    # Create root AGENT_INVOKED event
    root_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={"prompt": "Analyze data"},
        parent_event_id=None,
    )

    assert root_event.event_id is not None
    assert root_event.depth == 0
    assert root_event.source == EventSource.USER
    assert root_event.status == EventStatus.PENDING

    # Create child TOOL_EXECUTED event (agent used a tool)
    child_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={"tool": "csv_analyzer"},
        parent_event_id=root_event.event_id,
    )

    assert child_event.depth == 1
    assert child_event.parent_event_id == root_event.event_id
    assert child_event.source == EventSource.AGENT

    # Retrieve event tree
    tree = await event_service.get_event_tree(
        session_id=session_ctx.session_id, event_id=root_event.event_id
    )

    assert tree.event.event_id == root_event.event_id
    assert len(tree.children) == 1
    assert tree.children[0].event.event_id == child_event.event_id


@pytest.mark.asyncio
async def test_direct_tool_execution_creates_event(event_service, session_ctx):
    """Test that direct tool execution creates a USER-sourced event."""
    # Direct tool execution (no parent)
    tool_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.USER,
        data={"tool": "text_analyzer", "direct": True},
        parent_event_id=None,
    )

    assert tool_event.depth == 0
    assert tool_event.source == EventSource.USER
    assert tool_event.parent_event_id is None

    # Mark as completed
    completed_event = await event_service.update_event_status(
        session_id=session_ctx.session_id,
        event_id=tool_event.event_id,
        status=EventStatus.COMPLETED,
        result={"output": "Analysis complete"},
    )

    assert completed_event.status == EventStatus.COMPLETED
    assert completed_event.completed_at is not None


@pytest.mark.asyncio
async def test_event_tree_navigation(event_service, session_ctx):
    """Test navigating a complex event tree."""
    # Create root
    root = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={"prompt": "Complex task"},
        parent_event_id=None,
    )

    # Create first child
    child1 = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={"tool": "tool1"},
        parent_event_id=root.event_id,
    )

    # Create second child
    child2 = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={"tool": "tool2"},
        parent_event_id=root.event_id,
    )

    # Create grandchild under first child
    grandchild = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={"tool": "subtool"},
        parent_event_id=child1.event_id,
    )

    # Get full tree
    tree = await event_service.get_event_tree(
        session_id=session_ctx.session_id, event_id=root.event_id
    )

    assert len(tree.children) == 2
    assert tree.children[0].event.event_id == child1.event_id
    assert tree.children[1].event.event_id == child2.event_id
    assert len(tree.children[0].children) == 1
    assert tree.children[0].children[0].event.event_id == grandchild.event_id


@pytest.mark.asyncio
async def test_multi_level_event_hierarchy(event_service, session_ctx):
    """Test creating and retrieving multi-level event hierarchies."""
    # Create 4-level hierarchy
    root = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )

    child = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={},
        parent_event_id=root.event_id,
    )

    grandchild = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={},
        parent_event_id=child.event_id,
    )

    great_grandchild = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={},
        parent_event_id=grandchild.event_id,
    )

    assert root.depth == 0
    assert child.depth == 1
    assert grandchild.depth == 2
    assert great_grandchild.depth == 3

    # Verify event paths
    assert root.event_path.startswith("/")
    assert child.event_path.startswith(root.event_path)
    assert grandchild.event_path.startswith(child.event_path)
    assert great_grandchild.event_path.startswith(grandchild.event_path)


@pytest.mark.asyncio
async def test_event_filtering_by_depth(event_service, session_ctx):
    """Test filtering events by depth level."""
    # Create events at different depths
    root = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )

    child1 = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={},
        parent_event_id=root.event_id,
    )

    await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={},
        parent_event_id=root.event_id,
    )

    grandchild = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={},
        parent_event_id=child1.event_id,
    )

    # Filter depth 0 (root events)
    root_events, _ = await event_service.list_events(session_id=session_ctx.session_id, depth=0)
    assert len(root_events) == 1
    assert root_events[0].event_id == root.event_id

    # Filter depth 1 (child events)
    child_events, _ = await event_service.list_events(session_id=session_ctx.session_id, depth=1)
    assert len(child_events) == 2

    # Filter depth 2 (grandchild events)
    grandchild_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, depth=2
    )
    assert len(grandchild_events) == 1
    assert grandchild_events[0].event_id == grandchild.event_id


@pytest.mark.asyncio
async def test_event_filtering_by_status(event_service, session_ctx):
    """Test filtering events by status."""
    # Create events with different statuses
    pending_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )

    completed_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )
    await event_service.update_event_status(
        session_id=session_ctx.session_id,
        event_id=completed_event.event_id,
        status=EventStatus.COMPLETED,
    )

    failed_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )
    await event_service.update_event_status(
        session_id=session_ctx.session_id,
        event_id=failed_event.event_id,
        status=EventStatus.FAILED,
        error="Test error",
    )

    # Filter by PENDING
    pending_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, status=EventStatus.PENDING
    )
    assert len(pending_events) == 1
    assert pending_events[0].event_id == pending_event.event_id

    # Filter by COMPLETED
    completed_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, status=EventStatus.COMPLETED
    )
    assert len(completed_events) == 1
    assert completed_events[0].event_id == completed_event.event_id

    # Filter by FAILED
    failed_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, status=EventStatus.FAILED
    )
    assert len(failed_events) == 1
    assert failed_events[0].event_id == failed_event.event_id


@pytest.mark.asyncio
async def test_event_tree_with_mixed_sources(event_service, session_ctx):
    """Test event tree with mixed event sources (USER, AGENT, TOOL)."""
    # USER initiates agent
    user_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={"prompt": "Do work"},
        parent_event_id=None,
    )

    # AGENT executes tool
    agent_event = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={"tool": "main_tool"},
        parent_event_id=user_event.event_id,
    )

    # TOOL executes sub-tool
    await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={"tool": "sub_tool"},
        parent_event_id=agent_event.event_id,
    )

    # Filter by source
    user_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, source=EventSource.USER
    )
    assert len(user_events) == 1
    assert user_events[0].source == EventSource.USER

    agent_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, source=EventSource.AGENT
    )
    assert len(agent_events) == 1
    assert agent_events[0].source == EventSource.AGENT

    tool_events, _ = await event_service.list_events(
        session_id=session_ctx.session_id, source=EventSource.TOOL
    )
    assert len(tool_events) == 1
    assert tool_events[0].source == EventSource.TOOL


@pytest.mark.asyncio
async def test_cascade_delete_event_tree(event_service, session_ctx):
    """Test that deleting a parent event cascades to all descendants."""
    # Create event tree
    root = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.AGENT_INVOKED,
        source=EventSource.USER,
        data={},
        parent_event_id=None,
    )

    child1 = await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={},
        parent_event_id=root.event_id,
    )

    await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.AGENT,
        data={},
        parent_event_id=root.event_id,
    )

    await event_service.create_event(
        session_id=session_ctx.session_id,
        event_type=EventType.TOOL_EXECUTED,
        source=EventSource.TOOL,
        data={},
        parent_event_id=child1.event_id,
    )

    # Verify all events exist
    all_events, _ = await event_service.list_events(session_id=session_ctx.session_id)
    assert len(all_events) == 4

    # Delete root (should cascade to all descendants)
    await event_service.delete_event(session_id=session_ctx.session_id, event_id=root.event_id)

    # Verify all events are deleted
    remaining_events, _ = await event_service.list_events(session_id=session_ctx.session_id)
    assert len(remaining_events) == 0
