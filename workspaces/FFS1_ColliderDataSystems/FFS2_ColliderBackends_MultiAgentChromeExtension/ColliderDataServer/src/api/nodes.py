"""Node API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db import get_db, Application, Node
from src.schemas import NodeCreate, NodeUpdate, NodeResponse

router = APIRouter(prefix="/apps/{app_id}/nodes", tags=["nodes"])


@router.get("", response_model=NodeResponse)
async def get_node(
    app_id: str,
    path: str = Query(..., description="Node path, e.g., /dashboard"),
    db: AsyncSession = Depends(get_db)
):
    """Get node by path within an application."""
    # First verify app exists
    app_result = await db.execute(
        select(Application).where(Application.app_id == app_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get node
    result = await db.execute(
        select(Node).where(
            Node.application_id == app.id,
            Node.path == path
        )
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return NodeResponse.model_validate(node)


@router.get("/tree", response_model=list[NodeResponse])
async def get_node_tree(
    app_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all nodes for an application as a flat list."""
    app_result = await db.execute(
        select(Application).where(Application.app_id == app_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await db.execute(
        select(Node).where(Node.application_id == app.id).order_by(Node.path)
    )
    nodes = result.scalars().all()
    
    return [NodeResponse.model_validate(n) for n in nodes]


@router.post("", response_model=NodeResponse)
async def create_node(
    app_id: str,
    data: NodeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new node in an application."""
    # Verify app exists
    app_result = await db.execute(
        select(Application).where(Application.app_id == app_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if path already exists
    existing = await db.execute(
        select(Node).where(
            Node.application_id == app.id,
            Node.path == data.path
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Node path already exists")
    
    node = Node(
        application_id=app.id,
        parent_id=data.parent_id,
        path=data.path,
        container=data.container.model_dump(),
        metadata=data.metadata,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    
    # Set root_node_id if this is the first node
    if data.path == "/" and not app.root_node_id:
        app.root_node_id = node.id
        await db.commit()
    
    return NodeResponse.model_validate(node)


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    app_id: str,
    node_id: str,
    data: NodeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a node's container or metadata."""
    result = await db.execute(
        select(Node).where(Node.id == node_id)
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    if data.container is not None:
        node.container = data.container.model_dump()
    if data.metadata is not None:
        node.metadata = data.metadata
    
    await db.commit()
    await db.refresh(node)
    
    return NodeResponse.model_validate(node)
