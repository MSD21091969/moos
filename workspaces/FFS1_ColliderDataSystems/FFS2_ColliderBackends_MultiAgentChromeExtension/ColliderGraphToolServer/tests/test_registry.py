"""Tests for the GraphToolServer Tool Registry (Phase 2).

Covers:
- model_factory: JSON Schema → Pydantic model via create_model()
- tool_registry: register / discover / unregister / stats
- REST API: full CRUD lifecycle via httpx TestClient
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from src.core.model_factory import build_args_model
from src.core.tool_registry import ToolRegistry
from src.schemas.registry import GraphStepEntry, SubgraphManifest, ToolQuery


# ===================================================================
# model_factory
# ===================================================================


class TestModelFactory:
    def test_simple_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer"},
            },
            "required": ["query"],
        }
        Model = build_args_model("search", schema)
        assert issubclass(Model, BaseModel)
        assert Model.__name__ == "SearchArgs"

        m = Model(query="hello", top_k=5)
        assert m.query == "hello"
        assert m.top_k == 5

    def test_optional_fields_default_to_none(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["name"],
        }
        Model = build_args_model("my_tool", schema)
        m = Model(name="test")
        assert m.name == "test"
        assert m.limit is None

    def test_explicit_defaults(self):
        schema = {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "default": "fast"},
                "count": {"type": "integer", "default": 10},
            },
        }
        Model = build_args_model("config_tool", schema)
        m = Model()
        assert m.mode == "fast"
        assert m.count == 10

    def test_all_json_types(self):
        schema = {
            "type": "object",
            "properties": {
                "s": {"type": "string"},
                "i": {"type": "integer"},
                "n": {"type": "number"},
                "b": {"type": "boolean"},
                "a": {"type": "array"},
                "o": {"type": "object"},
            },
            "required": ["s", "i", "n", "b", "a", "o"],
        }
        Model = build_args_model("all_types", schema)
        m = Model(s="x", i=1, n=1.5, b=True, a=[1, 2], o={"k": "v"})
        assert m.s == "x"
        assert m.n == 1.5
        assert m.b is True

    def test_empty_schema(self):
        Model = build_args_model("empty", {})
        m = Model()
        assert isinstance(m, BaseModel)

    def test_class_name_formatting(self):
        Model = build_args_model("analyze_code_quality", {})
        assert Model.__name__ == "AnalyzeCodeQualityArgs"


# ===================================================================
# tool_registry
# ===================================================================


def _make_entry(
    name: str = "test_tool",
    visibility: str = "global",
    user: str = "user1",
    node: str = "node1",
) -> GraphStepEntry:
    return GraphStepEntry(
        tool_name=name,
        origin_node_id=node,
        owner_user_id=user,
        params_schema={
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        },
        visibility=visibility,
    )


class TestToolRegistry:
    @pytest.mark.asyncio
    async def test_register_and_get(self):
        reg = ToolRegistry()
        entry = _make_entry("search")
        model = await reg.register_tool(entry)

        assert issubclass(model, BaseModel)
        assert reg.get_tool("search") is entry
        assert reg.get_args_model("search") is model

    @pytest.mark.asyncio
    async def test_discover_all(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("search"))
        await reg.register_tool(_make_entry("analyze"))

        results = await reg.discover_tools(ToolQuery())
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_discover_by_text(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("search"))
        await reg.register_tool(_make_entry("analyze"))

        results = await reg.discover_tools(ToolQuery(query="sear"))
        assert len(results) == 1
        assert results[0].tool_name == "search"

    @pytest.mark.asyncio
    async def test_discover_visibility_filter(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("pub_tool", visibility="global"))
        await reg.register_tool(_make_entry("priv_tool", visibility="local"))

        results = await reg.discover_tools(
            ToolQuery(visibility_filter=["global"])
        )
        assert len(results) == 1
        assert results[0].tool_name == "pub_tool"

    @pytest.mark.asyncio
    async def test_discover_local_user_filter(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("my_tool", visibility="local", user="alice"))

        # Alice can see her own local tool
        results = await reg.discover_tools(
            ToolQuery(user_id="alice", visibility_filter=["local"])
        )
        assert len(results) == 1

        # Bob cannot see Alice's local tool
        results = await reg.discover_tools(
            ToolQuery(user_id="bob", visibility_filter=["local"])
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_unregister(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("temp"))
        assert reg.unregister_tool("temp") is True
        assert reg.get_tool("temp") is None
        assert reg.unregister_tool("temp") is False

    @pytest.mark.asyncio
    async def test_stats(self):
        reg = ToolRegistry()
        await reg.register_tool(_make_entry("t1", visibility="global"))
        await reg.register_tool(_make_entry("t2", visibility="local"))
        reg.register_workflow(
            SubgraphManifest(
                workflow_name="w1",
                origin_node_id="n1",
                owner_user_id="u1",
                steps=["t1", "t2"],
                entry_point="t1",
            )
        )
        s = reg.stats()
        assert s.total_tools == 2
        assert s.total_workflows == 1
        assert s.by_visibility == {"global": 1, "local": 1}

    @pytest.mark.asyncio
    async def test_workflow_register_and_discover(self):
        reg = ToolRegistry()
        manifest = SubgraphManifest(
            workflow_name="ci_pipeline",
            origin_node_id="n1",
            owner_user_id="u1",
            steps=["lint", "test", "deploy"],
            entry_point="lint",
        )
        reg.register_workflow(manifest)

        results = reg.discover_workflows(query="ci")
        assert len(results) == 1
        assert results[0].workflow_name == "ci_pipeline"


# ===================================================================
# REST API
# ===================================================================


@pytest.fixture
def app():
    from src.main import app as fastapi_app, tool_registry

    # Reset registry between tests
    tool_registry._tools.clear()
    tool_registry._workflows.clear()
    tool_registry._models.clear()
    return fastapi_app


class TestRegistryAPI:
    @pytest.mark.anyio
    async def test_register_tool(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/registry/tools",
                json={
                    "tool_name": "search",
                    "origin_node_id": "node1",
                    "owner_user_id": "user1",
                    "params_schema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                    "visibility": "global",
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["tool_name"] == "search"
            assert data["status"] == "registered"
            assert "args_schema" in data

    @pytest.mark.anyio
    async def test_discover_tools(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Register two tools
            for name in ["search", "analyze"]:
                await client.post(
                    "/api/v1/registry/tools",
                    json={
                        "tool_name": name,
                        "origin_node_id": "n1",
                        "owner_user_id": "u1",
                        "params_schema": {},
                        "visibility": "global",
                    },
                )

            resp = await client.post(
                "/api/v1/registry/tools/discover",
                json={"query": "sear"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 1
            assert data["tools"][0]["tool_name"] == "search"

    @pytest.mark.anyio
    async def test_get_tool(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/registry/tools",
                json={
                    "tool_name": "lookup",
                    "origin_node_id": "n1",
                    "owner_user_id": "u1",
                    "params_schema": {
                        "type": "object",
                        "properties": {"key": {"type": "string"}},
                        "required": ["key"],
                    },
                    "visibility": "global",
                },
            )

            resp = await client.get("/api/v1/registry/tools/lookup")
            assert resp.status_code == 200
            assert resp.json()["tool"]["tool_name"] == "lookup"

    @pytest.mark.anyio
    async def test_get_tool_not_found(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/registry/tools/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_tool(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/registry/tools",
                json={
                    "tool_name": "temp",
                    "origin_node_id": "n1",
                    "owner_user_id": "u1",
                    "params_schema": {},
                    "visibility": "local",
                },
            )

            resp = await client.delete("/api/v1/registry/tools/temp")
            assert resp.status_code == 200
            assert resp.json()["status"] == "unregistered"

            resp = await client.get("/api/v1/registry/tools/temp")
            assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_workflow_lifecycle(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Register
            resp = await client.post(
                "/api/v1/registry/workflows",
                json={
                    "workflow_name": "deploy",
                    "origin_node_id": "n1",
                    "owner_user_id": "u1",
                    "steps": ["build", "test", "ship"],
                    "entry_point": "build",
                },
            )
            assert resp.status_code == 201

            # Get
            resp = await client.get("/api/v1/registry/workflows/deploy")
            assert resp.status_code == 200
            assert resp.json()["workflow_name"] == "deploy"

            # Delete
            resp = await client.delete("/api/v1/registry/workflows/deploy")
            assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_stats(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/registry/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_tools"] == 0
            assert data["total_workflows"] == 0

    @pytest.mark.anyio
    async def test_health_includes_registry(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "registry" in data
            assert data["registry"]["total_tools"] == 0
