"""Tool management API endpoints.

Handles:
- List available tools (filtered by tier)
- Get tool details
- Tool discovery/search
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from src.api.dependencies import get_user_context
from src.api.models import ToolListResponse, ToolInfo as APIToolInfo
from src.models.context import UserContext
from src.services.tool_service import ToolService
from src.core.exceptions import ToolNotFoundError, PermissionDeniedError
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["Tools"])


def get_tool_service() -> ToolService:
    """Get tool service instance."""
    return ToolService()


@router.get("/available", response_model=ToolListResponse)
async def list_available_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search tool names/descriptions"),
    user_ctx: UserContext = Depends(get_user_context),
    tool_service: ToolService = Depends(get_tool_service),
):
    """List tools available to the current user based on their tier."""
    try:
        # Get tools via service layer (handles tier filtering)
        tool_infos = await tool_service.list_available_tools(
            user_ctx=user_ctx, category=category, search=search
        )

        # Convert service ToolInfo to API ToolInfo
        api_tools = [
            APIToolInfo(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
                quota_cost=t.quota_cost,
                required_tier=t.required_tier,
                category=t.category,
                enabled=t.enabled,
                tags=t.tags,
            )
            for t in tool_infos
        ]

        return ToolListResponse(tools=api_tools, count=len(api_tools))

    except Exception as e:
        logger.error("Failed to list tools", extra={"error": str(e)}, exc_info=True)
        return ToolListResponse(tools=[], count=0)


@router.get("/{tool_name}")
async def get_tool_details(
    tool_name: str,
    user_ctx: UserContext = Depends(get_user_context),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Get detailed information about a specific tool.

    **Use Case**:
    - User clicks on tool to see details
    - Frontend displays tool documentation
    """
    try:
        # Get tool via service layer (handles permission check)
        tool_info = await tool_service.get_tool_details(user_ctx=user_ctx, tool_name=tool_name)

        return APIToolInfo(
            name=tool_info.name,
            description=tool_info.description,
            parameters=tool_info.parameters,
            required_tier=tool_info.required_tier,
            quota_cost=tool_info.quota_cost,
            category=tool_info.category,
            enabled=tool_info.enabled,
            tags=tool_info.tags,
        )

    except ToolNotFoundError as e:
        logger.warning("Tool not found", extra={"tool_name": tool_name})
        raise HTTPException(status_code=404, detail=str(e))

    except PermissionDeniedError as e:
        logger.warning("Tier denied for tool", extra={"tool_name": tool_name, "error": str(e)})
        raise HTTPException(status_code=403, detail=str(e))

    except Exception as e:
        logger.error("Failed to get tool details", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
