"""REST client for GraphToolServer tool discovery endpoint."""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings

_DISCOVER_PATH = "/api/v1/registry/tools/discover"


async def discover_tools(
    query: str,
    visibility_filter: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """POST {graph_tool_url}/api/v1/registry/tools/discover → tool_schema dicts.

    Calls the GraphToolServer registry discover endpoint (ToolQuery schema).
    Returns a list of OpenClawToolSchema-compatible dicts ready to be merged
    into the agent's tool set.

    Args:
        query: Free-text or semantic search string.
        visibility_filter: Visibility levels to include (default: global + group).
        limit: Maximum number of tools to return.

    Returns:
        List of tool schema dicts, each with ``{type, function: {name, description, parameters}}``.
        Empty list if GraphToolServer is unavailable.
    """
    if visibility_filter is None:
        visibility_filter = ["global", "group"]

    payload = {
        "query": query,
        "visibility_filter": visibility_filter,
        "limit": limit,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.graph_tool_url}{_DISCOVER_PATH}",
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException):
        # GraphToolServer may not be running; silently return empty
        return []

    # Convert GraphToolServer GraphStepEntry list → OpenClawToolSchema dicts
    schemas: list[dict[str, Any]] = []
    for entry in data if isinstance(data, list) else []:
        tool_name: str = entry.get("tool_name", "")
        if not tool_name:
            continue
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": entry.get("description", ""),
                    "parameters": entry.get("params_schema", {"type": "object", "properties": {}}),
                },
            }
        )

    return schemas
