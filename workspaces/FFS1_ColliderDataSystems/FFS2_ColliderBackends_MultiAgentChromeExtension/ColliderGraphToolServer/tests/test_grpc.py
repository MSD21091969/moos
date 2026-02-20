"""Tests for the GraphToolServer gRPC service."""

import pytest
import datetime
import json
from unittest.mock import MagicMock, AsyncMock

from src.handlers.grpc_servicer import ColliderGraphServicer
from src.schemas.registry import GraphStepEntry, SubgraphManifest

# --- Dummy Tool ---
def dummy_tool(**kwargs):
    return {"echo": kwargs}

# --- Fixtures ---

class MockContext:
    """Mock gRPC ServicerContext."""
    pass

@pytest.fixture
def registry():
    reg = MagicMock()
    # Mock get_workflow behavior
    reg.get_workflow.return_value = None 
    return reg

@pytest.fixture
def servicer(registry):
    return ColliderGraphServicer(registry)

@pytest.fixture
def mock_context():
    return MockContext()

# --- Tests ---

@pytest.mark.asyncio
async def test_register_tool(servicer, registry, mock_context):
    request = MagicMock()
    request.tool_name = "test_tool"
    request.origin_node_id = "node1"
    request.owner_user_id = "user1"
    request.params_schema_json = b"{}"
    request.code_ref = "module.func"
    request.visibility = "local"

    # Mock success
    mock_model = MagicMock()
    mock_model.model_json_schema.return_value = {"type": "object"}
    registry.register_tool = AsyncMock(return_value=mock_model)
    
    response = await servicer.RegisterTool(request, mock_context)
    
    assert response.success
    assert response.tool_name == "test_tool"
    registry.register_tool.assert_called_once()

@pytest.mark.asyncio
async def test_discover_tools(servicer, registry, mock_context):
    request = MagicMock()
    request.query = "test"
    request.user_id = "user1"
    request.visibility_filter = []
    request.limit = 10

    # Mock discovery
    tool_entry = GraphStepEntry(
        tool_name="test_tool",
        origin_node_id="node1",
        owner_user_id="user1",
        params_schema={"type": "object"},
        code_ref="module.func",
        visibility="local",
        registered_at=datetime.datetime.now(datetime.timezone.utc)
    )
    registry.discover_tools = AsyncMock(return_value=[tool_entry])

    response = await servicer.DiscoverTools(request, mock_context)

    assert len(response.tools) == 1
    assert response.tools[0].tool_name == "test_tool"

@pytest.mark.asyncio
async def test_execute_subgraph_success(servicer, registry, mock_context):
    """Test successful subgraph execution."""
    request = MagicMock()
    request.workflow_name = "test_workflow"
    request.user_id = "user1"
    request.inputs_json = b'{"input": "val"}'

    # Mock workflow existence
    manifest = SubgraphManifest(
        workflow_name="test_workflow",
        origin_node_id="n1",
        owner_user_id="u1",
        steps=["step1"],
        entry_point="step1"
    )
    registry.get_workflow.return_value = manifest
    
    # Mock tool registry lookup
    tool_entry = GraphStepEntry(
        tool_name="step1",
        origin_node_id="n1",
        owner_user_id="u1",
        params_schema={},
        visibility="local",
        code_ref="tests.test_grpc:dummy_tool" 
    )
    registry.get_tool.side_effect = lambda name: tool_entry if name == "step1" else None

    # Run
    response = await servicer.ExecuteSubgraph(request, mock_context)

    assert response.success
    assert response.workflow_name == "test_workflow"
    # dummy_tool returns {"echo": kwargs}
    # input was {"input": "val"}
    # so result should be {"echo": {"input": "val"}}
    # merged into context? 
    # WorkflowExecutor logic: 
    # if result is dict, context.update(result)
    # so context becomes {"input": "val", "echo": {"input": "val"}}
    
    result = json.loads(response.result_json)
    assert result["echo"] == {"input": "val"}

@pytest.mark.asyncio
async def test_execute_subgraph_not_found(servicer, registry, mock_context):
    """Test execution of non-existent workflow."""
    request = MagicMock()
    request.workflow_name = "missing"
    request.user_id = "user1"
    request.inputs_json = b"{}"

    registry.get_workflow.return_value = None

    response = await servicer.ExecuteSubgraph(request, mock_context)

    assert not response.success
    assert "not found" in response.error_message
