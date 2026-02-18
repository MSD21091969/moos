from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_nodes(client: AsyncClient, admin_headers: dict):
    # Create an app first
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Node Test App"},
        headers=admin_headers,
    )
    assert app_resp.status_code == 201
    app_id = app_resp.json()["id"]

    # Create a root node
    node_resp = await client.post(
        f"/api/v1/apps/{app_id}/nodes/",
        json={
            "path": "/",
            "container": {"manifest": {"name": "test"}, "instructions": []},
        },
        headers=admin_headers,
    )
    assert node_resp.status_code == 201
    node_data = node_resp.json()
    assert node_data["path"] == "/"

    # List nodes
    list_resp = await client.get(
        f"/api/v1/apps/{app_id}/nodes/",
        headers=admin_headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_tree(client: AsyncClient, admin_headers: dict):
    # Create app
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Tree Test"},
        headers=admin_headers,
    )
    app_id = app_resp.json()["id"]

    # Create root node
    root = await client.post(
        f"/api/v1/apps/{app_id}/nodes/",
        json={"path": "/", "container": {}},
        headers=admin_headers,
    )
    root_id = root.json()["id"]

    # Create child node
    await client.post(
        f"/api/v1/apps/{app_id}/nodes/",
        json={"path": "/child", "parent_id": root_id, "container": {}},
        headers=admin_headers,
    )

    # Get tree
    tree_resp = await client.get(
        f"/api/v1/apps/{app_id}/nodes/tree",
        headers=admin_headers,
    )
    assert tree_resp.status_code == 200
    tree = tree_resp.json()
    assert len(tree) >= 1


@pytest.mark.asyncio
async def test_node_not_found(client: AsyncClient, admin_headers: dict):
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Not Found"},
        headers=admin_headers,
    )
    app_id = app_resp.json()["id"]
    response = await client.get(
        f"/api/v1/apps/{app_id}/nodes/00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )
    assert response.status_code == 404
