"""Registry models for tools and agents with tier and ACL support."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.links import ResourceLink


class ResourceTier(str, Enum):
    """Resource tier levels for access control."""

    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


@dataclass
class ToolMetadata:
    """
    Enhanced tool metadata with ACL support.

    Attributes:
        name: Tool identifier
        description: Brief description of what tool does
        category: Tool category for organization
        required_tier: Minimum tier needed to use tool (FREE/PRO/ENTERPRISE)
        quota_cost: Quota units consumed per execution
        enabled: Whether tool is currently available
        tags: Optional tags for discovery
        allowed_user_ids: ACL - specific users with access (empty = tier-based only)
        requires_admin: Whether tool requires admin privileges
    """

    name: str
    description: str
    category: str
    required_tier: str = "FREE"
    quota_cost: int = 1
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    # ACL fields
    allowed_user_ids: list[str] = field(default_factory=list)
    requires_admin: bool = False


@dataclass
class AgentMetadata:
    """
    Agent metadata for registry.

    Attributes:
        agent_id: Agent identifier
        name: Human-readable name
        description: Agent capabilities description
        required_tier: Minimum tier needed to use agent (FREE/PRO/ENTERPRISE)
        quota_cost_multiplier: Multiplier for quota calculations (default 1.0)
        enabled: Whether agent is currently available
        tags: Optional tags for discovery
        allowed_user_ids: ACL - specific users with access (empty = tier-based only)
        requires_admin: Whether agent requires admin privileges
        default_model: Default LLM model to use
        system_prompt: Agent's system prompt
        resource_links: Default resources (tools/agents) linked to this agent
    """

    agent_id: str
    name: str
    description: str
    required_tier: str = "FREE"
    quota_cost_multiplier: float = 1.0
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    # ACL fields
    allowed_user_ids: list[str] = field(default_factory=list)
    requires_admin: bool = False
    # Agent-specific
    default_model: str | None = None
    system_prompt: str | None = None
    # Recursive Composition
    resource_links: list["ResourceLink"] = field(default_factory=list)
