"""ColliderAgentRunner — FastAPI application entry point.

Exposes:
  GET  /health           — liveness probe
  POST /agent/session    — compose a ContextSet and cache as a session
  GET  /agent/chat       — SSE streaming LLM response (session_id or node_id)
  GET  /tools/discover   — proxy to GraphToolServer tool discovery
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.agent import runner as agent_runner
from src.core import graph_tool_client
from src.core.auth_client import auth_client
from src.core.config import settings
from src.core.session_store import session_store
from src.schemas.context_set import ContextSet, SessionResponse

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("collider.agent_runner")

app = FastAPI(
    title="ColliderAgentRunner",
    description=(
        "Local pydantic-ai agent runner — composes ContextSets from OpenClaw "
        "bootstrap and streams LLM responses"
    ),
    version="0.2.0",
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


@app.post("/agent/session", response_model=SessionResponse)
async def create_session(ctx: ContextSet) -> SessionResponse:
    """Compose a ContextSet into a reusable agent session.

    Authenticates as the given role, bootstraps all requested nodes, merges
    their contexts (leaf-wins), optionally runs vector tool discovery, and
    caches the result under a ``session_id``.

    The returned ``session_id`` should be passed to ``GET /agent/chat``.

    Args:
        ctx: ContextSet specifying role, node IDs, vector query, and filters.

    Returns:
        SessionResponse with session_id and a preview of the composed context.
    """
    try:
        system_prompt, tool_schemas, preview = await agent_runner.compose_context_set(ctx)
    except Exception as exc:
        logger.exception("Failed to compose context set")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session_id = session_store.create(system_prompt, tool_schemas)
    return SessionResponse(session_id=session_id, preview=preview)


@app.get("/agent/chat")
async def agent_chat(
    message: str = Query(..., description="User chat message"),
    session_id: str | None = Query(None, description="Session ID from POST /agent/session"),
    node_id: str | None = Query(None, description="Single node UUID (legacy, backward compat)"),
) -> EventSourceResponse:
    """Stream an LLM response for one chat turn.

    Accepts either a ``session_id`` (preferred — from POST /agent/session with a
    composed ContextSet) or a legacy ``node_id`` (single-node bootstrap).

    SSE event format::

        data: {"type": "delta", "text": "..."}
        data: {"type": "done"}
        data: {"type": "error", "message": "..."}

    Args:
        message: The user's chat input.
        session_id: Composed session from POST /agent/session (preferred).
        node_id: Single Collider node UUID (legacy backward-compat path).

    Returns:
        SSE stream of JSON events.
    """
    if session_id is None and node_id is None:
        raise HTTPException(
            status_code=422,
            detail="Provide either session_id (composed) or node_id (legacy).",
        )

    async def generate_session():
        entry = session_store.get(session_id)  # type: ignore[arg-type]
        if entry is None:
            yield {"data": json.dumps({"type": "error", "message": "Session not found or expired"})}
            return
        try:
            token = await auth_client.get_token()
            async for chunk in agent_runner.run_session_stream(
                system_prompt=entry["system_prompt"],
                tool_schemas=entry["tool_schemas"],
                user_message=message,
                token=token,
            ):
                yield {"data": json.dumps({"type": "delta", "text": chunk})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Session stream error %s", session_id)
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    async def generate_legacy():
        try:
            async for chunk in agent_runner.run_agent_stream(node_id, message):  # type: ignore[arg-type]
                yield {"data": json.dumps({"type": "delta", "text": chunk})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent stream error for node %s", node_id)
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    generator = generate_session() if session_id else generate_legacy()
    return EventSourceResponse(generator)


@app.get("/tools/discover")
async def tools_discover(
    query: str = Query(..., description="Semantic search query"),
    role: str = Query("app_user", description="Role to filter visibility for"),
) -> list[dict]:
    """Discover tools via GraphToolServer.

    Proxies to ``POST {graph_tool_url}/api/v1/registry/tools/discover`` so the
    Chrome extension only needs :8004 in its CORS/host_permissions, not :8001.

    Args:
        query: Free-text or semantic search string.
        role: Used to determine the visibility filter level.

    Returns:
        List of tool schema dicts.
    """
    visibility = ["global", "group"] if role in ("app_user", "app_admin") else ["global", "group", "local"]
    return await graph_tool_client.discover_tools(query=query, visibility_filter=visibility)
