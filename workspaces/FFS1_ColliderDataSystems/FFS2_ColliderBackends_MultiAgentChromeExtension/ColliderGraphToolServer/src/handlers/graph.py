from __future__ import annotations

import json

from fastapi import WebSocket


class GraphHandler:
    """Handles WebSocket messages for graph operations."""

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                raw = await websocket.receive_text()
                message = json.loads(raw)
                msg_type = message.get("type", "unknown")

                if msg_type == "traverse":
                    await self._handle_traverse(websocket, message)
                elif msg_type == "mutate":
                    await self._handle_mutate(websocket, message)
                elif msg_type == "query":
                    await self._handle_query(websocket, message)
                else:
                    await websocket.send_json(
                        {"type": "error", "detail": f"Unknown message type: {msg_type}"}
                    )
        except Exception:
            pass

    async def _handle_traverse(self, ws: WebSocket, message: dict) -> None:
        start_node = message.get("start_node", "root")
        await ws.send_json(
            {
                "type": "traverse_result",
                "start_node": start_node,
                "visited": [start_node],
                "edges": [],
            }
        )

    async def _handle_mutate(self, ws: WebSocket, message: dict) -> None:
        operation = message.get("operation", "add_node")
        await ws.send_json(
            {
                "type": "mutate_result",
                "operation": operation,
                "success": True,
            }
        )

    async def _handle_query(self, ws: WebSocket, message: dict) -> None:
        query = message.get("query", "")
        await ws.send_json(
            {
                "type": "query_result",
                "query": query,
                "nodes": [],
                "edges": [],
            }
        )
