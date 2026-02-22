from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket

from src.core.tool_registry import ToolRegistry
from src.handlers.graph import GraphHandler
from src.handlers.grpc_servicer import serve_grpc
from src.handlers.mcp_handler import (
    mcp_messages_endpoint,
    mcp_sse_endpoint,
)
from src.handlers.mcp_handler import (
    set_registry as mcp_set_registry,
)
from src.handlers.registry_api import router as registry_router
from src.handlers.registry_api import set_registry
from src.handlers.workflow import WorkflowHandler

# -- Shared registry instance -----------------------------------------
tool_registry = ToolRegistry()
set_registry(tool_registry)
mcp_set_registry(tool_registry)  # Wire same instance into MCP handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the gRPC server alongside the HTTP server."""
    import logging as _log
    grpc_task = asyncio.create_task(serve_grpc(tool_registry))
    # Give gRPC a moment to bind; if it fails the task raises quickly
    await asyncio.sleep(0.5)
    if grpc_task.done():
        exc = grpc_task.exception()
        if exc:
            _log.getLogger(__name__).error(
                "gRPC server failed to start on :50052 — %s\n"
                "NanoClaw tool calls via gRPC will not work.\n"
                "Fix: ensure grpcio is installed and port 50052 is free.",
                exc,
            )
            grpc_task = None
        else:
            _log.getLogger(__name__).info("gRPC server started on :50052")
    else:
        _log.getLogger(__name__).info("gRPC server started on :50052")
    yield
    if grpc_task and not grpc_task.done():
        grpc_task.cancel()
        try:
            await grpc_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Collider GraphTool Server",
    version="0.2.0",
    lifespan=lifespan,
)

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
