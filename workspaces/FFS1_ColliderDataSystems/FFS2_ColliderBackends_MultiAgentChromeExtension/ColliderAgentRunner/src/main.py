"""ColliderAgentRunner — context hydration service for NanoClaw agent sessions.

NanoClawBridge (ws://127.0.0.1:18789) handles all chat and LLM calls directly.
This service composes the NanoClaw workspace context from Collider node bootstraps.

Exposes:
  GET  /health                — liveness probe
  POST /agent/session         — compose a ContextSet, return session_id + nanoclaw_ws_url
  POST /agent/root/session    — compose root agent session from app root node
  GET  /tools/discover        — proxy to GraphToolServer tool discovery
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.agent import runner as agent_runner
from src.api import root as root_api
from src.core import graph_tool_client
from src.core.config import settings
from src.core.session_store import session_store
from src.core.workspace_writer import write_workspace
from src.schemas.context_set import ContextSet, SessionResponse

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("collider.agent_runner")

app = FastAPI(
    title="ColliderAgentRunner",
    description=(
        "Context hydration service — composes Collider node bootstraps into "
        "NanoClaw workspace sessions. Chat is handled by NanoClawBridge directly."
    ),
    version="0.3.0",
)

# CORS: allow the Chrome extension sidepanel and local dev servers to connect
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"(chrome-extension://.*|http://localhost(:\d+)?)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(root_api.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "ColliderAgentRunner"}


@app.post("/agent/session", response_model=SessionResponse)
async def create_session(ctx: ContextSet) -> SessionResponse:
    """Compose a ContextSet into a NanoClaw workspace session.

    Authenticates as the given role, bootstraps all requested nodes, merges
    their contexts (leaf-wins), optionally runs vector tool discovery,
    writes workspace files for Claude Code, and caches the session.

    Args:
        ctx: ContextSet specifying role, node IDs, vector query, and filters.

    Returns:
        SessionResponse with session_id, preview, and nanoclaw_ws_url.
    """
    try:
        composed = await agent_runner.compose_context_set(ctx)
    except Exception as exc:
        logger.exception("Failed to compose context set")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session_id = session_store.create(composed.system_prompt, composed.tool_schemas)

    # Write NanoClaw workspace files (CLAUDE.md, .mcp.json, skills/)
    static_skills = (
        Path(settings.nanoclaw_static_skills_dir)
        if settings.nanoclaw_static_skills_dir
        else None
    )
    try:
        await write_workspace(
            workspace_dir=Path(settings.nanoclaw_workspace_dir),
            agents_md=composed.agents_md,
            soul_md=composed.soul_md,
            tools_md=composed.tools_md,
            tool_schemas=composed.tool_schemas,
            skills=composed.skills,
            session_meta={**composed.session_meta, "session_id": session_id},
            static_skills_dir=static_skills,
        )
    except Exception:
        logger.exception("Failed to write NanoClaw workspace (non-fatal)")

    # Build WebSocket URL with auth token
    ws_url = settings.nanoclaw_bridge_url
    if settings.nanoclaw_bridge_token:
        ws_url = f"{ws_url}?token={settings.nanoclaw_bridge_token}"

    return SessionResponse(
        session_id=session_id,
        preview=composed.preview,
        nanoclaw_ws_url=ws_url,
    )


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
    visibility = (
        ["global", "group"]
        if role in ("app_user", "app_admin")
        else ["global", "group", "local"]
    )
    return await graph_tool_client.discover_tools(
        query=query, visibility_filter=visibility
    )
