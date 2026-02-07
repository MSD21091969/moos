"""Pydantic models for the application."""

# Core domain models
from src.models.users import User, UserCreate, UserUpdate, UserInDB
from src.models.sessions import (
    Session,
    SessionMetadata,
    SessionCreate,
    SessionUpdate,
    SessionSummary,
    SessionListResponse,
    SessionType,
    SessionStatus,
    SessionQuery,
)
from src.models.permissions import Tier, TIER_LIMITS

# Runtime contexts
from src.models.context import (
    UserContext,
    SessionContext,
    ToolDefinition,
    AgentDefinition,
    ToolContext,
    AgentContext,
)

# Events (moved from sessions.py)
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

# Common
from src.models.common import TimestampMixin, StatusEnum, ResponseStatus, ErrorResponse

__all__ = [
    # Users
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    # Sessions
    "Session",
    "SessionMetadata",
    "SessionCreate",
    "SessionUpdate",
    "SessionSummary",
    "SessionListResponse",
    "SessionType",
    "SessionStatus",
    "SessionQuery",
    # Permissions
    "Tier",
    "TIER_LIMITS",
    # Contexts
    "UserContext",
    "SessionContext",
    "ToolDefinition",
    "AgentDefinition",
    "ToolContext",
    "AgentContext",
    # Events
    "Event",
    "EventType",
    "EventSource",
    "EventStatus",
    "ToolEvent",
    "SessionEvent",
    "SessionEventTree",
    "SessionEventListResponse",
    # Common
    "TimestampMixin",
    "StatusEnum",
    "ResponseStatus",
    "ErrorResponse",
]
