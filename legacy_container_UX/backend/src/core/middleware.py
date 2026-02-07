"""Request correlation middleware for distributed tracing.

Provides:
- X-Request-ID generation/propagation for request correlation
- Context variables for request tracking across async calls
- Integration with Logfire structured logging
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import get_logger

logger = get_logger(__name__)

# Context variable for request ID (accessible across async calls)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for correlation tracking.

    Features:
    - Generates UUID for each request if not provided
    - Accepts X-Request-ID from client for distributed tracing
    - Adds X-Request-ID to response headers
    - Sets context variable for logging integration
    - Logs request start/end with timing
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation ID."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in context variable (accessible in route handlers)
        request_id_var.set(request_id)

        # Attach to request state (for route handlers)
        request.state.request_id = request_id

        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            },
        )

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )

        return response
