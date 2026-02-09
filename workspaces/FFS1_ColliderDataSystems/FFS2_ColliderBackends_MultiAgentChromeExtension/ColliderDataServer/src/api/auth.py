from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.db.models import AdminAccount, User
from src.schemas.users import UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

DEV_USER_EMAIL = "dev@collider.local"
DEV_USER_UID = "dev-firebase-uid-000"


@router.post("/verify", response_model=UserResponse)
async def verify_auth(db: AsyncSession = Depends(get_db)):
    """Stub auth: auto-authenticates as the dev user.

    In production, this would verify a Firebase ID token from the
    Authorization header and return the corresponding user.
    """
    result = await db.execute(select(User).where(User.firebase_uid == DEV_USER_UID))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=DEV_USER_EMAIL,
            firebase_uid=DEV_USER_UID,
            profile={"name": "Dev User", "role": "admin"},
        )
        db.add(user)
        await db.flush()

        admin = AdminAccount(user_id=user.id)
        db.add(admin)
        await db.flush()

    return user
