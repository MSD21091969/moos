"""
Local UX Runtime
================
Factory-level CLI tool for running workspace agents and pilots.

Two modes:
1. Workspace Agent: Loads from .agent/ hierarchy, uses WorkspaceContext
2. Pilot: Loads from pilots/ folders via ColliderPilotSpec, uses ContainerContext

Uses Factory patterns:
- AgentSpec for workspace agents
- ColliderPilotSpec for pilots
- DeepAgentCLI for Rich terminal interface

Usage:
    local-ux agent                    # Run workspace agent from cwd
    local-ux agent --workspace PATH   # Run from specific workspace
    local-ux pilot container          # Run container pilot
"""

from .context import (
    WorkspaceContext,
    ContainerContext,
    build_workspace_context,
    build_container_context,
)
from .workspace_agent import (
    run_workspace_agent,
    load_agent_hierarchy,
    find_agent_dirs,
    merge_agent_specs,
)
from .pilot_agent import run_pilot, load_pilot_spec

__all__ = [
    # Workspace Agent
    "run_workspace_agent",
    "load_agent_hierarchy",
    "find_agent_dirs",
    "merge_agent_specs",
    # Pilot
    "run_pilot",
    "load_pilot_spec",
    # Context
    "WorkspaceContext",
    "ContainerContext",
    "build_workspace_context",
    "build_container_context",
]
