"""Agent metadata models."""

from typing import Optional
from pydantic import BaseModel, Field
from src.models.links import ResourceLink


class AgentInfo(BaseModel):
    """Agent metadata for discovery and selection."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent purpose and capabilities")
    required_tier: str = Field(default="free", description="Minimum tier required")
    capabilities: dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    available_models: list[str] = Field(default_factory=list, description="Supported LLM models")
    quota_cost_per_message: int = Field(default=1, ge=1, description="Base quota cost")
    enabled: bool = Field(default=True, description="Whether agent is active")
    system_prompt: Optional[str] = Field(None, description="Default system prompt")
    max_tokens: Optional[int] = Field(None, ge=1, description="Max output tokens")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    
    # Recursive Composition
    resource_links: list[ResourceLink] = Field(
        default_factory=list, 
        description="Linked resources (tools, other agents)"
    )
