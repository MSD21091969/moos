"""Tests for the DataServer Execution API."""

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_execute_workflow_success(client, admin_headers):
    """Test successful workflow execution."""
    
    # Mock the GraphToolClient
    with patch("src.api.execution.GraphToolClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.execute_subgraph = AsyncMock(return_value={
            "success": True,
            "workflow_name": "test_workflow",
            "result": {"run": "success"}
        })
        mock_instance.close = AsyncMock()

        response = await client.post(
            "/execution/workflow/test_workflow",
            json={"input": "val"},
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json() == {"run": "success"}
        
        mock_instance.execute_subgraph.assert_called_once()
        args = mock_instance.execute_subgraph.call_args[1]
        assert args["workflow_name"] == "test_workflow"
        assert args["inputs"] == {"input": "val"}

@pytest.mark.asyncio
async def test_execute_workflow_failure(client, admin_headers):
    """Test failed workflow execution."""
    
    with patch("src.api.execution.GraphToolClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.execute_subgraph = AsyncMock(return_value={
            "success": False,
            "error_message": "Something went wrong"
        })
        mock_instance.close = AsyncMock()

        response = await client.post(
            "/execution/workflow/test_fail",
            json={},
            headers=admin_headers
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Something went wrong"
