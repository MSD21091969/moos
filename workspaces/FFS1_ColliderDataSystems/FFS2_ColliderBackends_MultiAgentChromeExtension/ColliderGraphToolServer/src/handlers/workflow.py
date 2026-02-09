from __future__ import annotations

import json

from fastapi import WebSocket

from src.core.config import settings


class WorkflowHandler:
    """Handles WebSocket messages for workflow execution."""

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                raw = await websocket.receive_text()
                message = json.loads(raw)
                msg_type = message.get("type", "unknown")

                if msg_type == "execute_workflow":
                    await self._handle_execute(websocket, message)
                elif msg_type == "query_graph":
                    await self._handle_query(websocket, message)
                elif msg_type == "ai_inference":
                    await self._handle_inference(websocket, message)
                else:
                    await websocket.send_json(
                        {"type": "error", "detail": f"Unknown message type: {msg_type}"}
                    )
        except Exception:
            pass

    async def _handle_execute(self, ws: WebSocket, message: dict) -> None:
        workflow_id = message.get("workflow_id", "unknown")
        # Send progress
        await ws.send_json(
            {
                "type": "workflow_progress",
                "workflow_id": workflow_id,
                "progress": 0.0,
                "status": "started",
            }
        )

        # Stub: execute workflow steps
        steps = message.get("steps", [])
        for i, step in enumerate(steps):
            progress = (i + 1) / max(len(steps), 1)
            await ws.send_json(
                {
                    "type": "workflow_progress",
                    "workflow_id": workflow_id,
                    "progress": progress,
                    "step": step,
                    "status": "running",
                }
            )

        # Send result
        await ws.send_json(
            {
                "type": "workflow_result",
                "workflow_id": workflow_id,
                "status": "completed",
                "result": {"message": "Workflow executed successfully"},
            }
        )

    async def _handle_query(self, ws: WebSocket, message: dict) -> None:
        query = message.get("query", "")
        await ws.send_json(
            {
                "type": "query_result",
                "query": query,
                "result": {"nodes": [], "edges": []},
            }
        )

    async def _handle_inference(self, ws: WebSocket, message: dict) -> None:
        prompt = message.get("prompt", "")
        await ws.send_json(
            {
                "type": "inference_result",
                "model": settings.default_model,
                "response": f"Stub inference response for: {prompt[:100]}",
            }
        )
