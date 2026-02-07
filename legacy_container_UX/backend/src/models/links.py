"""Resource Link model for the Collider architecture.

This model unifies all relationships (Tools, Agents, Users, Data) into a single,
context-rich structure that captures intent, configuration, and data flow.

Architecture Layers:
─────────────────────────────────────────────────────────────────────────────────
LAYER 1: Model Definitions (/definitions/{type}/{def_id})
   - agent_def: instructions, system_prompt, model_config (RUNTIME CODE)
   - tool_def: methods[], schema, execution_config (RUNTIME CODE)
   - source_def: connection_type, auth_config (RUNTIME CODE)
   - Tier-gated: system (all) vs custom (pro/ent)

LAYER 2: Container Instances (/agents/{id}, /tools/{id}, /sources/{id}, /sessions/{id})
   - ABSTRACTION LAYER decoupling runtime from orchestration
   - definition_id → points to model definition
   - introspection_data → exposes configurable params for ResourceLink
   - depth, owner_id, acl_groups[]
   
LAYER 3: ResourceLinks (parent/resource_links/{link_id})
   - ORCHESTRATION: connects containers into sessions
   - preset_params: override definition defaults
   - input_mappings: connect grid edges to parameters
   - metadata: x, y, color for grid display

Add Modes:
─────────────────────────────────────────────────────────────────────────────────
SESSION: Create only (no inject existing - circular dependency risk)
AGENT/TOOL/SOURCE: 
  - Create New (from definition) → fresh container + ResourceLink
  - Add Existing (owned/shared) → reference existing container via ResourceLink
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Type of resource being linked.
    
    Universal Object Model v4.1.0 defines 5 object types:
    - SESSION: Container, create-only (no inject due to circular deps)
    - AGENT: Container, create-new or add-existing
    - TOOL: Container, create-new or add-existing
    - SOURCE: Container, create-new or add-existing
    - USER: Direct ID (no instance), ACL member stub
    - INTROSPECTION: V4.1 internal property socket
    """

    SESSION = "session"  # Nested session (create-only, not inject)
    AGENT = "agent"      # AI executor container
    TOOL = "tool"        # Capability container
    SOURCE = "source"    # Data input container
    USER = "user"        # ACL member (direct ID, no instance)
    INTROSPECTION = "introspection"  # Internal property socket (V4.1)


class ResourceLink(BaseModel):
    """Universal connector for session/container resources.
    
    Part of Universal Object Model v4.1.0.
    All object relationships flow through ResourceLink.
    
    Identity Pattern:
    ─────────────────────────────────────────────────────────────────────────────
    resource_id: Definition ID or Direct ID
      - Definition ID (requires instance_id): agent_def_xxx, tool_def_xxx, source_def_xxx
      - Direct ID: user_xxx (no instance), session_xxx (instance_id = session_id)
    
    instance_id: Container document reference
      - For agent/tool/source: /agents/{id}, /tools/{id}, /sources/{id}
      - For session: /sessions/{id} (same as resource_id)
      - Can be FRESH (newly created) or EXISTING (owned/shared reference)
      - NULL for user links (direct ACL pointer)
    
    link_id: Unique within parent's resource_links collection
      - Format: {type}_{resource_id}_{suffix}
    
    Orchestration via ResourceLink:
    ─────────────────────────────────────────────────────────────────────────────
    - preset_params: Override container's definition defaults for THIS usage
    - input_mappings: Connect grid edges to container input slots
    - metadata: Visual properties (x, y, color) for grid display
    
    Note: depth is stored on Container Instance, not ResourceLink.
    Container needs depth to enforce tier-based max-depth rules.
    """

    # Identity
    link_id: str | None = Field(
        None, 
        description="Unique link ID within parent: {type}_{resource_id}_{suffix}"
    )
    resource_id: str = Field(
        ..., 
        description="Definition ID (agent_def_xxx, tool_def_xxx) or Direct ID (user_xxx, session_xxx)"
    )
    resource_type: ResourceType = Field(
        ..., 
        description="Type of resource: session|agent|tool|source|user|introspection"
    )
    instance_id: str | None = Field(
        None, 
        description="Container instance ID. NULL for user links. Can be fresh or existing container."
    )

    # V4.1 Introspection
    internal_path: str | None = Field(
        None, 
        description="Path to internal property for Introspection type (e.g. 'system_prompt', 'temperature')"
    )

    # Context
    description: str | None = Field(
        None, 
        description="Display title in UI (e.g., 'Q3 Sales Analyst', 'CSV Parser')"
    )
    role: str | None = Field(
        None, 
        description="For USER type: 'owner', 'editor', 'viewer'. For AGENT: semantic role."
    )

    # Configuration (Static overrides for this usage)
    preset_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Static config overrides for definition defaults (e.g., {'temperature': 0.7, 'format': 'csv'})"
    )

    # Data Flow (Dynamic bindings from grid edges)
    input_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Maps container input slots to session variables: {'data': '$upstream.output', 'config': '$session.settings'}"
    )

    # Visual Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="UI metadata: {x, y, color, display_name, collapsed}"
    )

    # Audit
    added_at: datetime = Field(..., description="Timestamp when link was created")
    added_by: str = Field(..., description="User ID who created the link")
    enabled: bool = Field(default=True, description="Whether the link is active in orchestration")
