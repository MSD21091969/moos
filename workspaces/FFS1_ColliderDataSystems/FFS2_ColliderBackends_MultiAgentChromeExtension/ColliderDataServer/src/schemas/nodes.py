from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    can_read: bool = False
    can_write: bool = False
    is_admin: bool = False


class PermissionUpdate(BaseModel):
    can_read: bool | None = None
    can_write: bool | None = None
    is_admin: bool | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    application_id: str
    can_read: bool
    can_write: bool
    is_admin: bool
    created_at: datetime
