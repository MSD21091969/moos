"""Atomic Collider management tools — callable via ToolRunner code_ref.

Each function is async, takes typed parameters matching its ToolDefinition
params_schema, and returns a dict.  Authentication uses COLLIDER_* environment
variables (the same ones loaded by all FFS2 services via secrets/api_keys.env).

code_ref format: "src.tools.collider_management:<function_name>"
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load shared secrets so COLLIDER_USERNAME / COLLIDER_PASSWORD are available
_secrets = Path("D:/FFS0_Factory/secrets/api_keys.env")
if _secrets.exists():
    load_dotenv(_secrets, override=False)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level auth cache
# ---------------------------------------------------------------------------

_token: str | None = None
_token_expires_at: float = 0.0


def _data_server_url() -> str:
    return os.environ.get("COLLIDER_DATA_SERVER_URL", "http://localhost:8000").rstrip(
        "/"
    )


async def _get_token() -> str:
    """Return a cached superadmin JWT or fetch a fresh one."""
    global _token, _token_expires_at
    if _token and time.time() < (_token_expires_at - 60):
        return _token
    username = os.environ.get("COLLIDER_SUPERADMIN_USERNAME") or os.environ.get(
        "COLLIDER_USERNAME", "superadmin"
    )
    password = os.environ.get("COLLIDER_SUPERADMIN_PASSWORD") or os.environ.get(
        "COLLIDER_PASSWORD", ""
    )
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_data_server_url()}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    _token = data["access_token"]
    _token_expires_at = time.time() + 23 * 3600
    logger.debug(
        "Tool auth token refreshed for user %s", data.get("user", {}).get("username")
    )
    return _token  # type: ignore[return-value]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Node management
# ---------------------------------------------------------------------------


async def list_nodes(app_id: str) -> dict[str, Any]:
    """List all nodes in a Collider application."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"nodes": resp.json()}


async def get_node(app_id: str, node_id: str) -> dict[str, Any]:
    """Get a single node by ID."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/{node_id}",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def get_node_tree(app_id: str) -> dict[str, Any]:
    """Get the full node tree for a Collider application."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/tree",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"tree": resp.json()}


async def create_node(
    app_id: str,
    path: str,
    parent_id: str | None = None,
    kind: str = "workspace",
    instructions: list[str] | None = None,
    rules: list[str] | None = None,
    knowledge: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new workspace node in the Collider graph.

    Args:
        app_id: Application UUID.
        path: Logical dot-separated path, e.g. 'factory/ffs1/my-new-node'.
        parent_id: Parent node UUID (optional).
        kind: Node kind — 'workspace', 'tool', or 'workflow'.
        instructions: List of instruction markdown strings (agent identity).
        rules: List of rule markdown strings (guardrails).
        knowledge: List of knowledge markdown strings (reference docs).
    """
    token = await _get_token()
    container: dict[str, Any] = {
        "version": "1.0.0",
        "kind": kind,
        "instructions": instructions or [],
        "rules": rules or [],
        "knowledge": knowledge or [],
        "skills": [],
        "tools": [],
        "workflows": [],
    }
    body: dict[str, Any] = {"path": path, "container": container}
    if parent_id:
        body["parent_id"] = parent_id
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/",
            json=body,
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def update_node(
    app_id: str,
    node_id: str,
    instructions: list[str] | None = None,
    rules: list[str] | None = None,
    knowledge: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing node's container content (partial update)."""
    token = await _get_token()
    container_update: dict[str, Any] = {}
    if instructions is not None:
        container_update["instructions"] = instructions
    if rules is not None:
        container_update["rules"] = rules
    if knowledge is not None:
        container_update["knowledge"] = knowledge
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/{node_id}",
            json={"container": container_update},
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def delete_node(app_id: str, node_id: str) -> dict[str, Any]:
    """Delete a node from the Collider graph."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{_data_server_url()}/api/v1/apps/{app_id}/nodes/{node_id}",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"deleted": node_id, "status": resp.status_code}


# ---------------------------------------------------------------------------
# Application management
# ---------------------------------------------------------------------------


async def list_apps() -> dict[str, Any]:
    """List all Collider applications."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/apps/",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"apps": resp.json()}


async def get_app(app_id: str) -> dict[str, Any]:
    """Get details for a specific Collider application, including root_node_id."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/apps/{app_id}",
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def create_app(
    display_name: str, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a new Collider application."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_data_server_url()}/api/v1/apps/",
            json={"display_name": display_name, "config": config or {}},
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Permission management
# ---------------------------------------------------------------------------


async def list_permissions(
    application_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """List permissions, optionally filtered by application or user."""
    token = await _get_token()
    params: dict[str, str] = {}
    if application_id:
        params["application_id"] = application_id
    if user_id:
        params["user_id"] = user_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/permissions/",
            params=params,
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"permissions": resp.json()}


async def grant_permission(
    user_id: str,
    application_id: str,
    role: str = "app_user",
) -> dict[str, Any]:
    """Grant a user access to a Collider application with a specified role.

    Args:
        user_id: Target user UUID.
        application_id: Target application UUID.
        role: One of 'app_user', 'app_admin', 'collider_admin', 'superadmin'.
    """
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_data_server_url()}/api/v1/permissions/",
            json={"user_id": user_id, "application_id": application_id, "role": role},
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def update_permission(perm_id: str, role: str) -> dict[str, Any]:
    """Update the role on an existing permission entry."""
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{_data_server_url()}/api/v1/permissions/{perm_id}",
            json={"role": role},
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Agent bootstrap & skill discovery
# ---------------------------------------------------------------------------


async def bootstrap_node(node_id: str, depth: int | None = None) -> dict[str, Any]:
    """Fetch the agent bootstrap context for a node.

    Returns agents_md, soul_md, tools_md, skills, and tool_schemas.
    """
    token = await _get_token()
    params: dict[str, Any] = {}
    if depth is not None:
        params["depth"] = depth
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/agent/bootstrap/{node_id}",
            params=params,
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]


async def list_skills(node_id: str | None = None) -> dict[str, Any]:
    """List available agent skills, optionally filtered to a specific node."""
    token = await _get_token()
    params: dict[str, str] = {}
    if node_id:
        params["node_id"] = node_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_data_server_url()}/api/v1/agent/skills",
            params=params,
            headers=_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"skills": resp.json()}
