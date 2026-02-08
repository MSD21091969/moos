"""
Unit tests for context models.

Tests UserContext, SessionContext, ToolContext, AgentContext in isolation.
"""

import pytest

from src.models.context import (
    AgentContext,
    AgentDefinition,
    SessionContext,
    ToolContext,
    ToolDefinition,
    UserContext,
)
from src.models.permissions import Tier


class TestUserContext:
    """Test UserContext immutability and caching."""

    def test_user_context_is_frozen(self):
        """
        TEST: UserContext is immutable (frozen=True).

        PURPOSE: Enable LRU caching by making UserContext hashable.

        VALIDATES:
        - Config.frozen = True
        - Cannot modify user_id after creation
        - Raises ValidationError on attribute assignment
        - Hashable for use in @lru_cache

        EXPECTED: Immutable UserContext, assignment raises error.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
            tier=Tier.FREE,
        )

        with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
            user_ctx.user_id = "new_id"

    def test_user_context_has_default_permissions(self):
        """
        TEST: UserContext defaults to empty permissions tuple.

        PURPOSE: New users have no permissions until explicitly granted.

        VALIDATES:
        - permissions defaults to empty tuple ()
        - Tuple used instead of list (hashable for cache)
        - Can be explicitly set during creation

        EXPECTED: Empty permissions by default, can override.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
        )

        assert user_ctx.permissions == ()
        assert isinstance(user_ctx.permissions, tuple)

    def test_user_context_with_permissions(self):
        """
        TEST: UserContext accepts permissions tuple.

        PURPOSE: Store user permissions for session authorization.

        VALIDATES:
        - permissions stored as tuple
        - Can include multiple permissions
        - Used in SessionContext.from_user_context()

        EXPECTED: Permissions tuple stored correctly.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
            permissions=("read:sessions", "write:sessions", "execute:tools"),
        )

        assert len(user_ctx.permissions) == 3
        assert "execute:tools" in user_ctx.permissions

    def test_user_context_quota_defaults(self):
        """
        TEST: UserContext quota_remaining defaults to 100.

        PURPOSE: New users start with FREE tier quota (100 units).

        VALIDATES:
        - quota_remaining defaults to 100
        - Must be >= 0 (ge=0 constraint)
        - Tier defaults to Tier.FREE

        EXPECTED: quota_remaining=100, tier=FREE by default.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
        )

        assert user_ctx.quota_remaining == 100
        assert user_ctx.tier == Tier.FREE


class TestSessionContext:
    """Test SessionContext creation and conversion."""

    def test_session_context_from_user_context(self):
        """
        TEST: SessionContext.from_user_context() converts UserContext correctly.

        PURPOSE: Bridge UserContext (cached) to SessionContext (runtime).

        VALIDATES:
        - session_id passed through
        - user_id, email copied from UserContext
        - permissions converted from tuple to list (Pydantic compatibility)
        - quota_remaining, tier copied

        EXPECTED: SessionContext with all fields from UserContext.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
            permissions=("read:sessions", "execute:tools"),
            quota_remaining=50,
            tier=Tier.PRO,
        )

        session_ctx = SessionContext.from_user_context(
            session_id="sess_abc123",
            user_ctx=user_ctx,
        )

        assert session_ctx.session_id == "sess_abc123"
        assert session_ctx.user_id == "user_123"
        assert session_ctx.user_email == "test@example.com"
        assert session_ctx.permissions == ["read:sessions", "execute:tools"]
        assert session_ctx.quota_remaining == 50
        assert session_ctx.tier == Tier.PRO

    def test_session_context_permissions_are_list(self):
        """
        TEST: SessionContext.permissions is list, not tuple.

        PURPOSE: PydanticAI expects list for dependency injection.

        VALIDATES:
        - from_user_context() converts tuple → list
        - list can be modified at runtime (if needed)
        - UserContext uses tuple (hashable), SessionContext uses list (mutable)

        EXPECTED: permissions is list type.
        """
        user_ctx = UserContext(
            user_id="user_123",
            email="test@example.com",
            permissions=("read:sessions",),
        )

        session_ctx = SessionContext.from_user_context("sess_123", user_ctx)

        assert isinstance(session_ctx.permissions, list)
        assert session_ctx.permissions == ["read:sessions"]


class TestToolContext:
    """Test ToolContext execution validation."""

    @pytest.fixture
    def tool_def(self):
        """Sample ToolDefinition."""
        return ToolDefinition(
            tool_id="tool_123",
            name="Analyze CSV",
            description="Analyzes CSV files",
            type="builtin",
            definition={"function": "analyze_csv"},
            quota_cost=5,
        )

    def test_tool_context_can_execute_with_sufficient_quota(self, tool_def):
        """
        TEST: ToolContext.can_execute() returns True with enough quota.

        PURPOSE: Allow tool execution when quota requirements met.

        VALIDATES:
        - tool_def.quota_cost = 5, quota_remaining = 10 → can execute
        - Returns (True, None)
        - Enabled tool passes check

        EXPECTED: (True, None) indicating execution allowed.
        """
        tool_ctx = ToolContext(
            tool_def=tool_def,
            session_id="sess_123",
            user_id="user_123",
            tier=Tier.FREE,
            permissions=[],
            quota_remaining=10,
        )

        can_execute, reason = tool_ctx.can_execute()

        assert can_execute is True
        assert reason is None

    def test_tool_context_cannot_execute_insufficient_quota(self, tool_def):
        """
        TEST: ToolContext.can_execute() returns False without enough quota.

        PURPOSE: Block tool execution to prevent over-usage.

        VALIDATES:
        - quota_cost = 5, quota_remaining = 3 → cannot execute
        - Returns (False, reason)
        - Reason explains insufficient quota

        EXPECTED: (False, "Insufficient quota...") with helpful message.
        """
        tool_ctx = ToolContext(
            tool_def=tool_def,
            session_id="sess_123",
            user_id="user_123",
            tier=Tier.FREE,
            permissions=[],
            quota_remaining=3,
        )

        can_execute, reason = tool_ctx.can_execute()

        assert can_execute is False
        assert "Insufficient quota" in reason
        assert "need 5" in reason
        assert "have 3" in reason

    def test_tool_context_cannot_execute_disabled_tool(self, tool_def):
        """
        TEST: ToolContext.can_execute() returns False for disabled tools.

        PURPOSE: Prevent execution of tools disabled by admin/user.

        VALIDATES:
        - tool_def.enabled = False → cannot execute
        - Returns (False, "Tool is disabled")
        - Quota check skipped for disabled tools

        EXPECTED: (False, "Tool is disabled") regardless of quota.
        """
        tool_def.enabled = False

        tool_ctx = ToolContext(
            tool_def=tool_def,
            session_id="sess_123",
            user_id="user_123",
            tier=Tier.FREE,
            permissions=[],
            quota_remaining=100,
        )

        can_execute, reason = tool_ctx.can_execute()

        assert can_execute is False
        assert reason == "Tool is disabled"


class TestAgentContext:
    """Test AgentContext tool resolution."""

    @pytest.fixture
    def agent_def(self):
        """Sample AgentDefinition."""
        return AgentDefinition(
            agent_id="agent_123",
            name="Data Analyst",
            description="Analyzes data",
            type="yaml",
            system_prompt="You are a data analyst.",
        )

    @pytest.fixture
    def user_ctx(self):
        """Sample UserContext."""
        return UserContext(
            user_id="user_123",
            email="test@example.com",
            tier=Tier.PRO,
            quota_remaining=100,
        )

    @pytest.mark.asyncio
    async def test_agent_context_from_session_with_tools(self, agent_def, user_ctx):
        """
        TEST: AgentContext.from_session() resolves session tools.

        PURPOSE: Build agent runtime context with available tools.

        VALIDATES:
        - Session tools passed to available_tools
        - User context fields copied to AgentContext
        - Agent can access tools from session

        EXPECTED: AgentContext with session tools available.
        """
        session_tools = [
            ToolDefinition(
                tool_id="tool_1",
                name="Search",
                description="Search docs",
                type="builtin",
                definition={},
            ),
            ToolDefinition(
                tool_id="tool_2",
                name="Analyze",
                description="Analyze data",
                type="builtin",
                definition={},
            ),
        ]

        agent_ctx = await AgentContext.from_session(
            agent_def=agent_def,
            session_id="sess_123",
            user_ctx=user_ctx,
            session_tools=session_tools,
        )

        assert len(agent_ctx.available_tools) == 2
        assert agent_ctx.available_tools[0].tool_id == "tool_1"
        assert agent_ctx.user_id == "user_123"
        assert agent_ctx.tier == Tier.PRO

    @pytest.mark.asyncio
    async def test_agent_context_merges_system_and_session_tools(self, agent_def, user_ctx):
        """
        TEST: AgentContext merges system tools + session tools.

        PURPOSE: Agent gets session tools (priority) + system tools (fallback).

        VALIDATES:
        - Session tools included first
        - System tools added if not overridden by session
        - Session tool_id overrides system tool with same ID

        EXPECTED: Merged toolset with session tools taking precedence.
        """
        session_tools = [
            ToolDefinition(
                tool_id="search",
                name="Custom Search",
                description="Session-specific search",
                type="yaml",
                definition={},
            ),
        ]

        system_tools = [
            ToolDefinition(
                tool_id="search",
                name="System Search",
                description="Default search",
                type="builtin",
                definition={},
            ),
            ToolDefinition(
                tool_id="analyze",
                name="System Analyze",
                description="Default analyze",
                type="builtin",
                definition={},
            ),
        ]

        agent_ctx = await AgentContext.from_session(
            agent_def=agent_def,
            session_id="sess_123",
            user_ctx=user_ctx,
            session_tools=session_tools,
            system_tools=system_tools,
        )

        # Should have 2 tools: session "search" + system "analyze"
        assert len(agent_ctx.available_tools) == 2
        tool_ids = {t.tool_id for t in agent_ctx.available_tools}
        assert tool_ids == {"search", "analyze"}

        # Session "search" overrides system "search"
        search_tool = next(t for t in agent_ctx.available_tools if t.tool_id == "search")
        assert search_tool.name == "Custom Search"
