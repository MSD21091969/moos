"""Tests for the evolved NodeContainer and related typed models.

Validates:
- Backward compat: empty NodeContainer matches v0 behavior
- New fields: version, species, api_boundary
- ToolDefinition / WorkflowDefinition round-trip
- TemplateCluster serialization
- ApiBoundary enforcement helper
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.core.boundary import enforce_node_boundary
from src.schemas.nodes import (
    ApiBoundary,
    ContainerSpecies,
    NodeContainer,
    ToolDefinition,
    WorkflowDefinition,
    WorkflowStep,
)
from src.schemas.templates import TemplateCluster, TemplateEntry


# ---------------------------------------------------------------------------
# NodeContainer backward compatibility
# ---------------------------------------------------------------------------


class TestNodeContainerBackwardCompat:
    """An empty NodeContainer must behave exactly like the v0 schema."""

    def test_empty_container_defaults(self):
        c = NodeContainer()
        assert c.version == "1.0.0"
        assert c.species is None
        assert c.manifest == {}
        assert c.instructions == []
        assert c.rules == []
        assert c.skills == []
        assert c.knowledge == []
        assert c.configs == {}
        assert c.tools == []
        assert c.workflows == []

    def test_legacy_dict_round_trip(self):
        """A v0-shaped dict (no version/species) should parse without error."""
        legacy = {
            "manifest": {"name": "test"},
            "instructions": ["do stuff"],
            "rules": ["be safe"],
            "skills": [],
            "tools": [],
            "knowledge": [],
            "workflows": [],
            "configs": {"key": "val"},
        }
        c = NodeContainer(**legacy)
        assert c.manifest == {"name": "test"}
        assert c.version == "1.0.0"
        assert c.species is None
        assert c.api_boundary == ApiBoundary()


# ---------------------------------------------------------------------------
# ContainerSpecies & ApiBoundary
# ---------------------------------------------------------------------------


class TestContainerSpecies:
    def test_species_values(self):
        assert ContainerSpecies.IDE == "ide"
        assert ContainerSpecies.OFFICE == "office"
        assert ContainerSpecies.CLOUD == "cloud"
        assert ContainerSpecies.SETTINGS == "settings"
        assert ContainerSpecies.CUSTOM == "custom"

    def test_species_on_container(self):
        c = NodeContainer(species=ContainerSpecies.IDE)
        assert c.species == ContainerSpecies.IDE
        dumped = c.model_dump()
        assert dumped["species"] == "ide"


class TestApiBoundary:
    def test_defaults(self):
        b = ApiBoundary()
        assert b.rest is True
        assert b.sse is True
        assert b.websocket is False
        assert b.webrtc is False
        assert b.native_messaging is False
        assert b.grpc is False

    def test_ide_boundary(self):
        b = ApiBoundary(
            rest=True,
            sse=True,
            websocket=True,
            native_messaging=True,
        )
        assert b.native_messaging is True
        assert b.webrtc is False  # still default


# ---------------------------------------------------------------------------
# ToolDefinition & WorkflowDefinition
# ---------------------------------------------------------------------------


class TestToolDefinition:
    def test_minimal_tool(self):
        t = ToolDefinition(name="search")
        assert t.name == "search"
        assert t.description == ""
        assert t.params_schema == {}
        assert t.code_ref == ""
        assert t.visibility == "local"

    def test_full_tool(self):
        t = ToolDefinition(
            name="analyze_codebase",
            description="AST analysis tool",
            params_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
            code_ref="tools.analyze:run",
            visibility="global",
        )
        assert t.visibility == "global"
        assert "path" in t.params_schema["properties"]

    def test_tool_in_container(self):
        c = NodeContainer(
            tools=[
                ToolDefinition(name="t1", code_ref="m1:f1"),
                ToolDefinition(name="t2", code_ref="m2:f2", visibility="group"),
            ]
        )
        assert len(c.tools) == 2
        assert c.tools[1].visibility == "group"


class TestWorkflowDefinition:
    def test_minimal_workflow(self):
        w = WorkflowDefinition(name="deploy")
        assert w.steps == []
        assert w.entry_step is None

    def test_workflow_with_steps(self):
        w = WorkflowDefinition(
            name="ci_pipeline",
            description="Run CI",
            entry_step="lint",
            steps=[
                WorkflowStep(tool_name="lint"),
                WorkflowStep(
                    tool_name="test",
                    condition="lint.success",
                    inputs_map={"test_dir": "lint.output_dir"},
                ),
                WorkflowStep(tool_name="deploy", condition="test.success"),
            ],
        )
        assert len(w.steps) == 3
        assert w.steps[1].condition == "lint.success"

    def test_workflow_in_container(self):
        c = NodeContainer(
            workflows=[WorkflowDefinition(name="w1")],
        )
        assert len(c.workflows) == 1
        dumped = c.model_dump()
        assert dumped["workflows"][0]["name"] == "w1"


# ---------------------------------------------------------------------------
# TemplateCluster
# ---------------------------------------------------------------------------


class TestTemplateCluster:
    def test_empty_cluster(self):
        tc = TemplateCluster(name="default")
        assert tc.version == "1.0.0"
        assert tc.templates == []

    def test_cluster_with_templates(self):
        tc = TemplateCluster(
            name="starter-kit",
            version="1.0.0",
            templates=[
                TemplateEntry(
                    name="ide-workspace",
                    species=ContainerSpecies.IDE,
                    container=NodeContainer(
                        species=ContainerSpecies.IDE,
                        api_boundary=ApiBoundary(
                            websocket=True, native_messaging=True
                        ),
                        tools=[ToolDefinition(name="file_search")],
                    ),
                ),
                TemplateEntry(
                    name="cloud-service",
                    species=ContainerSpecies.CLOUD,
                    container=NodeContainer(
                        species=ContainerSpecies.CLOUD,
                        api_boundary=ApiBoundary(websocket=True, webrtc=True),
                    ),
                ),
            ],
        )
        assert len(tc.templates) == 2
        assert tc.templates[0].container.api_boundary.native_messaging is True
        assert tc.templates[1].container.api_boundary.webrtc is True


# ---------------------------------------------------------------------------
# Boundary enforcement
# ---------------------------------------------------------------------------


class TestBoundaryEnforcement:
    @pytest.mark.anyio
    async def test_allowed_protocol(self):
        """REST is allowed by default — should not raise."""
        container_data = NodeContainer().model_dump()
        await enforce_node_boundary(container_data, "rest")

    @pytest.mark.anyio
    async def test_denied_protocol(self):
        """WebSocket is denied by default — should raise 403."""
        container_data = NodeContainer().model_dump()
        with pytest.raises(HTTPException) as exc_info:
            await enforce_node_boundary(container_data, "websocket")
        assert exc_info.value.status_code == 403

    @pytest.mark.anyio
    async def test_custom_boundary_allows(self):
        """If api_boundary grants websocket, it should pass."""
        c = NodeContainer(api_boundary=ApiBoundary(websocket=True))
        await enforce_node_boundary(c.model_dump(), "websocket")

    @pytest.mark.anyio
    async def test_legacy_empty_container(self):
        """An empty dict (v0 container) should fallback to defaults."""
        await enforce_node_boundary({}, "rest")  # allowed
        with pytest.raises(HTTPException):
            await enforce_node_boundary({}, "native_messaging")  # denied
