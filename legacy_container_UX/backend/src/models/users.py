"""User models for system-wide user and ACL management."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from src.models.common import TimestampMixin


class UserRole(str, Enum):
    """System user roles for ACL."""

    USER = "user"  # Regular user
    ADMIN = "admin"  # System administrator


class ACLRole(str, Enum):
    """Access control roles for session sharing."""

    OWNER = "owner"  # Full control, can delete/unshare
    EDITOR = "editor"  # Can modify content
    VIEWER = "viewer"  # Read-only access


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserCreate(BaseModel):
    """Request to create a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserUpdate(BaseModel):
    """Request to update user."""

    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


class User(TimestampMixin):
    """Complete user profile stored in Firestore 'users' collection.

    Collection: users/{user_id}

    Used for:
    - User discovery and team building
    - ACL management (who can share with whom)
    - Quota tracking
    - Team/organization management
    """

    user_id: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False

    # NEW: Quota & Tier
    tier: str = Field(default="free", description="Subscription tier: free|pro|enterprise")
    daily_quota: int = Field(default=100, ge=0, description="Daily quota allowance")
    quota_used_today: int = Field(default=0, ge=0, description="Quota used today")
    quota_reset_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # NEW: Status
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    role: UserRole = Field(default=UserRole.USER)

    # NEW: Teams / Organizations
    organization_id: str | None = Field(None, description="Organization this user belongs to")
    team_ids: list[str] = Field(default_factory=list, description="Team IDs user is member of")

    # NEW: Audit
    last_login_at: datetime | None = Field(None)
    ip_address: str | None = Field(None, description="Last known IP")
    login_count: int = Field(default=0)


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str


class UserProfile(BaseModel):
    """Lightweight user info for sharing/team discovery."""

    user_id: str
    email: str
    full_name: str | None = None
    tier: str


class UserList(BaseModel):
    """Paginated list of users."""

    users: list[UserProfile]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# User Preferences (Cross-Device State Sync)
# ============================================================================


class UserPreferences(TimestampMixin):
    """User UI preferences and session context for cross-device synchronization.

    Stored in PostgreSQL: user_preferences table
    One row per user (user_id is primary key)

    Purpose:
    - Preserve user's active session across devices
    - Sync draft messages (unsent text)
    - Remember UI state (active tabs, view modes, etc.)
    """

    user_id: str

    # Session context
    active_session_id: str | None = Field(None, description="Last active session for quick restore")

    # Draft messages per session (JSONB)
    draft_messages: dict[str, str] = Field(
        default_factory=dict, description="Unsent draft messages keyed by session_id"
    )

    # Active tab per session (JSONB)
    active_tabs: dict[str, str] = Field(
        default_factory=dict,
        description="Active tab selection per session (objects/workers/timeline/chat)",
    )

    # UI preferences (JSONB)
    ui_preferences: dict[str, str | bool | int] = Field(
        default_factory=dict,
        description="User UI preferences: theme, viewMode, sidebarCollapsed, etc.",
    )


class UserPreferencesUpdate(BaseModel):
    """Request to update user preferences (partial update)."""

    active_session_id: str | None = None
    draft_messages: dict[str, str] | None = None
    active_tabs: dict[str, str] | None = None
    ui_preferences: dict[str, str | bool | int] | None = None


class UserPreferencesResponse(BaseModel):
    """Response with user preferences."""

    user_id: str
    active_session_id: str | None
    draft_messages: dict[str, str]
    active_tabs: dict[str, str]
    ui_preferences: dict[str, str | bool | int]
    updated_at: datetime
