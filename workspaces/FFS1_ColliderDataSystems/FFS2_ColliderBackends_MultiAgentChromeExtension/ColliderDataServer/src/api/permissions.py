from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_collider_admin
from src.core.database import get_db
from src.db.models import AppPermission, User
from src.schemas.nodes import PermissionCreate, PermissionResponse, PermissionUpdate

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


@router.get("/", response_model=list[PermissionResponse])
async def list_permissions(
    user_id: str | None = None,
    application_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_collider_admin),
):
    query = select(AppPermission)
    if user_id is not None:
        query = query.where(AppPermission.user_id == user_id)
    if application_id is not None:
        query = query.where(AppPermission.application_id == application_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PermissionResponse, status_code=201)
async def create_permission(
    body: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_collider_admin),
):
    perm = AppPermission(**body.model_dump())
    db.add(perm)
    await db.flush()
    return perm


@router.patch("/{perm_id}", response_model=PermissionResponse)
async def update_permission(
    perm_id: str,
    body: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_collider_admin),
):
    result = await db.execute(select(AppPermission).where(AppPermission.id == perm_id))
    perm = result.scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(perm, field, value)
    await db.flush()
    await db.refresh(perm)
    return perm


@router.delete("/{perm_id}", status_code=204)
async def delete_permission(
    perm_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_collider_admin),
):
    result = await db.execute(select(AppPermission).where(AppPermission.id == perm_id))
    perm = result.scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    await db.delete(perm)
