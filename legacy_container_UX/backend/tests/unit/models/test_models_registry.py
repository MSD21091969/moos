"""Tests for registry models."""

from src.models.registry import ToolMetadata, AgentMetadata, ResourceTier


class TestToolMetadata:
    """Tests for ToolMetadata dataclass."""

    def test_tool_metadata_creation(self):
        """Test creating tool metadata with minimal fields."""
        metadata = ToolMetadata(
            name="test_tool",
            description="Test tool description",
            category="data_analysis",
        )
        assert metadata.name == "test_tool"
        assert metadata.description == "Test tool description"
        assert metadata.category == "data_analysis"
        assert metadata.required_tier == "FREE"
        assert metadata.quota_cost == 1
        assert metadata.enabled is True
        assert metadata.tags == []
        assert metadata.allowed_user_ids == []
        assert metadata.requires_admin is False

    def test_tool_metadata_with_acl(self):
        """Test creating tool metadata with ACL fields."""
        metadata = ToolMetadata(
            name="custom_tool",
            description="Custom tool",
            category="utility",
            allowed_user_ids=["user_123", "user_456"],
            requires_admin=True,
        )
        assert metadata.allowed_user_ids == ["user_123", "user_456"]
        assert metadata.requires_admin is True

    def test_tool_metadata_with_all_fields(self):
        """Test creating tool metadata with all fields."""
        metadata = ToolMetadata(
            name="advanced_tool",
            description="Advanced tool",
            category="data_analysis",
            required_tier="PRO",
            quota_cost=5,
            enabled=False,
            tags=["advanced", "analytics"],
            allowed_user_ids=["user_789"],
            requires_admin=False,
        )
        assert metadata.name == "advanced_tool"
        assert metadata.required_tier == "PRO"
        assert metadata.quota_cost == 5
        assert metadata.enabled is False
        assert metadata.tags == ["advanced", "analytics"]
        assert metadata.allowed_user_ids == ["user_789"]


class TestAgentMetadata:
    """Tests for AgentMetadata dataclass."""

    def test_agent_metadata_creation(self):
        """Test creating agent metadata with minimal fields."""
        metadata = AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent description",
        )
        assert metadata.agent_id == "test_agent"
        assert metadata.name == "Test Agent"
        assert metadata.description == "Test agent description"
        assert metadata.required_tier == "FREE"
        assert metadata.quota_cost_multiplier == 1.0
        assert metadata.enabled is True
        assert metadata.tags == []
        assert metadata.allowed_user_ids == []
        assert metadata.requires_admin is False
        assert metadata.default_model is None
        assert metadata.system_prompt is None

    def test_agent_metadata_with_acl(self):
        """Test creating agent metadata with ACL fields."""
        metadata = AgentMetadata(
            agent_id="custom_agent",
            name="Custom Agent",
            description="Custom agent",
            allowed_user_ids=["user_123"],
            requires_admin=True,
        )
        assert metadata.allowed_user_ids == ["user_123"]
        assert metadata.requires_admin is True

    def test_agent_metadata_with_all_fields(self):
        """Test creating agent metadata with all fields."""
        metadata = AgentMetadata(
            agent_id="advanced_agent",
            name="Advanced Agent",
            description="Advanced agent",
            required_tier="ENTERPRISE",
            quota_cost_multiplier=2.5,
            enabled=True,
            tags=["advanced", "enterprise"],
            allowed_user_ids=["user_999"],
            requires_admin=False,
            default_model="openai:gpt-4",
            system_prompt="You are an advanced assistant.",
        )
        assert metadata.agent_id == "advanced_agent"
        assert metadata.required_tier == "ENTERPRISE"
        assert metadata.quota_cost_multiplier == 2.5
        assert metadata.tags == ["advanced", "enterprise"]
        assert metadata.default_model == "openai:gpt-4"
        assert metadata.system_prompt == "You are an advanced assistant."


class TestResourceTier:
    """Tests for ResourceTier enum."""

    def test_resource_tier_values(self):
        """Test ResourceTier enum values."""
        assert ResourceTier.FREE == "FREE"
        assert ResourceTier.PRO == "PRO"
        assert ResourceTier.ENTERPRISE == "ENTERPRISE"
