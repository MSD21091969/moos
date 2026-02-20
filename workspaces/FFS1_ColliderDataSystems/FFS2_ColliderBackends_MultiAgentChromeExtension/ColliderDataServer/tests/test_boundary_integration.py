"""Integration tests for per-node API boundary enforcement."""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, UTC

from src.main import app
from src.schemas.nodes import NodeContainer, ApiBoundary
from src.db.models import Node, Application, User


@pytest.mark.asyncio
async def test_rest_boundary_enforcement(client, admin_headers):
    """Test that REST API respects api_boundary.rest."""
    from tests.conftest import test_session
    from src.db.models import Application, Node
    
    # Setup data
    async with test_session() as session:
        # Create App
        app = Application(display_name="boundary_test_app", config={})
        session.add(app)
        await session.commit()
        await session.refresh(app)
        
        # Create a node with REST disabled
        container_no_rest = NodeContainer(
            api_boundary=ApiBoundary(rest=False)
        )
        node_no_rest = Node(
            application_id=app.id,
            path="/no-rest",
            container=container_no_rest.model_dump(),
        )
        session.add(node_no_rest)
        
        # Create a node with REST enabled explicitly
        container_rest = NodeContainer(
            api_boundary=ApiBoundary(rest=True)
        )
        node_rest = Node(
            application_id=app.id,
            path="/yes-rest",
            container=container_rest.model_dump(),
        )
        session.add(node_rest)
        await session.commit()
        
        app_id = str(app.id)

    # 1. Access node with REST disabled -> 403
    resp = await client.get(
        "/api/v1/context/",
        params={"application_id": app_id, "path": "/no-rest"},
        headers=admin_headers
    )
    assert resp.status_code == 403
    assert "not permitted" in resp.json()["detail"]

    # 2. Access node with REST enabled -> 200
    resp = await client.get(
        "/api/v1/context/",
        params={"application_id": app_id, "path": "/yes-rest"},
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["container"]["api_boundary"]["rest"] is True


@pytest.mark.asyncio
async def test_sse_boundary_enforcement():
    """Test that broadcast_event respects api_boundary.sse."""
    from src.api.sse import broadcast_event, _clients as sse_clients
    import asyncio

    # Setup a fake client queue
    client_id = "test_client"
    queue = asyncio.Queue()
    sse_clients[client_id] = queue

    try:
        # 1. Broadcast event for node with SSE disabled
        container_no_sse = NodeContainer(
            api_boundary=ApiBoundary(sse=False)
        )
        await broadcast_event("update", {"container": container_no_sse.model_dump()})
        
        # Queue should be empty because event was dropped
        assert queue.empty()

        # 2. Broadcast event for node with SSE enabled
        container_sse = NodeContainer(
            api_boundary=ApiBoundary(sse=True)
        )
        await broadcast_event("update", {"container": container_sse.model_dump()})
        
        # Queue should have the event
        msg = await queue.get()
        assert msg["event"] == "update"
        assert msg["data"]["container"]["api_boundary"]["sse"] is True

    finally:
        sse_clients.pop(client_id, None)
