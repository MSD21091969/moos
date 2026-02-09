from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_nodes(client: AsyncClient):
    # Create an app first
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"app_id": "node-test-app", "display_name": "Node Test App"},
    )
    assert app_resp.status_code == 201

    # Create a root node
    node_resp = await client.post(
        "/api/v1/apps/node-test-app/nodes/",
        json={
            "path": "/",
            "container": {"manifest": {"name": "test"}, "instructions": []},
        },
    )
    assert node_resp.status_code == 201
    node_data = node_resp.json()
    assert node_data["path"] == "/"

    # List nodes
    list_resp = await client.get("/api/v1/apps/node-test-app/nodes/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_tree(client: AsyncClient):
    # Create app
    await client.post(
        "/api/v1/apps/",
        json={"app_id": "tree-test-app", "display_name": "Tree Test"},
    )

    # Create root node
    root = await client.post(
        "/api/v1/apps/tree-test-app/nodes/",
        json={"path": "/", "container": {}},
    )
    root_id = root.json()["id"]

    # Create child node
    await client.post(
        "/api/v1/apps/tree-test-app/nodes/",
        json={"path": "/child", "parent_id": root_id, "container": {}},
    )

    # Get tree
    tree_resp = await client.get("/api/v1/apps/tree-test-app/nodes/tree")
    assert tree_resp.status_code == 200
    tree = tree_resp.json()
    assert len(tree) >= 1


@pytest.mark.asyncio
async def test_node_not_found(client: AsyncClient):
    await client.post(
        "/api/v1/apps/",
        json={"app_id": "notfound-app", "display_name": "Not Found"},
    )
    response = await client.get(
        "/api/v1/apps/notfound-app/nodes/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
