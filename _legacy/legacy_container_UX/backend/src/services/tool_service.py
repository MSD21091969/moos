"""Tool discovery and management service."""

import inspect
from typing import Any, Dict, List, Optional, get_type_hints

from src.core.exceptions import PermissionDeniedError, ToolNotFoundError
from src.core.logging import get_logger
from src.core.tool_registry import (
    ToolCategory,
    ToolMetadata,
    ToolRegistry,
    get_tool_registry,
)
from src.models.context import UserContext, ToolDefinition
from src.models.permissions import Tier

logger = get_logger(__name__)


class ToolInfo:
    """Tool information for API responses."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required_tier: str,
        quota_cost: int,
        category: str,
        enabled: bool,
        tags: List[str],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.required_tier = required_tier
        self.quota_cost = quota_cost
        self.category = category
        self.enabled = enabled
        self.tags = tags


class ToolService:
    """Service for tool discovery and access control.

    Responsibilities:
    - Permission-based tool filtering
    - Tool discovery by category/search
    - Tool metadata extraction
    - Access validation
    - User-global and session-local tool loading
    """

    def __init__(self, firestore_client=None):
        """Initialize tool service."""
        self.registry: ToolRegistry = get_tool_registry()
        self.firestore = firestore_client

    async def list_available_tools(
        self,
        user_ctx: UserContext,
        category: Optional[str] = None,
        search: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[ToolInfo]:
        """
        List tools available to user, merging system, user-global, and session-local tools.

        Args:
            user_ctx: User context with permissions
            category: Optional category filter
            search: Optional search term (name/description)
            session_id: Optional session ID for session-local tools

        Returns:
            List of ToolInfo objects user can access
        """
        logger.info(
            "Listing merged tools",
            extra={
                "user_id": user_ctx.user_id,
                "tier": user_ctx.tier.value if isinstance(user_ctx.tier, Tier) else user_ctx.tier,
                "category": category,
                "search": search,
                "session_id": session_id,
            },
        )

        # Build merged toolset (session-local > user-global > system)
        merged_toolset = await self.build_merged_toolset(
            user_ctx=user_ctx,
            session_id=session_id,
            category=category,
            search=search,
        )

        # Convert merged toolset to ToolInfo list
        tool_infos: List[ToolInfo] = []
        tool_entries: Dict[str, Dict[str, Any]] = merged_toolset["tools"]

        for tool_data in tool_entries.values():
            parameters: Dict[str, Any] = {}
            if tool_data.get("source") == "system":
                func = self.registry.get_function(tool_data["name"])
                if func:
                    parameters = self._extract_parameters(func)

            tool_infos.append(
                ToolInfo(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    parameters=parameters,
                    required_tier=str(tool_data.get("required_tier", "FREE")),
                    quota_cost=int(tool_data["quota_cost"]),
                    category=str(tool_data["category"]),
                    enabled=bool(tool_data.get("enabled", True)),
                    tags=list(tool_data.get("tags", [])),
                )
            )

        logger.info("Merged tool listing complete", extra={"count": len(tool_infos)})
        return tool_infos

    async def get_tool_details(self, user_ctx: UserContext, tool_name: str) -> ToolInfo:
        """
        Get detailed information about a specific tool.

        Args:
            user_ctx: User context with permissions
            tool_name: Tool identifier

        Returns:
            ToolInfo with tool details

        Raises:
            ToolNotFoundError: If tool doesn't exist
            PermissionDeniedError: If user lacks permission
        """
        # Get tool metadata
        metadata = self.registry.get_metadata(tool_name)
        if not metadata:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        # Check access
        if not self._tier_can_access(user_ctx.tier, metadata.required_tier):
            raise PermissionDeniedError(
                f"Tier '{self._tier_value(user_ctx.tier)}' cannot access '{tool_name}'"
            )

        return self._metadata_to_info(metadata)

    def _metadata_to_info(self, metadata: ToolMetadata) -> ToolInfo:
        """Convert ToolMetadata to ToolInfo with parameter extraction."""
        # Get function from registry to extract parameters
        func = self.registry.get_function(metadata.name)
        parameters = self._extract_parameters(func) if func else {}

        return ToolInfo(
            name=metadata.name,
            description=metadata.description,
            parameters=parameters,
            required_tier=metadata.required_tier,
            quota_cost=metadata.quota_cost,
            category=metadata.category.value,
            enabled=metadata.enabled,
            tags=list(metadata.tags),
        )

    def _extract_parameters(self, func: Any) -> Dict[str, Any]:
        """
        Extract parameter information from function signature.

        Args:
            func: Function to inspect

        Returns:
            Dictionary mapping parameter names to type information
        """
        try:
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)

            parameters = {}
            for param_name, param in sig.parameters.items():
                # Skip self, ctx, session_ctx parameters
                if param_name in ("self", "ctx", "session_ctx"):
                    continue

                param_info = {"required": param.default == inspect.Parameter.empty}

                # Add type information if available
                if param_name in type_hints:
                    param_type = type_hints[param_name]
                    param_info["type"] = str(param_type).replace("typing.", "")

                # Add default value if present
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default

                parameters[param_name] = param_info

            return parameters
        except Exception as e:
            logger.warning(
                "Failed to extract parameters from function",
                extra={"function": str(func), "error": str(e)},
            )
            return {}

    def _tier_can_access(self, user_tier: Tier | str, required_tier: str) -> bool:
        """Return True when user's tier meets tool requirement."""

        tier_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        user_level = tier_hierarchy.get(self._tier_value(user_tier).upper(), 0)
        required_level = tier_hierarchy.get(required_tier.upper(), 0)
        return user_level >= required_level

    @staticmethod
    def _tier_value(tier: Tier | str) -> str:
        """Normalize tier enum or string to its lowercase string value."""

        if isinstance(tier, Tier):
            return tier.value
        return str(tier)

    async def get_tools_by_category(self, user_ctx: UserContext) -> Dict[str, List[ToolInfo]]:
        """
        Get tools grouped by category.

        Args:
            user_ctx: User context

        Returns:
            Dictionary mapping category to list of tools
        """
        tools = await self.list_available_tools(user_ctx)

        by_category: Dict[str, List[ToolInfo]] = {}
        for tool in tools:
            if tool.category not in by_category:
                by_category[tool.category] = []
            by_category[tool.category].append(tool)

        return by_category

    async def load_user_global_tools(self, user_id: str) -> List[ToolDefinition]:
        """
        Load user's global tools from Firestore.

        Args:
            user_id: User identifier

        Returns:
            List of user's global tool definitions
        """
        if not self.firestore:
            return []

        try:
            tools_ref = self.firestore.collection("users").document(user_id).collection("tools")
            docs = tools_ref.stream()

            tools: List[ToolDefinition] = []
            for doc in docs:
                tool_data = doc.to_dict()
                tool_data["tool_id"] = doc.id
                tools.append(ToolDefinition(**tool_data))

            logger.info(
                "Loaded global tools for user", extra={"tool_count": len(tools), "user_id": user_id}
            )
            return tools
        except Exception as e:
            logger.warning(
                "Failed to load user global tools", extra={"user_id": user_id, "error": str(e)}
            )
            return []

    async def load_session_local_tools(self, user_id: str, session_id: str) -> List[ToolDefinition]:
        """
        Load session-local tools from Firestore.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            List of session-local tool definitions
        """
        if not self.firestore:
            return []

        try:
            tools_ref = (
                self.firestore.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
                .collection("tools")
            )
            docs = tools_ref.stream()

            tools: List[ToolDefinition] = []
            for doc in docs:
                tool_data = doc.to_dict()
                tool_data["tool_id"] = doc.id
                tools.append(ToolDefinition(**tool_data))

            logger.info(
                "Loaded session-local tools",
                extra={"tool_count": len(tools), "session_id": session_id},
            )
            return tools
        except Exception as e:
            logger.warning(
                "Failed to load session-local tools",
                extra={"session_id": session_id, "error": str(e)},
            )
            return []

    async def build_merged_toolset(
        self,
        user_ctx: UserContext,
        session_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """
        Build a merged toolset combining:
        1. Global tier-tools (system tools)
        2. User-global tools
        3. Session-local tools (if session_id provided)

        Args:
            user_ctx: User context with permissions and tier
            session_id: Optional session ID for session-local tools
            category: Optional category filter
            search: Optional search term

        Returns:
            Dictionary with merged tool metadata
        """
        tools: Dict[str, Dict[str, Any]] = {}

        # 1. Add system (tier-based) tools
        system_tools = self.registry.list_available(
            user_tier=self._tier_value(user_ctx.tier),
            category=ToolCategory(category) if category else None,
        )

        for metadata in system_tools:
            tools[metadata.name] = {
                "name": metadata.name,
                "description": metadata.description,
                "category": metadata.category.value,
                "quota_cost": metadata.quota_cost,
                "tags": list(metadata.tags),
                "source": "system",
                "required_tier": metadata.required_tier,
                "enabled": metadata.enabled,
            }

        # 2. Add user-global tools
        user_global_tools = await self.load_user_global_tools(user_ctx.user_id)
        for tool_def in user_global_tools:
            tools[tool_def.tool_id] = {
                "name": tool_def.name,
                "description": tool_def.description,
                "category": tool_def.category,
                "quota_cost": tool_def.quota_cost,
                "tags": list(tool_def.tags),
                "source": "user_global",
                "required_tier": tool_def.definition.get("required_tier", "FREE")
                if isinstance(tool_def.definition, dict)
                else "FREE",
                "enabled": tool_def.enabled,
            }

        # 3. Add session-local tools
        if session_id:
            session_tools = await self.load_session_local_tools(user_ctx.user_id, session_id)
            for tool_def in session_tools:
                tools[tool_def.tool_id] = {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "category": tool_def.category,
                    "quota_cost": tool_def.quota_cost,
                    "tags": list(tool_def.tags),
                    "source": "session_local",
                    "required_tier": tool_def.definition.get("required_tier", "FREE")
                    if isinstance(tool_def.definition, dict)
                    else "FREE",
                    "enabled": tool_def.enabled,
                }

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered_tools = {}
            for k, v in tools.items():
                name = str(v.get("name", "")).lower()
                description = str(v.get("description", "")).lower()
                tags = v.get("tags", [])
                if isinstance(tags, list):
                    tag_matches = any(search_lower in str(tag).lower() for tag in tags)
                else:
                    tag_matches = search_lower in str(tags).lower()

                if search_lower in name or search_lower in description or tag_matches:
                    filtered_tools[k] = v
            tools = filtered_tools

        logger.info(
            "Built merged toolset for user",
            extra={"tool_count": len(tools), "user_id": user_ctx.user_id},
        )
        return {"tools": tools, "count": len(tools)}

    async def list_tools(self, tier: Tier) -> List[ToolInfo]:
        """
        List all available tools for tier (simplified version).

        Args:
            tier: User subscription tier

        Returns:
            List of ToolInfo objects

        Note:
            This is a simplified version of list_available_tools
            that doesn't require full UserContext.
        """
        from src.models.context import UserContext

        # Create minimal UserContext for tier
        user_ctx = UserContext(
            user_id="system",
            email="system@system.com",
            permissions=tuple(),
            quota_remaining=0,
            tier=tier,
        )

        return await self.list_available_tools(user_ctx)

    async def execute_tool(self, tool_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single tool by ID with parameters.

        Args:
            tool_id: Tool identifier
            params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolNotFoundError: Tool doesn't exist
            ValidationError: Invalid parameters
            ToolExecutionError: Execution failed
        """
        from src.core.exceptions import ToolExecutionError, ValidationError

        # Get tool function from registry
        func = self.registry.get_function(tool_id)
        if not func:
            raise ToolNotFoundError(f"Tool '{tool_id}' not found in registry")

        # Get tool metadata
        metadata = self.registry.get_metadata(tool_id)
        if not metadata or not metadata.enabled:
            raise ValidationError(f"Tool '{tool_id}' is not enabled")

        try:
            # Execute tool function
            logger.info("Executing tool with params", extra={"tool_id": tool_id, "params": params})

            # Call function with params
            result = await func(**params) if inspect.iscoroutinefunction(func) else func(**params)

            logger.info("Tool executed successfully", extra={"tool_id": tool_id})

            return {
                "tool_id": tool_id,
                "success": True,
                "result": result,
                "quota_cost": metadata.quota_cost,
            }

        except TypeError as e:
            # Parameter validation error
            raise ValidationError(f"Invalid parameters for tool '{tool_id}': {str(e)}")
        except Exception as e:
            # Tool execution error
            logger.error("Tool execution failed", extra={"tool_id": tool_id, "error": str(e)})
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
