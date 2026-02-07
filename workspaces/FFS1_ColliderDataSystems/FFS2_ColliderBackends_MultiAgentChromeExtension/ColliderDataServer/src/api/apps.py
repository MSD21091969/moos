"""Application API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db import get_db, Application, User, AppPermission, AdminAccount
from src.schemas import ApplicationCreate, ApplicationResponse
from src.api.auth import get_current_user
from src.api.permissions import RequireRead, RequireAdmin, require_app_read
from src.firebase_auth import FirebaseUser
from src.api.sse import broadcast_event

router = APIRouter(prefix="/apps", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List applications the user has access to."""
    user, _ = user_data

    # Get apps where user has explicit permission
    perm_result = await db.execute(
        select(Application)
        .join(AppPermission, AppPermission.application_id == Application.id)
        .where(AppPermission.user_id == user.id)
    )
    permitted_apps = list(perm_result.scalars().all())

    # Also get apps the user owns via AdminAccount
    owned_result = await db.execute(
        select(Application)
        .join(AdminAccount, AdminAccount.id == Application.owner_id)
        .where(AdminAccount.user_id == user.id)
    )
    owned_apps = list(owned_result.scalars().all())

    # Combine and dedupe
    all_apps = {a.id: a for a in permitted_apps + owned_apps}

    return [ApplicationResponse.model_validate(a) for a in all_apps.values()]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: str,
    perm: RequireRead,  # Enforces read permission
):
    """Get application by app_id (requires read permission)."""
    return ApplicationResponse.model_validate(perm.application)


@router.post("", response_model=ApplicationResponse)
async def create_application(
    data: ApplicationCreate,
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new application (authenticated users only)."""
    user, _ = user_data

    # Check if app_id already exists
    existing = await db.execute(
        select(Application).where(Application.app_id == data.app_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application ID already exists")

    # Create app
    app = Application(
        app_id=data.app_id,
        display_name=data.display_name,
        config={},
    )
    db.add(app)
    await db.flush()  # Get app.id

    # Grant creator admin permission
    permission = AppPermission(
        user_id=user.id,
        application_id=app.id,
        can_read=True,
        can_write=True,
        is_admin=True,
    )
    db.add(permission)

    await db.commit()
    await db.refresh(app)

    # Broadcast SSE event
    response = ApplicationResponse.model_validate(app)
    await broadcast_event(
        "app_created",
        {
            "app": response.model_dump(),
        },
    )

    return response


@router.delete("/{app_id}")
async def delete_application(
    app_id: str,
    perm: RequireAdmin,  # Enforces admin permission
    db: AsyncSession = Depends(get_db),
):
    """Delete an application (requires admin permission)."""
    await db.delete(perm.application)
    await db.commit()

    # Broadcast SSE event
    await broadcast_event(
        "app_deleted",
        {
            "app_id": app_id,
        },
    )

    return {"deleted": app_id}
