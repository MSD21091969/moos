from __future__ import annotations

from fastapi import FastAPI, WebSocket

from src.handlers.graph import GraphHandler
from src.handlers.workflow import WorkflowHandler

app = FastAPI(
    title="Collider GraphTool Server",
    version="0.1.0",
)

workflow_handler = WorkflowHandler()
graph_handler = GraphHandler()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "collider-graphtool-server"}


@app.websocket("/ws/workflow")
async def ws_workflow(websocket: WebSocket):
    await workflow_handler.handle(websocket)


@app.websocket("/ws/graph")
async def ws_graph(websocket: WebSocket):
    await graph_handler.handle(websocket)
