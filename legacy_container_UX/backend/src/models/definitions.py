"""Object definitions for the Universal Object Model v4.0.0.

Definitions are tier-gated templates stored in:
- /agent_definitions/
- /tool_definitions/
- /source_definitions/

They define schemas (inputs/outputs/capabilities) but don't store state.
Instances are created in /agents/, /tools/, /sources/ with definition_id reference.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class InputSpec(BaseModel):
    """Parameter schema for inputs."""
    
    type: str = Field(..., description="Data type: string, json, file, int, float, bool")
    required: bool = Field(default=True, description="Whether this input is required")
    default: Any | None = Field(None, description="Default value if not provided")
    description: str | None = Field(None, description="Human-readable description")
    validation: dict[str, Any] = Field(
        default_factory=dict,
        description="Validation rules: {min, max, pattern, enum, etc.}"
    )


class OutputSpec(BaseModel):
    """Return schema for outputs."""
    
    type: str = Field(..., description="Data type: string, json, file, int, float, bool, array")
    description: str | None = Field(None, description="Human-readable description")
    output_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema for complex outputs"
    )


class CapabilitySpec(BaseModel):
    """Tier-gated feature (model, method, setting)."""
    
    name: str = Field(..., description="Capability identifier: summarize, deep_analysis, etc.")
    tier: Literal["FREE", "PRO", "ENTERPRISE"] = Field(
        ...,
        description="Minimum tier required to use this capability"
    )
    description: str | None = Field(None, description="What this capability does")
    params: dict[str, InputSpec] = Field(
        default_factory=dict,
        description="Additional parameters for this capability"
    )


class ObjectDefinition(BaseModel):
    """Base class for all object definitions (agent/tool/source).
    
    Stored in Firestore collections: /agent_definitions/, /tool_definitions/, /source_definitions/
    """
    
    # Identity
    id: str = Field(..., description="Definition ID (agent_id, tool_id, source_id)")
    title: str = Field(..., min_length=1, max_length=200, description="Display name")
    description: str | None = Field(None, max_length=2000, description="Detailed description")
    
    # Tier gating
    min_tier: Literal["FREE", "PRO", "ENTERPRISE"] = Field(
        default="FREE",
        description="Minimum subscription tier required to use this definition"
    )
    
    # ACL
    acl: dict[str, str | list[str]] = Field(
        default_factory=lambda: {"owner": "", "editors": [], "viewers": []},
        description="Access control: {owner: str, editors: list[str], viewers: list[str]}"
    )
    
    # Metadata
    created_by: str = Field(..., description="User ID (systemadmin for system definitions)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tags & categorization
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    category: str | None = Field(None, description="Category: data, analytics, communication, etc.")
    
    # Status
    enabled: bool = Field(default=True, description="Whether this definition is available")
    deprecated: bool = Field(default=False, description="Whether this definition is deprecated")


class AgentDefinition(ObjectDefinition):
    """Agent template — AI executor with model and prompts.
    
    Agents are stateless executors with:
    - Model selection (tier-gated)
    - System prompts
    - Input/output schemas
    - Capabilities (summarize, deep_analysis, etc.)
    """
    
    # I/O Contract
    inputs: dict[str, InputSpec] = Field(
        default_factory=dict,
        description="Input parameters the agent accepts"
    )
    outputs: dict[str, OutputSpec] = Field(
        default_factory=dict,
        description="Output formats the agent produces"
    )
    
    # Agent-specific configuration
    models: list[str] = Field(
        default_factory=list,
        description="Available model IDs (tier-gated in capabilities)"
    )
    default_model: str = Field(..., description="Default model to use")
    system_prompt: str | None = Field(
        None,
        description="System prompt template (supports {{variables}})"
    )
    
    # Tier-gated features
    capabilities: list[CapabilitySpec] = Field(
        default_factory=list,
        description="Tier-gated capabilities (models, methods, settings)"
    )
    
    # Execution config
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class ToolDefinition(ObjectDefinition):
    """Tool template — deterministic function or API.
    
    Tools are stateless capabilities with:
    - Input/output schemas
    - Execution type (function, api, script)
    - Tier-gated capabilities
    """
    
    # I/O Contract
    inputs: dict[str, InputSpec] = Field(
        default_factory=dict,
        description="Input parameters the tool accepts"
    )
    outputs: dict[str, OutputSpec] = Field(
        default_factory=dict,
        description="Output formats the tool produces"
    )
    
    # Tool-specific configuration
    execute_type: Literal["function", "api", "script", "pipeline"] = Field(
        ...,
        description="How the tool is executed"
    )
    execute_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution-specific config: {endpoint, method, script_path, etc.}"
    )
    
    # Tier-gated features
    capabilities: list[CapabilitySpec] = Field(
        default_factory=list,
        description="Tier-gated capabilities (methods, formats, options)"
    )
    
    # Quota
    quota_cost: int = Field(default=1, ge=0, description="Quota units consumed per execution")
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class SourceType(str, Enum):
    """Types of data sources."""
    
    FILE = "file"           # Static file (CSV, JSON, PDF, etc.)
    API = "api"             # REST/GraphQL endpoint
    DATABASE = "database"   # SQL/NoSQL connection
    STREAM = "stream"       # Real-time data feed
    STORAGE = "storage"     # Cloud storage (S3, GCS, Azure Blob)


class SourceDefinition(ObjectDefinition):
    """Source template — data connector (output-only).
    
    Sources are system-defined connectors with:
    - Connection schema (required params)
    - Output formats
    - Authentication types
    
    Key difference from Agent/Tool:
    - NO inputs (doesn't accept data)
    - NO methods (doesn't process)
    - Output-only terminal
    """
    
    # Source type
    source_type: SourceType = Field(..., description="Type of data source")
    
    # Output contract (NO inputs)
    outputs: dict[str, OutputSpec] = Field(
        default_factory=dict,
        description="Output data formats provided by this source"
    )
    
    # Connection configuration
    connection_schema: dict[str, InputSpec] = Field(
        default_factory=dict,
        description="Required connection parameters (URL, credentials ref, etc.)"
    )
    auth_types: list[Literal["none", "api_key", "oauth", "basic", "connection_string"]] = Field(
        default_factory=lambda: ["none"],
        description="Supported authentication types"
    )
    
    # Data delivery
    frequency: Literal["once", "polling", "realtime"] = Field(
        default="once",
        description="How data is delivered"
    )
    format: str = Field(default="json", description="Default output format")
    
    # Quota
    quota_cost: int = Field(default=1, ge=0, description="Quota units per read/poll")
