"""Authentication API endpoints for user login and signup."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from src.core.database import get_db
from src.db.models import SystemRole, User
from src.schemas.users import LoginRequest, LoginResponse, SignupRequest, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user with username and password, return JWT token."""
    # Find user by username
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    access_token = create_access_token(user)

    return LoginResponse(
        access_token=access_token,
        user=user,
    )


@router.post("/signup", response_model=LoginResponse, status_code=201)
async def signup(
    body: SignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new user account (app_admin or app_user only).

    System admins must be created via seed or by superadmin.
    """
    # Validate role constraints
    if body.system_role not in [SystemRole.APP_ADMIN, SystemRole.APP_USER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only signup as app_admin or app_user. Contact admin for other roles.",
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists (if provided)
    if body.email:
        result = await db.execute(select(User).where(User.email == body.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Create new user
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        email=body.email,
        system_role=body.system_role,
        profile=body.profile,
    )
    db.add(user)
    await db.flush()

    # Generate JWT token
    access_token = create_access_token(user)

    return LoginResponse(
        access_token=access_token,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user info."""
    return current_user
