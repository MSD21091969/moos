"""WebSocket handler for workflow execution."""
import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

from src.graphs import execute_workflow, execute_tool


# Active connections by session ID
active_connections: Dict[str, WebSocket] = {}


async def websocket_handler(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket connection for workflow execution.
    
    Protocol:
    - Client sends: {"type": "workflow"|"tool", "payload": {...}}
    - Server responds: {"type": "result"|"error", "payload": {...}}
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            payload = message.get("payload", {})
            context = message.get("context", {})
            
            try:
                if msg_type == "workflow":
                    result = await execute_workflow(payload, context)
                elif msg_type == "tool":
                    result = await execute_tool(
                        tool_name=payload.get("name"),
                        tool_args=payload.get("args", {}),
                        context=context
                    )
                else:
                    result = {"error": f"Unknown message type: {msg_type}"}
                
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "payload": result
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "payload": {"error": str(e)}
                }))
                
    except WebSocketDisconnect:
        del active_connections[session_id]
