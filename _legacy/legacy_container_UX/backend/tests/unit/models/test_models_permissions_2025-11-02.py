"""
Unit tests for permission and tier limit calculations.

Tests business logic for tier-based access control in isolation.
"""

import pytest

from src.models.permissions import (
    Tier,
    can_use_tool,
    get_message_limit,
    get_quota_limit,
    get_session_limit,
    has_feature,
)

# ============================================================================
# Tier Limit Tests
# ============================================================================


class TestTierLimits:
    """Test tier limit calculations."""

    @pytest.mark.parametrize(
        "tier,expected_quota",
        [
            (Tier.FREE, 100),
            (Tier.PRO, 1000),
            (Tier.ENTERPRISE, 10000),
        ],
    )
    def test_quota_limits_by_tier(self, tier, expected_quota):
        """
        TEST: Validate tier-based daily quota allocation.

        PURPOSE: Ensure each subscription tier has correct daily quota limits to prevent
        over-usage and enforce business rules.

        VALIDATES:
        - FREE tier: 100 quota/day (10 AI agent requests with avg 10 quota cost)
        - PRO tier: 1000 quota/day (100 requests)
        - ENTERPRISE tier: 10000 quota/day (1000 requests)

        EXPECTED: get_quota_limit(tier) returns exact quota from TIER_LIMITS dict.
        """
        assert get_quota_limit(tier) == expected_quota

    @pytest.mark.parametrize(
        "tier,expected_sessions",
        [
            (Tier.FREE, 5),
            (Tier.PRO, 50),
            (Tier.ENTERPRISE, -1),  # Unlimited
        ],
    )
    def test_session_limits_by_tier(self, tier, expected_sessions):
        """
        TEST: Validate maximum concurrent active sessions per tier.

        PURPOSE: Enforce session creation limits to prevent resource exhaustion and
        ensure fair usage across tiers.

        VALIDATES:
        - FREE tier: 5 concurrent sessions (basic usage)
        - PRO tier: 50 concurrent sessions (professional usage)
        - ENTERPRISE tier: -1 (unlimited sessions)

        EXPECTED: get_session_limit(tier) returns max_sessions from TIER_LIMITS.
        """
        assert get_session_limit(tier) == expected_sessions

    @pytest.mark.parametrize(
        "tier,expected_messages",
        [
            (Tier.FREE, 20),  # Increased from 10 (Phase A audit fix - 2025-11-12)
            (Tier.PRO, 200),  # Increased from 100 (Phase A audit fix - 2025-11-12)
            (Tier.ENTERPRISE, 2000),  # Increased from 1000 (Phase A audit fix - 2025-11-12)
        ],
    )
    def test_message_limits_by_tier(self, tier, expected_messages):
        """
        TEST: Validate maximum messages per session for each tier.

        PURPOSE: Limit conversation depth to manage context window size and prevent
        unbounded session growth that impacts performance and costs.

        VALIDATES:
        - FREE tier: 20 messages/session (increased from 10 after Logfire analysis)
        - PRO tier: 200 messages/session (increased from 100 for better UX)
        - ENTERPRISE tier: 2000 messages/session (increased from 1000 for power users)

        REASON FOR INCREASE (2025-11-12 Phase A Audit):
        Logfire analysis showed 10+ users hitting FREE tier 10-message limit repeatedly.
        Frontend reduced chat history from 50→20 messages, so backend increased limits
        to match user expectations and improve UX.

        EXPECTED: get_message_limit(tier) returns message_limit from TIER_LIMITS.
        """
        assert get_message_limit(tier) == expected_messages


# ============================================================================
# Tool Permission Tests
# ============================================================================


class TestToolPermissions:
    """Test tier-based tool access."""

    def test_tool_filtering_delegated_to_registry(self):
        """
        TEST: Verify can_use_tool is deprecated and always returns True.

        PURPOSE: Document architectural shift where tool permission filtering moved
        from permissions.py to ToolRegistry for centralized tool access control.

        VALIDATES:
        - can_use_tool(any_tier, any_tool) always returns True (backward compatibility)
        - Tool filtering now handled in src/core/tool_registry.py via required_tier attribute
        - ToolRegistry.list_available(user_tier) performs actual filtering

        EXPECTED: All calls return True regardless of tier/tool combination.
        """
        # can_use_tool is deprecated - always returns True for backward compatibility
        # Real tool filtering happens in src/core/tool_registry.py via required_tier
        assert can_use_tool(Tier.FREE, "any_tool")
        assert can_use_tool(Tier.PRO, "any_tool")
        assert can_use_tool(Tier.ENTERPRISE, "any_tool")


# ============================================================================
# Feature Flag Tests
# ============================================================================


class TestFeatureFlags:
    """Test tier-based feature access."""

    @pytest.mark.parametrize(
        "tier,feature,expected",
        [
            (Tier.FREE, "agent_execution", True),
            (Tier.FREE, "advanced_analytics", False),
            (Tier.PRO, "advanced_analytics", True),
            (Tier.PRO, "streaming", True),
            (Tier.ENTERPRISE, "priority_support", True),
            (Tier.ENTERPRISE, "dedicated_support", True),
        ],
    )
    def test_feature_availability_by_tier(self, tier, feature, expected):
        """
        TEST: Validate feature flag gating by subscription tier.

        PURPOSE: Enforce feature access control to monetize advanced capabilities
        and prevent FREE tier users from accessing premium features.

        VALIDATES:
        - FREE: agent_execution (✓), advanced_analytics (✗)
        - PRO: advanced_analytics (✓), streaming (✓)
        - ENTERPRISE: priority_support (✓), dedicated_support (✓)

        EXPECTED: has_feature(tier, feature) matches TIER_LIMITS[tier]['features'][feature].
        """
        assert has_feature(tier, feature) == expected
