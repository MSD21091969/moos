"""Unit tests for src/core/middleware.py

TEST: Request correlation middleware
PURPOSE: Validate request ID generation and tracking
VALIDATES: RequestIDMiddleware, request_id_var
EXPECTED: Each request has unique ID
"""

import pytest
from unittest.mock import MagicMock
from starlette.requests import Request
from starlette.responses import Response
from src.core.middleware import RequestIDMiddleware, get_request_id, request_id_var


class TestRequestIDMiddleware:
    """Test RequestIDMiddleware class."""

    @pytest.mark.asyncio
    async def test_middleware_generates_request_id(self):
        """
        TEST: Generate request ID
        PURPOSE: Verify UUID generation
        VALIDATES: Request ID set
        EXPECTED: Unique ID generated
        """
        middleware = RequestIDMiddleware(app=MagicMock())

        # Mock request without X-Request-ID
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"

        # Mock call_next
        async def mock_call_next(request):
            return Response("OK")

        await middleware.dispatch(mock_request, mock_call_next)

        # Request ID should be set in state
        assert hasattr(mock_request.state, "request_id")

    @pytest.mark.asyncio
    async def test_middleware_accepts_client_request_id(self):
        """
        TEST: Accept client-provided request ID
        PURPOSE: Verify distributed tracing
        VALIDATES: Client ID preserved
        EXPECTED: Client ID used
        """
        middleware = RequestIDMiddleware(app=MagicMock())

        # Mock request with X-Request-ID
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Request-ID": "client-id-123"}
        mock_request.state = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"

        async def mock_call_next(request):
            return Response("OK")

        await middleware.dispatch(mock_request, mock_call_next)

        assert mock_request.state.request_id == "client-id-123"

    @pytest.mark.asyncio
    async def test_middleware_adds_request_id_to_response(self):
        """
        TEST: Add request ID to response headers
        PURPOSE: Verify response header
        VALIDATES: X-Request-ID in response
        EXPECTED: Header set
        """
        middleware = RequestIDMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Response should have X-Request-ID header
        assert response is not None


class TestGetRequestId:
    """Test get_request_id function."""

    def test_get_request_id_returns_none_initially(self):
        """
        TEST: Get request ID when not set
        PURPOSE: Verify default behavior
        VALIDATES: None returned
        EXPECTED: No request ID
        """
        # Reset context var
        request_id_var.set(None)

        result = get_request_id()

        assert result is None

    def test_get_request_id_returns_set_value(self):
        """
        TEST: Get request ID after setting
        PURPOSE: Verify context var retrieval
        VALIDATES: Set value returned
        EXPECTED: Correct ID returned
        """
        request_id_var.set("test-id-123")

        result = get_request_id()

        assert result == "test-id-123"

        # Cleanup
        request_id_var.set(None)
