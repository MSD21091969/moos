"""ColliderAgentRunner — FastAPI application entry point.

Exposes:
  GET  /health           — liveness probe
  GET  /agent/chat       — SSE streaming LLM response (node_id + message query params)
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.agent import runner as agent_runner
from src.core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("collider.agent_runner")

app = FastAPI(
    title="ColliderAgentRunner",
    description="Local pydantic-ai agent runner — bootstraps from OpenClaw and streams LLM responses",
    version="0.1.0",
)

# CORS: allow the Chrome extension sidepanel and local dev servers to connect
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"(chrome-extension://.*|http://localhost(:\d+)?)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "ColliderAgentRunner"}


@app.get("/agent/chat")
async def agent_chat(
    node_id: str = Query(..., description="Collider node UUID to bootstrap from"),
    message: str = Query(..., description="User chat message"),
) -> EventSourceResponse:
    """Stream an LLM response for a single chat turn.

    The agent authenticates to DataServer, bootstraps from the given node,
    builds its system prompt, and streams text deltas as SSE events.

    SSE event format:
      ``data: {"type": "delta", "text": "..."}``
      ``data: {"type": "done"}``
      ``data: {"type": "error", "message": "..."}``

    Args:
        node_id: Collider node UUID (leaf segment of selectedNodePath).
        message: The user's chat input.

    Returns:
        SSE stream of JSON events.
    """
    async def generate():
        try:
            async for chunk in agent_runner.run_agent_stream(node_id, message):
                yield {"data": json.dumps({"type": "delta", "text": chunk})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent stream error for node %s", node_id)
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(generate())
