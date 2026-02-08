"""Auth API routes."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from src.db import get_db, User, AppPermission
from src.schemas import (
    AuthVerifyRequest,
    AuthVerifyResponse,
    UserResponse,
    AppPermissionResponse,
)
from src.firebase_auth import verify_firebase_token, AuthError, FirebaseUser

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> tuple[User, FirebaseUser]:
    """
    Dependency to get current authenticated user from Authorization header.

    Usage:
        @router.get("/protected")
        async def protected_route(user_data: tuple = Depends(get_current_user)):
            db_user, firebase_user = user_data
            ...
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Extract token from "Bearer <token>" format
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Invalid authorization format. Use: Bearer <token>"
        )

    token = parts[1]

    try:
        firebase_user = await verify_firebase_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)

    # Get or create database user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_user.uid)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        # Also check by email for backwards compatibility
        if firebase_user.email:
            result = await db.execute(
                select(User).where(User.email == firebase_user.email)
            )
            db_user = result.scalar_one_or_none()
            if db_user and not db_user.firebase_uid:
                # Link existing user to Firebase UID
                db_user.firebase_uid = firebase_user.uid
                await db.commit()

    if not db_user:
        # Auto-create user
        db_user = User(
            email=firebase_user.email or f"{firebase_user.uid}@collider.local",
            firebase_uid=firebase_user.uid,
            profile={
                "display_name": firebase_user.name or firebase_user.email,
                "picture": firebase_user.picture,
            },
            container={},
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

    return db_user, firebase_user


@router.post("/verify", response_model=AuthVerifyResponse)
async def verify_token(request: AuthVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify Firebase ID token and return user with permissions.

    In production: Verifies Firebase JWT signature and claims.
    In development: Accepts email as token for testing.
    """
    try:
        firebase_user = await verify_firebase_token(request.id_token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)

    # Get or create user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_user.uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check by email for migration
        if firebase_user.email:
            result = await db.execute(
                select(User).where(User.email == firebase_user.email)
            )
            user = result.scalar_one_or_none()
            if user and not user.firebase_uid:
                user.firebase_uid = firebase_user.uid
                await db.commit()

    if not user:
        # Create new user
        user = User(
            email=firebase_user.email or f"{firebase_user.uid}@collider.local",
            firebase_uid=firebase_user.uid,
            profile={
                "display_name": firebase_user.name or firebase_user.email,
                "picture": firebase_user.picture,
            },
            container={},
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Get permissions
    perm_result = await db.execute(
        select(AppPermission).where(AppPermission.user_id == user.id)
    )
    permissions = perm_result.scalars().all()

    return AuthVerifyResponse(
        user=UserResponse.model_validate(user),
        permissions=[AppPermissionResponse.model_validate(p) for p in permissions],
    )
