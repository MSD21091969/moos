"""workspace_manager — MCP tool for agent-controlled IDE workspace management.

Allows the Nano agent to view, navigate, open, close, and focus IDE
workspace views (ffs6 and other applications) based on role permissions.

code_ref format: "src.tools.workspace_manager:<function_name>"
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Permission matrix
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "superadmin": {"view", "navigate", "open", "close", "focus", "status"},
    "collider_admin": {"view", "navigate", "open", "focus", "status"},
    "app_admin": {"view", "navigate", "status"},
    "app_user": {"view", "status"},
}


def _nanoclaw_bridge_url() -> str:
    return os.environ.get("NANOCLAW_BRIDGE_URL", "http://localhost:18789").rstrip("/")


def _ffs6_url() -> str:
    return os.environ.get("FFS6_URL", "http://localhost:4200").rstrip("/")


# ---------------------------------------------------------------------------
# Main tool entry point
# ---------------------------------------------------------------------------


async def workspace_manager(
    action: str,
    target: str = "",
    role: str = "app_user",
    session_id: str = "",
) -> dict[str, Any]:
    """Manage IDE workspace views.

    The agent calls this tool to interact with IDE workspace applications
    (ffs6 and other Collider frontend apps).

    Args:
        action: The operation to perform.
            - "view"     — Get current workspace state (open views, active node).
            - "navigate" — Navigate to a specific node in the workspace graph.
            - "open"     — Open a new workspace view for a node.
            - "close"    — Close a workspace view.
            - "focus"    — Bring a workspace view to the foreground.
            - "status"   — Get status of all workspace views.
        target: Node ID or workspace path to act on.
        role: Current user role for permission enforcement.
        session_id: Active agent session ID for context.

    Returns:
        Dict with result or error.
    """
    # Permission check
    allowed = ROLE_PERMISSIONS.get(role, set())
    if action not in allowed:
        return {
            "error": f"Permission denied: role '{role}' cannot perform '{action}'",
            "allowed_actions": sorted(allowed),
        }

    if action == "view":
        return await _get_workspace_view(target, session_id)
    elif action == "navigate":
        return await _navigate_workspace(target, session_id)
    elif action == "open":
        return await _open_workspace(target, session_id)
    elif action == "close":
        return await _close_workspace(target, session_id)
    elif action == "focus":
        return await _focus_workspace(target, session_id)
    elif action == "status":
        return await _get_workspace_status(session_id)
    else:
        return {"error": f"Unknown action: {action}"}


# ---------------------------------------------------------------------------
# Action implementations
# ---------------------------------------------------------------------------


async def _get_workspace_view(target: str, session_id: str) -> dict[str, Any]:
    """Get the current state of a workspace view."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_ffs6_url()}/api/workspace/view",
                params={"node_id": target, "session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {
                "active_node": target or "unknown",
                "status": "view_data_unavailable",
                "note": "ffs6 API not reachable, returning placeholder",
            }
    except httpx.ConnectError:
        return {
            "active_node": target or "unknown",
            "status": "offline",
            "note": "ffs6 is not running",
        }


async def _navigate_workspace(target: str, session_id: str) -> dict[str, Any]:
    """Navigate the workspace to a specific node."""
    if not target:
        return {"error": "target is required for navigate action"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_ffs6_url()}/api/workspace/navigate",
                json={"node_id": target, "session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"navigated": target, "status": "command_sent"}
    except httpx.ConnectError:
        return {"error": "ffs6 is not running", "target": target}


async def _open_workspace(target: str, session_id: str) -> dict[str, Any]:
    """Open a new workspace view for a node."""
    if not target:
        return {"error": "target is required for open action"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_ffs6_url()}/api/workspace/open",
                json={"node_id": target, "session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"opened": target, "status": "command_sent"}
    except httpx.ConnectError:
        return {"error": "ffs6 is not running", "target": target}


async def _close_workspace(target: str, session_id: str) -> dict[str, Any]:
    """Close a workspace view."""
    if not target:
        return {"error": "target is required for close action"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_ffs6_url()}/api/workspace/close",
                json={"node_id": target, "session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"closed": target, "status": "command_sent"}
    except httpx.ConnectError:
        return {"error": "ffs6 is not running", "target": target}


async def _focus_workspace(target: str, session_id: str) -> dict[str, Any]:
    """Bring a workspace view to the foreground."""
    if not target:
        return {"error": "target is required for focus action"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_ffs6_url()}/api/workspace/focus",
                json={"node_id": target, "session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"focused": target, "status": "command_sent"}
    except httpx.ConnectError:
        return {"error": "ffs6 is not running", "target": target}


async def _get_workspace_status(session_id: str) -> dict[str, Any]:
    """Get status of all workspace views."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_ffs6_url()}/api/workspace/status",
                params={"session_id": session_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"views": [], "status": "status_unavailable"}
    except httpx.ConnectError:
        return {"views": [], "status": "ffs6_offline"}
