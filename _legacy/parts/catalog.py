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
        "config_schema": None,
    },
    "agent_spec_v1": {
        "name": "agent_spec",
        "type": PartType.TEMPLATE,
        "path": "agent_factory.parts.templates.agent_spec:AgentSpec",
        "description": "Generic Agent Specification Template - unified pattern for L1 workspace agents and L2 application pilots",
        "status": PartStatus.STABLE,
        "config_schema": {
            "id": "string",
            "name": "string",
            "agent_dir": "string (optional)",
            "model": "string",
            "temperature": "number",
            "max_tokens": "number",
        },
    },
    # Toolsets
    "filesystem_v1": {
        "name": "filesystem_toolset",
        "type": PartType.TOOLSET,
        "path": "agent_factory.parts.toolsets.filesystem:FilesystemToolset",
        "description": "Scoped File Operations",
        "status": PartStatus.STABLE,
        "config_schema": {"root": "string"},
    },
    # Agents
    "tracer_v1": {
        "name": "tracer_agent",
        "type": PartType.AGENT,
        "path": "agent_factory.parts.agents.tracer:TracerAgent",
        "description": "Pipeline Verification Agent",
        "status": PartStatus.STABLE,
        "config_schema": None,
    },
    "workspace_agent_v1": {
        "name": "workspace_agent",
        "type": PartType.AGENT,
        "path": "agent_factory.parts.agents.workspace_agent:WorkspaceAgent",
        "description": "Generic L1 workspace agent - operates on filesystem/code with .agent/ hierarchy",
        "status": PartStatus.BETA,
        "config_schema": {
            "workspace_path": "Path (optional, default: cwd)",
            "agent_id": "string (default: 'workspace')",
        },
    },
    # Runtimes
    "workspace_runner_v1": {
        "name": "workspace_runner",
        "type": PartType.TEMPLATE,  # Using TEMPLATE as no RUNTIME type
        "path": "agent_factory.parts.runtimes.workspace_runner:WorkspaceRunner",
        "description": "TUI/Headless runner for workspace agents - textual-based chat interface",
        "status": PartStatus.BETA,
        "config_schema": {
            "provider": "string (default: 'gemini')",
            "model": "string (default: 'gemini-2.0-flash')",
            "stream_responses": "bool (default: true)",
        },
    },
    # Config
    "workspace_settings_v1": {
        "name": "workspace_settings",
        "type": PartType.TEMPLATE,
        "path": "agent_factory.parts.config.settings:load_workspace_settings",
        "description": "Workspace settings loader - merges .agent/configs/ hierarchy",
        "status": PartStatus.STABLE,
        "config_schema": None,
    },
}


def get_part(name: str) -> Optional[PartMetadata]:
    return CATALOG.get(name)
