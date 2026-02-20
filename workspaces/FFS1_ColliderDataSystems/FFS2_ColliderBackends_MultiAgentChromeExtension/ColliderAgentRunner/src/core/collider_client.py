"""HTTP client for ColliderDataServer — bootstrap and tool execution."""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings


async def get_bootstrap(node_id: str, token: str) -> dict[str, Any]:
    """Fetch the OpenClaw bootstrap context for a node.

    Args:
        node_id: The Collider node UUID to bootstrap from.
        token: Valid Bearer JWT.

    Returns:
        OpenClawBootstrap JSON dict (agents_md, soul_md, tools_md,
        skills, tool_schemas, session_context, …).

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.data_server_url}/api/v1/openclaw/bootstrap/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    token: str,
) -> dict[str, Any]:
    """Execute a Collider tool via DataServer.

    Args:
        tool_name: The tool name as registered in the tool registry.
        params: Tool input parameters (must match the tool's params_schema).
        token: Valid Bearer JWT.

    Returns:
        Tool execution result JSON dict.

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.data_server_url}/execution/tool/{tool_name}",
            json=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]
