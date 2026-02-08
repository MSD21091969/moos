"""
Unit tests for ToolRegistry.

Tests tool registration, tier-based filtering, quota validation in isolation.
"""

import pytest

from src.core.tool_registry import (
    ToolCategory,
    ToolRegistry,
    get_tool_registry,
    reset_tool_registry,
)


@pytest.fixture
def registry():
    """
    Fresh ToolRegistry instance for each test.

    PURPOSE: Isolate tests from each other, prevent cross-test contamination.
    """
    return ToolRegistry()


@pytest.fixture
def sample_tool_function():
    """Sample tool function for registration tests."""

    async def analyze_csv(file_path: str) -> dict:
        return {"status": "analyzed", "file": file_path}

    return analyze_csv


class TestToolRegistration:
    """Test tool registration and metadata storage."""

    def test_register_tool_with_decorator(self, registry, sample_tool_function):
        """
        TEST: Register tool using @registry.register decorator.

        PURPOSE: Verify tool registration stores metadata and function correctly.

        VALIDATES:
        - Tool metadata stored in _tools dict
        - Tool function stored in _tool_functions dict
        - Metadata includes name, description, category, tier, quota_cost
        - Decorator returns original function (doesn't wrap it)

        EXPECTED: Tool registered, metadata retrievable, function callable.
        """
        decorated = registry.register(
            name="analyze_csv",
            description="Analyze CSV file",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
            quota_cost=5,
        )(sample_tool_function)

        # Decorator returns original function
        assert decorated == sample_tool_function

        # Metadata stored correctly
        metadata = registry.get_metadata("analyze_csv")
        assert metadata is not None
        assert metadata.name == "analyze_csv"
        assert metadata.description == "Analyze CSV file"
        assert metadata.category == ToolCategory.DATA_ANALYSIS
        assert metadata.required_tier == "PRO"
        assert metadata.quota_cost == 5
        assert metadata.enabled is True

        # Function stored correctly
        func = registry.get_function("analyze_csv")
        assert func == sample_tool_function

    def test_register_tool_with_default_values(self, registry, sample_tool_function):
        """
        TEST: Register tool with default required_tier and quota_cost.

        PURPOSE: Ensure defaults allow all users to access basic tools.

        VALIDATES:
        - required_tier defaults to "FREE" (accessible to all users)
        - quota_cost defaults to 1 (minimal cost)
        - enabled defaults to True (tool immediately available)

        EXPECTED: Tool registered with FREE tier, quota_cost=1, enabled=True.
        """
        registry.register(
            name="simple_tool",
            description="Simple utility",
            category=ToolCategory.UTILITY,
        )(sample_tool_function)

        metadata = registry.get_metadata("simple_tool")
        assert metadata.required_tier == "FREE"
        assert metadata.quota_cost == 1
        assert metadata.enabled is True

    def test_register_tool_with_tags(self, registry, sample_tool_function):
        """
        TEST: Register tool with discovery tags.

        PURPOSE: Enable tag-based tool search and categorization.

        VALIDATES:
        - Tags stored in metadata.tags list
        - Empty tags list if not provided
        - Tags can be used for search_by_tag()

        EXPECTED: Tags stored correctly in ToolMetadata.
        """
        registry.register(
            name="export_csv",
            description="Export to CSV",
            category=ToolCategory.EXPORT,
            tags=["csv", "export", "data"],
        )(sample_tool_function)

        metadata = registry.get_metadata("export_csv")
        assert metadata.tags == ["csv", "export", "data"]

    def test_get_metadata_not_found(self, registry):
        """
        TEST: get_metadata() returns None for unregistered tool.

        PURPOSE: Handle missing tools gracefully without raising exceptions.

        VALIDATES:
        - get_metadata("nonexistent") returns None
        - No KeyError or ValueError raised
        - Caller can check: if metadata is None

        EXPECTED: Returns None for missing tools.
        """
        metadata = registry.get_metadata("nonexistent_tool")
        assert metadata is None


class TestTierBasedFiltering:
    """Test tier-based tool access filtering."""

    @pytest.fixture
    def populated_registry(self, registry, sample_tool_function):
        """Registry with tools at different tier levels."""
        # FREE tier tools
        registry.register(
            name="count_words",
            description="Count words",
            category=ToolCategory.UTILITY,
            required_tier="FREE",
        )(sample_tool_function)

        # PRO tier tools
        registry.register(
            name="analyze_csv",
            description="Analyze CSV",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
            quota_cost=5,
        )(sample_tool_function)

        # ENTERPRISE tier tools
        registry.register(
            name="track_versions",
            description="Version tracking",
            category=ToolCategory.VERSION_TRACKING,
            required_tier="ENTERPRISE",
            quota_cost=10,
        )(sample_tool_function)

        return registry

    def test_free_user_sees_only_free_tools(self, populated_registry):
        """
        TEST: FREE tier user can only list FREE tier tools.

        PURPOSE: Enforce tier-based access control to prevent unauthorized tool access.

        VALIDATES:
        - list_available("FREE") returns only required_tier="FREE" tools
        - PRO and ENTERPRISE tools excluded
        - Tier hierarchy: FREE (0) cannot access PRO (1) or ENTERPRISE (2)

        EXPECTED: Returns 1 tool (count_words), excludes analyze_csv and track_versions.
        """
        tools = populated_registry.list_available(user_tier="FREE")
        assert len(tools) == 1
        assert tools[0].name == "count_words"

    def test_pro_user_sees_free_and_pro_tools(self, populated_registry):
        """
        TEST: PRO tier user can list FREE and PRO tier tools.

        PURPOSE: PRO users inherit access to FREE tools + get PRO-exclusive tools.

        VALIDATES:
        - list_available("PRO") returns required_tier in ["FREE", "PRO"]
        - ENTERPRISE tools excluded
        - Tier hierarchy: PRO (1) >= FREE (0), PRO (1) < ENTERPRISE (2)

        EXPECTED: Returns 2 tools (count_words, analyze_csv), excludes track_versions.
        """
        tools = populated_registry.list_available(user_tier="PRO")
        tool_names = {t.name for t in tools}
        assert len(tools) == 2
        assert tool_names == {"count_words", "analyze_csv"}

    def test_enterprise_user_sees_all_tools(self, populated_registry):
        """
        TEST: ENTERPRISE tier user can list all tools (FREE, PRO, ENTERPRISE).

        PURPOSE: ENTERPRISE users have full tool access, highest privilege level.

        VALIDATES:
        - list_available("ENTERPRISE") returns all registered tools
        - Tier hierarchy: ENTERPRISE (2) >= all other tiers
        - No tools excluded by tier check

        EXPECTED: Returns 3 tools (count_words, analyze_csv, track_versions).
        """
        tools = populated_registry.list_available(user_tier="ENTERPRISE")
        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert tool_names == {"count_words", "analyze_csv", "track_versions"}

    def test_filter_by_category(self, populated_registry):
        """
        TEST: Filter tools by category (DATA_ANALYSIS, UTILITY, etc).

        PURPOSE: Allow users to discover tools by functional category.

        VALIDATES:
        - list_available(category=ToolCategory.DATA_ANALYSIS) filters correctly
        - Combines tier check AND category check
        - PRO user with DATA_ANALYSIS filter sees only analyze_csv

        EXPECTED: Returns 1 tool (analyze_csv) matching PRO tier + DATA_ANALYSIS category.
        """
        tools = populated_registry.list_available(
            user_tier="PRO",
            category=ToolCategory.DATA_ANALYSIS,
        )
        assert len(tools) == 1
        assert tools[0].name == "analyze_csv"


class TestQuotaValidation:
    """Test quota-based tool execution validation."""

    @pytest.fixture
    def registry_with_costs(self, registry, sample_tool_function):
        """Registry with tools having different quota costs."""
        registry.register(
            name="cheap_tool",
            description="Low cost",
            category=ToolCategory.UTILITY,
            quota_cost=1,
        )(sample_tool_function)

        registry.register(
            name="expensive_tool",
            description="High cost",
            category=ToolCategory.DATA_ANALYSIS,
            required_tier="PRO",
            quota_cost=20,
        )(sample_tool_function)

        return registry

    def test_can_execute_with_sufficient_quota(self, registry_with_costs):
        """
        TEST: can_execute() returns True when user has enough quota.

        PURPOSE: Allow tool execution when quota requirements are met.

        VALIDATES:
        - can_execute("cheap_tool", "FREE", quota_remaining=10) returns (True, None)
        - Quota check: quota_remaining (10) >= quota_cost (1)
        - No error reason returned

        EXPECTED: Returns (True, None) indicating execution allowed.
        """
        can_run, reason = registry_with_costs.can_execute(
            tool_name="cheap_tool",
            user_tier="FREE",
            quota_remaining=10,
        )
        assert can_run is True
        assert reason is None

    def test_cannot_execute_with_insufficient_quota(self, registry_with_costs):
        """
        TEST: can_execute() returns False when user lacks quota.

        PURPOSE: Block tool execution to prevent over-usage.

        VALIDATES:
        - can_execute("expensive_tool", "PRO", quota_remaining=5) returns (False, reason)
        - Quota check: quota_remaining (5) < quota_cost (20)
        - Reason explains: "Insufficient quota (need 20, have 5)"

        EXPECTED: Returns (False, "Insufficient quota...") with clear error message.
        """
        can_run, reason = registry_with_costs.can_execute(
            tool_name="expensive_tool",
            user_tier="PRO",
            quota_remaining=5,
        )
        assert can_run is False
        assert "Insufficient quota" in reason
        assert "need 20" in reason
        assert "have 5" in reason

    def test_cannot_execute_wrong_tier(self, registry_with_costs):
        """
        TEST: can_execute() returns False when user tier too low.

        PURPOSE: Enforce tier-based access control at execution time.

        VALIDATES:
        - can_execute("expensive_tool", "FREE", quota_remaining=100) returns (False, reason)
        - Tier check: FREE (0) < PRO (1)
        - Reason explains: "Requires PRO tier (you have FREE)"

        EXPECTED: Returns (False, "Requires PRO tier...") even with sufficient quota.
        """
        can_run, reason = registry_with_costs.can_execute(
            tool_name="expensive_tool",
            user_tier="FREE",
            quota_remaining=100,
        )
        assert can_run is False
        assert "Requires PRO tier" in reason
        assert "you have FREE" in reason


class TestToolEnabling:
    """Test tool enabling/disabling functionality."""

    def test_disabled_tool_not_in_list_available(self, registry, sample_tool_function):
        """
        TEST: Disabled tools excluded from list_available().

        PURPOSE: Allow admins to disable tools without unregistering them.

        VALIDATES:
        - Tool registered with enabled=True initially
        - disable_tool() sets enabled=False
        - list_available() skips disabled tools
        - get_metadata() still returns metadata (tool exists, just disabled)

        EXPECTED: Disabled tool not in list_available(), but metadata still retrievable.
        """
        registry.register(
            name="disabled_tool",
            description="Will be disabled",
            category=ToolCategory.UTILITY,
        )(sample_tool_function)

        # Tool initially available
        tools = registry.list_available(user_tier="FREE")
        assert len(tools) == 1

        # Disable tool
        registry.disable_tool("disabled_tool")

        # Tool no longer in list_available()
        tools = registry.list_available(user_tier="FREE")
        assert len(tools) == 0

        # Metadata still exists
        metadata = registry.get_metadata("disabled_tool")
        assert metadata is not None
        assert metadata.enabled is False

    def test_enable_disabled_tool(self, registry, sample_tool_function):
        """
        TEST: enable_tool() makes disabled tool available again.

        PURPOSE: Allow toggling tool availability without re-registration.

        VALIDATES:
        - disable_tool() → enabled=False
        - enable_tool() → enabled=True
        - list_available() includes re-enabled tool

        EXPECTED: Tool reappears in list_available() after enable_tool().
        """
        registry.register(
            name="toggleable_tool",
            description="Can be toggled",
            category=ToolCategory.UTILITY,
        )(sample_tool_function)

        registry.disable_tool("toggleable_tool")
        registry.enable_tool("toggleable_tool")

        tools = registry.list_available(user_tier="FREE")
        assert len(tools) == 1
        assert tools[0].name == "toggleable_tool"


class TestGlobalRegistry:
    """Test global registry singleton pattern."""

    def test_get_tool_registry_returns_singleton(self):
        """
        TEST: get_tool_registry() returns same instance across calls.

        PURPOSE: Ensure single global registry shared across app.

        VALIDATES:
        - First get_tool_registry() creates _global_registry
        - Second get_tool_registry() returns same instance
        - id(registry1) == id(registry2) (same memory address)

        EXPECTED: Singleton pattern enforced, same registry instance returned.
        """
        reset_tool_registry()  # Start fresh

        registry1 = get_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is registry2

    def test_reset_tool_registry_clears_singleton(self):
        """
        TEST: reset_tool_registry() allows creating fresh registry.

        PURPOSE: Enable test isolation by resetting global state.

        VALIDATES:
        - get_tool_registry() creates registry1
        - reset_tool_registry() sets _global_registry = None
        - get_tool_registry() creates NEW registry2
        - id(registry1) != id(registry2) (different instances)

        EXPECTED: reset_tool_registry() clears singleton, next call creates fresh instance.
        """
        registry1 = get_tool_registry()
        reset_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is not registry2
