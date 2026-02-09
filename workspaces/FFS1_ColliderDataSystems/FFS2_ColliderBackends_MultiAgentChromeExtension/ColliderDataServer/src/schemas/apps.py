from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    app_id: str
    display_name: str | None = None
    config: dict = {}


class ApplicationUpdate(BaseModel):
    display_name: str | None = None
    config: dict | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    app_id: str
    owner_id: str | None
    display_name: str | None
    config: dict
    root_node_id: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    app_id: str
    display_name: str | None
