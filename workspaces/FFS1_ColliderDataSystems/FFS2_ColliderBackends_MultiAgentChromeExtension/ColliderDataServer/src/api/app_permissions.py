from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.db.models import (
    AppAccessRequest,
    Application,
    AppPermission,
    AppRole,
    SystemRole,
    User,
)
from src.schemas.nodes import (
    AppAccessRequestApprove,
    AppAccessRequestCreate,
    AppAccessRequestResponse,
)

router = APIRouter(prefix="/api/v1/apps", tags=["app-permissions"])


@router.post("/{id}/request-access", response_model=AppAccessRequestResponse)
async def request_app_access(
    id: str,
    request: AppAccessRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request access to an application."""
    # Check if app exists
    result = await db.execute(select(Application).where(Application.id == id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check if already has permission
    result = await db.execute(
        select(AppPermission).where(
            AppPermission.user_id == current_user.id,
            AppPermission.application_id == id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="You already have access to this application"
        )

    # Check if pending request exists
    result = await db.execute(
        select(AppAccessRequest).where(
            AppAccessRequest.user_id == current_user.id,
            AppAccessRequest.application_id == id,
            AppAccessRequest.status == "pending",
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="You already have a pending request"
        )

    # Create request
    access_request = AppAccessRequest(
        user_id=current_user.id,
        application_id=id,
        message=request.message,
        status="pending",
    )
    db.add(access_request)
    await db.commit()
    await db.refresh(access_request)

    return access_request


@router.get("/{id}/pending-requests", response_model=list[AppAccessRequestResponse])
async def get_pending_requests(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending access requests for an application."""
    # Check if user can see requests (owner or COLLIDER_ADMIN+)
    if current_user.system_role not in [
        SystemRole.SUPERADMIN,
        SystemRole.COLLIDER_ADMIN,
    ]:
        # Check if user is app owner
        result = await db.execute(
            select(AppPermission).where(
                AppPermission.user_id == current_user.id,
                AppPermission.application_id == id,
                AppPermission.role == AppRole.APP_ADMIN,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")

    # Get pending requests
    result = await db.execute(
        select(AppAccessRequest).where(
            AppAccessRequest.application_id == id,
            AppAccessRequest.status == "pending",
        )
    )
    return result.scalars().all()


@router.post("/{id}/requests/{request_id}/approve")
async def approve_access_request(
    id: str,
    request_id: str,
    approval: AppAccessRequestApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve an access request and grant permission."""
    # Check authorization (owner or COLLIDER_ADMIN+)
    if current_user.system_role not in [
        SystemRole.SUPERADMIN,
        SystemRole.COLLIDER_ADMIN,
    ]:
        result = await db.execute(
            select(AppPermission).where(
                AppPermission.user_id == current_user.id,
                AppPermission.application_id == id,
                AppPermission.role == AppRole.APP_ADMIN,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")

    # Get request
    result = await db.execute(
        select(AppAccessRequest).where(AppAccessRequest.id == request_id)
    )
    access_request = result.scalar_one_or_none()
    if not access_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if access_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    # Create permission
    permission = AppPermission(
        user_id=access_request.user_id,
        application_id=id,
        role=approval.role,
    )
    db.add(permission)

    # Update request
    access_request.status = "approved"
    access_request.resolved_at = datetime.now(timezone.utc)
    access_request.resolved_by = current_user.id

    await db.commit()

    return {"message": "Access granted"}


@router.post("/{id}/requests/{request_id}/reject")
async def reject_access_request(
    id: str,
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject an access request."""
    # Same authorization check as approve
    if current_user.system_role not in [
        SystemRole.SUPERADMIN,
        SystemRole.COLLIDER_ADMIN,
    ]:
        result = await db.execute(
            select(AppPermission).where(
                AppPermission.user_id == current_user.id,
                AppPermission.application_id == id,
                AppPermission.role == AppRole.APP_ADMIN,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")

    # Get request
    result = await db.execute(
        select(AppAccessRequest).where(AppAccessRequest.id == request_id)
    )
    access_request = result.scalar_one_or_none()
    if not access_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if access_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    # Update request
    access_request.status = "rejected"
    access_request.resolved_at = datetime.now(timezone.utc)
    access_request.resolved_by = current_user.id

    await db.commit()

    return {"message": "Access denied"}
