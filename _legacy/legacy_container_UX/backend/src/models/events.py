"""Event and message models for session history.

Moved from sessions.py for better separation of concerns.
Events represent all interactions within a session:
- User messages
- Agent responses
- Tool executions
- System events

Enhanced with hierarchical event system for tracking execution trees.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


# ============================================================================
# Event Types and Sources
# ============================================================================


class EventType(str, Enum):
    """Type of event in session history."""

    # Message types (replacing Message model)
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    SYSTEM_MESSAGE = "system_message"
    TOOL_MESSAGE = "tool_message"

    # Agent execution types
    AGENT_RUN_START = "agent_run_start"
    AGENT_RUN_COMPLETE = "agent_run_complete"
    AGENT_RUN_FAILED = "agent_run_failed"

    # Tool execution types
    USER_TOOL_EXECUTION = "user_tool_execution"
    AGENT_TOOL_EXECUTION = "agent_tool_execution"

    # DEPRECATED: Keep for backward compatibility during deployment
    AGENT_RESPONSE = "agent_response"  # DEPRECATED: Use AGENT_MESSAGE
    AGENT_INVOKED = "agent_invoked"  # DEPRECATED: Use AGENT_RUN_START
    TOOL_EXECUTED = "tool_executed"  # DEPRECATED: Use USER_TOOL_EXECUTION
    TOOL_CALL = "tool_call"  # DEPRECATED: Use AGENT_TOOL_EXECUTION
    TOOL_RETURN = "tool_return"  # DEPRECATED: Use AGENT_TOOL_EXECUTION
    SYSTEM_EVENT = "system_event"  # DEPRECATED: Use SYSTEM_MESSAGE


class EventSource(str, Enum):
    """Source of event for hierarchical tracking."""

    USER = "user"
    AGENT = "agent"
    TOOL = "tool"
    FRAMEWORK = "framework"
    SYSTEM = "system"


class EventStatus(str, Enum):
    """Status of event execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Event Models
# ============================================================================


class Event(BaseModel):
    """
    Base event model.

    Storage: /users/{uid}/sessions/{sid}/events/{event_id}
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event timestamp")

    # Content (polymorphic based on event_type)
    content: Any = Field(..., description="Event content (structure varies by type)")

    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional event metadata")


class ToolEvent(BaseModel):
    """
    Tool execution event with embedded scenario context.

    Used for knowledge-based sessions where tools embed
    "when/how" usage information for RAG/agent learning.
    """

    tool_id: str = Field(..., description="Tool identifier")
    tool_name: str = Field(..., description="Tool name")
    args: dict = Field(..., description="Tool arguments")
    result: Any = Field(..., description="Tool execution result")

    # NEW: Scenario embedding (when/how to use)
    scenario_context: Optional[dict] = Field(
        None,
        description="Embedded knowledge: situation, workflow, expected outcome",
    )

    # Execution metadata
    quota_cost: int = Field(default=1, ge=0, description="Quota consumed")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")


# ============================================================================
# Hierarchical Session Events
# ============================================================================


class SessionEvent(BaseModel):
    """
    Hierarchical event model for tracking execution trees.

    Supports efficient single-query tree retrieval using event_path.
    Storage: /users/{uid}/sessions/{sid}/events/{event_id}

    Example hierarchy:
        Root event (depth=0): evt_abc123, path="/evt_abc123"
        └─ Child event (depth=1): evt_def456, path="/evt_abc123/evt_def456"
           └─ Grandchild (depth=2): evt_ghi789, path="/evt_abc123/evt_def456/evt_ghi789"

    Query all descendants of evt_abc123:
        WHERE event_path STARTS WITH "/evt_abc123/" OR event_id = "evt_abc123"
    """

    # Identity
    event_id: str = Field(..., description="Unique event identifier (evt_XXXXXXXXXXXX)")
    session_id: str = Field(..., description="Parent session ID")

    # Hierarchy
    parent_event_id: str | None = Field(None, description="Parent event ID (None for root events)")
    event_path: str = Field(
        ...,
        description="Hierarchical path (/evt_root/evt_child/...) for efficient queries",
    )
    depth: int = Field(default=0, ge=0, description="Tree depth (0=root, 1=child, ...)")

    # Classification
    event_type: EventType = Field(..., description="Type of event")
    source: EventSource = Field(..., description="Event source (USER, AGENT, TOOL, etc.)")
    status: EventStatus = Field(default=EventStatus.PENDING, description="Execution status")

    # Timing
    timestamp: datetime = Field(..., description="Event creation timestamp")
    completed_at: datetime | None = Field(None, description="Event completion timestamp")
    duration_ms: int | None = Field(None, description="Execution duration in milliseconds")

    # Content
    data: dict[str, Any] = Field(
        default_factory=dict, description="Event data (structure varies by type)"
    )
    result: Any = Field(None, description="Event result (for COMPLETED status)")
    error: str | None = Field(None, description="Error message (for FAILED status)")

    # Storage optimization
    result_storage_path: str | None = Field(
        None, description="Cloud storage path for large results (>100KB)"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    quota_cost: int = Field(default=0, ge=0, description="Quota consumed by this event")


class SessionEventTree(BaseModel):
    """
    Event tree structure for hierarchical display.

    Used for GET /sessions/{id}/events/{event_id}/tree endpoint.
    """

    event: SessionEvent = Field(..., description="Root event")
    children: list["SessionEventTree"] = Field(
        default_factory=list, description="Child event trees"
    )
    total_descendants: int = Field(default=0, ge=0, description="Total number of descendants")


# Allow forward reference for recursive model
SessionEventTree.model_rebuild()


class SessionEventListResponse(BaseModel):
    """Response for listing session events."""

    session_id: str = Field(..., description="Session identifier")
    events: list[SessionEvent] = Field(..., description="Events (chronological)")
    total: int = Field(..., ge=0, description="Total events in session")
    page: int = Field(default=1, ge=1, description="Current page")
    page_size: int = Field(default=50, ge=1, le=500, description="Items per page")
    has_more: bool = Field(..., description="Whether more events exist")
