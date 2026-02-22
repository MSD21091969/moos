"""Tests for /agent/session and /tools/discover endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


# ---------------------------------------------------------------------------
# POST /agent/session
# ---------------------------------------------------------------------------

VALID_CONTEXT_SET = {
    "role": "app_user",
    "app_id": "c57ab23a-4a57-4b28-a34c-9700320565ea",
    "node_ids": ["node-uuid-1"],
    "vector_query": None,
    "visibility_filter": ["global", "group"],
    "depth": None,
    "inherit_ancestors": False,
}

MOCK_PREVIEW = SessionPreview(
    node_count=3,
    skill_count=1,
    tool_count=5,
    role="app_user",
    vector_matches=0,
)


def _mock_composed(
    system_prompt: str = "system prompt text",
    tool_schemas: list | None = None,
    preview: SessionPreview | None = None,
) -> ComposedContext:
    return ComposedContext(
        system_prompt=system_prompt,
        agents_md="agent instructions",
        soul_md="rules",
        tools_md="reference docs",
        tool_schemas=tool_schemas or [{"name": "tool1"}],
        skills=[],
        preview=preview or MOCK_PREVIEW,
        session_meta={"role": "app_user", "app_id": "test"},
    )


async def test_create_session_success(client: AsyncClient):
    """Valid ContextSet returns a session_id, preview, and nanoclaw_ws_url."""
    with (
        patch(
            "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
        patch("src.main.write_workspace", new_callable=AsyncMock),
    ):
        mock_compose.return_value = _mock_composed()
        response = await client.post("/agent/session", json=VALID_CONTEXT_SET)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID
    preview = data["preview"]
    assert preview["node_count"] == 3
    assert preview["tool_count"] == 5
    assert preview["role"] == "app_user"
    assert "nanoclaw_ws_url" in data


async def test_create_session_stores_in_session_store(client: AsyncClient):
    """Session created by API is retrievable from the module-level store."""
    with (
        patch(
            "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
        patch("src.main.write_workspace", new_callable=AsyncMock),
    ):
        mock_compose.return_value = _mock_composed(system_prompt="stored prompt")
        response = await client.post("/agent/session", json=VALID_CONTEXT_SET)

    session_id = response.json()["session_id"]
    entry = session_store.get(session_id)
    assert entry is not None
    assert entry["system_prompt"] == "stored prompt"


async def test_create_session_writes_workspace(client: AsyncClient):
    """Session compose calls write_workspace with correct args."""
    with (
        patch(
            "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
        patch("src.main.write_workspace", new_callable=AsyncMock) as mock_write,
    ):
        mock_compose.return_value = _mock_composed()
        await client.post("/agent/session", json=VALID_CONTEXT_SET)

    mock_write.assert_called_once()
    call_kwargs = mock_write.call_args[1]
    assert call_kwargs["agents_md"] == "agent instructions"
    assert call_kwargs["soul_md"] == "rules"
    assert call_kwargs["tools_md"] == "reference docs"


async def test_create_session_invalid_role(client: AsyncClient):
    """Invalid role triggers 422 validation error."""
    bad_ctx = {**VALID_CONTEXT_SET, "role": "admin_hacker"}
    response = await client.post("/agent/session", json=bad_ctx)
    assert response.status_code == 422


async def test_create_session_compose_failure_returns_500(client: AsyncClient):
    """If compose_context_set raises, endpoint returns 500."""
    with patch(
        "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
    ) as mock_compose:
        mock_compose.side_effect = RuntimeError("DataServer unreachable")
        response = await client.post("/agent/session", json=VALID_CONTEXT_SET)

    assert response.status_code == 500
    assert "DataServer unreachable" in response.json()["detail"]


async def test_create_session_empty_node_ids(client: AsyncClient):
    """Empty node_ids is valid (falls back to app-wide bootstrap)."""
    ctx = {**VALID_CONTEXT_SET, "node_ids": []}
    with (
        patch(
            "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
        patch("src.main.write_workspace", new_callable=AsyncMock),
    ):
        mock_compose.return_value = _mock_composed(tool_schemas=[])
        response = await client.post("/agent/session", json=ctx)

    assert response.status_code == 200


async def test_create_session_workspace_failure_nonfatal(client: AsyncClient):
    """If write_workspace fails, session still returns successfully."""
    with (
        patch(
            "src.main.agent_runner.compose_context_set", new_callable=AsyncMock
        ) as mock_compose,
        patch("src.main.write_workspace", new_callable=AsyncMock) as mock_write,
    ):
        mock_compose.return_value = _mock_composed()
        mock_write.side_effect = OSError("Permission denied")
        response = await client.post("/agent/session", json=VALID_CONTEXT_SET)

    assert response.status_code == 200  # Non-fatal


# ---------------------------------------------------------------------------
# GET /tools/discover
# ---------------------------------------------------------------------------


async def test_tools_discover_proxies_to_graphtool(client: AsyncClient):
    """/tools/discover proxies to graph_tool_client.discover_tools."""
    mock_tools = [{"name": "list_apps", "description": "Lists apps", "score": 0.9}]

    with patch(
        "src.main.graph_tool_client.discover_tools", new_callable=AsyncMock
    ) as mock_disc:
        mock_disc.return_value = mock_tools
        response = await client.get("/tools/discover?query=list+apps")

    assert response.status_code == 200
    assert response.json() == mock_tools
    mock_disc.assert_called_once()


async def test_tools_discover_superadmin_gets_local_visibility(client: AsyncClient):
    """superadmin role includes 'local' in visibility filter."""
    with patch(
        "src.main.graph_tool_client.discover_tools", new_callable=AsyncMock
    ) as mock_disc:
        mock_disc.return_value = []
        await client.get("/tools/discover?query=any&role=superadmin")

    call_kwargs = mock_disc.call_args[1]
    assert "local" in call_kwargs["visibility_filter"]


async def test_tools_discover_app_user_excludes_local(client: AsyncClient):
    """app_user role does NOT include 'local' in visibility filter."""
    with patch(
        "src.main.graph_tool_client.discover_tools", new_callable=AsyncMock
    ) as mock_disc:
        mock_disc.return_value = []
        await client.get("/tools/discover?query=any&role=app_user")

    call_kwargs = mock_disc.call_args[1]
    assert "local" not in call_kwargs["visibility_filter"]
