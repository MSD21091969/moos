"""
TEST: src/services/agent_service.py - Agent execution service
PURPOSE: Validate agent execution, quota checks, session management, tool tracking
VALIDATES: AgentExecutionResult, quota enforcement, session creation, tool usage extraction
EXPECTED: Successful agent runs, quota validation, proper session handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import InsufficientQuotaError, ValidationError
from src.models.context import UserContext
from src.models.permissions import Tier
from src.services.agent_service import AgentExecutionResult, AgentService


class TestAgentExecutionResult:
    """Test AgentExecutionResult data structure."""

    def test_result_initialization(self):
        """
        TEST: Initialize AgentExecutionResult
        PURPOSE: Validate result object creation with all fields
        VALIDATES: All fields accessible after initialization
        EXPECTED: Result contains session_id, response, tools, quota data
        """
        result = AgentExecutionResult(
            session_id="sess_123abc456def",
            message_id="msg_789",
            response="Agent response text",
            tools_used=["text_transform", "count_words"],
            new_messages_count=2,
            quota_used=5,
            quota_remaining=95,
            model_used="openai:gpt-4o",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        assert result.session_id == "sess_123abc456def"
        assert result.message_id == "msg_789"
        assert result.response == "Agent response text"
        assert result.tools_used == ["text_transform", "count_words"]
        assert result.new_messages_count == 2
        assert result.quota_used == 5
        assert result.quota_remaining == 95
        assert result.model_used == "openai:gpt-4o"
        assert result.usage["input_tokens"] == 100
        assert result.usage["output_tokens"] == 50


class TestAgentService:
    """Test suite for AgentService."""

    @pytest.fixture
    def user_ctx(self):
        """Create UserContext for testing."""
        return UserContext(
            user_id="user_test_123",
            email="test@test.com",
            tier=Tier.PRO,
            permissions=["agent:run", "tools:use"],
            quota_remaining=100,
        )

    @pytest.fixture
    def mock_session_service(self):
        """Create mock SessionService."""
        service = AsyncMock()
        # Make async methods return values properly
        session_new = MagicMock(session_id="sess_new_123")
        service.create = AsyncMock(return_value=session_new)

        session_existing = MagicMock(
            session_id="sess_existing_456", user_id="user_test_123", event_count=5
        )
        service.get = AsyncMock(return_value=session_existing)
        service.add_message = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def mock_tool_service(self):
        """Create mock ToolService."""
        service = MagicMock()
        return service

    @pytest.fixture
    def agent_service(self, mock_session_service, mock_tool_service):
        """Create AgentService with mocked dependencies."""
        return AgentService(session_service=mock_session_service, tool_service=mock_tool_service)

    @pytest.mark.asyncio
    async def test_run_agent_returns_response_text(self, agent_service, user_ctx):
        """
        TEST: run_agent() returns response text
        PURPOSE: Validate simplified interface returns only text
        VALIDATES: run_agent() wraps execute() and extracts response
        EXPECTED: String response text returned
        """
        with patch.object(agent_service, "execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = AgentExecutionResult(
                session_id="sess_123",
                message_id="msg_456",
                response="Test response",
                tools_used=[],
                new_messages_count=2,
                quota_used=3,
                quota_remaining=97,
                model_used="openai:gpt-4o",
                usage={"input_tokens": 50, "output_tokens": 30},
            )

            response = await agent_service.run_agent(user_ctx, "Test message")

            assert response == "Test response"
            mock_exec.assert_called_once_with(user_ctx, "Test message", None, None)

    @pytest.mark.asyncio
    async def test_execute_creates_session_when_none_provided(
        self, agent_service, user_ctx, mock_session_service
    ):
        """
        TEST: Auto-create session when session_id is None
        PURPOSE: Validate ephemeral session creation
        VALIDATES: execute() creates session if not provided
        EXPECTED: New session_id generated, session_id in result
        """
        with patch("src.services.agent_service.demo_agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.response = "Agent response"
            mock_result.new_messages = MagicMock(return_value=[])
            # Create usage object with input/output tokens
            mock_usage = MagicMock()
            mock_usage.input_tokens = 100
            mock_usage.output_tokens = 50
            mock_result.usage = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)

            with patch(
                "src.services.agent_service.uuid.uuid4", return_value=MagicMock(hex="abc123def456")
            ):
                result = await agent_service.execute(user_ctx, "Test message", session_id=None)

            # Session ID generated (not created in database, just ephemeral)
            assert result.session_id is not None
            assert result.session_id.startswith("sess_")
            assert len(result.session_id) == 17  # "sess_" + 12 hex chars

    @pytest.mark.asyncio
    async def test_execute_uses_existing_session(
        self, agent_service, user_ctx, mock_session_service
    ):
        """
        TEST: Use existing session when session_id provided
        PURPOSE: Validate session continuation
        VALIDATES: execute() uses provided session_id
        EXPECTED: SessionService.get() called, no create()
        """
        with patch("src.services.agent_service.demo_agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.response = "Agent response"
            mock_result.new_messages = MagicMock(return_value=[])
            # Create usage object with input/output tokens
            mock_usage = MagicMock()
            mock_usage.input_tokens = 100
            mock_usage.output_tokens = 50
            mock_result.usage = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)

            # Mock the container and session service
            with patch("src.core.container.get_container") as mock_get_container:
                mock_container = MagicMock()
                mock_container.firestore_client = MagicMock()
                mock_get_container.return_value = mock_container

                # Create mock session service that will be instantiated
                mock_session = MagicMock(
                    session_id="sess_existing_456",
                    user_id="user_test_123",
                    event_count=5,
                    is_active=True,
                    status="active",
                )

                with patch("src.services.session_service.SessionService") as MockSessionService:
                    mock_svc = AsyncMock()
                    mock_svc.get = AsyncMock(return_value=mock_session)
                    MockSessionService.return_value = mock_svc

                    with patch(
                        "src.services.agent_service.uuid.uuid4",
                        return_value=MagicMock(hex="abc123"),
                    ):
                        await agent_service.execute(
                            user_ctx, "Test message", session_id="sess_existing_456"
                        )

                    # Existing session retrieved
                    mock_svc.get.assert_called_once_with("sess_existing_456", "user_test_123")

    @pytest.mark.asyncio
    async def test_execute_raises_insufficient_quota(self, agent_service, user_ctx):
        """
        TEST: Raise InsufficientQuotaError when quota too low
        PURPOSE: Validate quota pre-check (Level 2)
        VALIDATES: execute() checks quota before running agent
        EXPECTED: InsufficientQuotaError raised, agent not executed
        """
        # Set quota to 0
        user_ctx_no_quota = UserContext(
            user_id="user_test_123",
            email="test@test.com",
            tier=Tier.FREE,
            permissions=["agent:run"],
            quota_remaining=0,
        )

        with pytest.raises(InsufficientQuotaError):
            await agent_service.execute(user_ctx_no_quota, "Test message")

    @pytest.mark.asyncio
    async def test_execute_validates_message_limit(
        self, agent_service, user_ctx, mock_session_service
    ):
        """
        TEST: Validate message count limit per tier
        PURPOSE: Validate tier-based message limits enforced
        VALIDATES: execute() checks message count against tier limit
        EXPECTED: ValidationError raised when limit exceeded

        NOTE: Message limits increased in Phase A audit (2025-11-12):
        - FREE: 10 → 20 messages
        - PRO: 100 → 200 messages
        - ENTERPRISE: 1000 → 2000 messages
        """
        # Mock session with max messages for FREE tier (20, increased from 10)
        mock_session = MagicMock(
            session_id="sess_full_123",
            user_id="user_test_123",
            event_count=20,  # Updated from 10 to match new FREE tier limit
            is_active=True,
            status="active",
        )

        # FREE tier user
        user_ctx_free = UserContext(
            user_id="user_test_123",
            email="test@test.com",
            tier=Tier.FREE,
            permissions=["agent:run"],
            quota_remaining=100,
        )

        # Mock the container and session service
        with patch("src.core.container.get_container") as mock_get_container:
            mock_container = MagicMock()
            mock_container.firestore_client = MagicMock()
            mock_get_container.return_value = mock_container

            with patch("src.services.session_service.SessionService") as MockSessionService:
                mock_svc = AsyncMock()
                mock_svc.get = AsyncMock(return_value=mock_session)
                MockSessionService.return_value = mock_svc

                with pytest.raises(ValidationError, match="Session message limit reached"):
                    await agent_service.execute(
                        user_ctx_free, "Test message", session_id="sess_full_123"
                    )

    @pytest.mark.asyncio
    async def test_execute_tracks_quota_usage(self, agent_service, user_ctx):
        """
        TEST: Track quota usage during execution
        PURPOSE: Validate quota deduction calculation
        VALIDATES: execute() calculates quota_used, quota_remaining
        EXPECTED: Result contains accurate quota tracking
        """
        with patch("src.services.agent_service.demo_agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.data = "Agent response"
            mock_result.all_messages.return_value = []
            mock_result.new_message_count.return_value = 2
            # Create usage object with input/output tokens (PydanticAI format)
            mock_usage = MagicMock()
            mock_usage.input_tokens = 1000
            mock_usage.output_tokens = 500
            mock_result.usage = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)

            with patch(
                "src.services.agent_service.uuid.uuid4", return_value=MagicMock(hex="abc123")
            ):
                result = await agent_service.execute(user_ctx, "Test message")

            # Quota formula: 1 + tools_used + (tokens / 1000)
            # With 1500 tokens = 1 + 0 + 1.5 = 2.5 → 3
            assert result.quota_used >= 1
            assert result.quota_remaining == user_ctx.quota_remaining - result.quota_used

    @pytest.mark.asyncio
    async def test_execute_extracts_tool_usage(self, agent_service, user_ctx):
        """
        TEST: Extract tool names from execution
        PURPOSE: Validate tool usage tracking
        VALIDATES: execute() identifies tools used in messages
        EXPECTED: tools_used list in result
        """
        with patch("src.services.agent_service.demo_agent") as mock_agent:
            # Mock messages with tool calls - proper structure
            mock_part = MagicMock()
            mock_part.tool_name = "text_transform"

            mock_message = MagicMock()
            mock_message.parts = [mock_part]

            mock_result = MagicMock()
            mock_result.response = "Agent response"
            mock_result.new_messages = MagicMock(return_value=[mock_message])
            # Create usage object with input/output tokens
            mock_usage = MagicMock()
            mock_usage.input_tokens = 100
            mock_usage.output_tokens = 50
            mock_result.usage = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)

            with patch(
                "src.services.agent_service.uuid.uuid4", return_value=MagicMock(hex="abc123")
            ):
                result = await agent_service.execute(user_ctx, "Test message")

            assert "text_transform" in result.tools_used
            assert isinstance(result.tools_used, list)

    @pytest.mark.asyncio
    async def test_execute_returns_model_and_usage(self, agent_service, user_ctx):
        """
        TEST: Return model name and token usage
        PURPOSE: Validate execution metadata
        VALIDATES: execute() captures model_used and usage stats
        EXPECTED: Result contains model name and token counts
        """
        with patch("src.services.agent_service.demo_agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.response = "Model response text"
            mock_result.new_messages = MagicMock(return_value=[])
            # Create usage object with input/output tokens
            mock_usage = MagicMock()
            mock_usage.input_tokens = 200
            mock_usage.output_tokens = 100
            mock_result.usage = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)

            with patch(
                "src.services.agent_service.uuid.uuid4", return_value=MagicMock(hex="abc123")
            ):
                result = await agent_service.execute(user_ctx, "Test message")

            assert result.model_used is not None
            assert "input_tokens" in result.usage or "request_tokens" in result.usage
            assert result.usage["total_tokens"] == 300  # 200 + 100


class TestAgentDiscovery:
    """Test suite for agent discovery methods (user-global, session-local, merged).

    Tests the 3-layer agent discovery architecture:
    1. System agents (from AgentRegistry)
    2. User-global agents (from Firestore /users/{uid}/agents/)
    3. Session-local agents (from Firestore /users/{uid}/sessions/{sid}/agents/)

    Validates:
    - Correct Firestore path queries
    - Merged agentset with precedence (session > user > system)
    - Search filtering
    - Source annotation ("system" | "user_global" | "session_local")
    """

    @pytest.fixture
    def user_ctx(self):
        """Create UserContext for testing."""
        return UserContext(
            user_id="user_test_123",
            email="test@test.com",
            tier=Tier.PRO,
            permissions=["agent:run"],
            quota_remaining=100,
        )

    @pytest.fixture
    def mock_firestore(self):
        """Create mock Firestore client."""
        return MagicMock()

    @pytest.fixture
    def agent_service_with_firestore(self, mock_firestore):
        """Create AgentService with mocked Firestore."""
        return AgentService(firestore_client=mock_firestore)

    @pytest.mark.asyncio
    async def test_load_user_global_agents_returns_empty_without_firestore(self):
        """
        TEST: load_user_global_agents returns empty list without Firestore
        PURPOSE: Validate graceful handling when Firestore not configured
        VALIDATES: Returns [] when firestore_client is None
        EXPECTED: Empty list, no errors
        """
        service = AgentService(firestore_client=None)
        agents = await service.load_user_global_agents("user_123")
        assert agents == []

    @pytest.mark.asyncio
    async def test_load_user_global_agents_queries_correct_path(
        self, agent_service_with_firestore, mock_firestore
    ):
        """
        TEST: load_user_global_agents queries /users/{uid}/agents/
        PURPOSE: Validate correct Firestore path
        VALIDATES: Queries correct collection path
        EXPECTED: Firestore collection("users").document(user_id).collection("agents") called
        """
        # Mock Firestore response
        mock_doc1 = MagicMock()
        mock_doc1.id = "agent_abc123"
        mock_doc1.to_dict.return_value = {
            "name": "Legal Analyst",
            "description": "Analyzes legal docs",
            "system_prompt": "You are a legal analyst",
            "model": "openai:gpt-4",
            "enabled": True,
            "tags": ["legal"],
            "type": "yaml",
        }

        mock_doc2 = MagicMock()
        mock_doc2.id = "agent_xyz789"
        mock_doc2.to_dict.return_value = {
            "name": "Data Scientist",
            "description": "Data analysis expert",
            "system_prompt": "You are a data scientist",
            "model": "openai:gpt-4",
            "enabled": True,
            "tags": ["data"],
            "type": "yaml",
        }

        mock_collection = MagicMock()
        mock_collection.stream.return_value = [mock_doc1, mock_doc2]

        mock_firestore.collection.return_value.document.return_value.collection.return_value = (
            mock_collection
        )

        agents = await agent_service_with_firestore.load_user_global_agents("user_123")

        assert len(agents) == 2
        assert agents[0].agent_id == "agent_abc123"
        assert agents[0].name == "Legal Analyst"
        assert agents[1].agent_id == "agent_xyz789"
        assert agents[1].name == "Data Scientist"

        # Verify correct path called
        mock_firestore.collection.assert_called_with("users")

    @pytest.mark.asyncio
    async def test_load_session_local_agents_returns_empty_without_firestore(self):
        """
        TEST: load_session_local_agents returns empty list without Firestore
        PURPOSE: Validate graceful handling when Firestore not configured
        VALIDATES: Returns [] when firestore_client is None
        EXPECTED: Empty list, no errors
        """
        service = AgentService(firestore_client=None)
        agents = await service.load_session_local_agents("user_123", "sess_456")
        assert agents == []

    @pytest.mark.asyncio
    async def test_load_session_local_agents_queries_correct_path(
        self, agent_service_with_firestore, mock_firestore
    ):
        """
        TEST: load_session_local_agents queries /users/{uid}/sessions/{sid}/agents/
        PURPOSE: Validate correct Firestore path for session-local agents
        VALIDATES: Queries correct nested collection path
        EXPECTED: Returns session-specific agents
        """
        # Mock Firestore response
        mock_doc = MagicMock()
        mock_doc.id = "agent_session123"
        mock_doc.to_dict.return_value = {
            "name": "Session Agent",
            "description": "Session-specific agent",
            "system_prompt": "You are a session agent",
            "model": "openai:gpt-4o-mini",
            "enabled": True,
            "tags": ["session"],
            "type": "yaml",
        }

        mock_collection = MagicMock()
        mock_collection.stream.return_value = [mock_doc]

        (
            mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value
        ) = mock_collection

        agents = await agent_service_with_firestore.load_session_local_agents(
            "user_123", "sess_456"
        )

        assert len(agents) == 1
        assert agents[0].agent_id == "agent_session123"
        assert agents[0].name == "Session Agent"

    @pytest.mark.asyncio
    async def test_build_merged_agentset_includes_system_agents(
        self, agent_service_with_firestore, user_ctx
    ):
        """
        TEST: build_merged_agentset includes system agents
        PURPOSE: Validate system agents from registry are included
        VALIDATES: AgentRegistry.list_available() called and results included
        EXPECTED: System agents present in merged result with source='system'
        """
        from src.core.agent_registry import get_agent_registry, reset_agent_registry
        from pydantic_ai import Agent

        # Reset and populate registry
        reset_agent_registry()
        registry = get_agent_registry()

        test_agent = Agent("test")
        registry.register(
            agent_id="demo_agent",
            name="Demo Agent",
            description="Demo agent for testing",
            agent_instance=test_agent,
            required_tier="FREE",
            enabled=True,
        )

        # Mock Firestore to return no custom agents
        mock_firestore = agent_service_with_firestore.firestore
        mock_firestore.collection.return_value.document.return_value.collection.return_value.stream.return_value = []

        merged = await agent_service_with_firestore.build_merged_agentset(user_ctx)

        assert merged["count"] >= 1
        assert "demo_agent" in merged["agents"]
        assert merged["agents"]["demo_agent"]["source"] == "system"
        assert merged["agents"]["demo_agent"]["name"] == "Demo Agent"

    @pytest.mark.asyncio
    async def test_build_merged_agentset_user_global_overrides_system(
        self, agent_service_with_firestore, user_ctx
    ):
        """
        TEST: build_merged_agentset - user-global agents override system
        PURPOSE: Validate precedence: user-global > system
        VALIDATES: When agent_id exists in both, user-global version wins
        EXPECTED: Merged result has user-global agent, source='user_global'
        """
        from src.core.agent_registry import get_agent_registry, reset_agent_registry
        from pydantic_ai import Agent

        # Setup system agent
        reset_agent_registry()
        registry = get_agent_registry()
        test_agent = Agent("test")
        registry.register(
            agent_id="shared_agent",
            name="System Version",
            description="System agent",
            agent_instance=test_agent,
            required_tier="FREE",
            enabled=True,
        )

        # Mock user-global agent with same ID
        mock_doc = MagicMock()
        mock_doc.id = "shared_agent"
        mock_doc.to_dict.return_value = {
            "name": "User Custom Version",
            "description": "User's custom agent",
            "system_prompt": "Custom prompt",
            "model": "openai:gpt-4",
            "enabled": True,
            "tags": ["custom"],
            "type": "yaml",
        }

        mock_firestore = agent_service_with_firestore.firestore
        mock_firestore.collection.return_value.document.return_value.collection.return_value.stream.return_value = [
            mock_doc
        ]

        merged = await agent_service_with_firestore.build_merged_agentset(user_ctx)

        assert "shared_agent" in merged["agents"]
        assert merged["agents"]["shared_agent"]["source"] == "user_global"
        assert merged["agents"]["shared_agent"]["name"] == "User Custom Version"

    @pytest.mark.asyncio
    async def test_build_merged_agentset_session_local_overrides_all(
        self, agent_service_with_firestore, user_ctx
    ):
        """
        TEST: build_merged_agentset - session-local overrides all
        PURPOSE: Validate precedence: session-local > user-global > system
        VALIDATES: When agent_id exists in all three, session-local wins
        EXPECTED: Merged result has session-local agent, source='session_local'
        """
        from src.core.agent_registry import get_agent_registry, reset_agent_registry
        from pydantic_ai import Agent

        # Setup system agent
        reset_agent_registry()
        registry = get_agent_registry()
        test_agent = Agent("test")
        registry.register(
            agent_id="shared_agent",
            name="System Version",
            description="System agent",
            agent_instance=test_agent,
            required_tier="FREE",
            enabled=True,
        )

        # Mock user-global agent
        mock_user_doc = MagicMock()
        mock_user_doc.id = "shared_agent"
        mock_user_doc.to_dict.return_value = {
            "name": "User Version",
            "description": "User agent",
            "system_prompt": "User prompt",
            "model": "openai:gpt-4",
            "enabled": True,
            "tags": ["user"],
            "type": "yaml",
        }

        # Mock session-local agent
        mock_session_doc = MagicMock()
        mock_session_doc.id = "shared_agent"
        mock_session_doc.to_dict.return_value = {
            "name": "Session Version",
            "description": "Session agent",
            "system_prompt": "Session prompt",
            "model": "openai:gpt-4o-mini",
            "enabled": True,
            "tags": ["session"],
            "type": "yaml",
        }

        mock_firestore = agent_service_with_firestore.firestore

        # Setup mock chain for user-global agents
        user_agents_collection = MagicMock()
        user_agents_collection.stream.return_value = [mock_user_doc]

        # Setup mock chain for session-local agents
        session_agents_collection = MagicMock()
        session_agents_collection.stream.return_value = [mock_session_doc]

        # Mock the Firestore path hierarchy
        def collection_side_effect(name):
            if name == "users":
                users_mock = MagicMock()

                def document_side_effect(doc_id):
                    doc_mock = MagicMock()

                    def sub_collection_side_effect(col_name):
                        if col_name == "agents":
                            return user_agents_collection
                        elif col_name == "sessions":
                            sessions_mock = MagicMock()

                            def sessions_document_side_effect(sess_id):
                                sess_doc_mock = MagicMock()

                                def sess_sub_collection_side_effect(sess_col_name):
                                    if sess_col_name == "agents":
                                        return session_agents_collection
                                    return MagicMock()

                                sess_doc_mock.collection.side_effect = (
                                    sess_sub_collection_side_effect
                                )
                                return sess_doc_mock

                            sessions_mock.document.side_effect = sessions_document_side_effect
                            return sessions_mock
                        return MagicMock()

                    doc_mock.collection.side_effect = sub_collection_side_effect
                    return doc_mock

                users_mock.document.side_effect = document_side_effect
                return users_mock
            return MagicMock()

        mock_firestore.collection.side_effect = collection_side_effect

        merged = await agent_service_with_firestore.build_merged_agentset(
            user_ctx, session_id="sess_456"
        )

        assert "shared_agent" in merged["agents"]
        assert merged["agents"]["shared_agent"]["source"] == "session_local"
        assert merged["agents"]["shared_agent"]["name"] == "Session Version"

    @pytest.mark.asyncio
    async def test_build_merged_agentset_applies_search_filter(
        self, agent_service_with_firestore, user_ctx
    ):
        """
        TEST: build_merged_agentset applies search filter
        PURPOSE: Validate search filtering by name/description/tags
        VALIDATES: Only matching agents returned when search provided
        EXPECTED: Filtered results match search term
        """
        from src.core.agent_registry import get_agent_registry, reset_agent_registry
        from pydantic_ai import Agent

        # Setup multiple system agents
        reset_agent_registry()
        registry = get_agent_registry()
        test_agent = Agent("test")

        registry.register(
            agent_id="legal_agent",
            name="Legal Analyst",
            description="Analyzes legal documents",
            agent_instance=test_agent,
            required_tier="FREE",
            enabled=True,
            tags=["legal", "analysis"],
        )

        registry.register(
            agent_id="data_agent",
            name="Data Scientist",
            description="Analyzes data patterns",
            agent_instance=test_agent,
            required_tier="FREE",
            enabled=True,
            tags=["data", "science"],
        )

        # Mock no custom agents
        mock_firestore = agent_service_with_firestore.firestore
        mock_firestore.collection.return_value.document.return_value.collection.return_value.stream.return_value = []

        # Search for "legal"
        merged = await agent_service_with_firestore.build_merged_agentset(user_ctx, search="legal")

        assert merged["count"] == 1
        assert "legal_agent" in merged["agents"]
        assert "data_agent" not in merged["agents"]
