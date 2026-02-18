from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.auth import get_current_user
from src.core.database import get_db
from src.db.models import Application, Node, User
from src.schemas.nodes import NodeCreate, NodeResponse, NodeTreeResponse, NodeUpdate

router = APIRouter(prefix="/api/v1/apps/{id}/nodes", tags=["nodes"])


async def _get_application(id: str, db: AsyncSession) -> Application:
    result = await db.execute(select(Application).where(Application.id == id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.get("/", response_model=list[NodeResponse])
async def list_nodes(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    app = await _get_application(id, db)
    result = await db.execute(
        select(Node).where(Node.application_id == app.id).order_by(Node.path)
    )
    return result.scalars().all()


@router.get("/tree", response_model=list[NodeTreeResponse])
async def get_tree(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Return the full node tree for an application."""
    app = await _get_application(id, db)
    result = await db.execute(
        select(Node)
        .where(Node.application_id == app.id)
        .options(selectinload(Node.children))
        .order_by(Node.path)
    )
    all_nodes = result.scalars().unique().all()

    # Build tree from flat list
    root_nodes = [n for n in all_nodes if n.parent_id is None]

    def build_tree(node: Node) -> NodeTreeResponse:
        return NodeTreeResponse(
            id=node.id,
            path=node.path,
            container=node.container,
            metadata_=node.metadata_,
            children=[build_tree(c) for c in node.children],
        )

    return [build_tree(n) for n in root_nodes]


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    app = await _get_application(id, db)
    result = await db.execute(
        select(Node).where(Node.id == node_id, Node.application_id == app.id)
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.post("/", response_model=NodeResponse, status_code=201)
async def create_node(
    id: str,
    body: NodeCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    app = await _get_application(id, db)
    node = Node(
        application_id=app.id,
        parent_id=body.parent_id,
        path=body.path,
        container=body.container.model_dump(),
        metadata_=body.metadata,
    )
    db.add(node)
    await db.flush()
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    id: str,
    node_id: str,
    body: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    app = await _get_application(id, db)
    result = await db.execute(
        select(Node).where(Node.id == node_id, Node.application_id == app.id)
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    update_data = body.model_dump(exclude_unset=True)
    if "metadata" in update_data:
        update_data["metadata_"] = update_data.pop("metadata")
    for field, value in update_data.items():
        setattr(node, field, value)
    await db.flush()
    await db.refresh(node)
    return node


@router.delete("/{node_id}", status_code=204)
async def delete_node(
    id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    app = await _get_application(id, db)
    result = await db.execute(
        select(Node).where(Node.id == node_id, Node.application_id == app.id)
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.delete(node)
