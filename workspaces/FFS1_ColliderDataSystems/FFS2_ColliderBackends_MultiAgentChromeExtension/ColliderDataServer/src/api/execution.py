"""API endpoints for executing workflows and individual tools."""

import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.db.models import User

router = APIRouter(prefix="/execution", tags=["execution"])
logger = logging.getLogger(__name__)


@router.post("/workflow/{workflow_name}", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_name: str,
    inputs: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a workflow by name."""

    # TODO: Check permissions?
    # For now, any auth'd user can execute any workflow they can see.
    # The GraphToolServer handles visibility checks (in theory), or we should check here?
    # Discovery checks visibility. Execution might need separate checks.
    # We pass the user_id to GraphToolServer, so it can check ownership/visibility if needed.

    client = GraphToolClient()
    try:
        response = await client.execute_subgraph(
            workflow_name=workflow_name, user_id=str(current_user.id), inputs=inputs
        )

        if not response["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.get("error_message", "Execution failed"),
            )

        return response["result"]

    finally:
        await client.close()


@router.post("/tool/{tool_name}", response_model=Dict[str, Any])
async def execute_tool(
    tool_name: str,
    inputs: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a registered tool by name via GraphToolServer REST API."""
    import httpx

    graph_tool_url = os.environ.get(
        "GRAPHTOOL_SERVER_URL", "http://localhost:8005"
    ).rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{graph_tool_url}/api/v1/registry/tools/{tool_name}/execute",
                json=inputs,
                timeout=30.0,
            )
            response = resp.json()
    except Exception as e:
        logger.exception(f"GraphToolServer request failed for tool '{tool_name}'")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GraphToolServer unreachable: {e}",
        )

    if not response.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' failed: {response.get('error_message', 'unknown')}",
        )

    return response.get("result", {})
