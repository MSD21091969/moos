"""HTTP client for ColliderDataServer — bootstrap and tool execution."""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings


async def get_bootstrap(
    node_id: str,
    token: str,
    depth: int | None = None,
) -> dict[str, Any]:
    """Fetch the agent bootstrap context for a node.

    Args:
        node_id: The Collider node UUID to bootstrap from.
        token: Valid Bearer JWT.
        depth: Optional subtree depth limit passed to the bootstrap endpoint.
            ``None`` means full subtree (default).

    Returns:
        AgentBootstrap JSON dict (agents_md, soul_md, tools_md,
        skills, tool_schemas, session_context, …).

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
    """
    params = {}
    if depth is not None:
        params["depth"] = depth

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.data_server_url}/api/v1/agent/bootstrap/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def get_node_ancestors(
    app_id: str,
    node_id: str,
    token: str,
) -> list[dict[str, Any]]:
    """Return ancestor nodes of a node in root-to-leaf order.

    Calls ``GET /api/v1/apps/{app_id}/nodes/{node_id}/ancestors``.

    Args:
        app_id: The Collider application UUID.
        node_id: The target node UUID whose ancestors to fetch.
        token: Valid Bearer JWT.

    Returns:
        List of NodeResponse dicts, sorted root-first (shortest path first).
        Returns an empty list if the node is a root or the endpoint fails.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.data_server_url}/api/v1/apps/{app_id}/nodes/{node_id}/ancestors",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def get_app(app_id: str, token: str) -> dict[str, Any]:
    """Fetch application details including root_node_id.

    Args:
        app_id: The Collider application UUID.
        token: Valid Bearer JWT.

    Returns:
        ApplicationResponse JSON dict (id, display_name, root_node_id, …).

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.data_server_url}/api/v1/apps/{app_id}",
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
