from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user, require_collider_admin
from src.core.database import get_db
from src.db.models import Application, User
from src.schemas.apps import ApplicationCreate, ApplicationResponse, ApplicationUpdate

router = APIRouter(prefix="/api/v1/apps", tags=["applications"])


@router.get("/", response_model=list[ApplicationResponse])
async def list_apps(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Application).order_by(Application.id))
    return result.scalars().all()


@router.get("/{id}", response_model=ApplicationResponse)
async def get_app(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Application).where(Application.id == id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def create_app(
    body: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = Application(**body.model_dump(), owner_id=current_user.id)
    db.add(app)
    await db.flush()
    return app


@router.patch("/{id}", response_model=ApplicationResponse)
async def update_app(
    id: str,
    body: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Application).where(Application.id == id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    await db.flush()
    await db.refresh(app)
    return app


@router.delete("/{id}", status_code=204)
async def delete_app(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_collider_admin),
):
    result = await db.execute(select(Application).where(Application.id == id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
