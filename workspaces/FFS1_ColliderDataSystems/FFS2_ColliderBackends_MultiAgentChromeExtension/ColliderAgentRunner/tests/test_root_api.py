"""Tests for POST /agent/root/session endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from src.agent.runner import ComposedContext
from src.core.session_store import session_store
from src.main import app
from src.schemas.context_set import SessionPreview


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


MOCK_APP_UUID = "c57ab23a-4a57-4b28-a34c-9700320565ea"
MOCK_ROOT_NODE = "root-node-uuid-abc"

MOCK_PREVIEW = SessionPreview(
    node_count=10,
    skill_count=2,
    tool_count=15,
    role="superadmin",
    vector_matches=0,
)


def _mock_composed(
    system_prompt: str = "root system prompt",
    preview: SessionPreview | None = None,
) -> ComposedContext:
    return ComposedContext(
        system_prompt=system_prompt,
        agents_md="root agent instructions",
        soul_md="root rules",
        tools_md="root reference docs",
        tool_schemas=[{"name": "spawn_subagent"}],
        skills=[],
        preview=preview or MOCK_PREVIEW,
        session_meta={"role": "superadmin", "app_id": MOCK_APP_UUID},
    )


def _root_patches(mock_app=None, composed=None):
    """Context manager stack for root session patches."""
    if mock_app is None:
        mock_app = {"id": MOCK_APP_UUID, "root_node_id": MOCK_ROOT_NODE}
    if composed is None:
        composed = _mock_composed()

    return (
        patch(
            "src.api.root.auth_client.get_token_for_role",
            new_callable=AsyncMock,
            return_value="super-token",
        ),
        patch(
            "src.api.root.collider_client.get_app",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
        patch(
            "src.api.root.agent_runner.compose_context_set",
            new_callable=AsyncMock,
            return_value=composed,
        ),
        patch("src.api.root.write_workspace", new_callable=AsyncMock),
    )


async def test_root_session_success(client: AsyncClient):
    """Valid app_id returns a session_id with root session metadata."""
    p1, p2, p3, p4 = _root_patches()
    with p1, p2, p3, p4:
        response = await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    preview = data["preview"]
    assert preview["tool_count"] == 15
    assert preview["role"] == "superadmin"


async def test_root_session_uses_24h_ttl(client: AsyncClient):
    """Root sessions are stored with 24-hour TTL."""
    p1, p2, p3, p4 = _root_patches()
    with p1, p2, p3, p4:
        response = await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    sid = response.json()["session_id"]
    entry = session_store.get(sid)
    assert entry is not None
    assert entry["ttl_seconds"] == 24 * 3600


async def test_root_session_stores_is_root_flag(client: AsyncClient):
    """Root session entry has is_root=True in metadata."""
    p1, p2, p3, p4 = _root_patches()
    with p1, p2, p3, p4:
        response = await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    sid = response.json()["session_id"]
    entry = session_store.get(sid)
    assert entry["is_root"] is True
    assert entry["role"] == "superadmin"
    assert entry["app_id"] == MOCK_APP_UUID


async def test_root_session_writes_workspace(client: AsyncClient):
    """Root session writes to the root workspace directory."""
    p1, p2, p3, p4 = _root_patches()
    with p1, p2, p3 as mock_compose, p4 as mock_write:
        await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    mock_write.assert_called_once()
    call_kwargs = mock_write.call_args[1]
    assert call_kwargs["agents_md"] == "root agent instructions"
    assert call_kwargs["session_meta"]["is_root"] is True


async def test_root_session_fallback_no_root_node(client: AsyncClient):
    """If app has no root_node_id, falls back to empty node_ids bootstrap."""
    mock_app_no_root = {"id": MOCK_APP_UUID, "root_node_id": None}
    p1, p2, p3, p4 = _root_patches(mock_app=mock_app_no_root)
    with p1, p2, p3 as mock_compose, p4:
        response = await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    assert response.status_code == 200
    call_ctx = mock_compose.call_args[0][0]
    assert call_ctx.node_ids == []


async def test_root_session_compose_failure_returns_500(client: AsyncClient):
    """If compose fails entirely, returns 500."""
    mock_app = {"id": MOCK_APP_UUID, "root_node_id": MOCK_ROOT_NODE}

    with (
        patch(
            "src.api.root.auth_client.get_token_for_role",
            new_callable=AsyncMock,
            return_value="super-token",
        ),
        patch(
            "src.api.root.collider_client.get_app",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
        patch(
            "src.api.root.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
    ):
        mock_compose.side_effect = RuntimeError("Bootstrap failed")
        response = await client.post(
            "/agent/root/session",
            json={"app_id": MOCK_APP_UUID},
        )

    assert response.status_code == 500
    assert "Bootstrap failed" in response.json()["detail"]


async def test_root_session_missing_app_id(client: AsyncClient):
    """Missing app_id triggers 422."""
    response = await client.post("/agent/root/session", json={})
    assert response.status_code == 422


async def test_root_session_always_authenticates_as_superadmin(client: AsyncClient):
    """Root session always uses superadmin role regardless of request."""
    p1, p2, p3, p4 = _root_patches()
    with p1 as mock_auth, p2, p3, p4:
        await client.post("/agent/root/session", json={"app_id": MOCK_APP_UUID})

    mock_auth.assert_called_once_with("superadmin")
