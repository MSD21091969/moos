"""REST API routes for the Tool Registry.

Provides endpoints for:
- Registering tools and workflows
- Discovering tools (filtered by query, visibility, user)
- Inspecting registry stats
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.schemas.registry import GraphStepEntry, SubgraphManifest, ToolQuery

# Registry instance is injected at app startup (see main.py)
from src.core.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])

# Module-level reference set by main.py
_registry: ToolRegistry | None = None


def set_registry(registry: ToolRegistry) -> None:
    """Called by main.py to inject the shared registry instance."""
    global _registry
    _registry = registry


def _get_registry() -> ToolRegistry:
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    return _registry


# ------------------------------------------------------------------
# Tool endpoints
# ------------------------------------------------------------------


@router.post("/tools", status_code=201)
async def register_tool(entry: GraphStepEntry):
    """Register a new tool. Returns the generated args model schema."""
    registry = _get_registry()
    model = await registry.register_tool(entry)
    return {
        "tool_name": entry.tool_name,
        "args_schema": model.model_json_schema(),
        "status": "registered",
    }


@router.post("/tools/discover")
async def discover_tools(query: ToolQuery):
    """Discover tools matching query criteria."""
    registry = _get_registry()
    results = await registry.discover_tools(query)
    return {
        "query": query.query,
        "count": len(results),
        "tools": [r.model_dump() for r in results],
    }


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get details for a specific tool."""
    registry = _get_registry()
    entry = registry.get_tool(tool_name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    args_model = registry.get_args_model(tool_name)
    return {
        "tool": entry.model_dump(),
        "args_schema": args_model.model_json_schema() if args_model else None,
    }


@router.delete("/tools/{tool_name}")
async def unregister_tool(tool_name: str):
    """Remove a tool from the registry."""
    registry = _get_registry()
    if not registry.unregister_tool(tool_name):
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return {"tool_name": tool_name, "status": "unregistered"}


# ------------------------------------------------------------------
# Workflow endpoints
# ------------------------------------------------------------------


@router.post("/workflows", status_code=201)
async def register_workflow(manifest: SubgraphManifest):
    """Register a workflow (subgraph manifest)."""
    registry = _get_registry()
    registry.register_workflow(manifest)
    return {
        "workflow_name": manifest.workflow_name,
        "steps": manifest.steps,
        "status": "registered",
    }


@router.get("/workflows/{workflow_name}")
async def get_workflow(workflow_name: str):
    """Get details for a specific workflow."""
    registry = _get_registry()
    manifest = registry.get_workflow(workflow_name)
    if not manifest:
        raise HTTPException(
            status_code=404, detail=f"Workflow '{workflow_name}' not found"
        )
    return manifest.model_dump()


@router.delete("/workflows/{workflow_name}")
async def unregister_workflow(workflow_name: str):
    """Remove a workflow from the registry."""
    registry = _get_registry()
    if not registry.unregister_workflow(workflow_name):
        raise HTTPException(
            status_code=404, detail=f"Workflow '{workflow_name}' not found"
        )
    return {"workflow_name": workflow_name, "status": "unregistered"}


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------


@router.get("/stats")
async def registry_stats():
    """Return registry summary statistics."""
    registry = _get_registry()
    return registry.stats().model_dump()
