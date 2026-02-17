from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.db.models import SystemRole


class UserResponse(BaseModel):
    """Response schema for user data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    system_role: SystemRole
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Response for successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignupRequest(BaseModel):
    """Request body for user signup."""

    username: str
    password: str
    system_role: SystemRole = SystemRole.APP_USER


class UserCreate(BaseModel):
    """Internal schema for creating users."""

    username: str
    password_hash: str
    system_role: SystemRole = SystemRole.APP_USER


class UserUpdate(BaseModel):
    """Schema for updating users."""

    system_role: SystemRole | None = None


class UserBrief(BaseModel):
    """Brief user info for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    system_role: SystemRole
