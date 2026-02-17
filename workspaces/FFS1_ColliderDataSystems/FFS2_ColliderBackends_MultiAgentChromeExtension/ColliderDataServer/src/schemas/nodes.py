from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.db.models import AppRole


class NodeContainer(BaseModel):
    manifest: dict = {}
    instructions: list[str] = []
    rules: list[str] = []
    skills: list[str] = []
    tools: list[dict] = []
    knowledge: list[str] = []
    workflows: list[dict] = []
    configs: dict = {}


class NodeCreate(BaseModel):
    path: str
    parent_id: str | None = None
    container: NodeContainer = NodeContainer()
    metadata: dict = {}


class NodeUpdate(BaseModel):
    path: str | None = None
    container: NodeContainer | None = None
    metadata: dict | None = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    parent_id: str | None
    path: str
    container: dict
    metadata_: dict
    created_at: datetime
    updated_at: datetime


class NodeTreeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    path: str
    container: dict
    metadata_: dict
    children: list[NodeTreeResponse] = []


class PermissionCreate(BaseModel):
    user_id: str
    application_id: str
    role: AppRole = AppRole.APP_USER


class PermissionUpdate(BaseModel):
    role: AppRole | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    application_id: str
    role: AppRole
    created_at: datetime


class AppAccessRequestCreate(BaseModel):
    """Request access to an application."""

    application_id: str
    message: str | None = None


class AppAccessRequestResponse(BaseModel):
    """Response for access request."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    application_id: str
    message: str | None
    status: str
    requested_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None


class AppAccessRequestApprove(BaseModel):
    """Approve access request with specified role."""

    role: AppRole = AppRole.APP_USER
