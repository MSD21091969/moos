"""Dynamic pydantic-ai tool builders from OpenClaw tool_schemas."""

from __future__ import annotations

import json
from typing import Any

from pydantic_ai import Tool

from src.core import collider_client


def build_tools(tool_schemas: list[dict[str, Any]], token: str) -> list[Tool]:  # type: ignore[type-arg]
    """Create pydantic-ai Tool objects from OpenClaw tool_schema entries.

    Each tool wraps ``POST /execution/tool/{name}`` on DataServer.
    Tools are rebuilt on every bootstrap call so live registry changes
    are always reflected without a restart.

    Args:
        tool_schemas: List of OpenClawToolSchema dicts, each with
            ``{"type": "function", "function": {name, description, parameters}}``.
        token: Valid Bearer JWT passed into every execute_tool call.

    Returns:
        List of pydantic-ai Tool instances ready to pass to Agent().
    """
    tools: list[Tool] = []  # type: ignore[type-arg]

    for schema in tool_schemas:
        fn_meta = schema.get("function", {})
        tool_name: str = fn_meta.get("name", "")
        description: str = fn_meta.get("description", "")

        if not tool_name:
            continue

        # Capture loop variables in default args
        def _make_fn(name: str = tool_name, tok: str = token):  # noqa: ANN202
            async def _tool_fn(**kwargs: Any) -> str:
                """Execute a Collider tool via DataServer gRPC passthrough."""
                result = await collider_client.execute_tool(name, kwargs, tok)
                return json.dumps(result)

            _tool_fn.__name__ = name
            _tool_fn.__doc__ = description or f"Execute the '{name}' Collider tool."
            return _tool_fn

        tools.append(
            Tool(
                _make_fn(),
                name=tool_name,
                description=description or f"Execute the '{tool_name}' Collider tool.",
            )
        )

    return tools
