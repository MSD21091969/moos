"""Tests for Template Registry API."""

import pytest
from httpx import AsyncClient

from src.core.templates import registry

@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient):
    # Ensure registry is loaded
    registry.load_all()
    
    resp = await client.get("/api/v1/templates/")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 2
    
    names = [t["name"] for t in templates]
    assert "ide-workspace" in names
    assert "chrome-agent" in names


@pytest.mark.asyncio
async def test_get_template_details(client: AsyncClient):
    registry.load_all()
    
    resp = await client.get("/api/v1/templates/ide-workspace")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ide-workspace"
    assert data["species"] == "ide"
    assert data["container"]["api_boundary"]["native_messaging"] is True


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient):
    registry.load_all()
    
    resp = await client.get("/api/v1/templates/non-existent-template")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_instantiate_placeholder(client: AsyncClient):
    resp = await client.post("/api/v1/templates/ide-workspace/instantiate")
    assert resp.status_code == 200
    assert "Not implemented yet" in resp.json()["message"]
