"""Full integration tests for resource discovery endpoints.

Tests all 4 resource API endpoints with real/mock Firestore:
1. GET /resources/tools - List available tools
2. GET /resources/tools/{tool_name} - Get tool details
3. GET /resources/agents - List available agents
4. GET /resources/agents/{agent_id} - Get agent details
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_list_available_tools(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/tools - List available tools."""
    response = enterprise_client.get(
        "/resources/tools",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to list tools: {response.text}"
    tools = response.json()

    # Validate response is a list
    assert isinstance(tools, list)

    # If tools exist, validate structure
    if len(tools) > 0:
        tool = tools[0]
        assert "name" in tool
        assert "description" in tool
        assert "category" in tool
        assert "required_tier" in tool
        assert "quota_cost" in tool
        assert "enabled" in tool


@pytest.mark.integration
def test_list_tools_by_category(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/tools?category=X - Filter tools by category."""
    # Test valid category
    response = enterprise_client.get(
        "/resources/tools?category=export",
        headers=enterprise_headers,
    )
    assert (
        response.status_code == 200
    ), f"Failed to list tools for valid category export: {response.text}"
    tools = response.json()
    assert isinstance(tools, list)

    # Test invalid categories - should return 400
    for category in ["text_analysis", "invalid_category_xyz"]:
        response = enterprise_client.get(
            f"/resources/tools?category={category}",
            headers=enterprise_headers,
        )
        assert (
            response.status_code == 400
        ), f"Should return 400 for invalid category {category}: {response.text}"


@pytest.mark.integration
def test_get_tool_details(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/tools/{tool_name} - Get tool details."""
    # First get list of tools
    list_response = enterprise_client.get(
        "/resources/tools",
        headers=enterprise_headers,
    )
    assert list_response.status_code == 200
    tools = list_response.json()

    if len(tools) == 0:
        pytest.skip("No tools available to test")

    # Get details for first tool
    tool_name = tools[0]["name"]
    response = enterprise_client.get(
        f"/resources/tools/{tool_name}",
        headers=enterprise_headers,
    )

    assert (
        response.status_code == 200
    ), f"Failed to get tool details for {tool_name}: {response.text}"
    tool_details = response.json()

    # Validate structure
    assert tool_details["name"] == tool_name
    assert "description" in tool_details
    assert "category" in tool_details
    assert "required_tier" in tool_details
    assert "quota_cost" in tool_details
    assert "can_execute" in tool_details


@pytest.mark.integration
def test_get_nonexistent_tool(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/tools/{tool_name} - 404 for non-existent tool."""
    response = enterprise_client.get(
        "/resources/tools/nonexistent_tool_xyz",
        headers=enterprise_headers,
    )

    assert response.status_code == 404, "Should return 404 for non-existent tool"


@pytest.mark.integration
def test_list_available_agents(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/agents - List available agents."""
    response = enterprise_client.get(
        "/resources/agents",
        headers=enterprise_headers,
    )

    assert response.status_code == 200, f"Failed to list agents: {response.text}"
    agents = response.json()

    # Validate response is a list
    assert isinstance(agents, list)

    # If agents exist, validate structure
    if len(agents) > 0:
        agent = agents[0]
        assert "agent_id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "required_tier" in agent
        assert "enabled" in agent


@pytest.mark.integration
def test_get_agent_details(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/agents/{agent_id} - Get agent details."""
    # First get list of agents
    list_response = enterprise_client.get(
        "/resources/agents",
        headers=enterprise_headers,
    )
    assert list_response.status_code == 200
    agents = list_response.json()

    if len(agents) == 0:
        pytest.skip("No agents available to test")

    # Get details for first agent
    agent_id = agents[0]["agent_id"]
    response = enterprise_client.get(
        f"/resources/agents/{agent_id}",
        headers=enterprise_headers,
    )

    assert (
        response.status_code == 200
    ), f"Failed to get agent details for {agent_id}: {response.text}"
    agent_details = response.json()

    # Validate structure
    assert agent_details["agent_id"] == agent_id
    assert "name" in agent_details
    assert "description" in agent_details
    assert "required_tier" in agent_details
    assert "can_execute" in agent_details


@pytest.mark.integration
def test_get_nonexistent_agent(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/agents/{agent_id} - 404 for non-existent agent."""
    response = enterprise_client.get(
        "/resources/agents/nonexistent_agent_xyz",
        headers=enterprise_headers,
    )

    assert response.status_code == 404, "Should return 404 for non-existent agent"


@pytest.mark.integration
def test_invalid_tool_category(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test GET /resources/tools?category=invalid - Error for invalid category."""
    response = enterprise_client.get(
        "/resources/tools?category=invalid_category_xyz",
        headers=enterprise_headers,
    )

    # Should return 400 for invalid category
    assert response.status_code == 400, "Should return 400 for invalid category"
