from __future__ import annotations

from fastapi import FastAPI, WebSocket
from starlette.requests import Request

from src.core.tool_registry import ToolRegistry
from src.handlers.graph import GraphHandler
from src.handlers.mcp_handler import (
    mcp_messages_endpoint,
    mcp_sse_endpoint,
    set_registry as mcp_set_registry,
)
from src.handlers.registry_api import router as registry_router, set_registry
from src.handlers.workflow import WorkflowHandler

app = FastAPI(
    title="Collider GraphTool Server",
    version="0.2.0",
)

# -- Shared registry instance -----------------------------------------
tool_registry = ToolRegistry()
set_registry(tool_registry)
mcp_set_registry(tool_registry)  # Wire same instance into MCP handler

# -- REST API ----------------------------------------------------------
app.include_router(registry_router)

# -- MCP (Model Context Protocol) transport ----------------------------
# GET  /mcp/sse        → SSE stream (client connects here)
# POST /mcp/messages/  → JSON-RPC request body endpoint
app.add_route("/mcp/sse", mcp_sse_endpoint, methods=["GET"])
app.add_route("/mcp/messages/", mcp_messages_endpoint, methods=["POST"])

# -- Handlers ----------------------------------------------------------
workflow_handler = WorkflowHandler()
graph_handler = GraphHandler()


@app.get("/health")
async def health_check():
    stats = tool_registry.stats()
    return {
        "status": "ok",
        "service": "collider-graphtool-server",
        "registry": stats.model_dump(),
    }


@app.websocket("/ws/workflow")
async def ws_workflow(websocket: WebSocket):
    await workflow_handler.handle(websocket)


@app.websocket("/ws/graph")
async def ws_graph(websocket: WebSocket):
    await graph_handler.handle(websocket)
