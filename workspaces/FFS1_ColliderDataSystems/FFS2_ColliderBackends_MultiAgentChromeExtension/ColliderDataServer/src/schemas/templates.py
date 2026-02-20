"""Collider Template Cluster — versioned library of pre-hydrated containers.

A TemplateCluster is a portable registry of NodeContainer templates that
can be instantiated into new nodes.  Think: workspace/workflow/tool
starter kits that ship with sensible defaults.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.schemas.nodes import ContainerSpecies, NodeContainer


class TemplateEntry(BaseModel):
    """One named template in a cluster."""

    name: str
    description: str = ""
    species: ContainerSpecies = ContainerSpecies.CUSTOM
    container: NodeContainer = NodeContainer()


class TemplateCluster(BaseModel):
    """Versioned library of hydrated workspace context templates.

    Initially loaded from YAML/JSON on disk (alongside ``.agent/``),
    later served via API.
    """

    version: str = "1.0.0"
    name: str
    templates: list[TemplateEntry] = []
