"""API endpoints for executing workflows and individual tools."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.core.grpc_client import GraphToolClient
from src.db.models import User

router = APIRouter(prefix="/execution", tags=["execution"])


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
            workflow_name=workflow_name,
            user_id=str(current_user.id),
            inputs=inputs
        )
        
        if not response["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.get("error_message", "Execution failed")
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
    """Execute a single registered tool by name.

    Calls the GraphToolServer ``ExecuteTool`` RPC directly, bypassing any
    workflow wrapper.  The tool must be registered in the GraphToolServer's
    in-memory registry (via ``POST /api/v1/registry/tools`` or via a
    NodeContainer seed that triggers ``register_tool``).

    This endpoint is referenced in the OpenClaw bootstrap response as the
    ``execute_tool_schema`` function definition, enabling OpenClaw agents to
    invoke individual Collider tools via function calling.
    """
    client = GraphToolClient()
    try:
        response = await client.execute_tool(
            tool_name=tool_name,
            user_id=str(current_user.id),
            inputs=inputs,
        )

        if not response["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.get("error_message", "Tool execution failed"),
            )

        return response["result"]

    finally:
        await client.close()
