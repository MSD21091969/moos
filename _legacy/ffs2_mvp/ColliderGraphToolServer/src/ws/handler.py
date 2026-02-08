"""WebSocket handler for workflow execution."""

import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from dataclasses import asdict

from src.graphs import (
    execute_workflow,
    execute_tool,
    workflow_engine,
    Workflow,
    WorkflowContext,
    StepResult,
)


# Active connections by session ID
active_connections: Dict[str, WebSocket] = {}


async def websocket_handler(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket connection for workflow execution.

    Protocol:
    - Client sends: {"type": "workflow"|"tool"|"workflow_run", "payload": {...}}
    - Server responds: {"type": "result"|"error"|"step_start"|"step_complete", "payload": {...}}
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
                    # Legacy simple workflow execution
                    result = await execute_workflow(payload, context)
                    await websocket.send_text(
                        json.dumps({"type": "result", "payload": result})
                    )

                elif msg_type == "workflow_run":
                    # New streaming workflow execution
                    await handle_workflow_run(websocket, payload, context)

                elif msg_type == "tool":
                    result = await execute_tool(
                        tool_name=payload.get("name"),
                        tool_args=payload.get("args", {}),
                        context=context,
                    )
                    await websocket.send_text(
                        json.dumps({"type": "result", "payload": result})
                    )

                elif msg_type == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "payload": {"session_id": session_id}}
                        )
                    )

                else:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "payload": {
                                    "error": f"Unknown message type: {msg_type}"
                                },
                            }
                        )
                    )

            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "payload": {"error": str(e)}})
                )

    except WebSocketDisconnect:
        del active_connections[session_id]


async def handle_workflow_run(
    websocket: WebSocket,
    workflow_data: dict,
    context_data: dict,
):
    """
    Execute a workflow with streaming step updates.

    Sends:
    - {"type": "workflow_start", "payload": {"workflow_id": "..."}}
    - {"type": "step_start", "payload": {"step_id": "..."}}
    - {"type": "step_complete", "payload": {...step_result...}}
    - {"type": "workflow_complete", "payload": {"results": [...]}}
    """
    # Parse workflow definition
    workflow = Workflow.from_dict(workflow_data)

    # Create execution context
    ctx = WorkflowContext(
        user_id=context_data.get("user_id", "anonymous"),
        app_id=context_data.get("app_id", "unknown"),
        node_path=context_data.get("node_path", "/"),
        container=context_data.get("container", {}),
        variables=context_data.get("variables", {}),
        secrets=context_data.get("secrets", {}),
    )

    # Notify workflow start
    await websocket.send_text(
        json.dumps(
            {
                "type": "workflow_start",
                "payload": {
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "step_count": len(workflow.steps),
                },
            }
        )
    )

    # Callbacks for streaming
    async def on_step_start(step_id: str):
        await websocket.send_text(
            json.dumps({"type": "step_start", "payload": {"step_id": step_id}})
        )

    async def on_step_complete(result: StepResult):
        await websocket.send_text(
            json.dumps(
                {
                    "type": "step_complete",
                    "payload": {
                        "step_id": result.step_id,
                        "status": result.status.value,
                        "output": result.output,
                        "error": result.error,
                        "duration_ms": result.duration_ms,
                    },
                }
            )
        )

    # Execute workflow
    results = await workflow_engine.execute(
        workflow,
        ctx,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
    )

    # Notify workflow complete
    all_success = all(r.status.value in ("completed", "skipped") for r in results)

    await websocket.send_text(
        json.dumps(
            {
                "type": "workflow_complete",
                "payload": {
                    "workflow_id": workflow.id,
                    "success": all_success,
                    "results": [
                        {
                            "step_id": r.step_id,
                            "status": r.status.value,
                            "output": r.output,
                            "error": r.error,
                            "duration_ms": r.duration_ms,
                        }
                        for r in results
                    ],
                    "variables": ctx.variables,
                },
            }
        )
    )
