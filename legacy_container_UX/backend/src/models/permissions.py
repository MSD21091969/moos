"""Permission and tier management."""

from enum import Enum
from typing import Any, TypedDict


class Tier(str, Enum):
    """User subscription tier."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TierLimits(TypedDict):
    """Limits for a tier."""

    quota_daily: int
    max_sessions: int
    message_limit: int
    allowed_tools: list[str]
    features: dict[str, bool]


# Tier-based limits keyed by tier value for compatibility with TypedDict lookups
TIER_LIMITS: dict[str, TierLimits] = {
    Tier.FREE.value: {
        "quota_daily": 100,
        "max_sessions": 5,
        "message_limit": 20,  # Increased from 10
        "allowed_tools": [],  # System tools filtered by tier in tool_registry
        "features": {
            "agent_execution": True,
            "session_management": True,
            "tool_discovery": True,
            "advanced_analytics": False,
            "export_excel": False,
            "streaming": False,
            "custom_tools": False,
            "custom_agents": False,
        },
    },
    Tier.PRO.value: {
        "quota_daily": 1000,
        "max_sessions": 50,
        "message_limit": 200,  # Increased from 100
        "allowed_tools": [],  # System tools filtered by tier in tool_registry
        "features": {
            "agent_execution": True,
            "session_management": True,
            "tool_discovery": True,
            "advanced_analytics": True,
            "export_excel": True,
            "streaming": True,
            "custom_tools": True,
            "custom_agents": True,
        },
    },
    Tier.ENTERPRISE.value: {
        "quota_daily": 10000,
        "max_sessions": -1,  # Unlimited
        "message_limit": 2000,  # Increased from 1000
        "allowed_tools": [],  # System tools filtered by tier in tool_registry
        "features": {
            "agent_execution": True,
            "session_management": True,
            "tool_discovery": True,
            "advanced_analytics": True,
            "export_excel": True,
            "streaming": True,
            "custom_tools": True,
            "custom_agents": True,
            "priority_support": True,
            "dedicated_support": True,
        },
    },
}


def get_tier_limit(tier: Tier, limit_key: str) -> Any:
    """
    Get limit value for a tier.

    Args:
        tier: User's subscription tier
        limit_key: Limit to retrieve (quota_daily, max_sessions, etc.)

    Returns:
        Limit value

    Raises:
        KeyError: If limit_key doesn't exist
    """
    limits = TIER_LIMITS[tier.value]
    return limits[limit_key]  # type: ignore


def can_use_tool(tier: Tier, tool_name: str) -> bool:
    """
    Check if tier can use a specific tool.

    NOTE: Tool access is now managed by the tool_registry via required_tier.
    This function is deprecated and kept for backward compatibility.
    Use ToolRegistry.list_available(user_tier) instead.

    Args:
        tier: User's subscription tier
        tool_name: Name of tool to check

    Returns:
        True (tools are filtered by tier in tool_registry, not here)
    """
    # Tool filtering is handled by tool_registry.py based on required_tier
    # This always returns True for backward compatibility
    return True


def has_feature(tier: Tier, feature: str) -> bool:
    """
    Check if tier has access to a feature.

    Args:
        tier: User's subscription tier
        feature: Feature name to check

    Returns:
        True if tier has feature access
    """
    features = TIER_LIMITS[tier.value]["features"]
    return bool(features.get(feature, False))


def get_quota_limit(tier: Tier) -> int:
    """Get daily quota limit for tier."""
    return int(TIER_LIMITS[tier.value]["quota_daily"])


def get_session_limit(tier: Tier) -> int:
    """Get max sessions limit for tier (-1 = unlimited)."""
    return int(TIER_LIMITS[tier.value]["max_sessions"])


def get_message_limit(tier: Tier) -> int:
    """Get maximum messages per session for tier."""
    return {
        Tier.FREE: 20,  # Increased from 10 to match frontend chat limit
        Tier.PRO: 200,  # Increased from 100 for better UX
        Tier.ENTERPRISE: 2000,  # Increased from 1000 for power users
    }[tier]
