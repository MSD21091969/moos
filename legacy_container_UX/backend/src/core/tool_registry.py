"""Tool registry for managing available tools with metadata."""

from typing import Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class ToolCategory(str, Enum):
    """Tool categories for organization."""

    DATA_ANALYSIS = "data_analysis"
    MODEL_MAPPING = "model_mapping"
    VERSION_TRACKING = "version_tracking"
    EXPORT = "export"
    FIRESTORE = "firestore"
    FILESYSTEM = "filesystem"
    UTILITY = "utility"
    # E-T-L Pipeline Categories
    EXTRACT = "extract"  # Data source connectors (taps)
    TRANSFORM = "transform"  # Data processing (mappers)
    LOAD = "load"  # Data destination connectors (targets)


@dataclass
class ToolMetadata:
    """
    Metadata for a registered tool.

    Attributes:
        name: Tool identifier
        description: Brief description of what tool does
        category: Tool category for organization
        required_tier: Minimum tier needed to use tool (FREE/PRO/ENTERPRISE)
        quota_cost: Quota units consumed per execution
        enabled: Whether tool is currently available
        tags: Optional tags for discovery
        allowed_user_ids: ACL - specific users with access (empty = tier-based only)
        requires_admin: Whether tool requires admin privileges
    """

    name: str
    description: str
    category: ToolCategory
    required_tier: str  # "FREE", "PRO", or "ENTERPRISE"
    quota_cost: int = 1
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    # ACL fields
    allowed_user_ids: list[str] = field(default_factory=list)
    requires_admin: bool = False


class ToolRegistry:
    """
    Registry for managing available tools.

    Provides:
    - Tool registration with metadata
    - Permission-based discovery
    - Quota cost tracking
    - Tool enabling/disabling
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, ToolMetadata] = {}
        self._tool_functions: dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        required_tier: str = "FREE",
        quota_cost: int = 1,
        tags: Optional[list[str]] = None,
        allowed_user_ids: Optional[list[str]] = None,
        requires_admin: bool = False,
    ) -> Callable:
        """
        Register a tool with metadata.

        Args:
            name: Tool identifier
            description: What the tool does
            category: Tool category
            required_tier: Minimum tier needed ("FREE", "PRO", "ENTERPRISE")
            quota_cost: Quota units per execution
            tags: Optional tags for discovery
            allowed_user_ids: ACL - specific users with access
            requires_admin: Whether tool requires admin privileges

        Returns:
            Decorator function

        Example:
            >>> @registry.register(
            ...     name="analyze_csv",
            ...     description="Analyze CSV file",
            ...     category=ToolCategory.DATA_ANALYSIS,
            ...     required_tier="PRO",
            ...     quota_cost=5
            ... )
            ... async def analyze_csv(file_path: str):
            ...     ...
        """

        def decorator(func: Callable) -> Callable:
            metadata = ToolMetadata(
                name=name,
                description=description,
                category=category,
                required_tier=required_tier,
                quota_cost=quota_cost,
                tags=tags or [],
                allowed_user_ids=allowed_user_ids or [],
                requires_admin=requires_admin,
            )

            self._tools[name] = metadata
            self._tool_functions[name] = func

            return func

        return decorator

    def get_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.

        Args:
            tool_name: Tool identifier

        Returns:
            ToolMetadata or None if not found
        """
        return self._tools.get(tool_name)

    def get_function(self, tool_name: str) -> Optional[Callable]:
        """
        Get function for a tool.

        Args:
            tool_name: Tool identifier

        Returns:
            Tool function or None if not found
        """
        return self._tool_functions.get(tool_name)

    def list_available(
        self,
        user_tier: str,
        category: Optional[ToolCategory] = None,
        user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> list[ToolMetadata]:
        """
        List tools available to a user based on tier and ACL.

        Args:
            user_tier: User's subscription tier ("FREE", "PRO", "ENTERPRISE")
            category: Optional category filter
            user_id: User identifier (for ACL checks)
            is_admin: Whether user is admin (bypasses all restrictions)

        Returns:
            List of available tool metadata

        Example:
            >>> tools = registry.list_available(
            ...     user_tier="PRO",
            ...     category=ToolCategory.DATA_ANALYSIS,
            ...     user_id="user_123"
            ... )
        """
        available = []
        tier_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        user_tier_level = tier_hierarchy.get(user_tier.upper(), 0)

        for tool in self._tools.values():
            # Skip disabled tools
            if not tool.enabled:
                continue

            # Filter by category if specified
            if category and tool.category != category:
                continue

            # Admin bypass
            if is_admin:
                available.append(tool)
                continue

            # Check if admin required
            if tool.requires_admin:
                continue

            # Check ACL (if specified)
            if tool.allowed_user_ids:
                if user_id and user_id in tool.allowed_user_ids:
                    available.append(tool)
                continue

            # Check tier access
            tool_tier_level = tier_hierarchy.get(tool.required_tier.upper(), 0)
            if user_tier_level >= tool_tier_level:
                available.append(tool)

        return available

    def can_execute(
        self,
        tool_name: str,
        user_tier: str,
        quota_remaining: int,
        user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can execute a tool.

        Args:
            tool_name: Tool to check
            user_tier: User's subscription tier
            quota_remaining: User's remaining quota
            user_id: User identifier (for ACL)
            is_admin: Whether user is admin

        Returns:
            (can_execute: bool, reason: Optional[str])

        Example:
            >>> can_run, reason = registry.can_execute(
            ...     "analyze_csv",
            ...     user_tier="PRO",
            ...     quota_remaining=10,
            ...     user_id="user_123"
            ... )
            >>> if not can_run:
            ...     print(f"Cannot run: {reason}")
        """
        metadata = self.get_metadata(tool_name)

        if not metadata:
            return False, f"Tool '{tool_name}' not found"

        if not metadata.enabled:
            return False, f"Tool '{tool_name}' is disabled"

        # Admin bypass
        if is_admin:
            # Still check quota
            if quota_remaining < metadata.quota_cost:
                return (
                    False,
                    f"Insufficient quota (need {metadata.quota_cost}, have {quota_remaining})",
                )
            return True, None

        # Check if admin required
        if metadata.requires_admin:
            return False, "Admin privileges required"

        # Check ACL (if specified)
        if metadata.allowed_user_ids:
            if not user_id or user_id not in metadata.allowed_user_ids:
                return False, "Not authorized to use this tool"
            # Still check quota and tier
        else:
            # Check tier access
            tier_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
            user_tier_level = tier_hierarchy.get(user_tier.upper(), 0)
            tool_tier_level = tier_hierarchy.get(metadata.required_tier.upper(), 0)

            if user_tier_level < tool_tier_level:
                return False, f"Requires {metadata.required_tier} tier (you have {user_tier})"

        if quota_remaining < metadata.quota_cost:
            return False, f"Insufficient quota (need {metadata.quota_cost}, have {quota_remaining})"

        return True, None

    def enable_tool(self, tool_name: str):
        """Enable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = True

    def disable_tool(self, tool_name: str):
        """Disable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = False

    def get_all_categories(self) -> list[ToolCategory]:
        """Get list of all categories with registered tools."""
        categories = set()
        for tool in self._tools.values():
            categories.add(tool.category)
        return sorted(categories, key=lambda c: c.value)

    def search_by_tag(self, tag: str) -> list[ToolMetadata]:
        """
        Search tools by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of tools with matching tag
        """
        return [tool for tool in self._tools.values() if tag in tool.tags and tool.enabled]


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def reset_tool_registry():
    """Reset global registry (for testing)."""
    global _global_registry
    _global_registry = None
