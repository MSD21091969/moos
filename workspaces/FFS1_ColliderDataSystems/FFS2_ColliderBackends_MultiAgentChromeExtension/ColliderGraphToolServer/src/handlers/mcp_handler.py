"""MCP (Model Context Protocol) server handler for ColliderGraphToolServer.

Exposes every registered ``ToolDefinition`` in the in-memory ``ToolRegistry``
as a native MCP tool so that any MCP-compatible client (Claude Code, Cursor,
Zed, VS Code Copilot …) can discover and invoke Collider tools natively.

Transport: SSE (server-sent events) over HTTP.
Endpoints registered in ``main.py``:
  GET  /mcp/sse        — client connects here to establish SSE stream
  POST /mcp/messages/  — client posts JSON-RPC requests here

Usage (Claude Code):
  claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse

Architecture note:
  ``list_tools`` queries the ToolRegistry on every request (pull-based), so
  tools registered after server start appear automatically without a restart.
  ``call_tool`` delegates to the same ``ToolRunner.execute()`` path used by the
  gRPC ``ExecuteTool`` RPC, keeping the execution path consistent.

Visibility policy:
  Only tools with ``visibility in ("group", "global")`` are exposed via MCP.
  ``local`` tools (owner-private) remain invisible to MCP clients.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from src.core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level registry reference (set once at startup from main.py)
# ---------------------------------------------------------------------------

_registry: ToolRegistry | None = None


def set_registry(registry: ToolRegistry) -> None:
    """Wire up the shared ToolRegistry instance used by all MCP handlers."""
    global _registry
    _registry = registry


def _get_registry() -> ToolRegistry:
    if _registry is None:
        raise RuntimeError("MCP handler: ToolRegistry not set — call set_registry() first")
    return _registry


# ---------------------------------------------------------------------------
# MCP Server definition (low-level Server API for dynamic tool dispatch)
# ---------------------------------------------------------------------------

_mcp_server = Server("collider-tools")
_sse_transport = SseServerTransport("/mcp/messages/")


@_mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return all group/global-visible registry tools as MCP Tool entries."""
    registry = _get_registry()
    tools: list[Tool] = []
    for entry in registry._tools.values():
        if entry.visibility not in ("group", "global"):
            continue
        tools.append(
            Tool(
                name=entry.tool_name,
                description=getattr(entry, "description", None) or entry.tool_name,
                inputSchema=entry.params_schema or {"type": "object", "properties": {}},
            )
        )
    return tools


@_mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch an MCP tool call to the ToolRunner execution engine."""
    from src.core.execution import ToolExecutionError, ToolRunner

    registry = _get_registry()
    tool = registry.get_tool(name)

    if tool is None:
        logger.warning("MCP call_tool: tool '%s' not found in registry", name)
        return [TextContent(type="text", text=f"Error: tool '{name}' not found in registry")]

    if tool.visibility not in ("group", "global"):
        return [TextContent(type="text", text=f"Error: tool '{name}' is not accessible via MCP")]

    try:
        result = await ToolRunner.execute(tool, arguments or {})
        return [TextContent(type="text", text=json.dumps(result, default=str))]
    except ToolExecutionError as exc:
        logger.error("MCP call_tool execution error for '%s': %s", name, exc)
        return [TextContent(type="text", text=f"Execution error: {exc}")]
    except Exception:
        logger.exception("MCP call_tool unexpected error for '%s'", name)
        return [TextContent(type="text", text="Internal error during tool execution")]


# ---------------------------------------------------------------------------
# FastAPI-compatible endpoint handlers (mounted in main.py)
# ---------------------------------------------------------------------------


async def mcp_sse_endpoint(request: Request) -> None:
    """Handle the MCP SSE connection (GET /mcp/sse).

    The client connects here to establish a server-sent events stream.
    All JSON-RPC messages flow back over this stream.
    """
    async with _sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await _mcp_server.run(
            streams[0],
            streams[1],
            _mcp_server.create_initialization_options(),
        )


async def mcp_messages_endpoint(request: Request) -> Response:
    """Handle MCP POST messages (POST /mcp/messages/).

    The client posts JSON-RPC request bodies here.  The SSE stream
    established via ``mcp_sse_endpoint`` receives the responses.
    """
    await _sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
    return Response()
