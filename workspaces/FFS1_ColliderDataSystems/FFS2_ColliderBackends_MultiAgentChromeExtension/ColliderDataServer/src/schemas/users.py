from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    firebase_uid: str
    profile: dict = {}


class UserUpdate(BaseModel):
    email: str | None = None
    profile: dict | None = None
    container: dict | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    firebase_uid: str
    profile: dict
    container: dict
    created_at: datetime
    updated_at: datetime


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
