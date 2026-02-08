"""Unit tests for src/api/routes/tools.py - FIXED VERSION

TEST: Tool management endpoints with proper dependency overrides
PURPOSE: Validate tool listing and discovery
VALIDATES: Tier-based filtering, tool details
PATTERN: Use app.dependency_overrides instead of direct patching
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app as main_app
from src.api.dependencies import get_user_context, get_app_container
from src.api.routes.tools import get_tool_service
from src.models.context import UserContext
from src.models.permissions import Tier
from src.services.tool_service import ToolService, ToolInfo
from src.core.exceptions import ToolNotFoundError, PermissionDeniedError


# Fixtures


@pytest.fixture
def test_user_context():
    """UserContext for testing."""
    return UserContext(
        user_id="user_test",
        email="test@example.com",
        permissions=("read_data", "write_data", "execute_tools"),
        quota_remaining=1000,
        tier=Tier.PRO,
    )


@pytest.fixture
def mock_tool_service():
    """Mock ToolService for dependency override."""
    service = AsyncMock(spec=ToolService)
    return service


@pytest.fixture
def sample_tools():
    """Sample tool infos."""
    return [
        ToolInfo(
            name="search_text",
            description="Search text with regex",
            parameters={"text": "str", "pattern": "str"},
            required_tier=Tier.FREE,
            quota_cost=1,
            category="text",
            enabled=True,
            tags=["search", "regex"],
        ),
        ToolInfo(
            name="export_json",
            description="Export data as JSON",
            parameters={"data": "dict", "path": "str"},
            required_tier=Tier.PRO,
            quota_cost=2,
            category="export",
            enabled=True,
            tags=["export", "json"],
        ),
    ]


@pytest.fixture
def client(test_user_context, mock_tool_service):
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_user_context():
        return test_user_context

    def override_tool_service():
        return mock_tool_service

    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_user_context] = override_user_context
    test_app.dependency_overrides[get_tool_service] = override_tool_service
    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestListTools:
    """Test GET /tools/available endpoint."""

    def test_list_tools_success(self, client, mock_tool_service, sample_tools):
        """
        TEST: List available tools
        PURPOSE: Verify tool discovery
        VALIDATES: Tier filtering, response structure
        EXPECTED: 200 with tools array
        """
        mock_tool_service.list_available_tools.return_value = sample_tools

        response = client.get("/tools/available")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["count"] == 2
        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "search_text"

    def test_list_tools_filtered_by_category(self, client, mock_tool_service, sample_tools):
        """
        TEST: Filter tools by category
        PURPOSE: Verify category filtering
        VALIDATES: Query parameter handling
        EXPECTED: Service called with category filter
        """
        mock_tool_service.list_available_tools.return_value = [sample_tools[0]]

        response = client.get("/tools/available?category=text")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

        # Verify service called with filter
        mock_tool_service.list_available_tools.assert_called_once()
        call_kwargs = mock_tool_service.list_available_tools.call_args.kwargs
        assert call_kwargs["category"] == "text"

    def test_list_tools_search(self, client, mock_tool_service, sample_tools):
        """
        TEST: Search tools by keyword
        PURPOSE: Verify search functionality
        VALIDATES: Search parameter handling
        EXPECTED: Filtered results
        """
        mock_tool_service.list_available_tools.return_value = [sample_tools[1]]

        response = client.get("/tools/available?search=export")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tools"][0]["name"] == "export_json"


class TestGetToolDetails:
    """Test GET /tools/{tool_name} endpoint."""

    def test_get_tool_details_success(self, client, mock_tool_service, sample_tools):
        """
        TEST: Get tool details
        PURPOSE: Verify tool detail retrieval
        VALIDATES: Service integration
        EXPECTED: 200 with tool info
        """
        mock_tool_service.get_tool_details.return_value = sample_tools[0]

        response = client.get("/tools/search_text")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "search_text"
        assert data["description"] == "Search text with regex"
        assert data["required_tier"] == "free"

    def test_get_tool_not_found(self, client, mock_tool_service):
        """
        TEST: Get non-existent tool
        PURPOSE: Verify error handling
        VALIDATES: ToolNotFoundError → 404
        EXPECTED: 404 not found
        """
        mock_tool_service.get_tool_details.side_effect = ToolNotFoundError("Tool not found")

        response = client.get("/tools/nonexistent_tool")

        assert response.status_code == 404

    def test_get_tool_permission_denied(self, client, mock_tool_service):
        """
        TEST: Get tool requiring higher tier
        PURPOSE: Verify tier enforcement
        VALIDATES: PermissionDeniedError → 403
        EXPECTED: 403 forbidden
        """
        mock_tool_service.get_tool_details.side_effect = PermissionDeniedError(
            "Tool requires ENTERPRISE tier"
        )

        response = client.get("/tools/premium_tool")

        assert response.status_code == 403
