from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_app(client: AsyncClient, admin_headers: dict):
    response = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Test App"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == "Test App"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_apps(client: AsyncClient, admin_headers: dict):
    await client.post(
        "/api/v1/apps/",
        json={"display_name": "List Test"},
        headers=admin_headers,
    )
    response = await client.get("/api/v1/apps/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_app(client: AsyncClient, admin_headers: dict):
    create = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Get Test"},
        headers=admin_headers,
    )
    assert create.status_code == 201
    app_id = create.json()["id"]

    response = await client.get(f"/api/v1/apps/{app_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == app_id


@pytest.mark.asyncio
async def test_get_app_not_found(client: AsyncClient, admin_headers: dict):
    response = await client.get(
        "/api/v1/apps/00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_app_unauthenticated(client: AsyncClient):
    response = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Unauth Test"},
    )
    assert response.status_code == 401
