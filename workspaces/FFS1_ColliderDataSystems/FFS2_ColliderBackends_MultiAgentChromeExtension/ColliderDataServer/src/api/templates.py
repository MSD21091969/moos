"""Template Registry API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.core.templates import registry
from src.schemas.templates import TemplateEntry

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("/", response_model=list[TemplateEntry])
async def list_templates():
    """List all available node templates."""
    return registry.list_templates()


@router.get("/{name}", response_model=TemplateEntry)
async def get_template(name: str):
    """Get a specific template by name."""
    template = registry.get_template(name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return template


@router.post("/{name}/instantiate")
async def instantiate_template(name: str):
    """(Future) Instantiate a template into a new node.
    
    For now, the frontend can just fetch the template and use `POST /nodes`
    to create the node with the template's container.
    """
    # Placeholder for server-side instantiation logic if needed later
    return {"message": "Not implemented yet. Use GET to fetch container and POST /nodes to create."}
