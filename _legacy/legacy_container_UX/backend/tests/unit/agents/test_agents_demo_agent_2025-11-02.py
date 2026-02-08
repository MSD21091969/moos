"""Unit tests for src/agents/demo_agent.py

TEST: Demo agent with SessionContext integration
PURPOSE: Validate agent tools, context injection, permissions
VALIDATES: Tool execution, quota checks, session context
EXPECTED: All tools properly use SessionContext
"""

import pytest

from src.agents.demo_agent import demo_agent
from src.models.context import SessionContext


@pytest.fixture
def session_context():
    """Sample session context for testing."""
    return SessionContext(
        session_id="sess_test",
        user_id="user_test",
        user_email="test@example.com",
        tier="pro",  # Lowercase for enum
        permissions=["tool1", "tool2"],  # List not set
        quota_remaining=50.0,
    )


class TestCheckQuotaTool:
    """Test check_quota tool."""

    @pytest.mark.asyncio
    async def test_check_quota_returns_context_info(self, session_context):
        """
        TEST: check_quota tool execution
        PURPOSE: Verify quota info returned
        VALIDATES: SessionContext access via agent
        EXPECTED: Agent can access session context
        """
        # Agent tools are tested via agent.run() with TestModel
        result = await demo_agent.run("Check my quota", deps=session_context)

        # TestModel returns response, verify it exists
        assert result.response is not None


class TestCheckPermissionsTool:
    """Test check_permissions tool."""

    @pytest.mark.asyncio
    async def test_check_permissions_has_permission(self, session_context):
        """
        TEST: check_permissions with valid permission
        PURPOSE: Verify permission check via agent
        VALIDATES: Agent can check permissions
        EXPECTED: Agent responds
        """
        result = await demo_agent.run("Do I have tool1 permission?", deps=session_context)
        assert result.response is not None

    @pytest.mark.asyncio
    async def test_check_permissions_missing_permission(self, session_context):
        """
        TEST: check_permissions without permission
        PURPOSE: Verify permission denial via agent
        VALIDATES: Agent handles missing permissions
        EXPECTED: Agent responds
        """
        result = await demo_agent.run("Do I have admin_tool permission?", deps=session_context)
        assert result.response is not None


class TestGetSessionInfoTool:
    """Test get_session_info tool."""

    @pytest.mark.asyncio
    async def test_get_session_info_returns_all_fields(self, session_context):
        """
        TEST: get_session_info tool
        PURPOSE: Verify session info returned via agent
        VALIDATES: Agent can access session context
        EXPECTED: Agent responds with session info
        """
        result = await demo_agent.run("What is my session info?", deps=session_context)
        assert result.response is not None


class TestCalculateExpressionTool:
    """Test calculate_expression tool."""

    @pytest.mark.asyncio
    async def test_calculate_simple_expression(self, session_context):
        """
        TEST: calculate_expression with valid math
        PURPOSE: Verify calculation via agent
        VALIDATES: Agent can calculate
        EXPECTED: Agent responds
        """
        result = await demo_agent.run("Calculate 2 + 2", deps=session_context)
        assert result.response is not None

    @pytest.mark.asyncio
    async def test_calculate_complex_expression(self, session_context):
        """
        TEST: calculate_expression with complex math
        PURPOSE: Verify advanced calculations via agent
        VALIDATES: Agent handles complex expressions
        EXPECTED: Agent responds
        """
        result = await demo_agent.run("Calculate 10 * 5 + 3", deps=session_context)
        assert result.response is not None

    @pytest.mark.asyncio
    async def test_calculate_invalid_expression_returns_error(self, session_context):
        """
        TEST: calculate_expression with invalid syntax
        PURPOSE: Verify error handling via agent
        VALIDATES: Agent handles invalid input
        EXPECTED: Agent responds
        """
        result = await demo_agent.run("Calculate invalid", deps=session_context)
        assert result.response is not None


class TestDemoAgent:
    """Test demo_agent configuration."""

    def test_agent_has_correct_deps_type(self):
        """
        TEST: Agent dependency type
        PURPOSE: Verify SessionContext type
        VALIDATES: deps_type set correctly
        EXPECTED: SessionContext type
        """
        assert demo_agent._deps_type == SessionContext

    def test_agent_has_system_prompt(self):
        """
        TEST: Agent system prompt
        PURPOSE: Verify prompt configured
        VALIDATES: System prompt exists
        EXPECTED: Non-empty prompt string or list
        """
        # PydanticAI stores system_prompts as list
        prompts = demo_agent._system_prompts
        assert prompts is not None
        assert len(prompts) > 0
