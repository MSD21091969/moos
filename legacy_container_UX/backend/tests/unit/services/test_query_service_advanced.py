import pytest
from unittest.mock import AsyncMock, MagicMock, call
from src.services.query_service import QueryService
from src.models.queries import (
    ResourceFilter, 
    QueryScope, 
    BatchOperationRequest, 
    BatchOperationType,
    ResourceIdentifier
)
from src.models.links import ResourceLink, ResourceType

@pytest.fixture
def mock_container_service():
    service = AsyncMock()
    # Mock _get_container_type
    service._get_container_type = MagicMock(side_effect=lambda x: "agent" if "agent" in x else "tool")
    
    # Mock list_resources
    async def list_resources_side_effect(container_id, user_id):
        if container_id == "agent_1":
            return [
                ResourceLink(
                    link_id="link_2",
                    resource_id="tool_def_1",
                    resource_type=ResourceType.TOOL,
                    instance_id="tool_1",
                    added_at="2025-01-01T00:00:00Z",
                    added_by="user_1"
                )
            ]
        return []
    service.list_resources.side_effect = list_resources_side_effect
    
    return service

@pytest.fixture
def mock_session_service():
    service = AsyncMock()
    # Mock get_resources for session
    async def get_resources_side_effect(session_id, user_id):
        if session_id == "sess_1":
            return [
                ResourceLink(
                    link_id="link_1",
                    resource_id="agent_def_1",
                    resource_type=ResourceType.AGENT,
                    instance_id="agent_1",
                    added_at="2025-01-01T00:00:00Z",
                    added_by="user_1"
                ),
                ResourceLink(
                    link_id="link_3",
                    resource_id="tool_def_2",
                    resource_type=ResourceType.TOOL,
                    instance_id="tool_2",
                    added_at="2025-01-01T00:00:00Z",
                    added_by="user_1"
                )
            ]
        return []
    service.get_resources.side_effect = get_resources_side_effect
    return service

@pytest.fixture
def query_service(mock_container_service, mock_session_service):
    return QueryService(mock_container_service, mock_session_service)

@pytest.mark.asyncio
async def test_find_resources_subtree(query_service):
    result = await query_service.find_resources(
        user_id="user_1",
        scope_id="sess_1",
        query=ResourceFilter(),
        scope_type=QueryScope.SUBTREE
    )
    
    # Should find 3 resources: Agent 1, Tool 1 (child of Agent 1), Tool 2
    assert result.total == 3
    
    # Verify parent_ids
    ids = {r["link_id"]: r["parent_id"] for r in result.results}
    assert ids["link_1"] == "sess_1"
    assert ids["link_3"] == "sess_1"
    assert ids["link_2"] == "agent_1"

@pytest.mark.asyncio
async def test_batch_delete(query_service, mock_session_service, mock_container_service):
    request = BatchOperationRequest(
        operation=BatchOperationType.DELETE,
        items=[
            ResourceIdentifier(parent_id="sess_1", parent_type="session", link_id="link_1"),
            ResourceIdentifier(parent_id="agent_1", parent_type="agent", link_id="link_2")
        ]
    )
    
    result = await query_service.execute_batch_operation("user_1", request)
    
    assert result.success_count == 2
    assert result.failure_count == 0
    
    mock_session_service.remove_resource_link.assert_called_once_with("sess_1", "user_1", "link_1")
    mock_container_service.remove_resource.assert_called_once_with("agent_1", "link_2", "user_1")
