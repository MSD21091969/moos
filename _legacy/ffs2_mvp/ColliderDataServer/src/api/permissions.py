"""
Permission Middleware
Provides FastAPI dependencies for checking user permissions on applications and nodes.
"""

from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db import get_db, User, Application, AppPermission
from src.api.auth import get_current_user
from src.firebase_auth import FirebaseUser


class PermissionChecker:
    """
    FastAPI dependency factory for permission checks.

    Usage:
        @router.get("/{app_id}/nodes")
        async def get_nodes(
            app_id: str,
            permission: Permission = Depends(require_app_read("app_id")),
        ):
            # permission.user, permission.app, permission.perm available
            ...
    """

    def __init__(
        self,
        app_id_param: str = "app_id",
        require_read: bool = False,
        require_write: bool = False,
        require_admin: bool = False,
        allow_owner: bool = True,
    ):
        self.app_id_param = app_id_param
        self.require_read = require_read
        self.require_write = require_write
        self.require_admin = require_admin
        self.allow_owner = allow_owner


class Permission:
    """Result of permission check - contains user, app, and permission details."""

    def __init__(
        self,
        user: User,
        firebase_user: FirebaseUser,
        application: Application,
        permission: AppPermission | None,
        is_owner: bool = False,
    ):
        self.user = user
        self.firebase_user = firebase_user
        self.application = application
        self.permission = permission
        self.is_owner = is_owner

    @property
    def can_read(self) -> bool:
        return self.is_owner or (self.permission and self.permission.can_read)

    @property
    def can_write(self) -> bool:
        return self.is_owner or (self.permission and self.permission.can_write)

    @property
    def is_admin(self) -> bool:
        return self.is_owner or (self.permission and self.permission.is_admin)


async def get_app_permission(
    app_id: str,
    user_data: tuple[User, FirebaseUser],
    db: AsyncSession,
) -> Permission:
    """
    Get permission for a user on an application.
    Does NOT enforce any access - just retrieves the permission state.
    """
    user, firebase_user = user_data

    # Get application
    result = await db.execute(select(Application).where(Application.app_id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail=f"Application not found: {app_id}")

    # Check if user is owner via AdminAccount
    is_owner = False
    if app.owner_id:
        from src.db import AdminAccount

        admin_result = await db.execute(
            select(AdminAccount).where(
                and_(AdminAccount.id == app.owner_id, AdminAccount.user_id == user.id)
            )
        )
        is_owner = admin_result.scalar_one_or_none() is not None

    # Get explicit permission
    perm_result = await db.execute(
        select(AppPermission).where(
            and_(
                AppPermission.user_id == user.id, AppPermission.application_id == app.id
            )
        )
    )
    permission = perm_result.scalar_one_or_none()

    return Permission(
        user=user,
        firebase_user=firebase_user,
        application=app,
        permission=permission,
        is_owner=is_owner,
    )


def require_app_read(app_id_param: str = "app_id"):
    """
    Dependency that requires read access to an application.

    Usage:
        @router.get("/{app_id}/data")
        async def get_data(
            app_id: str,
            perm: Permission = Depends(require_app_read()),
        ):
            ...
    """

    async def dependency(
        app_id: str,
        user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Permission:
        perm = await get_app_permission(app_id, user_data, db)

        if not perm.can_read:
            raise HTTPException(
                status_code=403, detail=f"Read access denied for application: {app_id}"
            )

        return perm

    return dependency


def require_app_write(app_id_param: str = "app_id"):
    """
    Dependency that requires write access to an application.
    """

    async def dependency(
        app_id: str,
        user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Permission:
        perm = await get_app_permission(app_id, user_data, db)

        if not perm.can_write:
            raise HTTPException(
                status_code=403, detail=f"Write access denied for application: {app_id}"
            )

        return perm

    return dependency


def require_app_admin(app_id_param: str = "app_id"):
    """
    Dependency that requires admin access to an application.
    """

    async def dependency(
        app_id: str,
        user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Permission:
        perm = await get_app_permission(app_id, user_data, db)

        if not perm.is_admin:
            raise HTTPException(
                status_code=403, detail=f"Admin access denied for application: {app_id}"
            )

        return perm

    return dependency


# Convenience type aliases
RequireRead = Annotated[Permission, Depends(require_app_read())]
RequireWrite = Annotated[Permission, Depends(require_app_write())]
RequireAdmin = Annotated[Permission, Depends(require_app_admin())]
