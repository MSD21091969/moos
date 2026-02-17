from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_collider_admin
from src.core.database import get_db
from src.db.models import SystemRole, User

router = APIRouter(prefix="/api/v1/users", tags=["roles"])


class AssignRoleRequest(BaseModel):
    """Request body for assigning a system role."""

    system_role: SystemRole


@router.post("/{user_id}/assign-role")
async def assign_system_role(
    user_id: str,
    request: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_collider_admin),
):
    """
    Assign system role to a user.
    Only SUPERADMIN and COLLIDER_ADMIN can assign roles.
    COLLIDER_ADMIN can only assign APP_ADMIN or APP_USER.
    """
    # Get target user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # COLLIDER_ADMIN cannot assign SUPERADMIN or COLLIDER_ADMIN roles
    if current_user.system_role == SystemRole.COLLIDER_ADMIN:
        if request.system_role in [SystemRole.SUPERADMIN, SystemRole.COLLIDER_ADMIN]:
            raise HTTPException(
                status_code=403,
                detail="COLLIDER_ADMIN can only assign APP_ADMIN or APP_USER roles",
            )

    # Update role
    user.system_role = request.system_role
    await db.commit()
    await db.refresh(user)

    return {"message": f"User {user.username} assigned role {request.system_role}"}
