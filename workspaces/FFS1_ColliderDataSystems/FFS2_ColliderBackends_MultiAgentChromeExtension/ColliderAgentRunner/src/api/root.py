"""Root agent API — boots from the application's root NodeContainer as superadmin.

The root agent has system-wide access:
  - Bootstraps from Application.root_node_id (full subtree, depth=None)
  - Authenticates as superadmin
  - Session TTL is 24 hours (vs 4h for regular sessions)
  - Chat is handled directly by the Chrome extension via NanoClawBridge WebSocket

Endpoints:
  POST /agent/root/session   — compose root context, return session_id + nanoclaw_ws_url
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agent import runner as agent_runner
from src.core import collider_client
from src.core.auth_client import auth_client
from src.core.config import settings
from src.core.session_store import session_store
from src.core.workspace_writer import write_workspace
from src.schemas.context_set import ContextSet, SessionResponse

logger = logging.getLogger("collider.root_agent")

router = APIRouter(prefix="/agent/root", tags=["root-agent"])

_ROOT_SESSION_TTL = 24 * 3600  # 24 hours


class RootSessionRequest(BaseModel):
    """Request body for POST /agent/root/session."""

    app_id: str
    """The Collider Application UUID to bootstrap the root agent from."""


@router.post("/session", response_model=SessionResponse)
async def create_root_session(body: RootSessionRequest) -> SessionResponse:
    """Compose a root agent session from the application's root NodeContainer.

    1. Authenticates as superadmin.
    2. Fetches Application to get root_node_id.
    3. Bootstraps the root node with full subtree depth.
    4. Caches the session with a 24h TTL.
    5. Returns nanoclaw_ws_url for the Chrome extension to connect directly.

    Args:
        body: RootSessionRequest with app_id.

    Returns:
        SessionResponse with session_id, context preview, and nanoclaw_ws_url.

    Raises:
        HTTPException 404: If the application has no root_node_id set.
        HTTPException 500: On bootstrap or composition failure.
    """
    try:
        token = await auth_client.get_token_for_role("superadmin")

        # Resolve root_node_id from the application
        app = await collider_client.get_app(body.app_id, token)
        root_node_id: str | None = app.get("root_node_id")

        if not root_node_id:
            logger.warning(
                "Application %s has no root_node_id — falling back to first node",
                body.app_id,
            )
            ctx = ContextSet(
                role="superadmin",
                app_id=body.app_id,
                node_ids=[],
                depth=None,
                inherit_ancestors=False,
            )
        else:
            ctx = ContextSet(
                role="superadmin",
                app_id=body.app_id,
                node_ids=[root_node_id],
                depth=None,  # full subtree
                inherit_ancestors=False,
            )

        composed = await agent_runner.compose_context_set(ctx)

    except Exception as exc:
        logger.exception("Failed to compose root session for app %s", body.app_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Store session with extended TTL
    session_id = session_store.create_with_ttl(
        system_prompt=composed.system_prompt,
        tool_schemas=composed.tool_schemas,
        ttl_seconds=_ROOT_SESSION_TTL,
        extra={"app_id": body.app_id, "role": "superadmin", "is_root": True},
    )

    # Write to root-specific NanoClaw workspace
    static_skills = (
        Path(settings.nanoclaw_static_skills_dir)
        if settings.nanoclaw_static_skills_dir
        else None
    )
    try:
        await write_workspace(
            workspace_dir=Path(settings.nanoclaw_root_workspace_dir),
            agents_md=composed.agents_md,
            soul_md=composed.soul_md,
            tools_md=composed.tools_md,
            tool_schemas=composed.tool_schemas,
            skills=composed.skills,
            session_meta={
                **composed.session_meta,
                "session_id": session_id,
                "is_root": True,
            },
            static_skills_dir=static_skills,
        )
    except Exception:
        logger.exception("Failed to write root NanoClaw workspace (non-fatal)")

    logger.info(
        "Root session created: app=%s  nodes=%d  tools=%d  session=%s",
        body.app_id,
        composed.preview.node_count,
        composed.preview.tool_count,
        session_id[:8],
    )

    return SessionResponse(
        session_id=session_id,
        preview=composed.preview,
        nanoclaw_ws_url=settings.nanoclaw_bridge_url,
    )
