"""Tests for the DataServer Execution API.

The /execution/tool/{name} endpoint forwards to GraphToolServer via REST (httpx).
The /execution/workflow/{name} endpoint is currently stub-only (GraphToolClient removed).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_execute_tool_success(client, admin_headers):
    """Tool execution forwards to GraphToolServer and returns result."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "result": {"apps": ["app1", "app2"]},
    }

    with patch("httpx.AsyncClient") as MockHttpx:
        mock_http = MockHttpx.return_value.__aenter__.return_value
        mock_http.post = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/execution/tool/list_apps",
            json={},
            headers=admin_headers,
        )

    assert response.status_code == 200
    assert response.json() == {"apps": ["app1", "app2"]}


@pytest.mark.asyncio
async def test_execute_tool_failure_from_graphtool(client, admin_headers):
    """When GraphToolServer returns success=False, DataServer returns 400."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": False,
        "error_message": "Tool raised an exception",
    }

    with patch("httpx.AsyncClient") as MockHttpx:
        mock_http = MockHttpx.return_value.__aenter__.return_value
        mock_http.post = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/execution/tool/bad_tool",
            json={},
            headers=admin_headers,
        )

    assert response.status_code == 400
    assert "bad_tool" in response.json()["detail"]
    assert "Tool raised an exception" in response.json()["detail"]


@pytest.mark.asyncio
async def test_execute_tool_graphtool_unreachable(client, admin_headers):
    """When GraphToolServer is down, DataServer returns 502."""
    with patch("httpx.AsyncClient") as MockHttpx:
        mock_http = MockHttpx.return_value.__aenter__.return_value
        mock_http.post = AsyncMock(side_effect=Exception("Connection refused"))

        response = await client.post(
            "/execution/tool/list_apps",
            json={},
            headers=admin_headers,
        )

    assert response.status_code == 502
    assert "unreachable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_execute_tool_requires_auth(client):
    """Tool execution endpoint requires authentication."""
    response = await client.post(
        "/execution/tool/list_apps",
        json={},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_execute_tool_with_inputs(client, admin_headers):
    """Inputs dict is forwarded to GraphToolServer correctly."""
    captured = {}

    async def capture_post(url, *, json, timeout):
        captured["url"] = url
        captured["json"] = json
        m = MagicMock()
        m.json.return_value = {"success": True, "result": {"ok": True}}
        return m

    with patch("httpx.AsyncClient") as MockHttpx:
        mock_http = MockHttpx.return_value.__aenter__.return_value
        mock_http.post = capture_post

        await client.post(
            "/execution/tool/my_tool",
            json={"param": "value"},
            headers=admin_headers,
        )

    assert captured["json"] == {"param": "value"}
    assert "my_tool" in captured["url"]


@pytest.mark.asyncio
async def test_execute_tool_result_empty_on_missing(client, admin_headers):
    """If GraphToolServer returns success but no result, returns empty dict."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True}

    with patch("httpx.AsyncClient") as MockHttpx:
        mock_http = MockHttpx.return_value.__aenter__.return_value
        mock_http.post = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/execution/tool/empty_result_tool",
            json={},
            headers=admin_headers,
        )

    assert response.status_code == 200
    assert response.json() == {}
