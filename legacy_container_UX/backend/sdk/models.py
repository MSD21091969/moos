"""Type-safe models for collider-sdk.

Mirror of API models with enhanced type hints for SDK users.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """Current user information."""

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    permissions: List[str] = Field(..., description="User permissions")
    quota_remaining: int = Field(..., ge=0, description="Remaining API quota")
    tier: str = Field(..., description="User tier: free, pro, enterprise")


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""

    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    description: Optional[str] = Field(None, max_length=1000, description="Session description")
    tags: List[str] = Field(default_factory=list, description="Session tags for filtering")
    session_type: str = Field(
        default="chat", description="Session type: chat, analysis, workflow, simulation"
    )
    ttl_hours: int = Field(default=24, gt=0, le=8760, description="Session TTL in hours")
    domain: Optional[str] = Field(
        default=None, description="Business domain: legal, medical, finance, etc."
    )
    scenario: Optional[str] = Field(
        default=None, description="Scenario description for simulation sessions"
    )
    clone_from_session_id: Optional[str] = Field(
        default=None,
        pattern=r"^sess_[a-f0-9]{12}$",
        description="Clone agents/tools from existing session",
    )


class Session(BaseModel):
    """Complete session information."""

    session_id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    tags: List[str] = Field(..., description="Session tags")
    session_type: str = Field(..., description="Session type: chat, analysis, workflow, simulation")
    status: str = Field(..., description="Session status: active, completed, expired, archived")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_active: bool = Field(..., description="Whether session is currently active")
    message_count: int = Field(default=0, ge=0, description="Number of messages in session")
    # New fields for agent management, sharing, and provenance
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


class SessionList(BaseModel):
    """Paginated list of sessions."""

    sessions: List[Session] = Field(..., description="List of sessions")
    total: int = Field(..., ge=0, description="Total number of sessions")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


class SessionUpdateRequest(BaseModel):
    """Request to update session metadata."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(default=None)
    status: Optional[str] = Field(
        default=None, description="Update status: active, completed, archived"
    )
    active_agent_id: Optional[str] = Field(default=None, description="Update active agent ID")
    domain: Optional[str] = Field(default=None, description="Update business domain")
    scenario: Optional[str] = Field(default=None, description="Update scenario description")


class AgentRunRequest(BaseModel):
    """Request to execute agent with a message."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message to agent")
    session_id: Optional[str] = Field(
        None,
        pattern=r"^sess_[a-f0-9]{12}$",
        description="Session ID (optional - auto-creates if None)",
    )
    stream: bool = Field(default=False, description="Enable streaming responses")
    model: Optional[str] = Field(
        None, pattern=r"^[a-zA-Z0-9\-_.]+$", description="Override default model (e.g., 'gpt-4')"
    )


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


class ToolInfo(BaseModel):
    """Information about a single tool."""

    name: str = Field(..., description="Tool name/identifier")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters schema")
    required_tier: str = Field(..., description="Minimum tier required to use tool")
    quota_cost: int = Field(..., ge=0, description="Quota cost per invocation")
    category: str = Field(..., description="Tool category")
    enabled: bool = Field(..., description="Whether the tool is currently enabled")
    tags: List[str] = Field(default_factory=list, description="Discovery tags for the tool")


class ToolList(BaseModel):
    """List of available tools."""

    tools: List[ToolInfo] = Field(..., description="Available tools for current user")
    count: int = Field(..., ge=0, description="Number of available tools")


class Message(BaseModel):
    """A single message in conversation history."""

    message_id: str = Field(..., description="Unique message identifier")
    role: str = Field(..., description="Message role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made (if any)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MessageHistory(BaseModel):
    """Message history for a session."""

    session_id: str = Field(..., description="Session identifier")
    messages: List[Message] = Field(..., description="List of messages")
    total: int = Field(..., ge=0, description="Total messages in session")
    has_more: bool = Field(..., description="Whether more messages exist")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = Field(None, description="Field that caused error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class AgentCapabilities(BaseModel):
    """Agent capabilities based on user tier."""

    models: List[str] = Field(..., description="Available models")
    features: Dict[str, bool] = Field(..., description="Feature flags")


class MessageExportRequest(BaseModel):
    """Request to export session messages."""

    session_id: str = Field(..., description="Session ID to export")
    format: str = Field(default="json", description="Export format: json, csv, txt")
    include_metadata: bool = Field(default=True, description="Include message metadata")


class JobTriggerResponse(BaseModel):
    """Response from job trigger."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
