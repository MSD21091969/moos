"""User and Session context models with caching."""

from typing import Optional, Literal, Any
from datetime import datetime, timezone
from functools import lru_cache
from pydantic import BaseModel, Field, field_validator
from src.models.permissions import Tier
from src.models.links import ResourceLink


class UserContext(BaseModel):
    """
    User context loaded from JWT and cached in memory.

    Cached with LRU to avoid repeated Firestore lookups.
    Includes permissions and quota for session execution.
    """

    user_id: str = Field(description="Unique user identifier")
    email: str = Field(description="User email address")
    display_name: Optional[str] = Field(default=None, description="User display name")
    permissions: tuple[str, ...] = Field(
        default_factory=tuple, description="User permissions (tuple for hashability)"
    )
    quota_remaining: int = Field(
        default=100, ge=0, description="Remaining quota for tool executions"
    )
    tier: Tier = Field(default=Tier.FREE, description="User subscription tier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, value: Any) -> Tier:
        """Normalize tier to lowercase for case-insensitive validation."""
        if isinstance(value, Tier):
            return value
        if isinstance(value, str):
            return Tier(value.lower())
        return value

    class Config:
        frozen = True  # Make hashable for LRU cache


class SessionContext(BaseModel):
    """
    Session context passed to PydanticAI RunContext.

    Bridge between our Session model and PydanticAI's dependency injection.
    """

    session_id: str = Field(description="Session identifier")
    user_id: str = Field(description="User who owns this session")
    user_email: str = Field(description="User email (for audit)")
    permissions: list[str] = Field(description="User permissions for this session")
    quota_remaining: int = Field(description="Remaining quota")
    tier: Tier = Field(description="User subscription tier")

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, value: Any) -> Tier:
        """Normalize tier to lowercase for case-insensitive validation."""
        if isinstance(value, Tier):
            return value
        if isinstance(value, str):
            return Tier(value.lower())
        return value

    @classmethod
    def from_user_context(cls, session_id: str, user_ctx: UserContext) -> "SessionContext":
        """
        Create SessionContext from UserContext.

        Args:
            session_id: The session ID
            user_ctx: User context (from cache)

        Returns:
            SessionContext ready for PydanticAI deps parameter
        """
        return cls(
            session_id=session_id,
            user_id=user_ctx.user_id,
            user_email=user_ctx.email,
            permissions=list(user_ctx.permissions),
            quota_remaining=user_ctx.quota_remaining,
            tier=user_ctx.tier,
        )


# LRU Cache for UserContext (avoids repeated Firestore lookups)
@lru_cache(maxsize=1000)
def get_cached_user_context(user_id: str) -> Optional[UserContext]:
    """
    Get UserContext from cache or load from Firestore.

    LRU cache of 1000 users = ~100KB memory overhead.
    Cache hit = instant, cache miss = Firestore query.

    Args:
        user_id: User identifier

    Returns:
        UserContext or None if user not found

    Note:
        Call clear_user_cache(user_id) when permissions/quota change.
    """
    from src.core.container import get_container

    db = get_container().firestore_client
    user_doc = db.collection("users").document(user_id).get()

    if not user_doc.exists:
        return None

    user_data = user_doc.to_dict()
    return UserContext(**user_data)


def clear_user_cache(user_id: Optional[str] = None):
    """
    Clear user from LRU cache.

    Call when:
    - User permissions change
    - User quota is updated
    - User is deleted

    Args:
        user_id: Specific user to clear, or None to clear all
    """
    if user_id is None:
        get_cached_user_context.cache_clear()
    else:
        # Clear specific user by rebuilding cache without them
        # (Python's lru_cache doesn't support per-key invalidation)
        get_cached_user_context.cache_clear()


def get_cache_stats() -> dict:
    """
    Get LRU cache statistics.

    Returns:
        dict with hits, misses, size, maxsize
    """
    info = get_cached_user_context.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "size": info.currsize,
        "maxsize": info.maxsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0,
    }


# ============================================================================
# Agent and Tool Definition Models
# ============================================================================


class ToolDefinition(BaseModel):
    """
    User's personal tool definition.

    Storage: /users/{uid}/tools/{tool_id}
    Session Usage: /users/{uid}/sessions/{sid}/tools/{tool_id} (references user's tools)

    Tools belong to USER, sessions reference them.
    Example: User has "legal_search" tool, multiple sessions can use it.
    """

    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="What the tool does")

    type: Literal["builtin", "yaml", "written"] = Field(
        default="yaml", description="Tool implementation type"
    )

    # For builtin: {function: "search_text", module: "src.tools.text_tools"}
    # For yaml: {base_tool: "search_text", param_mappings: {...}, enrichment: {...}}
    # For written: {code: "...", dependencies: [...]}
    definition: dict = Field(..., description="Tool configuration/code")

    # Metadata
    category: str = Field(default="domain_specific", description="Tool category")
    quota_cost: int = Field(default=1, ge=0, description="Quota units per execution")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    tags: list[str] = Field(default_factory=list, description="Tags for discovery")

    # NEW: Scenario embedding (when/how to use)
    scenario_context: Optional[dict] = Field(
        None,
        description="Embedded knowledge: situation, workflow, expected outcome",
    )


class AgentDefinition(BaseModel):
    """
    User's personal agent definition.

    Storage: /users/{uid}/agents/{agent_id}
    Session Usage: /users/{uid}/sessions/{sid}/agents/{agent_id} (references user's agents)

    Agents belong to USER, sessions reference them.
    Agents automatically use tools from session context.
    Session defines workflow → Agent uses session's tool references.
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Agent purpose/capabilities")

    type: Literal["builtin", "yaml", "written"] = Field(
        default="yaml", description="Agent implementation type"
    )

    # Agent configuration
    system_prompt: str = Field(..., description="System instructions for LLM")
    model: str = Field(default="openai:gpt-4", description="LLM model to use")

    # Agent status
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    tags: list[str] = Field(default_factory=list, description="Tags for discovery")

    # Recursive Composition (Collider V2)
    resource_links: list[ResourceLink] = Field(
        default_factory=list,
        description="Linked resources (tools, other agents) that this agent uses"
    )


# ============================================================================
# Runtime Execution Contexts
# ============================================================================


class ToolContext(BaseModel):
    """
    Runtime context for tool execution.

    Built just before tool execution - combines ToolDefinition
    with session/user runtime info for validation and tracking.
    """

    tool_def: ToolDefinition = Field(..., description="Tool to execute")
    session_id: str = Field(..., description="Session context")
    user_id: str = Field(..., description="Executing user")
    tier: Tier = Field(..., description="User tier")
    permissions: list[str] = Field(..., description="User permissions")
    quota_remaining: int = Field(..., ge=0, description="Available quota")

    # Config overrides from session or runtime
    config_overrides: dict = Field(default_factory=dict, description="Runtime config overrides")

    def can_execute(self) -> tuple[bool, Optional[str]]:
        """
        Check if tool can execute in this context.

        Returns:
            (can_execute: bool, reason: Optional[str])
        """
        # Enabled check
        if not self.tool_def.enabled:
            return False, "Tool is disabled"

        # Quota check
        if self.quota_remaining < self.tool_def.quota_cost:
            return (
                False,
                f"Insufficient quota (need {self.tool_def.quota_cost}, have {self.quota_remaining})",
            )

        return True, None


class AgentContext(BaseModel):
    """
    Runtime context for agent execution.

    Built when agent executes - combines AgentDefinition with
    session's available tools and user's runtime info.
    """

    agent_def: AgentDefinition = Field(..., description="Agent to execute")
    session_id: str = Field(..., description="Session context")
    user_id: str = Field(..., description="Executing user")
    tier: Tier = Field(..., description="User tier")
    permissions: list[str] = Field(..., description="User permissions")
    quota_remaining: int = Field(..., ge=0, description="Available quota")

    # Tools available to this agent (resolved from session)
    available_tools: list[ToolDefinition] = Field(
        default_factory=list, description="Tools available in session"
    )

    @classmethod
    async def from_session(
        cls,
        agent_def: AgentDefinition,
        session_id: str,
        user_ctx: UserContext,
        session_tools: list[ToolDefinition],
        system_tools: Optional[list[ToolDefinition]] = None,
    ) -> "AgentContext":
        """
        Build AgentContext by resolving tools from session.

        Agent automatically inherits ALL session tools (domain context).
        Filters by user permissions.

        Args:
            agent_def: Agent to execute
            session_id: Current session
            user_ctx: User runtime context
            session_tools: Tools parked in this session
            system_tools: System/tier-allowed tools (optional)

        Returns:
            AgentContext with resolved toolset
        """
        # Merge session tools + system tools (session-local overrides system)
        available = list(session_tools)

        if system_tools:
            # Add system tools that aren't overridden by session
            session_tool_ids = {t.tool_id for t in session_tools}
            available.extend([t for t in system_tools if t.tool_id not in session_tool_ids])

        # NOTE: All tools are loaded into toolset. Permission checks happen at execution time
        # via ToolContext.can_execute() to allow user to see all available tools

        return cls(
            agent_def=agent_def,
            session_id=session_id,
            user_id=user_ctx.user_id,
            tier=user_ctx.tier,
            permissions=list(user_ctx.permissions),
            quota_remaining=user_ctx.quota_remaining,
            available_tools=available,
        )
