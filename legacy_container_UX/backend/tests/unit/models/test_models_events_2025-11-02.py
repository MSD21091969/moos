"""
Unit tests for event models.

Tests Event, ToolEvent, SessionEvent, and EventType enums in isolation.
Updated for event-first architecture (post-PR #60).
"""

from datetime import datetime

from src.models.events import (
    Event,
    EventType,
    EventSource,
    EventStatus,
    ToolEvent,
    SessionEvent,
    SessionEventTree,
    SessionEventListResponse,
)


class TestEventType:
    """Test EventType enum values."""

    def test_message_event_types(self):
        """
        TEST: EventType includes message types.

        PURPOSE: Validate message event types replace old Message model.

        VALIDATES:
        - USER_MESSAGE, AGENT_MESSAGE, SYSTEM_MESSAGE, TOOL_MESSAGE all exist
        - Values are lowercase with underscores
        - Can be used in equality checks

        EXPECTED: All message event types accessible.
        """
        assert EventType.USER_MESSAGE == "user_message"
        assert EventType.AGENT_MESSAGE == "agent_message"
        assert EventType.SYSTEM_MESSAGE == "system_message"
        assert EventType.TOOL_MESSAGE == "tool_message"

    def test_agent_execution_event_types(self):
        """
        TEST: EventType includes agent execution types.

        PURPOSE: Track agent run lifecycle.

        VALIDATES:
        - AGENT_RUN_START, AGENT_RUN_COMPLETE, AGENT_RUN_FAILED exist

        EXPECTED: All agent run types accessible.
        """
        assert EventType.AGENT_RUN_START == "agent_run_start"
        assert EventType.AGENT_RUN_COMPLETE == "agent_run_complete"
        assert EventType.AGENT_RUN_FAILED == "agent_run_failed"

    def test_tool_execution_event_types(self):
        """
        TEST: EventType includes tool execution types.

        PURPOSE: Distinguish user-initiated vs agent-initiated tool calls.

        VALIDATES:
        - USER_TOOL_EXECUTION, AGENT_TOOL_EXECUTION exist

        EXPECTED: Both tool execution types accessible.
        """
        assert EventType.USER_TOOL_EXECUTION == "user_tool_execution"
        assert EventType.AGENT_TOOL_EXECUTION == "agent_tool_execution"

    def test_deprecated_event_types_for_backward_compatibility(self):
        """
        TEST: Deprecated EventType values still exist.

        PURPOSE: Ensure backward compatibility during migration.

        VALIDATES:
        - AGENT_RESPONSE, AGENT_INVOKED, TOOL_EXECUTED still exist
        - These are DEPRECATED and should not be used in new code

        EXPECTED: Deprecated types accessible but marked for removal.
        """
        assert EventType.AGENT_RESPONSE == "agent_response"
        assert EventType.AGENT_INVOKED == "agent_invoked"
        assert EventType.TOOL_EXECUTED == "tool_executed"


class TestEventSource:
    """Test EventSource enum values."""

    def test_event_source_values(self):
        """
        TEST: EventSource enum includes all source types.

        PURPOSE: Validate event origin tracking.

        VALIDATES:
        - USER, AGENT, TOOL, FRAMEWORK, SYSTEM all exist

        EXPECTED: All source types accessible.
        """
        assert EventSource.USER == "user"
        assert EventSource.AGENT == "agent"
        assert EventSource.TOOL == "tool"
        assert EventSource.FRAMEWORK == "framework"
        assert EventSource.SYSTEM == "system"


class TestEventStatus:
    """Test EventStatus enum values."""

    def test_event_status_values(self):
        """
        TEST: EventStatus enum includes all execution states.

        PURPOSE: Track event lifecycle.

        VALIDATES:
        - PENDING, IN_PROGRESS, COMPLETED, FAILED all exist

        EXPECTED: All status types accessible.
        """
        assert EventStatus.PENDING == "pending"
        assert EventStatus.IN_PROGRESS == "in_progress"
        assert EventStatus.COMPLETED == "completed"
        assert EventStatus.FAILED == "failed"


class TestEvent:
    """Test Event model."""

    def test_event_with_user_message(self):
        """
        TEST: Event stores user message content.

        PURPOSE: Track user inputs in session history.

        VALIDATES:
        - event_type = EventType.USER_MESSAGE
        - content can be string (message text)
        - timestamp auto-generated
        - metadata defaults to empty dict

        EXPECTED: Event with user message stored.
        """
        event = Event(
            event_id="evt_123",
            event_type=EventType.USER_MESSAGE,
            timestamp=datetime.utcnow(),
            content="Hello, how can you help?",
        )

        assert event.event_type == EventType.USER_MESSAGE
        assert event.content == "Hello, how can you help?"
        assert event.metadata == {}

    def test_event_with_metadata(self):
        """
        TEST: Event includes optional metadata dict.

        PURPOSE: Store additional context (user_agent, IP, etc).

        VALIDATES:
        - metadata dict stored correctly
        - Can include any key-value pairs
        - Useful for audit trails

        EXPECTED: Event with metadata.
        """
        event = Event(
            event_id="evt_123",
            event_type=EventType.SYSTEM_MESSAGE,
            timestamp=datetime.utcnow(),
            content="Session started",
            metadata={"ip_address": "192.168.1.1", "user_agent": "Chrome"},
        )

        assert event.metadata["ip_address"] == "192.168.1.1"


class TestToolEvent:
    """Test ToolEvent model."""

    def test_tool_event_with_execution_details(self):
        """
        TEST: ToolEvent stores tool execution details.

        PURPOSE: Track tool calls with args and results.

        VALIDATES:
        - tool_id, tool_name, args, result all stored
        - quota_cost defaults to 1
        - execution_time_ms optional

        EXPECTED: Complete tool execution record.
        """
        tool_event = ToolEvent(
            tool_id="tool_123",
            tool_name="export_json",
            args={"data": [1, 2, 3], "filename": "export.json"},
            result={"status": "success", "path": "/exports/export.json"},
            quota_cost=2,
            execution_time_ms=150,
        )

        assert tool_event.tool_name == "export_json"
        assert tool_event.quota_cost == 2
        assert tool_event.execution_time_ms == 150

    def test_tool_event_with_scenario_context(self):
        """
        TEST: ToolEvent includes scenario embedding for RAG.

        PURPOSE: Store "when/how to use" knowledge for agent learning.

        VALIDATES:
        - scenario_context optional dict field
        - Can store situation, workflow, expected outcome

        EXPECTED: Scenario context stored for knowledge retrieval.
        """
        tool_event = ToolEvent(
            tool_id="tool_123",
            tool_name="regex_replace",
            args={"pattern": r"\d+", "replacement": "NUM"},
            result="Document NUM has NUM pages",
            scenario_context={
                "situation": "Anonymizing document content",
                "workflow": "Data cleaning for GDPR compliance",
                "expected_outcome": "Numbers replaced with placeholder",
            },
        )

        assert tool_event.scenario_context is not None
        assert tool_event.scenario_context["situation"] == "Anonymizing document content"


class TestSessionEvent:
    """Test SessionEvent model (hierarchical events)."""

    def test_session_event_minimal(self):
        """
        TEST: SessionEvent with minimal required fields.

        PURPOSE: Validate basic event creation.

        VALIDATES:
        - event_id, session_id, event_path, event_type, source, timestamp required
        - depth defaults to 0 for root events
        - status defaults to PENDING

        EXPECTED: SessionEvent created successfully.
        """
        event = SessionEvent(
            event_id="evt_abc123",
            session_id="sess_xyz789",
            event_path="/evt_abc123",
            event_type=EventType.USER_MESSAGE,
            source=EventSource.USER,
            timestamp=datetime.utcnow(),
        )

        assert event.event_id == "evt_abc123"
        assert event.depth == 0
        assert event.status == EventStatus.PENDING
        assert event.parent_event_id is None

    def test_session_event_hierarchical(self):
        """
        TEST: SessionEvent with parent-child relationship.

        PURPOSE: Track execution trees.

        VALIDATES:
        - parent_event_id references parent
        - event_path includes parent path
        - depth increments for children

        EXPECTED: Child event linked to parent.
        """
        parent = SessionEvent(
            event_id="evt_parent",
            session_id="sess_123",
            event_path="/evt_parent",
            event_type=EventType.AGENT_RUN_START,
            source=EventSource.AGENT,
            timestamp=datetime.utcnow(),
            depth=0,
        )

        child = SessionEvent(
            event_id="evt_child",
            session_id="sess_123",
            event_path="/evt_parent/evt_child",
            parent_event_id="evt_parent",
            event_type=EventType.AGENT_TOOL_EXECUTION,
            source=EventSource.TOOL,
            timestamp=datetime.utcnow(),
            depth=1,
        )

        assert child.parent_event_id == "evt_parent"
        assert child.depth == 1
        assert child.event_path.startswith(parent.event_path)

    def test_session_event_with_data_and_result(self):
        """
        TEST: SessionEvent stores execution data and result.

        PURPOSE: Track event payload and outcome.

        VALIDATES:
        - data dict stores event-specific information
        - result stores outcome (for COMPLETED status)
        - error stores error message (for FAILED status)

        EXPECTED: Data and result stored correctly.
        """
        event = SessionEvent(
            event_id="evt_123",
            session_id="sess_456",
            event_path="/evt_123",
            event_type=EventType.USER_TOOL_EXECUTION,
            source=EventSource.USER,
            timestamp=datetime.utcnow(),
            status=EventStatus.COMPLETED,
            data={"tool_name": "export_csv", "rows": 100},
            result={"file_path": "/exports/data.csv", "size_bytes": 5120},
            quota_cost=5,
        )

        assert event.data["tool_name"] == "export_csv"
        assert event.result["file_path"] == "/exports/data.csv"
        assert event.quota_cost == 5


class TestSessionEventTree:
    """Test SessionEventTree model."""

    def test_session_event_tree_structure(self):
        """
        TEST: SessionEventTree represents hierarchical event structure.

        PURPOSE: Display event trees in API responses.

        VALIDATES:
        - event is root SessionEvent
        - children is list of SessionEventTree (recursive)
        - total_descendants counts all descendants

        EXPECTED: Tree structure with correct counts.
        """
        root_event = SessionEvent(
            event_id="evt_root",
            session_id="sess_123",
            event_path="/evt_root",
            event_type=EventType.AGENT_RUN_START,
            source=EventSource.AGENT,
            timestamp=datetime.utcnow(),
        )

        tree = SessionEventTree(
            event=root_event,
            children=[],
            total_descendants=0,
        )

        assert tree.event.event_id == "evt_root"
        assert tree.children == []
        assert tree.total_descendants == 0


class TestSessionEventListResponse:
    """Test SessionEventListResponse model."""

    def test_session_event_list_response(self):
        """
        TEST: SessionEventListResponse paginates events.

        PURPOSE: API response for listing session events.

        VALIDATES:
        - session_id, events, total, page, page_size, has_more fields
        - events is list of SessionEvent
        - pagination metadata included

        EXPECTED: Valid API response structure.
        """
        event = SessionEvent(
            event_id="evt_123",
            session_id="sess_456",
            event_path="/evt_123",
            event_type=EventType.USER_MESSAGE,
            source=EventSource.USER,
            timestamp=datetime.utcnow(),
        )

        response = SessionEventListResponse(
            session_id="sess_456",
            events=[event],
            total=10,
            page=1,
            page_size=50,
            has_more=False,
        )

        assert response.session_id == "sess_456"
        assert len(response.events) == 1
        assert response.total == 10
        assert response.has_more is False
