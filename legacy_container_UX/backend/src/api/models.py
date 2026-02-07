"""API request/response models for OpenAPI documentation and validation.

These models define the contract between frontend and backend.
Every endpoint has explicit request/response models for:
- Input validation (Pydantic)
- Output consistency
- Auto-generated API docs (Swagger/OpenAPI)
- Type safety for frontend clients
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Import from domain models (avoid duplication)
from src.models.common import ErrorResponse
from src.models.sessions import SessionType


def _normalize_tags(value: Optional[List[str]]) -> List[str]:
    """Normalize and validate tag lists with shared rules."""
    if value is None:
        return []

    if not isinstance(value, list):
        raise TypeError("tags must be provided as a list")

    cleaned: List[str] = []
    for raw in value:
        if not isinstance(raw, str):
            raise ValueError("tags must contain only strings")

        tag = raw.strip()
        if not tag:
            raise ValueError("tags cannot contain empty values")
        if len(tag) > 50:
            raise ValueError("tags cannot exceed 50 characters")

        cleaned.append(tag)

    if len(cleaned) > 10:
        raise ValueError("A maximum of 10 tags is allowed per session")

    return cleaned


__all__ = [
    "UserInfoResponse",
    "SessionCreateRequest",
    "SessionResponse",
    "SessionListResponse",
    "TraceEventResponse",
    "TraceStatsResponse",
    "EventExecutionSummary",
    "QuotaUsageResponse",
    "AgentCapabilitiesResponse",
    "SessionUpdateRequest",
    "AgentRunRequest",
    "AgentRunResponse",
    "ToolInfo",
    "ToolListResponse",
    "ErrorDetail",
    "HealthResponse",
    # New dashboard & activity models
    "DashboardStatsResponse",
    "ActivityItem",
    "SessionActivityResponse",
    # Batch operations (2025-11-14)
    "BatchSessionCreateRequest",
    "BatchSessionCreateResponse",
    # Re-exported from domain models:
    "ErrorResponse",  # from src.models.common
]


# ============================================================================
# Authentication & User Models
# ============================================================================


class UserInfoResponse(BaseModel):
    """Current user information (from JWT token)."""

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    permissions: List[str] = Field(..., description="User permissions")
    quota_remaining: int = Field(..., ge=0, description="Remaining API quota")
    tier: str = Field(..., description="User tier: free, pro, enterprise")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123456",
                "email": "user@example.com",
                "display_name": "John Doe",
                "permissions": ["read_data", "write_data", "execute_tools"],
                "quota_remaining": 1000,
                "tier": "pro",
            }
        }


# ============================================================================
# Session Management Models
# ============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""

    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    description: str = Field(default="", max_length=1000, description="Session description")
    tags: List[str] = Field(default_factory=list, description="Session tags for filtering")
    session_type: str = Field(
        default="chat", description="Session type: chat, analysis, workflow, simulation"
    )
    ttl_hours: int = Field(
        default=24, gt=0, le=8760, description="Session TTL in hours (max 1 year)"
    )
    domain: Optional[str] = Field(
        None, description="Business domain: legal, medical, finance, etc."
    )
    scenario: Optional[str] = Field(
        None, description="Scenario description for simulation sessions"
    )
    clone_from_session_id: Optional[str] = Field(
        None, pattern=r"^sess_[a-f0-9]{12}$", description="Clone agents/tools from existing session"
    )
    parent_session_id: Optional[str] = Field(
        None,
        pattern=r"^sess_[a-f0-9]{12}$",
        description="Parent session ID (for creating child sessions in containers)",
    )
    is_container: bool = Field(
        default=False, description="Whether this session acts as a container for other sessions"
    )
    child_node_ids: List[str] = Field(
        default_factory=list, description="Frontend node IDs for child sessions (ReactFlow)"
    )
    visual_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Frontend visual state: {color, collapsed, position: {x, y}}",
    )
    theme_color: Optional[str] = Field(
        None,
        description="Session theme color for frontend UI (hex color code, e.g., '#3b82f6')",
    )

    @field_validator("session_type", mode="before")
    @classmethod
    def normalize_session_type(cls, value: str | SessionType | None) -> str:
        """Normalize session_type to lowercase without enforcing enum membership here."""
        if value is None:
            return SessionType.CHAT.value

        if isinstance(value, SessionType):
            return value.value

        if not isinstance(value, str):
            raise TypeError("session_type must be a string")

        return value.strip().lower()

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Optional[List[str]]) -> List[str]:
        """Ensure tags are a list of <=10 trimmed strings with max length 50."""
        return _normalize_tags(value)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Q4 Sales Analysis",
                "description": "Analyzing Q4 sales data for trends",
                "tags": ["sales", "q4", "analysis"],
                "session_type": "analysis",
                "ttl_hours": 72,
                "domain": "finance",
            }
        }


class SessionResponse(BaseModel):
    """Complete session information."""

    session_id: str = Field(..., description="Unique session identifier")
    table_id: Optional[str] = Field(None, description="Table ID (alias for session_id in table UI)")
    title: str = Field(..., description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    tags: List[str] = Field(..., description="Session tags")
    session_type: str = Field(..., description="Session type: chat, analysis, workflow, simulation")
    status: str = Field(..., description="Session status: active, completed, expired, archived")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_active: bool = Field(..., description="Whether session is currently active")
    # New fields for domain knowledge and agent management
    domain: Optional[str] = Field(None, description="Business domain")
    scenario: Optional[str] = Field(None, description="Simulation scenario description")
    active_agent_id: Optional[str] = Field(
        None, description="Active agent ID from /agents/ subcollection"
    )
    is_shared: bool = Field(default=False, description="Whether session is shared with other users")
    shared_with_users: List[str] = Field(
        default_factory=list, description="User IDs with shared access"
    )
    source_session_id: Optional[str] = Field(None, description="Session ID this was cloned from")
    collection_schemas: Dict[str, str] = Field(
        default_factory=dict, description="Data collection schemas (table definitions)"
    )

    # Container hierarchy (2025-11-14 - Frontend staging queue support)
    parent_session_id: Optional[str] = Field(
        None, description="Parent session ID for nested sessions"
    )
    child_sessions: List[str] = Field(
        default_factory=list, description="List of child session IDs (for containers)"
    )

    # Visual UI enhancement fields
    preview: Optional[str] = Field(
        None, description="First 100 chars of conversation preview", max_length=100
    )
    last_activity: Optional[datetime] = Field(None, description="Last message timestamp")
    message_count: int = Field(default=0, ge=0, description="Total message count in session")
    tool_usage_summary: Dict[str, int] = Field(
        default_factory=dict, description="Tool usage counts: {tool_name: count}"
    )
    color_theme: Optional[str] = Field(None, description="UI color theme identifier")
    theme_color: Optional[str] = Field(
        None,
        description="Session theme color for frontend UI (hex color code, e.g., '#3b82f6')",
    )
    contents: Optional[Dict[str, int]] = Field(
        None, description="Table contents summary: {objects: int, workers: int, messages: int}"
    )
    actions: Optional[List[str]] = Field(None, description="Available actions for this table")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123def456",
                "title": "Q4 Sales Analysis",
                "description": "Analyzing Q4 sales data",
                "tags": ["sales", "q4"],
                "session_type": "analysis",
                "status": "active",
                "created_at": "2025-10-27T10:00:00Z",
                "updated_at": "2025-10-27T12:30:00Z",
                "expires_at": "2025-10-30T10:00:00Z",
                "is_active": True,
            }
        }


class SessionListResponse(BaseModel):
    """Paginated list of sessions."""

    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., ge=0, description="Total number of sessions")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")

    class Config:
        json_schema_extra = {
            "example": {"sessions": [], "total": 42, "page": 1, "page_size": 20, "has_more": True}
        }


class SessionUpdateRequest(BaseModel):
    """Request to update session metadata."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, description="Update status: active, completed, archived")
    active_agent_id: Optional[str] = Field(None, description="Update active agent ID")
    domain: Optional[str] = Field(None, description="Update business domain")
    scenario: Optional[str] = Field(None, description="Update scenario description")
    collections_to_add: Optional[Dict[str, str]] = Field(
        None, description="Collections to add: {name: schema}"
    )
    collections_to_remove: Optional[List[str]] = Field(
        None, description="Collections to remove by name"
    )
    visual_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Update frontend visual state (opaque JSON)"
    )
    theme_color: Optional[str] = Field(
        None,
        description="Update session theme color (hex color code, e.g., '#3b82f6')",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def validate_update_tags(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        return _normalize_tags(value)


class BatchSessionCreateRequest(BaseModel):
    """Request to create multiple sessions in one operation (max 25)."""

    sessions: List[SessionCreateRequest] = Field(
        ..., min_length=1, max_length=25, description="List of sessions to create (max 25)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "title": "Child Session 1",
                        "session_type": "chat",
                        "parent_session_id": "sess_abc123def456",
                    },
                    {
                        "title": "Child Session 2",
                        "session_type": "analysis",
                        "parent_session_id": "sess_abc123def456",
                    },
                ]
            }
        }


class BatchSessionCreateResponse(BaseModel):
    """Response from batch session creation."""

    sessions: List[SessionResponse] = Field(..., description="Successfully created sessions")
    total: int = Field(..., ge=0, description="Total sessions requested")
    success_count: int = Field(..., ge=0, description="Number of successfully created sessions")
    failed_count: int = Field(default=0, ge=0, description="Number of failed sessions")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors: [{index: int, title: str, error: str}]",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [],
                "total": 5,
                "success_count": 4,
                "failed_count": 1,
                "errors": [{"index": 2, "title": "Invalid Session", "error": "Title too long"}],
            }
        }


# ============================================================================
# Agent Execution Models
# ============================================================================


class AgentRunRequest(BaseModel):
    """Request to execute agent with a message.

    In session-centric architecture:
    - session_id provided → continue existing conversation
    - session_id None → auto-create ephemeral session for one-off queries
    """

    message: str = Field(..., min_length=1, max_length=10000, description="User message to agent")
    session_id: Optional[str] = Field(
        None,
        description="Session ID (optional - auto-creates if None)",
    )
    stream: bool = Field(default=False, description="Enable streaming responses")
    model: Optional[str] = Field(
        None, pattern=r"^[a-zA-Z0-9\-_.]+$", description="Override default model (e.g., 'gpt-4')"
    )

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: Optional[str]) -> Optional[str]:
        """Normalize session IDs to lowercase; let route handle pattern validation."""
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError("session_id must be a string")

        trimmed = value.strip()
        if not trimmed:
            return None

        return trimmed.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Analyze the sales data and find trends",
                "session_id": "sess_abc123def456",
                "stream": False,
            }
        }


class AgentRunResponse(BaseModel):
    """Response from agent execution."""

    session_id: str = Field(..., description="Session ID where conversation occurred")
    message_id: str = Field(..., description="Unique message identifier")
    response: str = Field(..., description="Agent's response text")
    tools_used: List[str] = Field(default_factory=list, description="List of tools called")
    new_messages_count: int = Field(..., ge=0, description="Number of new messages in session")
    quota_used: int = Field(..., ge=0, description="Quota consumed by this request")
    quota_remaining: int = Field(..., ge=0, description="Remaining quota after request")
    model_used: str = Field(..., description="Model used for generation")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    event_id: Optional[str] = Field(None, description="Event ID for tracking execution tree")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of tool calls: [{tool_name, parameters, result, status, duration_ms}]",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123def456",
                "message_id": "msg_xyz789",
                "response": "I've analyzed the sales data. Here are the key trends...",
                "tools_used": ["analyze_dataframe", "create_chart"],
                "new_messages_count": 2,
                "quota_used": 5,
                "quota_remaining": 995,
                "model_used": "gpt-4",
                "usage": {"input_tokens": 150, "output_tokens": 300, "total_tokens": 450},
                "event_id": "evt_abc123def456",
                "tool_calls": [
                    {
                        "tool_name": "analyze_dataframe",
                        "parameters": {"df": "sales_data.csv"},
                        "result": "Analysis complete",
                        "status": "success",
                        "duration_ms": 234,
                    }
                ],
            }
        }


# ============================================================================
# Tool Management Models
# ============================================================================


class ToolInfo(BaseModel):
    """Information about a single tool."""

    name: str = Field(..., description="Tool name/identifier")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters schema")
    required_tier: str = Field(
        ..., description="Minimum tier required to execute tool (FREE, PRO, ENTERPRISE)"
    )
    quota_cost: int = Field(..., ge=0, description="Quota cost per invocation")
    category: str = Field(..., description="Tool category: data_analysis, export, etc.")
    enabled: bool = Field(..., description="Whether the tool is currently enabled")
    tags: List[str] = Field(default_factory=list, description="Discovery tags for the tool")

    # Visual UI enhancement fields
    icon: Optional[str] = Field(None, description="Emoji or icon identifier for UI display")
    usage_count: int = Field(default=0, ge=0, description="Total usage count across all sessions")
    example_use_case: Optional[str] = Field(None, description="Example use case description")
    estimated_quota_cost: float = Field(
        default=1.0, ge=0, description="Estimated average quota cost"
    )


class ToolListResponse(BaseModel):
    """List of available tools."""

    tools: List[ToolInfo] = Field(..., description="Available tools for current user")
    count: int = Field(..., ge=0, description="Number of available tools")

    class Config:
        json_schema_extra = {
            "example": {
                "tools": [
                    {
                        "name": "analyze_dataframe",
                        "description": "Analyze pandas DataFrame",
                        "parameters": {"df": "DataFrame", "analysis_type": "str"},
                        "required_tier": "PRO",
                        "quota_cost": 2,
                        "category": "data_analysis",
                        "enabled": True,
                        "tags": ["analysis", "data"],
                    }
                ],
                "count": 1,
            }
        }


# ============================================================================
# Error Response Models
# ============================================================================
# NOTE: ErrorResponse imported from src.models.common (avoiding duplication)


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = Field(
        None, description="Field that caused error (for validation errors)"
    )
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


# ============================================================================
# Health & Status Models
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    checks: Dict[str, str] = Field(default_factory=dict, description="Individual component health")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "my-tiny-data-collider",
                "version": "2.0.0",
                "timestamp": "2025-10-27T12:00:00Z",
                "checks": {"database": "healthy", "cache": "healthy", "llm": "healthy"},
            }
        }


# ============================================================================
# Trace Explorer Models (PydanticAI-style)
# ============================================================================


class EventExecutionSummary(BaseModel):
    """Execution summary for event (agent/tool performance metrics)."""

    total_duration_ms: int = Field(..., ge=0, description="Total execution time in milliseconds")
    tools_called: List[str] = Field(
        default_factory=list, description="Tools executed during this event"
    )
    tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed")
    error_count: int = Field(default=0, ge=0, description="Number of errors in subtree")
    quota_cost: int = Field(default=0, ge=0, description="Quota consumed by this event")


class TraceEventResponse(BaseModel):
    """Enhanced event response for trace explorer UI."""

    event_id: str = Field(..., description="Unique event identifier")
    session_id: str = Field(..., description="Parent session ID")
    parent_event_id: Optional[str] = Field(None, description="Parent event ID")
    event_path: str = Field(..., description="Hierarchical path")
    depth: int = Field(..., ge=0, description="Tree depth")
    event_type: str = Field(..., description="Event type")
    source: str = Field(..., description="Event source")
    status: str = Field(..., description="Event status")
    timestamp: datetime = Field(..., description="Event timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Execution duration")

    # Enhanced trace data
    tool_name: Optional[str] = Field(None, description="Tool name if tool execution")
    input_preview: Optional[Dict[str, Any]] = Field(
        None, description="Truncated input data (first 500 chars)"
    )
    output_preview: Optional[Dict[str, Any]] = Field(
        None, description="Truncated output data (first 500 chars)"
    )
    error_details: Optional[str] = Field(None, description="Error message if failed")

    # Tree metadata
    child_count: int = Field(default=0, ge=0, description="Direct children count")
    total_descendants: int = Field(default=0, ge=0, description="Total descendants")
    execution_summary: Optional[EventExecutionSummary] = Field(
        None, description="Aggregated execution metrics"
    )

    # Visual UI enhancement fields
    depth_level: int = Field(
        default=0, ge=0, description="0=root, 1=child, 2=grandchild (for tree view)"
    )
    siblings_count: int = Field(
        default=0, ge=0, description="Number of sibling events at same level"
    )
    is_collapsed: bool = Field(
        default=False, description="Server-side default for UI collapse state"
    )
    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context: {triggered_by: 'user', chain_id: '...'}",
    )


class TraceStatsResponse(BaseModel):
    """Session-level trace statistics for dashboard."""

    session_id: str = Field(..., description="Session identifier")
    total_events: int = Field(..., ge=0, description="Total events in session")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Event count by type")
    by_status: Dict[str, int] = Field(default_factory=dict, description="Event count by status")
    quota_breakdown: Dict[str, int] = Field(
        default_factory=dict, description="Quota usage by category"
    )
    execution_times: Dict[str, int] = Field(
        default_factory=dict, description="Execution time percentiles (avg_ms, p50_ms, p95_ms)"
    )
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Failed events ratio")


# ============================================================================
# Missing Response Schemas (from OpenAPI analysis)
# ============================================================================


class QuotaUsageResponse(BaseModel):
    """User quota usage statistics and history."""

    user_id: str = Field(..., description="User identifier")
    tier: str = Field(..., description="User tier")
    quota: Dict[str, Any] = Field(
        ..., description="Quota details (total, used, remaining, reset_at)"
    )
    usage_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Last 7 days usage breakdown"
    )
    billing_period: Dict[str, str] = Field(
        default_factory=dict, description="Current billing period (start, end)"
    )
    tools_used: Dict[str, int] = Field(default_factory=dict, description="Tool usage counts")
    sessions_count: int = Field(default=0, ge=0, description="Total sessions created")
    messages_count: int = Field(default=0, ge=0, description="Total messages sent")


class AgentCapabilitiesResponse(BaseModel):
    """Agent capabilities based on user tier."""

    available_models: List[str] = Field(
        default_factory=list, description="Available AI models for current tier"
    )
    available_tools: List[str] = Field(
        default_factory=list, description="Available tools for current tier"
    )
    max_messages_per_session: int = Field(..., ge=0, description="Message limit per session")
    max_concurrent_sessions: int = Field(..., ge=0, description="Concurrent session limit")
    features: Dict[str, bool] = Field(
        default_factory=dict, description="Feature flags (streaming, file_upload, etc.)"
    )

    # Visual UI enhancement fields
    personality: Optional[str] = Field(
        None, description="Agent personality: analytical, creative, technical"
    )
    specializations: List[str] = Field(
        default_factory=list, description="Agent specialization areas"
    )
    example_prompts: List[str] = Field(
        default_factory=list, description="Example prompts to demonstrate capabilities"
    )
    performance_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Performance metrics: {avg_response_time: 1.2, success_rate: 0.95}",
    )


# ============================================================================
# Dashboard & Activity Feed Models (NEW)
# ============================================================================


class DashboardStatsResponse(BaseModel):
    """Dashboard overview statistics for visualization."""

    total_sessions: int = Field(..., ge=0, description="Total number of sessions")
    active_sessions: int = Field(..., ge=0, description="Currently active sessions")
    total_messages: int = Field(..., ge=0, description="Total messages sent")
    total_tool_calls: int = Field(..., ge=0, description="Total tool invocations")

    # Most used items
    most_used_tools: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top tools with usage counts: [{name, count, last_used}]"
    )
    most_used_agents: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top agents with usage counts: [{agent_id, name, count}]"
    )

    # Quota trends (7-day chart data)
    quota_usage_trend: List[Dict[str, Any]] = Field(
        default_factory=list, description="Daily quota usage for 7 days: [{date, used, limit}]"
    )

    # Recent activity
    recent_activity: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent activity items: [{type, timestamp, session_id, preview}]",
    )

    # Session distribution
    session_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Sessions by status: {active: 5, completed: 10, archived: 2}",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 42,
                "active_sessions": 5,
                "total_messages": 384,
                "total_tool_calls": 127,
                "most_used_tools": [
                    {"name": "web_search", "count": 45, "last_used": "2025-11-07T12:00:00Z"},
                    {"name": "calculator", "count": 32, "last_used": "2025-11-07T11:30:00Z"},
                ],
                "most_used_agents": [
                    {"agent_id": "agent_abc123", "name": "Data Analyst", "count": 23}
                ],
                "quota_usage_trend": [
                    {"date": "2025-11-01", "used": 45, "limit": 100},
                    {"date": "2025-11-02", "used": 67, "limit": 100},
                ],
                "recent_activity": [
                    {
                        "type": "message",
                        "timestamp": "2025-11-07T12:30:00Z",
                        "session_id": "sess_abc123",
                        "preview": "Analyze the sales data...",
                    }
                ],
                "session_distribution": {"active": 5, "completed": 30, "archived": 7},
            }
        }


class ActivityItem(BaseModel):
    """Single activity item for session activity feed."""

    activity_id: str = Field(..., description="Unique activity identifier")
    activity_type: str = Field(
        ..., description="Activity type: message, tool_call, document_upload, agent_switch"
    )
    timestamp: datetime = Field(..., description="Activity timestamp")
    user_id: str = Field(..., description="User who performed the activity")
    session_id: str = Field(..., description="Parent session ID")

    # Content fields (populated based on activity_type)
    message_content: Optional[str] = Field(None, description="Message text (for message type)")
    message_role: Optional[str] = Field(None, description="Message role: user, assistant, tool")
    tool_name: Optional[str] = Field(None, description="Tool name (for tool_call type)")
    tool_result: Optional[str] = Field(None, description="Tool result preview (truncated)")
    document_name: Optional[str] = Field(
        None, description="Document name (for document_upload type)"
    )
    agent_id: Optional[str] = Field(None, description="Agent ID (for agent_switch type)")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata: {duration_ms, tokens_used, status}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "activity_id": "act_xyz789",
                "activity_type": "message",
                "timestamp": "2025-11-07T12:30:00Z",
                "user_id": "user_123",
                "session_id": "sess_abc123",
                "message_content": "Analyze the sales data for Q4",
                "message_role": "user",
                "metadata": {},
            }
        }


class SessionActivityResponse(BaseModel):
    """Session activity feed response."""

    session_id: str = Field(..., description="Session identifier")
    activities: List[ActivityItem] = Field(..., description="Chronological activity items")
    total_count: int = Field(..., ge=0, description="Total number of activities")
    has_more: bool = Field(..., description="Whether more activities exist")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "activities": [],
                "total_count": 42,
                "has_more": True,
            }
        }
