"""Node API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db import get_db, Application, Node
from src.schemas import NodeCreate, NodeUpdate, NodeResponse
from src.api.permissions import RequireRead, RequireWrite
from src.inheritance import resolve_container
from src.api.sse import broadcast_event

router = APIRouter(prefix="/apps/{app_id}/nodes", tags=["nodes"])


@router.get("", response_model=NodeResponse)
async def get_node(
    app_id: str,
    path: str = Query(..., description="Node path, e.g., /dashboard"),
    perm: RequireRead = None,  # Enforces read permission
    db: AsyncSession = Depends(get_db),
):
    """Get node by path within an application (requires read permission)."""
    # perm.application is already verified
    app = perm.application

    # Get node
    result = await db.execute(
        select(Node).where(Node.application_id == app.id, Node.path == path)
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return NodeResponse.model_validate(node)


@router.get("/tree", response_model=list[NodeResponse])
async def get_node_tree(
    app_id: str,
    perm: RequireRead = None,  # Enforces read permission
    db: AsyncSession = Depends(get_db),
):
    """Get all nodes for an application as a flat list (requires read permission)."""
    app = perm.application

    result = await db.execute(
        select(Node).where(Node.application_id == app.id).order_by(Node.path)
    )
    nodes = result.scalars().all()

    return [NodeResponse.model_validate(n) for n in nodes]


@router.post("", response_model=NodeResponse)
async def create_node(
    app_id: str,
    data: NodeCreate,
    perm: RequireWrite = None,  # Enforces write permission
    db: AsyncSession = Depends(get_db),
):
    """Create a new node in an application (requires write permission)."""
    app = perm.application

    # Check if path already exists
    existing = await db.execute(
        select(Node).where(Node.application_id == app.id, Node.path == data.path)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Node path already exists")

    node = Node(
        application_id=app.id,
        parent_id=data.parent_id,
        path=data.path,
        container=data.container.model_dump(),
        node_metadata=data.node_metadata,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)

    # Set root_node_id if this is the first node
    if data.path == "/" and not app.root_node_id:
        app.root_node_id = node.id
        await db.commit()

    # Broadcast SSE event
    response = NodeResponse.model_validate(node)
    await broadcast_event(
        "node_created",
        {
            "node": response.model_dump(),
            "app_id": app_id,
        },
    )

    return response


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    app_id: str,
    node_id: str,
    data: NodeUpdate,
    perm: RequireWrite = None,  # Enforces write permission
    db: AsyncSession = Depends(get_db),
):
    """Update a node's container or metadata (requires write permission)."""
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Verify node belongs to the app
    if node.application_id != perm.application.id:
        raise HTTPException(
            status_code=404, detail="Node not found in this application"
        )

    if data.container is not None:
        node.container = data.container.model_dump()
    if data.node_metadata is not None:
        node.node_metadata = data.node_metadata

    await db.commit()
    await db.refresh(node)

    # Broadcast SSE event
    response = NodeResponse.model_validate(node)
    await broadcast_event(
        "node_updated",
        {
            "node": response.model_dump(),
            "app_id": app_id,
            "node_path": node.path,
        },
    )

    return response


@router.get("/resolved", response_model=dict)
async def get_resolved_container(
    app_id: str,
    path: str = Query(..., description="Node path, e.g., /dashboard"),
    perm: RequireRead = None,  # Enforces read permission
    db: AsyncSession = Depends(get_db),
):
    """
    Get a node's container with inheritance resolved.

    This returns the fully merged container, combining:
    - Root (/) container
    - All ancestor containers
    - The target node's container

    Child values override parent values per inheritance rules.
    """
    app = perm.application

    # Get all nodes for this application
    result = await db.execute(select(Node).where(Node.application_id == app.id))
    nodes = result.scalars().all()

    # Build containers dict
    containers = {n.path: n.container for n in nodes}

    if path not in containers:
        raise HTTPException(status_code=404, detail="Node not found")

    # Resolve inheritance
    resolved = resolve_container(path, containers)

    return {
        "path": path,
        "container": resolved,
        "ancestry": _get_ancestry(path),
    }


def _get_ancestry(path: str) -> list[str]:
    """Get list of ancestor paths from root to the given path."""
    if path == "/":
        return ["/"]

    ancestry = ["/"]
    parts = path.strip("/").split("/")
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        ancestry.append(current)

    return ancestry


@router.delete("/{node_id}")
async def delete_node(
    app_id: str,
    node_id: str,
    perm: RequireWrite = None,  # Enforces write permission
    db: AsyncSession = Depends(get_db),
):
    """Delete a node (requires write permission)."""
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Verify node belongs to the app
    if node.application_id != perm.application.id:
        raise HTTPException(
            status_code=404, detail="Node not found in this application"
        )

    node_path = node.path
    await db.delete(node)
    await db.commit()

    # Broadcast SSE event
    await broadcast_event(
        "node_deleted",
        {
            "node_id": node_id,
            "node_path": node_path,
            "app_id": app_id,
        },
    )

    return {"deleted": node_id}
