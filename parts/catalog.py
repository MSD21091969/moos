"""The Parts Catalog.

This is the SINGLE SOURCE OF TRUTH for what the Factory exports.
If it is in CATALOG, it is a supported Part.
"""
from enum import Enum
from typing import TypedDict, Optional, Dict, Any

class PartType(str, Enum):
    AGENT = "agent"
    SKILL = "skill"
    TEMPLATE = "template"
    TOOLSET = "toolset"

class PartStatus(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"

class PartMetadata(TypedDict):
    name: str
    type: PartType
    path: str
    description: str
    status: PartStatus
    config_schema: Optional[Dict[str, Any]]

CATALOG: Dict[str, PartMetadata] = {
    # Templates
    "deep_agent_v1": {
        "name": "deep_agent",
        "type": PartType.TEMPLATE,
        "path": "agent_factory.parts.templates.deep_agent:DeepAgent",
        "description": "Standard DeepAgent Class",
        "status": PartStatus.STABLE,
        "config_schema": None
    },
    
    # Toolsets
    "filesystem_v1": {
        "name": "filesystem_toolset",
        "type": PartType.TOOLSET,
        "path": "agent_factory.parts.toolsets.filesystem:FilesystemToolset",
        "description": "Scoped File Operations",
        "status": PartStatus.STABLE,
        "config_schema": {"root": "string"}
    },

    # Agents
    "tracer_v1": {
        "name": "tracer_agent",
        "type": PartType.AGENT,
        "path": "agent_factory.parts.agents.tracer:TracerAgent",
        "description": "Pipeline Verification Agent",
        "status": PartStatus.STABLE,
        "config_schema": None
    }
}

def get_part(name: str) -> Optional[PartMetadata]:
    return CATALOG.get(name)
