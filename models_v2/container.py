"""Container Model - Session Context and Artifact Holder.

The Container acts as the bridge between:
1. User (Ownership/ACL)
2. Graph Tool (DefinitionID)
3. Runtime State (Artifacts/Context)

It is the primary persistence unit for a User's work session.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class AccessControlEntry(BaseModel):
    """Permissions for shared containers."""
    grantee_id: str
    permission: Literal["read", "editor", "admin"] = "read"
    granted_at: datetime = Field(default_factory=datetime.utcnow)

class ArtifactReference(BaseModel):
    """Reference to an artifact (Canvas, File, Report) held in the container."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["canvas", "file", "report", "image"]
    name: str
    uri: str  # Path or URI to the actual content
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Container(BaseModel):
    """
    The Session Context Object.
    
    Persists the state of a user's interaction with a specific functionality (Definition).
    """
    id: UUID = Field(default_factory=uuid4)
    owner_id: str  # References UserObject.id
    name: str = "New Container"
    
    # The "Tool" context
    definition_id: Optional[UUID] = None  # The Graph Definition driving this container
    
    # State Persistence
    artifacts: List[ArtifactReference] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict) # Chat history, variables
    
    # Visual Metadata
    visual_x: float = 0.0
    visual_y: float = 0.0
    visual_color: str = "#3b82f6"
    
    # Security
    is_public: bool = False
    acl: List[AccessControlEntry] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_artifact(self, artifact: ArtifactReference):
        """Add an artifact to the container."""
        self.artifacts.append(artifact)
        self.updated_at = datetime.utcnow()

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactReference]:
        """Retrieve an artifact by ID."""
        return next((a for a in self.artifacts if a.id == artifact_id), None)
        
    def can_access(self, user_id: str) -> bool:
        """Check if a user has access."""
        if self.is_public:
            return True
        if self.owner_id == user_id:
            return True
        return any(entry.grantee_id == user_id for entry in self.acl)
