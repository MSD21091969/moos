"""Auth API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db import get_db, User, AppPermission
from src.schemas import AuthVerifyRequest, AuthVerifyResponse, UserResponse, AppPermissionResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=AuthVerifyResponse)
async def verify_token(
    request: AuthVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify Firebase ID token and return user with permissions.
    
    MVP: For now, we do simplified auth lookup.
    Production: Verify Firebase token with firebase-admin SDK.
    """
    # MVP: Look up user by token (in production, decode Firebase JWT first)
    # For testing, we'll accept email directly as token
    result = await db.execute(
        select(User).where(User.email == request.id_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Auto-create user for MVP testing
        user = User(
            email=request.id_token,
            firebase_uid=f"test_{request.id_token}",
            profile={"display_name": request.id_token.split("@")[0]},
            container={}
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
        permissions=[AppPermissionResponse.model_validate(p) for p in permissions]
    )
