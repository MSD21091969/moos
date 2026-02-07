"""Agent registry for managing available agents with metadata and ACL."""

from typing import Optional
from pydantic_ai import Agent

from src.models.registry import AgentMetadata


class AgentRegistry:
    """
    Registry for managing available agents.

    Provides:
    - Agent registration with metadata
    - Tier and ACL-based discovery
    - Permission checking
    - Agent enabling/disabling
    """

    def __init__(self):
        """Initialize empty registry."""
        self._agents: dict[str, AgentMetadata] = {}
        self._agent_instances: dict[str, Agent] = {}

    def register(
        self,
        agent_id: str,
        name: str,
        description: str,
        agent_instance: Agent,
        required_tier: str = "FREE",
        quota_cost_multiplier: float = 1.0,
        tags: Optional[list[str]] = None,
        allowed_user_ids: Optional[list[str]] = None,
        requires_admin: bool = False,
        enabled: bool = True,
        default_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Agent:
        """
        Register an agent with metadata.

        Args:
            agent_id: Agent identifier
            name: Human-readable name
            description: Agent capabilities
            agent_instance: PydanticAI Agent instance
            required_tier: Minimum tier needed ("FREE", "PRO", "ENTERPRISE")
            quota_cost_multiplier: Multiplier for quota calculations
            tags: Optional tags for discovery
            allowed_user_ids: ACL - specific users with access
            requires_admin: Whether agent requires admin privileges
            enabled: Whether agent is currently available
            default_model: Default LLM model to use
            system_prompt: Agent's system prompt

        Returns:
            Agent instance (for chaining)

        Example:
            >>> registry = AgentRegistry()
            >>> agent = Agent("openai:gpt-4", deps_type=SessionContext)
            >>> registry.register(
            ...     agent_id="demo_agent",
            ...     name="Demo Agent",
            ...     description="Helpful assistant",
            ...     agent_instance=agent,
            ...     required_tier="FREE"
            ... )
        """
        metadata = AgentMetadata(
            agent_id=agent_id,
            name=name,
            description=description,
            required_tier=required_tier,
            quota_cost_multiplier=quota_cost_multiplier,
            enabled=enabled,
            tags=tags or [],
            allowed_user_ids=allowed_user_ids or [],
            requires_admin=requires_admin,
            default_model=default_model,
            system_prompt=system_prompt,
        )

        self._agents[agent_id] = metadata
        self._agent_instances[agent_id] = agent_instance

        return agent_instance

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get metadata for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentMetadata or None if not found
        """
        return self._agents.get(agent_id)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent instance.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        return self._agent_instances.get(agent_id)

    def list_available(
        self,
        user_tier: str,
        user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> list[AgentMetadata]:
        """
        List agents available to a user based on tier and ACL.

        Args:
            user_tier: User's subscription tier ("FREE", "PRO", "ENTERPRISE")
            user_id: User identifier (for ACL checks)
            is_admin: Whether user is admin (bypasses all restrictions)

        Returns:
            List of available agent metadata

        Example:
            >>> agents = registry.list_available(
            ...     user_tier="PRO",
            ...     user_id="user_123"
            ... )
        """
        available = []
        tier_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        user_tier_level = tier_hierarchy.get(user_tier.upper(), 0)

        for agent in self._agents.values():
            # Skip disabled agents
            if not agent.enabled:
                continue

            # Admin bypass
            if is_admin:
                available.append(agent)
                continue

            # Check if admin required
            if agent.requires_admin:
                continue

            # Check ACL (if specified)
            if agent.allowed_user_ids:
                if user_id and user_id in agent.allowed_user_ids:
                    available.append(agent)
                continue

            # Check tier access
            agent_tier_level = tier_hierarchy.get(agent.required_tier.upper(), 0)
            if user_tier_level >= agent_tier_level:
                available.append(agent)

        return available

    def can_execute(
        self,
        agent_id: str,
        user_tier: str,
        user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can execute an agent.

        Args:
            agent_id: Agent to check
            user_tier: User's subscription tier
            user_id: User identifier (for ACL)
            is_admin: Whether user is admin

        Returns:
            (can_execute: bool, reason: Optional[str])

        Example:
            >>> can_run, reason = registry.can_execute(
            ...     "demo_agent",
            ...     user_tier="PRO",
            ...     user_id="user_123"
            ... )
            >>> if not can_run:
            ...     print(f"Cannot run: {reason}")
        """
        metadata = self.get_metadata(agent_id)

        if not metadata:
            return False, f"Agent '{agent_id}' not found"

        if not metadata.enabled:
            return False, f"Agent '{agent_id}' is disabled"

        # Admin bypass
        if is_admin:
            return True, None

        # Check if admin required
        if metadata.requires_admin:
            return False, "Admin privileges required"

        # Check ACL (if specified)
        if metadata.allowed_user_ids:
            if not user_id or user_id not in metadata.allowed_user_ids:
                return False, "Not authorized to use this agent"
            return True, None

        # Check tier access
        tier_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        user_tier_level = tier_hierarchy.get(user_tier.upper(), 0)
        agent_tier_level = tier_hierarchy.get(metadata.required_tier.upper(), 0)

        if user_tier_level < agent_tier_level:
            return False, f"Requires {metadata.required_tier} tier (you have {user_tier})"

        return True, None

    def enable_agent(self, agent_id: str):
        """Enable an agent."""
        if agent_id in self._agents:
            self._agents[agent_id].enabled = True

    def disable_agent(self, agent_id: str):
        """Disable an agent."""
        if agent_id in self._agents:
            self._agents[agent_id].enabled = False

    def list_all_ids(self) -> list[str]:
        """Get list of all registered agent IDs."""
        return list(self._agents.keys())

    def search_by_tag(self, tag: str) -> list[AgentMetadata]:
        """
        Search agents by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of agents with matching tag
        """
        return [agent for agent in self._agents.values() if tag in agent.tags and agent.enabled]


# Global registry instance
_global_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create global agent registry."""
    global _global_agent_registry
    if _global_agent_registry is None:
        _global_agent_registry = AgentRegistry()
    return _global_agent_registry


def reset_agent_registry():
    """Reset global registry (for testing)."""
    global _global_agent_registry
    _global_agent_registry = None
