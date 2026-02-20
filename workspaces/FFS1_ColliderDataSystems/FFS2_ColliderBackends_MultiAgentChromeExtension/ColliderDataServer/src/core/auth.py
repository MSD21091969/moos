"""Authentication utilities for JWT token generation and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.db.models import SystemRole, User

# JWT bearer token scheme
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token for a user."""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.access_token_expire_hours)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user.id,
        "username": user.username,
        "system_role": user.system_role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency to extract and validate current user from JWT."""
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def require_system_role(
    required_role: SystemRole,
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency factory to require specific system role or higher."""
    # Accept both enum and string for robustness
    role_hierarchy = {
        "superadmin": 4,
        "collider_admin": 3,
        "app_admin": 2,
        "app_user": 1,
    }
    # Normalize to string
    current_role = str(current_user.system_role)
    required_role_str = str(required_role)
    if role_hierarchy.get(current_role, 0) < role_hierarchy.get(required_role_str, 999):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires {required_role_str} role or higher",
        )
    return current_user


async def require_superadmin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require superadmin role."""
    return await require_system_role(SystemRole.SUPERADMIN, user)


async def require_collider_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require collider_admin role or higher."""
    return await require_system_role(SystemRole.COLLIDER_ADMIN, user)
