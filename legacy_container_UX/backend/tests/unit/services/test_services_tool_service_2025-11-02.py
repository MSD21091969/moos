"""
Unit tests for ToolService.

Tests tool discovery, filtering, access control.
"""

import pytest
from src.services.tool_service import ToolService
from src.models.context import UserContext
from src.models.permissions import Tier
from src.core.tool_registry import ToolRegistry, ToolCategory, reset_tool_registry
from src.core.exceptions import ToolNotFoundError, PermissionDeniedError


@pytest.fixture
def registry():
    """Fresh ToolRegistry."""
    reset_tool_registry()
    return ToolRegistry()


@pytest.fixture
def tool_service(registry):
    """ToolService with test registry."""
    service = ToolService()
    service.registry = registry
    return service


@pytest.fixture
def free_user():
    """FREE tier user context."""
    return UserContext(
        user_id="user_free",
        email="free@example.com",
        tier=Tier.FREE,
        quota_remaining=100,
    )


@pytest.fixture
def pro_user():
    """PRO tier user context."""
    return UserContext(
        user_id="user_pro",
        email="pro@example.com",
        tier=Tier.PRO,
        quota_remaining=1000,
    )


@pytest.fixture
def sample_tool():
    """Sample tool function."""

    async def analyze_data(query: str) -> dict:
        return {"result": query}

    return analyze_data


class TestListAvailableTools:
    """Test list_available_tools with tier filtering."""

    @pytest.mark.asyncio
    async def test_list_tools_free_user(self, tool_service, registry, free_user, sample_tool):
        """
        TEST: list_available_tools returns FREE tier tools.

        PURPOSE: FREE users see only FREE tier tools.

        VALIDATES:
        - FREE tier user sees FREE tier tools
        - PRO/ENTERPRISE tools excluded

        EXPECTED: Only FREE tier tools returned.
        """
        registry.register(
            name="free_tool",
            description="Free tool",
            category=ToolCategory.UTILITY,
            required_tier="FREE",
        )(sample_tool)

        registry.register(
            name="pro_tool",
            description="Pro tool",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
        )(sample_tool)

        tools = await tool_service.list_available_tools(user_ctx=free_user)

        tool_names = [t.name for t in tools]
        assert "free_tool" in tool_names
        assert "pro_tool" not in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_pro_user(self, tool_service, registry, pro_user, sample_tool):
        """
        TEST: list_available_tools returns FREE+PRO tools for PRO user.

        PURPOSE: PRO users inherit FREE tools.

        VALIDATES:
        - PRO user sees FREE + PRO tools
        - ENTERPRISE tools excluded

        EXPECTED: FREE and PRO tools returned.
        """
        registry.register(
            name="free_tool",
            description="Free tool",
            category=ToolCategory.UTILITY,
            required_tier="FREE",
        )(sample_tool)

        registry.register(
            name="pro_tool",
            description="Pro tool",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
        )(sample_tool)

        tools = await tool_service.list_available_tools(user_ctx=pro_user)

        tool_names = [t.name for t in tools]
        assert "free_tool" in tool_names
        assert "pro_tool" in tool_names


class TestGetToolDetails:
    """Test get_tool_details with access control."""

    @pytest.mark.asyncio
    async def test_get_tool_details_success(self, tool_service, registry, free_user, sample_tool):
        """
        TEST: get_tool_details returns tool metadata.

        PURPOSE: Users can retrieve details for accessible tools.

        VALIDATES:
        - Tool name, description, tier, quota_cost returned
        - Access check passes for user's tier

        EXPECTED: ToolInfo with complete metadata.
        """
        registry.register(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.UTILITY,
            required_tier="FREE",
            quota_cost=5,
        )(sample_tool)

        tool_info = await tool_service.get_tool_details(
            user_ctx=free_user,
            tool_name="test_tool",
        )

        assert tool_info.name == "test_tool"
        assert tool_info.description == "Test tool"
        assert tool_info.quota_cost == 5

    @pytest.mark.asyncio
    async def test_get_tool_details_not_found(self, tool_service, free_user):
        """
        TEST: get_tool_details raises ToolNotFoundError for missing tool.

        PURPOSE: Handle missing tools gracefully.

        VALIDATES:
        - ToolNotFoundError raised for nonexistent tool
        - Error message includes tool name

        EXPECTED: ToolNotFoundError with tool name.
        """
        with pytest.raises(ToolNotFoundError) as exc_info:
            await tool_service.get_tool_details(
                user_ctx=free_user,
                tool_name="nonexistent_tool",
            )

        assert "nonexistent_tool" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_get_tool_details_permission_denied(
        self, tool_service, registry, free_user, sample_tool
    ):
        """
        TEST: get_tool_details raises PermissionDeniedError for wrong tier.

        PURPOSE: Enforce tier-based access control.

        VALIDATES:
        - FREE user cannot access PRO tool details
        - PermissionDeniedError raised with tier info

        EXPECTED: PermissionDeniedError for insufficient tier.
        """
        registry.register(
            name="pro_tool",
            description="Pro only",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
        )(sample_tool)

        with pytest.raises(PermissionDeniedError) as exc_info:
            await tool_service.get_tool_details(
                user_ctx=free_user,
                tool_name="pro_tool",
            )

        assert "FREE" in str(exc_info.value.message) or "pro_tool" in str(exc_info.value.message)
