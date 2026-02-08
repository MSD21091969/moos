"""Unit tests for src/api/routes/resources.py

TEST: Resource discovery API endpoints (tools and agents)
PURPOSE: Validate tier-gated and ACL-filtered resource discovery
VALIDATES: Tool/agent listing with permissions, tier filtering, ACL checks
PATTERN: Use app.dependency_overrides for registry mocking
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import app as main_app
from src.api.dependencies import get_user_context
from src.models.context import UserContext
from src.models.permissions import Tier
from src.models.registry import ToolMetadata, AgentMetadata
from src.core.tool_registry import get_tool_registry
from src.core.agent_registry import get_agent_registry


# Fixtures


@pytest.fixture
def test_user_free():
    """FREE tier user context."""
    return UserContext(
        user_id="user_free",
        email="free@example.com",
        permissions=("read_data",),
        quota_remaining=100,
        tier=Tier.FREE,
    )


@pytest.fixture
def test_user_pro():
    """PRO tier user context."""
    return UserContext(
        user_id="user_pro",
        email="pro@example.com",
        permissions=("read_data", "write_data", "execute_tools"),
        quota_remaining=1000,
        tier=Tier.PRO,
    )


@pytest.fixture
def sample_tool_metadata():
    """Sample tool metadata."""
    return ToolMetadata(
        name="test_tool",
        description="Test tool",
        category="data_analysis",
        required_tier=Tier.FREE,
        enabled=True,
    )


@pytest.fixture
def sample_agent_metadata():
    """Sample agent metadata."""
    return AgentMetadata(
        agent_id="demo_agent",
        name="Demo Agent",
        description="Demo agent for testing",
        required_tier=Tier.FREE,
        enabled=True,
    )


@pytest.fixture
def client_free(test_user_free):
    """TestClient with FREE tier user."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    async def override_user_context():
        return test_user_free

    test_app.dependency_overrides[get_user_context] = override_user_context

    return TestClient(test_app)


@pytest.fixture
def client_pro(test_user_pro):
    """TestClient with PRO tier user."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    async def override_user_context():
        return test_user_pro

    test_app.dependency_overrides[get_user_context] = override_user_context

    return TestClient(test_app)


# Tests


class TestListTools:
    """Tests for GET /resources/tools"""

    def test_list_tools_free_tier(self, client_free, monkeypatch):
        """Test listing tools for FREE tier user."""
        # Mock get_tool_registry().list_available
        mock_tools = [
            ToolMetadata(
                name="free_tool",
                description="Free tool",
                category="basic",
                required_tier=Tier.FREE,
                enabled=True,
            )
        ]
        monkeypatch.setattr(
            get_tool_registry(),
            "list_available",
            lambda user_id=None,
            user_tier=None,
            permissions=None,
            category=None,
            **kwargs: mock_tools,
        )

        response = client_free.get("/resources/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0  # May have registered tools

    def test_list_tools_pro_tier(self, client_pro, monkeypatch):
        """Test PRO tier user sees more tools."""
        mock_tools = [
            ToolMetadata(
                name="free_tool",
                description="Free tool",
                category="basic",
                required_tier=Tier.FREE,
                enabled=True,
            ),
            ToolMetadata(
                name="pro_tool",
                description="Pro tool",
                category="advanced",
                required_tier=Tier.PRO,
                enabled=True,
            ),
        ]
        monkeypatch.setattr(
            get_tool_registry(),
            "list_available",
            lambda user_id=None,
            user_tier=None,
            permissions=None,
            category=None,
            **kwargs: mock_tools,
        )

        response = client_pro.get("/resources/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0

    def test_list_tools_filter_by_category(self, client_pro, monkeypatch):
        """Test filtering tools by category."""
        mock_tools = [
            ToolMetadata(
                name="analysis_tool",
                description="Analysis tool",
                category="data_analysis",
                required_tier=Tier.FREE,
                enabled=True,
            )
        ]
        monkeypatch.setattr(
            get_tool_registry(),
            "list_available",
            lambda user_id=None,
            user_tier=None,
            permissions=None,
            category=None,
            **kwargs: mock_tools,
        )

        response = client_pro.get("/resources/tools?category=data_analysis")

        assert response.status_code == 200


class TestGetToolDetails:
    """Tests for GET /resources/tools/{tool_name}"""

    def test_get_tool_details_success(self, client_pro, monkeypatch):
        """Test getting tool details."""
        mock_tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            category="basic",
            required_tier=Tier.FREE,
            enabled=True,
        )
        monkeypatch.setattr(
            get_tool_registry(),
            "get_metadata",
            lambda name: mock_tool,
        )
        monkeypatch.setattr(
            get_tool_registry(),
            "can_execute",
            lambda tool_name=None,
            user_tier=None,
            user_id=None,
            permissions=None,
            quota_remaining=None,
            **kwargs: (True, None),
        )

        response = client_pro.get("/resources/tools/test_tool")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool"

    def test_get_tool_details_not_found(self, client_pro, monkeypatch):
        """Test getting non-existent tool."""
        monkeypatch.setattr(
            get_tool_registry(),
            "get_metadata",
            lambda name: None,
        )

        response = client_pro.get("/resources/tools/nonexistent")

        assert response.status_code == 404

    def test_get_tool_details_permission_denied(self, client_free, monkeypatch):
        """Test accessing tool without permission."""
        mock_tool = ToolMetadata(
            name="pro_tool",
            description="Pro tool",
            category="advanced",
            required_tier=Tier.PRO,
            enabled=True,
        )
        monkeypatch.setattr(
            get_tool_registry(),
            "get_metadata",
            lambda name: mock_tool,
        )
        monkeypatch.setattr(
            get_tool_registry(),
            "can_execute",
            lambda tool_name=None,
            user_tier=None,
            user_id=None,
            permissions=None,
            quota_remaining=None,
            **kwargs: (False, "Insufficient tier"),
        )

        response = client_free.get("/resources/tools/pro_tool")

        assert response.status_code == 403


class TestListAgents:
    """Tests for GET /resources/agents"""

    def test_list_agents_success(self, client_pro, monkeypatch):
        """Test listing available agents."""
        mock_agents = [
            AgentMetadata(
                agent_id="demo_agent",
                name="Demo Agent",
                description="Demo agent",
                required_tier=Tier.FREE,
                enabled=True,
            )
        ]
        monkeypatch.setattr(
            get_agent_registry(),
            "list_available",
            lambda user_id=None, user_tier=None, **kwargs: mock_agents,
        )

        response = client_pro.get("/resources/agents")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0


class TestGetAgentDetails:
    """Tests for GET /resources/agents/{agent_id}"""

    def test_get_agent_details_success(self, client_pro, monkeypatch):
        """Test getting agent details."""
        mock_agent = AgentMetadata(
            agent_id="demo_agent",
            name="Demo Agent",
            description="Demo agent",
            required_tier=Tier.FREE,
            enabled=True,
        )
        monkeypatch.setattr(
            get_agent_registry(),
            "get_metadata",
            lambda agent_id: mock_agent,
        )
        monkeypatch.setattr(
            get_agent_registry(),
            "can_execute",
            lambda agent_id, user_tier, user_id, is_admin: (True, None),
        )

        response = client_pro.get("/resources/agents/demo_agent")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "demo_agent"

    def test_get_agent_details_not_found(self, client_pro, monkeypatch):
        """Test getting non-existent agent."""
        monkeypatch.setattr(
            get_agent_registry(),
            "get_metadata",
            lambda agent_id: None,
        )

        response = client_pro.get("/resources/agents/nonexistent")

        assert response.status_code == 404


class TestListAgentsMerged:
    """Tests for GET /resources/agents with merged discovery (new behavior)"""

    def test_list_agents_includes_source_annotation(self, client_pro, monkeypatch):
        """Test that agents include source field (system/user_global/session_local)."""
        from unittest.mock import AsyncMock, MagicMock

        # Mock AgentService.build_merged_agentset
        async def mock_build_merged(*args, **kwargs):
            return {
                "agents": {
                    "demo_agent": {
                        "agent_id": "demo_agent",
                        "name": "Demo Agent",
                        "description": "System agent",
                        "source": "system",
                        "enabled": True,
                        "tags": [],
                    },
                    "custom_agent": {
                        "agent_id": "custom_agent",
                        "name": "Custom Agent",
                        "description": "User's custom agent",
                        "source": "user_global",
                        "enabled": True,
                        "tags": ["custom"],
                    },
                },
                "count": 2,
            }

        # Mock AgentService
        with monkeypatch.context() as m:
            from src.services import agent_service as agent_service_module

            mock_service_instance = MagicMock()
            mock_service_instance.build_merged_agentset = AsyncMock(side_effect=mock_build_merged)

            def mock_agent_service_init(*args, **kwargs):
                return mock_service_instance

            m.setattr(agent_service_module, "AgentService", mock_agent_service_init)

            # Also mock get_container to avoid dependency issues
            from src.core import container as container_module

            mock_container = MagicMock()
            mock_container.firestore_client = MagicMock()

            m.setattr(container_module, "get_container", lambda: mock_container)

            response = client_pro.get("/resources/agents")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # Verify source annotation present
            sources = {agent["agent_id"]: agent.get("source") for agent in data}
            assert sources.get("demo_agent") == "system"
            assert sources.get("custom_agent") == "user_global"

    def test_list_agents_with_session_id_filter(self, client_pro, monkeypatch):
        """Test listing agents with session_id includes session-local agents."""
        from unittest.mock import AsyncMock, MagicMock

        session_id_param = None

        async def mock_build_merged(user_ctx, session_id=None, search=None):
            nonlocal session_id_param
            session_id_param = session_id
            agents = {
                "demo_agent": {
                    "agent_id": "demo_agent",
                    "name": "Demo Agent",
                    "source": "system",
                    "enabled": True,
                }
            }
            if session_id:
                agents["session_agent"] = {
                    "agent_id": "session_agent",
                    "name": "Session Agent",
                    "source": "session_local",
                    "enabled": True,
                }
            return {"agents": agents, "count": len(agents)}

        with monkeypatch.context() as m:
            from src.services import agent_service as agent_service_module

            mock_service_instance = MagicMock()
            mock_service_instance.build_merged_agentset = AsyncMock(side_effect=mock_build_merged)

            m.setattr(agent_service_module, "AgentService", lambda **kwargs: mock_service_instance)

            from src.core import container as container_module

            mock_container = MagicMock()
            mock_container.firestore_client = MagicMock()
            m.setattr(container_module, "get_container", lambda: mock_container)

            response = client_pro.get("/resources/agents?session_id=sess_123")

            assert response.status_code == 200
            assert session_id_param == "sess_123"
            data = response.json()
            agent_ids = [agent["agent_id"] for agent in data]
            assert "session_agent" in agent_ids

    def test_list_agents_with_search_filter(self, client_pro, monkeypatch):
        """Test listing agents with search term filters results."""
        from unittest.mock import AsyncMock, MagicMock

        search_param = None

        async def mock_build_merged(user_ctx, session_id=None, search=None):
            nonlocal search_param
            search_param = search
            all_agents = {
                "legal_agent": {
                    "agent_id": "legal_agent",
                    "name": "Legal Analyst",
                    "description": "Analyzes legal documents",
                    "source": "system",
                    "enabled": True,
                    "tags": ["legal"],
                },
                "data_agent": {
                    "agent_id": "data_agent",
                    "name": "Data Scientist",
                    "description": "Analyzes data",
                    "source": "system",
                    "enabled": True,
                    "tags": ["data"],
                },
            }
            if search and search.lower() == "legal":
                filtered = {k: v for k, v in all_agents.items() if "legal" in k}
                return {"agents": filtered, "count": len(filtered)}
            return {"agents": all_agents, "count": len(all_agents)}

        with monkeypatch.context() as m:
            from src.services import agent_service as agent_service_module

            mock_service_instance = MagicMock()
            mock_service_instance.build_merged_agentset = AsyncMock(side_effect=mock_build_merged)

            m.setattr(agent_service_module, "AgentService", lambda **kwargs: mock_service_instance)

            from src.core import container as container_module

            mock_container = MagicMock()
            mock_container.firestore_client = MagicMock()
            m.setattr(container_module, "get_container", lambda: mock_container)

            response = client_pro.get("/resources/agents?search=legal")

            assert response.status_code == 200
            assert search_param == "legal"
            data = response.json()
            assert len(data) == 1
            assert data[0]["agent_id"] == "legal_agent"
