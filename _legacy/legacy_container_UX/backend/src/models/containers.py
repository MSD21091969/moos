"""Container instance models for Universal Object Model v4.0.0.

Container instances are documents in:
- /usersessions/{user_id}/
- /sessions/{instance_id}/
- /agents/{instance_id}/
- /tools/{instance_id}/
- /sources/{instance_id}/

They reference definitions via definition_id and have parent_id + depth for hierarchy.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ===== User Identity & Preferences =====
# Stored in UserSession, drives ChatAgent persona and UX vocabulary

class UxVocabulary(BaseModel):
    """User's preferred terminology for UI display."""
    session: str = Field(default="session", description="Term for session (e.g., 'sticky note')")
    session_plural: str = Field(default="sessions", description="Plural (e.g., 'sticky notes')")
    container: str = Field(default="container", description="Term for container (e.g., 'sticky')")
    container_plural: str = Field(default="containers", description="Plural (e.g., 'stickies')")
    workspace: str = Field(default="workspace", description="Term for workspace (e.g., 'collider space')")
    agent: str = Field(default="agent", description="Term for agent")
    tool: str = Field(default="tool", description="Term for tool")
    source: str = Field(default="source", description="Term for source")


class UserIdentityPreferences(BaseModel):
    """User identity and ChatAgent persona preferences."""
    
    # User display name (shown in UI, referenced by agent)
    display_name: str = Field(default="User", description="User's display name (e.g., 'Sam')")
    
    # ChatAgent persona
    agent_name: str = Field(default="Navigator", description="Agent's name (e.g., 'HAL')")
    agent_personality: str | None = Field(None, description="Agent personality (e.g., 'helpful')")
    
    # UX terminology - how user refers to elements
    ux_vocabulary: UxVocabulary = Field(default_factory=UxVocabulary)
    
    # Additional preferences
    voice_enabled: bool = Field(default=True, description="Enable voice mode")
    preferred_model: Literal["cloud", "local"] = Field(default="cloud", description="Preferred AI model")
    thinking_visible: bool = Field(default=False, description="Show Gemini 3 thinking in UI")


class ContainerBase(BaseModel):
    """Base class for all container instances.
    
    All containers have:
    - Unique instance_id
    - Parent reference (parent_id)
    - Depth tracking (0=UserSession, 1-4=nested, tier-gated)
    - ACL (cached from USER ResourceLinks)
    
    Depth limits (enforced by service layer):
    - FREE: max L2
    - PRO/ENT: max L4
    """
    
    # Identity
    instance_id: str = Field(..., description="Unique container instance ID")
    
    # Hierarchy
    parent_id: str | None = Field(None, description="Parent container ID (None for UserSession)")
    depth: int = Field(..., ge=0, le=4, description="Container depth: 0=UserSession, 1-4=nested (tier-gated)")
    
    # ACL (cached from USER ResourceLinks in /resources/)
    acl: dict[str, str | list[str]] = Field(
        default_factory=lambda: {"owner": "", "editors": [], "viewers": []},
        description="Access control: {owner: str, editors: list[str], viewers: list[str]}"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User ID who created this container")


class UserSession(ContainerBase):
    """User's workspace root (L0).
    
    Created once on sign-in. Contains:
    - USER ResourceLink (owner)
    - SESSION ResourceLinks (ACL-permitted sessions)
    
    No other container types at L0 (design choice: workspace is global view).
    """
    
    user_id: str = Field(..., description="Owner user ID (instance_id == user_id)")
    depth: int = Field(default=0, description="Always 0 for UserSession")
    parent_id: None = Field(default=None, description="Always None for root")
    
    # User identity and preferences (drives ChatAgent persona & UX vocabulary)
    preferences: UserIdentityPreferences = Field(
        default_factory=UserIdentityPreferences,
        description="User identity, agent persona, and UX vocabulary preferences"
    )
    
    # No definition_id (UserSession is not templated)
    

class AgentInstance(ContainerBase):
    """Agent instance referencing AgentDefinition.
    
    Created when user adds agent from registry to a parent container.
    """
    
    definition_id: str = Field(..., description="Points to /agent_definitions/{agent_id}")
    title: str | None = Field(None, description="Override definition title")
    
    # Runtime state (optional)
    active_model: str | None = Field(None, description="Currently selected model")
    system_prompt_override: str | None = Field(None, description="Override definition system_prompt")


class ToolInstance(ContainerBase):
    """Tool instance referencing ToolDefinition.
    
    Created when user adds tool from registry to a parent container.
    """
    
    definition_id: str = Field(..., description="Points to /tool_definitions/{tool_id}")
    title: str | None = Field(None, description="Override definition title")
    
    # Runtime config (optional)
    execute_config_override: dict = Field(
        default_factory=dict,
        description="Override definition execute_config"
    )


class SourceInstance(ContainerBase):
    """Source instance referencing SourceDefinition.
    
    Created when user adds source from registry to a parent container.
    Stores connection credentials (encrypted).
    """
    
    definition_id: str = Field(..., description="Points to /source_definitions/{source_id}")
    title: str | None = Field(None, description="Override definition title")
    
    # Connection details (encrypted in Firestore)
    connection_config: dict = Field(
        default_factory=dict,
        description="Encrypted connection parameters (URL, credentials ref, etc.)"
    )
    
    # Connection status
    connected: bool = Field(default=False, description="Whether connection is active")
    last_connected_at: datetime | None = Field(None, description="Last successful connection")
    connection_error: str | None = Field(None, description="Last connection error message")
