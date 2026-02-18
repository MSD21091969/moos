from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.db.models import Application, Node, User

router = APIRouter(prefix="/api/v1/context", tags=["context"])


@router.get("/")
async def get_context(
    application_id: str = Query(..., description="Application UUID"),
    path: str = Query("/", description="Node path"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Read the node container at the given path in the application."""
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(
        select(Node).where(Node.application_id == app.id, Node.path == path)
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    return {"application_id": application_id, "path": path, "container": node.container}


@router.post("/")
async def set_context(
    application_id: str = Query(..., description="Application UUID"),
    path: str = Query("/", description="Node path"),
    container: dict = {},
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Write the node container at the given path."""
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(
        select(Node).where(Node.application_id == app.id, Node.path == path)
    )
    node = result.scalar_one_or_none()

    if node is None:
        node = Node(
            application_id=app.id,
            path=path,
            container=container,
        )
        db.add(node)
    else:
        node.container = container

    await db.flush()
    return {"application_id": application_id, "path": path, "container": node.container}
