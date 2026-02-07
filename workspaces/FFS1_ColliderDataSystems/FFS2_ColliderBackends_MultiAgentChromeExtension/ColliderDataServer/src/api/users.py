"""User API routes - account management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.db import get_db, User

router = APIRouter(prefix="/users", tags=["users"])


class UpdateSecretsRequest(BaseModel):
    """Request to update user secrets."""
    secrets: Dict[str, str]


class UpdateContainerRequest(BaseModel):
    """Request to update user container."""
    secrets: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None


class UserContainerResponse(BaseModel):
    """Response with user container."""
    id: str
    email: str
    container: Dict[str, Any]


@router.get("/me", response_model=UserContainerResponse)
async def get_current_user(
    email: str,  # MVP: Pass email as query param; Production: Get from JWT
    db: AsyncSession = Depends(get_db)
):
    """Get current user's full container."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserContainerResponse(
        id=str(user.id),
        email=user.email,
        container=user.container or {}
    )


@router.patch("/me/secrets")
async def update_user_secrets(
    request: UpdateSecretsRequest,
    email: str,  # MVP: Pass email as query param; Production: Get from JWT
    db: AsyncSession = Depends(get_db)
):
    """Update user secrets (merge with existing)."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Merge secrets into container
    container = dict(user.container or {})
    existing_secrets = dict(container.get("secrets", {}))
    existing_secrets.update(request.secrets)
    container["secrets"] = existing_secrets
    
    user.container = container
    await db.commit()
    
    return {
        "status": "ok",
        "message": f"Updated {len(request.secrets)} secret(s)",
        "secrets_keys": list(existing_secrets.keys())
    }


@router.patch("/me/container")
async def update_user_container(
    request: UpdateContainerRequest,
    email: str,  # MVP: Pass email as query param; Production: Get from JWT
    db: AsyncSession = Depends(get_db)
):
    """Update user container fields (merge with existing)."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Merge into container
    container = dict(user.container or {})
    
    if request.secrets:
        existing_secrets = dict(container.get("secrets", {}))
        existing_secrets.update(request.secrets)
        container["secrets"] = existing_secrets
    
    if request.settings:
        existing_settings = dict(container.get("settings", {}))
        existing_settings.update(request.settings)
        container["settings"] = existing_settings
    
    user.container = container
    await db.commit()
    
    return {"status": "ok", "message": "Container updated"}
