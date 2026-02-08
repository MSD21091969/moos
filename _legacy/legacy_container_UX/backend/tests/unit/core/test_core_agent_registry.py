"""Tests for agent registry."""

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from src.core.agent_registry import AgentRegistry, get_agent_registry, reset_agent_registry
from src.models.context import SessionContext


@pytest.fixture
def registry():
    """Create fresh agent registry for each test."""
    reset_agent_registry()
    return AgentRegistry()


@pytest.fixture
def sample_agent():
    """Create sample agent instance."""
    return Agent(TestModel(), deps_type=SessionContext)


class TestAgentRegistryRegistration:
    """Tests for agent registration."""

    def test_register_agent_minimal(self, registry, sample_agent):
        """Test registering agent with minimal fields."""
        agent = registry.register(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            agent_instance=sample_agent,
        )

        assert agent is sample_agent
        assert "test_agent" in registry.list_all_ids()

        metadata = registry.get_metadata("test_agent")
        assert metadata is not None
        assert metadata.agent_id == "test_agent"
        assert metadata.name == "Test Agent"
        assert metadata.required_tier == "FREE"

    def test_register_agent_with_acl(self, registry, sample_agent):
        """Test registering agent with ACL."""
        registry.register(
            agent_id="custom_agent",
            name="Custom Agent",
            description="Custom agent",
            agent_instance=sample_agent,
            allowed_user_ids=["user_123", "user_456"],
        )

        metadata = registry.get_metadata("custom_agent")
        assert metadata.allowed_user_ids == ["user_123", "user_456"]

    def test_register_agent_admin_only(self, registry, sample_agent):
        """Test registering admin-only agent."""
        registry.register(
            agent_id="admin_agent",
            name="Admin Agent",
            description="Admin only",
            agent_instance=sample_agent,
            requires_admin=True,
        )

        metadata = registry.get_metadata("admin_agent")
        assert metadata.requires_admin is True

    def test_get_agent_instance(self, registry, sample_agent):
        """Test retrieving agent instance."""
        registry.register(
            agent_id="test_agent",
            name="Test",
            description="Test",
            agent_instance=sample_agent,
        )

        retrieved = registry.get_agent("test_agent")
        assert retrieved is sample_agent


class TestAgentRegistryDiscovery:
    """Tests for agent discovery and filtering."""

    def test_list_available_by_tier(self, registry, sample_agent):
        """Test listing agents filtered by tier."""
        # Register agents with different tiers
        agent1 = Agent(TestModel(), deps_type=SessionContext)
        agent2 = Agent(TestModel(), deps_type=SessionContext)
        agent3 = Agent(TestModel(), deps_type=SessionContext)

        registry.register("free_agent", "Free", "Free tier", agent1, required_tier="FREE")
        registry.register("pro_agent", "Pro", "Pro tier", agent2, required_tier="PRO")
        registry.register(
            "enterprise_agent", "Enterprise", "Enterprise tier", agent3, required_tier="ENTERPRISE"
        )

        # FREE tier user sees only FREE agents
        free_agents = registry.list_available(user_tier="FREE")
        assert len(free_agents) == 1
        assert free_agents[0].agent_id == "free_agent"

        # PRO tier user sees FREE and PRO
        pro_agents = registry.list_available(user_tier="PRO")
        assert len(pro_agents) == 2
        agent_ids = [a.agent_id for a in pro_agents]
        assert "free_agent" in agent_ids
        assert "pro_agent" in agent_ids

        # ENTERPRISE tier user sees all
        enterprise_agents = registry.list_available(user_tier="ENTERPRISE")
        assert len(enterprise_agents) == 3

    def test_list_available_with_acl(self, registry, sample_agent):
        """Test listing agents filtered by ACL."""
        agent1 = Agent(TestModel(), deps_type=SessionContext)
        agent2 = Agent(TestModel(), deps_type=SessionContext)

        # Public agent (tier-based)
        registry.register("public_agent", "Public", "Public", agent1, required_tier="FREE")

        # Custom agent (ACL-based)
        registry.register(
            "custom_agent",
            "Custom",
            "Custom",
            agent2,
            allowed_user_ids=["user_123"],
        )

        # user_123 sees both
        user_123_agents = registry.list_available(user_tier="FREE", user_id="user_123")
        assert len(user_123_agents) == 2

        # user_456 sees only public
        user_456_agents = registry.list_available(user_tier="FREE", user_id="user_456")
        assert len(user_456_agents) == 1
        assert user_456_agents[0].agent_id == "public_agent"

    def test_list_available_admin_bypass(self, registry, sample_agent):
        """Test admin sees all agents regardless of tier/ACL."""
        agent1 = Agent(TestModel(), deps_type=SessionContext)
        agent2 = Agent(TestModel(), deps_type=SessionContext)
        agent3 = Agent(TestModel(), deps_type=SessionContext)

        registry.register("free_agent", "Free", "Free", agent1, required_tier="FREE")
        registry.register("admin_agent", "Admin", "Admin only", agent2, requires_admin=True)
        registry.register("custom_agent", "Custom", "Custom", agent3, allowed_user_ids=["user_999"])

        # Admin sees all agents
        admin_agents = registry.list_available(
            user_tier="FREE", user_id="admin_user", is_admin=True
        )
        assert len(admin_agents) == 3

    def test_list_available_excludes_disabled(self, registry, sample_agent):
        """Test disabled agents are excluded from listing."""
        agent1 = Agent(TestModel(), deps_type=SessionContext)

        registry.register("enabled_agent", "Enabled", "Enabled", agent1, enabled=True)
        registry.register("disabled_agent", "Disabled", "Disabled", sample_agent, enabled=False)

        agents = registry.list_available(user_tier="FREE")
        assert len(agents) == 1
        assert agents[0].agent_id == "enabled_agent"


class TestAgentRegistryPermissions:
    """Tests for permission checking."""

    def test_can_execute_tier_check(self, registry, sample_agent):
        """Test can_execute with tier requirements."""
        registry.register("pro_agent", "Pro", "Pro only", sample_agent, required_tier="PRO")

        # PRO user can execute
        can_run, reason = registry.can_execute("pro_agent", user_tier="PRO")
        assert can_run is True
        assert reason is None

        # FREE user cannot
        can_run, reason = registry.can_execute("pro_agent", user_tier="FREE")
        assert can_run is False
        assert "PRO tier" in reason

    def test_can_execute_acl_check(self, registry, sample_agent):
        """Test can_execute with ACL."""
        registry.register(
            "custom_agent",
            "Custom",
            "Custom",
            sample_agent,
            allowed_user_ids=["user_123"],
        )

        # user_123 can execute
        can_run, reason = registry.can_execute("custom_agent", user_tier="FREE", user_id="user_123")
        assert can_run is True

        # user_456 cannot
        can_run, reason = registry.can_execute("custom_agent", user_tier="FREE", user_id="user_456")
        assert can_run is False
        assert "Not authorized" in reason

    def test_can_execute_admin_check(self, registry, sample_agent):
        """Test can_execute with admin requirement."""
        registry.register("admin_agent", "Admin", "Admin", sample_agent, requires_admin=True)

        # Admin can execute
        can_run, reason = registry.can_execute("admin_agent", user_tier="FREE", is_admin=True)
        assert can_run is True

        # Regular user cannot
        can_run, reason = registry.can_execute("admin_agent", user_tier="FREE", is_admin=False)
        assert can_run is False
        assert "Admin privileges required" in reason

    def test_can_execute_not_found(self, registry):
        """Test can_execute with non-existent agent."""
        can_run, reason = registry.can_execute("missing_agent", user_tier="FREE")
        assert can_run is False
        assert "not found" in reason

    def test_can_execute_disabled(self, registry, sample_agent):
        """Test can_execute with disabled agent."""
        registry.register("disabled_agent", "Disabled", "Disabled", sample_agent, enabled=False)

        can_run, reason = registry.can_execute("disabled_agent", user_tier="FREE")
        assert can_run is False
        assert "disabled" in reason


class TestAgentRegistryManagement:
    """Tests for agent management operations."""

    def test_enable_disable_agent(self, registry, sample_agent):
        """Test enabling and disabling agents."""
        registry.register("test_agent", "Test", "Test", sample_agent, enabled=True)

        # Disable agent
        registry.disable_agent("test_agent")
        metadata = registry.get_metadata("test_agent")
        assert metadata.enabled is False

        # Enable agent
        registry.enable_agent("test_agent")
        metadata = registry.get_metadata("test_agent")
        assert metadata.enabled is True

    def test_search_by_tag(self, registry, sample_agent):
        """Test searching agents by tag."""
        agent1 = Agent(TestModel(), deps_type=SessionContext)
        agent2 = Agent(TestModel(), deps_type=SessionContext)

        registry.register("agent1", "Agent 1", "First", agent1, tags=["data", "analysis"])
        registry.register("agent2", "Agent 2", "Second", agent2, tags=["export", "data"])

        # Search for "data" tag
        data_agents = registry.search_by_tag("data")
        assert len(data_agents) == 2

        # Search for "analysis" tag
        analysis_agents = registry.search_by_tag("analysis")
        assert len(analysis_agents) == 1
        assert analysis_agents[0].agent_id == "agent1"


class TestGlobalAgentRegistry:
    """Tests for global registry singleton."""

    def test_get_agent_registry_singleton(self):
        """Test global registry is singleton."""
        reset_agent_registry()

        registry1 = get_agent_registry()
        registry2 = get_agent_registry()

        assert registry1 is registry2

    def test_reset_agent_registry(self):
        """Test resetting global registry."""
        registry1 = get_agent_registry()
        reset_agent_registry()
        registry2 = get_agent_registry()

        assert registry1 is not registry2
