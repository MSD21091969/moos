"""Authentication endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from src.services.auth_service import AuthService
from src.api.dependencies import get_auth_service
from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Token response with expiry info."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiry


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get an OAuth2 access token.
    """
    try:
        logger.info("Login attempt for user", extra={"username": form_data.username})
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning("Failed login attempt for user", extra={"username": form_data.username})
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth_service.create_access_token(
            data={
                "sub": user.user_id,
                "tier": user.tier.value.lower()
                if hasattr(user.tier, "value")
                else str(user.tier).lower(),
            }
        )
        logger.info("Successful login for user", extra={"username": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Login error", extra={"username": form_data.username, "error": str(e)}, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Authentication service error")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh an expired access token using a refresh token.

    **No authentication required** - the refresh token acts as proof of identity.

    The SDK uses this to automatically extend sessions without re-authentication.

    Args:
        req: RefreshTokenRequest with refresh_token

    Returns:
        TokenResponse with new access token and expiry time

    Raises:
        HTTPException 401: If refresh token is invalid or expired
    """
    try:
        # Decode and validate refresh token
        try:
            payload = jwt.decode(
                req.refresh_token,
                settings.SECRET_KEY,  # Correct field name in Settings
                algorithms=[settings.ALGORITHM],  # Correct field name in Settings
            )
            email: Optional[str] = payload.get("sub")
        except JWTError as e:
            logger.warning("Invalid refresh token", extra={"error": str(e)})
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from service to verify still exists and get tier
        user = await auth_service.get_user_by_email(email)
        if not user:
            logger.warning("Refresh token for non-existent user", extra={"email": email})
            raise HTTPException(
                status_code=401,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access token
        access_token = auth_service.create_access_token(
            data={
                "sub": user.email,
                "tier": user.tier.value.lower()
                if hasattr(user.tier, "value")
                else str(user.tier).lower(),
            }
        )

        # Calculate expiry time
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert minutes to seconds

        logger.info("Token refreshed", extra={"email": email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Token refresh service error")
