"""Pydantic schemas for API requests/responses."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# =============================================================================
# User Schemas
# =============================================================================

class UserProfile(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserBase(BaseModel):
    email: str
    profile: UserProfile = Field(default_factory=UserProfile)


class UserResponse(UserBase):
    id: str
    container: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Application Schemas
# =============================================================================

class ApplicationBase(BaseModel):
    app_id: str
    display_name: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(ApplicationBase):
    id: str
    root_node_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Node Container Schemas
# =============================================================================

class NodeContainer(BaseModel):
    """Universal .agent structure."""
    manifest: dict = Field(default_factory=dict)
    instructions: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)
    workflows: list[dict] = Field(default_factory=list)
    configs: dict = Field(default_factory=dict)


class NodeBase(BaseModel):
    path: str
    container: NodeContainer = Field(default_factory=NodeContainer)
    metadata: dict = Field(default_factory=dict)


class NodeCreate(NodeBase):
    parent_id: Optional[str] = None


class NodeUpdate(BaseModel):
    container: Optional[NodeContainer] = None
    metadata: Optional[dict] = None


class NodeResponse(NodeBase):
    id: str
    application_id: str
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Permission Schemas
# =============================================================================

class AppPermissionBase(BaseModel):
    can_read: bool = False
    can_write: bool = False
    is_admin: bool = False


class AppPermissionResponse(AppPermissionBase):
    id: str
    user_id: str
    application_id: str

    class Config:
        from_attributes = True


# =============================================================================
# Auth Schemas
# =============================================================================

class AuthVerifyRequest(BaseModel):
    id_token: str


class AuthVerifyResponse(BaseModel):
    user: UserResponse
    permissions: list[AppPermissionResponse]
