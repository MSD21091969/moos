"""Resource discovery API routes.

Handles listing available tools and agents based on user tier and ACL.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.api.dependencies import get_user_context
from src.api.models import ErrorResponse
from src.models.context import UserContext
from src.core.tool_registry import get_tool_registry
from src.core.agent_registry import get_agent_registry
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/resources", tags=["Resource Discovery"])


# ============================================================================
# Tool Discovery
# ============================================================================


@router.get(
    "/tools",
    response_model=List[dict],
    summary="List available tools",
    description="List all tools available to the user based on tier and ACL",
)
async def list_available_tools(
    user_ctx: UserContext = Depends(get_user_context),
    category: str | None = None,
):
    """
    List tools available to current user.

    Filters based on:
    - User tier (FREE/PRO/ENTERPRISE)
    - User-specific ACL (allowed_user_ids)
    - Admin privileges

    **Authentication Required**: Yes

    **Query Parameters**:
    - category: Filter by tool category (optional)

    **Returns**: List of tool metadata objects
    """
    try:
        tool_registry = get_tool_registry()

        # Determine if user is admin (simple check - enhance as needed)
        is_admin = "admin" in user_ctx.permissions

        # List available tools
        from src.core.tool_registry import ToolCategory

        category_filter = None
        if category:
            try:
                category_filter = ToolCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        tools = tool_registry.list_available(
            user_tier=user_ctx.tier,
            category=category_filter,
            user_id=user_ctx.user_id,
            is_admin=is_admin,
        )

        # Convert to dict for JSON response
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "required_tier": tool.required_tier,
                "quota_cost": tool.quota_cost,
                "enabled": tool.enabled,
                "tags": tool.tags,
                "requires_admin": tool.requires_admin,
            }
            for tool in tools
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list tools", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get(
    "/tools/{tool_name}",
    response_model=dict,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Tool not found"},
    },
    summary="Get tool details",
)
async def get_tool_details(
    tool_name: str,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Get details for a specific tool.

    Validates user has access to the tool.

    **Authentication Required**: Yes
    """
    try:
        tool_registry = get_tool_registry()

        # Get tool metadata
        tool = tool_registry.get_metadata(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Check if user can access this tool
        is_admin = "admin" in user_ctx.permissions
        can_execute, reason = tool_registry.can_execute(
            tool_name=tool_name,
            user_tier=user_ctx.tier,
            quota_remaining=user_ctx.quota_remaining,
            user_id=user_ctx.user_id,
            is_admin=is_admin,
        )

        if not can_execute and not tool.enabled:
            # Tool exists but is disabled - still return 404
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        if not can_execute:
            raise HTTPException(status_code=403, detail=reason or "Access denied")

        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "required_tier": tool.required_tier,
            "quota_cost": tool.quota_cost,
            "enabled": tool.enabled,
            "tags": tool.tags,
            "requires_admin": tool.requires_admin,
            "can_execute": can_execute,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get tool details", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tool details: {str(e)}")


# ============================================================================
# Agent Discovery
# ============================================================================


@router.get(
    "/agents",
    response_model=List[dict],
    summary="List available agents",
    description="List all agents available to the user (system + user-global + session-local)",
)
async def list_available_agents(
    user_ctx: UserContext = Depends(get_user_context),
    session_id: str | None = None,
    search: str | None = None,
):
    """
    List agents available to current user.

    Merges agents from three sources (session-local overrides user-global overrides system):
    - System agents (from AgentRegistry, filtered by tier/ACL)
    - User-global agents (from /users/{uid}/agents/)
    - Session-local agents (from /users/{uid}/sessions/{sid}/agents/ if session_id provided)

    **Authentication Required**: Yes

    **Query Parameters**:
    - session_id: Optional session ID to include session-local agents
    - search: Optional search term (filters by name/description/tags)

    **Returns**: List of agent metadata objects with source annotation
    """
    try:
        from src.services.agent_service import AgentService
        from src.core.container import get_container

        # Get firestore client from container
        container = get_container()
        agent_service = AgentService(firestore_client=container.firestore_client)

        # Build merged agentset
        merged = await agent_service.build_merged_agentset(
            user_ctx=user_ctx,
            session_id=session_id,
            search=search,
        )

        # Convert to list for JSON response
        agent_list = list(merged["agents"].values())

        return agent_list

    except Exception as e:
        logger.error("Failed to list agents", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get(
    "/agents/{agent_id}",
    response_model=dict,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Agent not found"},
    },
    summary="Get agent details",
)
async def get_agent_details(
    agent_id: str,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Get details for a specific agent.

    Validates user has access to the agent.

    **Authentication Required**: Yes
    """
    try:
        agent_registry = get_agent_registry()

        # Get agent metadata
        agent = agent_registry.get_metadata(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        # Check if user can access this agent
        is_admin = "admin" in user_ctx.permissions
        can_execute, reason = agent_registry.can_execute(
            agent_id=agent_id,
            user_tier=user_ctx.tier,
            user_id=user_ctx.user_id,
            is_admin=is_admin,
        )

        if not can_execute and not agent.enabled:
            # Agent exists but is disabled - still return 404
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        if not can_execute:
            raise HTTPException(status_code=403, detail=reason or "Access denied")

        return {
            "agent_id": str(agent.agent_id),
            "name": str(agent.name),
            "description": str(agent.description),
            "required_tier": str(agent.required_tier),
            "quota_cost_multiplier": float(agent.quota_cost_multiplier),
            "enabled": bool(agent.enabled),
            "tags": list(agent.tags) if agent.tags else [],
            "requires_admin": bool(agent.requires_admin),
            "default_model": str(agent.default_model) if agent.default_model else None,
            "system_prompt": str(agent.system_prompt) if agent.system_prompt else None,
            "can_execute": bool(can_execute),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent details", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}")
