from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_app(client: AsyncClient):
    response = await client.post(
        "/api/v1/apps/",
        json={"app_id": "test-app", "display_name": "Test App"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["app_id"] == "test-app"
    assert data["display_name"] == "Test App"


@pytest.mark.asyncio
async def test_list_apps(client: AsyncClient):
    # Create an app first
    await client.post(
        "/api/v1/apps/",
        json={"app_id": "list-test", "display_name": "List Test"},
    )
    response = await client.get("/api/v1/apps/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_app(client: AsyncClient):
    # Create
    create = await client.post(
        "/api/v1/apps/",
        json={"app_id": "get-test", "display_name": "Get Test"},
    )
    assert create.status_code == 201

    # Get
    response = await client.get("/api/v1/apps/get-test")
    assert response.status_code == 200
    assert response.json()["app_id"] == "get-test"


@pytest.mark.asyncio
async def test_get_app_not_found(client: AsyncClient):
    response = await client.get("/api/v1/apps/nonexistent")
    assert response.status_code == 404
