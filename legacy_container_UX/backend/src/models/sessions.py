"""Session models for Universal Object Model v5.0.0.

Session is a "naked" container - a ContainerBase subclass without definition_id.
Sessions group agents, tools, and sources for a specific user task/context.
"""

import re
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.containers import ContainerBase

# Session ID pattern: sess_ followed by 12 hexadecimal characters
SESSION_ID_PATTERN = re.compile(r"^sess_[a-f0-9]{12}$")


class SessionType(str, Enum):
    """Type of session."""

    INTERACTIVE = "interactive"
    WORKFLOW = "workflow"
    CHAT = "chat"
    ANALYSIS = "analysis"
    SIMULATION = "simulation"  # For knowledge-embedded sessions


class SessionStatus(str, Enum):
    """Session lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class SessionMetadata(BaseModel):
    """User-defined session metadata (Casefile-like)."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    tags: list[str] = Field(default_factory=list)
    session_type: SessionType
    ttl_hours: int = Field(default=24, gt=0, le=8760)
    custom_fields: dict[str, str] = Field(default_factory=dict)

    # NEW: Domain context
    domain: str | None = Field(None, description="Business domain: legal, medical, finance, etc.")
    scenario: str | None = Field(None, description="Scenario description for simulation sessions")

    # NEW: Container and visual metadata (2025-11-14 - Frontend UX support)
    is_container: bool = Field(
        default=False, description="Whether this session acts as a container for other sessions"
    )
    child_node_ids: list[str] = Field(
        default_factory=list, description="Frontend node IDs for child sessions (ReactFlow)"
    )
    visual_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Frontend visual state: {color, collapsed, position: {x, y}, size: {width, height}}",
    )
    theme_color: str | None = Field(
        None,
        description="Session theme color for frontend UI (hex color code, e.g., '#3b82f6')",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Ensure tags stay within length/count limits and remove accidental whitespace."""
        if len(tags) > 10:
            raise ValueError("A session can have at most 10 tags")

        cleaned: list[str] = []
        for raw in tags:
            if not isinstance(raw, str):
                raise ValueError("Tags must be strings")

            tag = raw.strip()
            if not tag:
                raise ValueError("Tags cannot be empty strings")
            if len(tag) > 50:
                raise ValueError("Tags cannot exceed 50 characters")

            cleaned.append(tag)

        return cleaned


class SessionCreate(BaseModel):
    """Request to create a new session."""

    metadata: SessionMetadata
    initial_collections: dict[str, str] = Field(default_factory=dict)
    clone_from_session_id: str | None = Field(
        None, description="Clone agents/tools from existing session"
    )
    parent_id: str | None = Field(
        None,
        description="Parent container ID (usersession_{user_id} or session_{id})",
    )
    depth: int | None = Field(
        None,
        description="Container depth (0=UserSession, 1-4=nested, tier-gated). Computed from parent if not provided.",
    )


class SessionUpdate(BaseModel):
    """Request to update session metadata or collections."""

    # Direct metadata fields (convenience for API)
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    domain: str | None = None
    scenario: str | None = None

    # Full metadata update (alternative to individual fields)
    metadata: SessionMetadata | None = None

    # Collections management
    collections_to_add: dict[str, str] = Field(default_factory=dict)
    collections_to_remove: list[str] = Field(default_factory=list)

    # Session-level fields
    active_agent_id: str | None = Field(None, description="Set active agent for session")
    status: SessionStatus | None = Field(None, description="Update session status")

    # Preferences update
    preferences: dict[str, str] | None = Field(None, description="Update session preferences")

    # Visual metadata update (2025-11-24 - Frontend sync support)
    visual_metadata: dict[str, Any] | None = Field(
        None, description="Update frontend visual state (opaque JSON)"
    )
    theme_color: str | None = Field(
        None, description="Update session theme color"
    )

    # Resource reference updates
    session_tool_definitions: list[str] | None = Field(
        None,
        description="Replace tool definition identifiers referenced by this session",
    )
    session_agent_definitions: list[str] | None = Field(
        None,
        description="Replace agent definition identifiers referenced by this session",
    )
    session_datasources: list[str] | None = Field(
        None,
        description="Replace datasource attachment identifiers linked to this session",
    )
    session_acl_members: list[str] | None = Field(
        None,
        description="Replace ACL attachment identifiers linked to this session",
    )


class SessionQuery(BaseModel):
    """Query parameters for searching sessions."""

    tags: list[str] = Field(default_factory=list)
    session_type: SessionType | None = None
    status: SessionStatus | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class Session(ContainerBase):
    # Override to allow auto-sync with session_id
    instance_id: str = Field(default="", description="Alias of session_id for ContainerBase")
    """Session container - a "naked" container without definition_id.

    Session = Domain Context Container
    Contains agents, tools, sources, and nested sessions in /resources/ subcollection.
    
    Key differences from other containers:
    - No definition_id (sessions are created directly, not from templates)
    - Has SessionMetadata for user-facing properties (title, description, tags)
    - Has session_id as primary identifier (instance_id is alias)
    """

    # Session-specific identity (instance_id inherited from ContainerBase)
    session_id: str = Field(..., pattern=r"^sess_[a-f0-9]{12}$")
    
    # Session has no definition (naked container)
    definition_id: None = Field(default=None, description="Sessions have no definition (naked container)")
    
    # Session metadata (user-facing properties)
    metadata: SessionMetadata
    status: SessionStatus = SessionStatus.ACTIVE
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    
    # Legacy collection schemas (kept for backward compatibility)
    collection_schemas: dict[str, str] = Field(
        default_factory=dict, description="Data collection schemas"
    )

    custom_fields: dict[str, str] = Field(default_factory=dict)

    # Session preferences (theme, UI settings, etc.)
    preferences: dict[str, str] = Field(
        default_factory=dict,
        description="User preferences for this session (theme, view mode, etc.)",
    )

    # Sharing & hierarchy
    is_shared: bool = Field(default=False, description="Whether the session is shared")
    shared_with_users: list[str] = Field(
        default_factory=list, description="User IDs with shared access"
    )
    parent_session_id: str | None = Field(
        default=None, description="Parent session ID for nested session hierarchies"
    )
    child_sessions: list[str] = Field(
        default_factory=list, description="Child session IDs (legacy compatibility)"
    )
    source_session_id: str | None = Field(
        default=None, description="Source session ID for cloned sessions"
    )

    # Agent management
    active_agent_id: str | None = Field(
        None, description="Active agent instance ID"
    )

    # Event tracking
    event_count: int = Field(default=0, ge=0, description="Number of root events")
    last_event_at: datetime | None = Field(None, description="Last event timestamp")

    # Creator info (created_by inherited from ContainerBase)
    created_by_email: str | None = Field(None, description="Email of session creator")
    
    @model_validator(mode="after")
    def _sync_instance_id(self):
        """Ensure instance_id mirrors session_id for serialization/storage."""
        # ContainerBase defines instance_id as a field; keep it aligned to session_id
        object.__setattr__(self, "instance_id", self.session_id)
        return self

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id matches pattern sess_[a-f0-9]{12}."""
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError(
                f"session_id must match pattern 'sess_XXXXXXXXXXXX' where X is lowercase hex (0-9a-f). Got: {v}"
            )
        return v

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "acl": self.acl,
            "definition_id": self.definition_id,
            "metadata": self.metadata.model_dump(),
            "status": self.status.value,
            "collection_schemas": self.collection_schemas,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "created_by": self.created_by,
            "is_expired": self.is_expired,
            "is_active": self.is_active,
        }


class SessionSummary(BaseModel):
    """Lightweight session information for listing."""

    session_id: str = Field(..., pattern=r"^sess_[a-f0-9]{12}$")
    title: str
    description: str | None
    tags: list[str]
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    is_active: bool
    domain: str | None = Field(None, description="Business domain")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id matches pattern."""
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError(
                f"session_id must match pattern 'sess_XXXXXXXXXXXX' where X is lowercase hex. Got: {v}"
            )
        return v


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionSummary]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# Message History Models - MOVED TO src/models/events.py
# ============================================================================
# Import from events.py:
#   from src.models.events import (
#       MessageRole, Message, MessageHistoryRequest,
#       MessageHistoryResponse, MessageExportRequest
#   )
