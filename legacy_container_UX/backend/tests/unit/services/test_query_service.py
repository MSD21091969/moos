import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.query_service import QueryService
from src.models.queries import GraphTraversalQuery, ResourceFilter, QueryScope
from src.models.links import ResourceLink, ResourceType

@pytest.fixture
def mock_container_service():
    service = AsyncMock()
    # _get_container_type is synchronous in the real class
    service._get_container_type = MagicMock(return_value="agent")
    service.get_instance.return_value = {"title": "Test Agent", "depth": 1}
    service.list_resources.return_value = []
    return service

@pytest.fixture
def mock_session_service():
    service = AsyncMock()
    service.get.return_value = MagicMock(metadata=MagicMock(title="Test Session"), depth=0)
    service.get_resources.return_value = [
        ResourceLink(
            link_id="link_1",
            resource_id="agent_def_1",
            resource_type=ResourceType.AGENT,
            instance_id="agent_1",
            added_at="2025-01-01T00:00:00Z",
            added_by="user_1"
        )
    ]
    return service

@pytest.fixture
def query_service(mock_container_service, mock_session_service):
    return QueryService(mock_container_service, mock_session_service)

@pytest.mark.asyncio
async def test_find_resources_session_scope(query_service, mock_session_service):
    result = await query_service.find_resources(
        user_id="user_1",
        scope_id="sess_1",
        query=ResourceFilter(resource_types=["agent"]),
        scope_type=QueryScope.SESSION
    )
    
    assert result.total == 1
    assert result.results[0]["resource_type"] == "agent"
    mock_session_service.get_resources.assert_called_once_with("sess_1", "user_1")

@pytest.mark.asyncio
async def test_traverse_chain_tier_limit(query_service):
    # Test that FREE tier caps depth at 1
    query = GraphTraversalQuery(
        start_node_id="agent_1",
        max_depth=5,
        direction="down"
    )
    
    # We expect the service to cap max_depth internally, 
    # but since we mocked the traversal logic (it's empty in the implementation currently),
    # we just verify the method runs without error and respects the tier arg.
    
    # Actually, let's verify the logic by checking if it modifies the query object
    # But pydantic models are mutable.
    
    await query_service.traverse_chain(
        user_id="user_1",
        query=query,
        user_tier="FREE"
    )
    
    assert query.max_depth == 1

@pytest.mark.asyncio
async def test_traverse_chain_pro_tier(query_service):
    # Test that PRO tier allows depth 3
    query = GraphTraversalQuery(
        start_node_id="agent_1",
        max_depth=5,
        direction="down"
    )
    
    await query_service.traverse_chain(
        user_id="user_1",
        query=query,
        user_tier="PRO"
    )
    
    assert query.max_depth == 3
