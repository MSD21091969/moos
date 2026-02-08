from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

# === Collider Models ===

class UserContainer(BaseModel):
    id: str
    owner_id: str
    parent_id: Optional[str] = None
    name: str
    definition_id: Optional[str] = None
    visual_x: float = 0.0
    visual_y: float = 0.0
    visual_color: str = "#3b82f6"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ContainerACL(BaseModel):
    id: str
    container_id: str
    grantee_id: str
    permission: str
    granted_at: Optional[str] = None

# === Agent Studio Models ===

class UserMessage(BaseModel):
    content: str
    timestamp: Optional[str] = None

class AgentToken(BaseModel):
    content: str

class StreamEnd(BaseModel):
    pass

class ErrorMessage(BaseModel):
    detail: str

class ToolStart(BaseModel):
    tool_name: str
    args: dict

class ToolEnd(BaseModel):
    tool_name: str
    result: str

class ApprovalRequired(BaseModel):
    id: str
    action: str
    details: str

class FileChanged(BaseModel):
    path: str
    action: str

class TodosUpdate(BaseModel):
    todos: List[dict]

class SkillsUpdate(BaseModel):
    skills: List[str]
