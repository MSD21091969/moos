"""Unit tests for src/core/security.py

TEST: Security headers middleware
PURPOSE: Validate HTTP security headers
VALIDATES: SecurityHeadersMiddleware, OWASP headers
EXPECTED: All security headers added
"""

import pytest
from unittest.mock import MagicMock
from starlette.requests import Request
from starlette.responses import Response
from src.core.security import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware class."""

    @pytest.mark.asyncio
    async def test_middleware_adds_hsts_header(self):
        """
        TEST: Add HSTS header
        PURPOSE: Verify Strict-Transport-Security
        VALIDATES: HSTS header present
        EXPECTED: max-age=31536000 set
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    async def test_middleware_adds_csp_header(self):
        """
        TEST: Add CSP header
        PURPOSE: Verify Content-Security-Policy
        VALIDATES: CSP header present
        EXPECTED: default-src 'self' set
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    @pytest.mark.asyncio
    async def test_middleware_adds_x_frame_options(self):
        """
        TEST: Add X-Frame-Options header
        PURPOSE: Verify clickjacking protection
        VALIDATES: X-Frame-Options DENY
        EXPECTED: Header set to DENY
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.headers.get("X-Frame-Options") == "DENY"

    @pytest.mark.asyncio
    async def test_middleware_adds_x_content_type_options(self):
        """
        TEST: Add X-Content-Type-Options header
        PURPOSE: Verify MIME sniffing protection
        VALIDATES: X-Content-Type-Options nosniff
        EXPECTED: Header set to nosniff
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_middleware_adds_xss_protection(self):
        """
        TEST: Add X-XSS-Protection header
        PURPOSE: Verify XSS protection
        VALIDATES: X-XSS-Protection header
        EXPECTED: Header set to 1; mode=block
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "X-XSS-Protection" in response.headers
        assert "1; mode=block" in response.headers["X-XSS-Protection"]

    @pytest.mark.asyncio
    async def test_middleware_adds_referrer_policy(self):
        """
        TEST: Add Referrer-Policy header
        PURPOSE: Verify referrer policy
        VALIDATES: Referrer-Policy header
        EXPECTED: strict-origin-when-cross-origin
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Referrer-Policy" in response.headers
        assert "strict-origin-when-cross-origin" in response.headers["Referrer-Policy"]

    @pytest.mark.asyncio
    async def test_middleware_adds_permissions_policy(self):
        """
        TEST: Add Permissions-Policy header
        PURPOSE: Verify permissions policy
        VALIDATES: Permissions-Policy header
        EXPECTED: geolocation, microphone disabled
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("OK")

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Permissions-Policy" in response.headers
        assert "geolocation=()" in response.headers["Permissions-Policy"]

    @pytest.mark.asyncio
    async def test_middleware_preserves_response_content(self):
        """
        TEST: Preserve original response
        PURPOSE: Verify response not modified
        VALIDATES: Content preserved
        EXPECTED: Original response returned
        """
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)

        async def mock_call_next(request):
            return Response("Test Content", status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert b"Test Content" in response.body
