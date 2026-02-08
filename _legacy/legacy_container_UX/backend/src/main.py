"""Main FastAPI application for Cloud Run deployment.

Clean architecture with:
- Proper request/response models (src/api/models.py)
- Router-based endpoints (src/api/routes/)
- Dependency injection (src/api/dependencies.py)
- Auto-generated OpenAPI documentation
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from starlette.responses import JSONResponse

from src.api.models import (
    ErrorResponse,
    HealthResponse,
)
from src.api.routes import (
    agent,
    auth,
    containers,  # V4.0.0: Unified container instances
    dashboard,
    definitions,  # V4.0.0: Definition registry
    documents,
    events,
    files,  # Added files router
    jobs,
    oauth,
    query,  # V4.1.0: Unified Query API
    rate_limit,
    resources,
    session_resources,
    sessions,
    tools,
    user,
    usersessions,  # V4.0.0: Workspace root
    workspace,
    v5_containers,  # V5.0.0: Unified container API with SSE
)
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.core.rate_limiter import get_rate_limiter
from src.core.security import SecurityHeadersMiddleware

# Load environment variables from .env file before reading configuration
# (Must be after imports to avoid E402 linting errors)
if os.environ.get("ENVIRONMENT") != "test":
    load_dotenv()

# Setup logging with Logfire
setup_logging()
logger = logging.getLogger(__name__)


# Helper function for background Redis connection
async def _connect_redis():
    """Connect to Redis in background (non-blocking startup)."""
    from src.core.redis_client import redis_client

    try:
        await redis_client.connect()
        logger.info("Redis connection initialized (background)")
    except Exception as e:
        logger.warning(
            "Redis connection failed (continuing without cache)", extra={"error": str(e)}
        )


# Graceful shutdown handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for graceful startup and shutdown.

    Startup:
    - Register tools
    - Initialize dependencies

    Shutdown:
    - Drain connections (30s timeout)
    - Cleanup container resources
    """
    # Startup
    logger.info("Starting My Tiny Data Collider API v2.0.0")
    logger.info(
        "Environment configuration",
        extra={
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "port": os.getenv("PORT", "not set"),
            "gcp_project": os.getenv("GCP_PROJECT", "not set"),
            "firestore_database": os.getenv("FIRESTORE_DATABASE", "not set"),
            "use_firestore_mocks": os.getenv("USE_FIRESTORE_MOCKS", "not set"),
            "redis_enabled": os.getenv("REDIS_ENABLED", "not set"),
            "k_service": os.getenv("K_SERVICE", "not set"),
        },
    )

    # Validate environment variables (skip in Cloud Run - uses workload identity)
    if not os.getenv("K_SERVICE"):
        from src.core.env_validator import validate_on_startup

        validate_on_startup()

    # Initialize Redis connection (optional for graceful degradation)
    # Defer connection to background to speed up startup
    from src.core.redis_client import redis_client

    redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    if redis_enabled:
        logger.info("Redis connection will be initialized in background")
        # Don't await - let it connect in background
        asyncio.create_task(_connect_redis())
    else:
        logger.info("Redis disabled via REDIS_ENABLED=false")

    # Register tools
    from src.tools import register_all_tools

    register_all_tools()

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down My Tiny Data Collider API")

    # Disconnect Redis (if connected)
    if redis_enabled and redis_client._client is not None:
        try:
            await redis_client.disconnect()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning("Redis disconnect error", extra={"error": str(e)})

    # Give in-flight requests time to complete (30 second grace period)
    logger.info("Draining connections (30s grace period)")
    await asyncio.sleep(2)  # Brief pause to let current requests finish

    # Cleanup container
    from src.core.container import get_container

    container = get_container()
    await container.reset()

    logger.info("Shutdown complete")


# Create FastAPI app with lifespan
def custom_generate_unique_id(route):
    """Generate operation IDs for OpenAPI schema."""
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name


app = FastAPI(
    title="My Tiny Data Collider",
    lifespan=lifespan,
    description="""
AI agent platform for session-based data analysis with quota management and tool permissions.

**Authentication:** All endpoints require JWT Bearer token except `/health` and `/`
**Documentation:** [GitHub Repository](https://github.com/MSD21091969/my-tiny-data-collider)
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    contact={
        "name": "My Tiny Data Collider",
        "url": "https://github.com/MSD21091969/my-tiny-data-collider",
    },
    license_info={
        "name": "MIT",
    },
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

# Instrument FastAPI with Logfire for automatic tracing (skip in test environment)
# Defer until after app is created to speed up startup
if settings.environment != "test":
    try:
        logger.info("Instrumenting FastAPI with Logfire...")
        logfire.instrument_fastapi(app)
        logger.info("Logfire instrumentation complete")
    except Exception as e:
        logger.warning("Logfire instrumentation failed (non-fatal)", extra={"error": str(e)})

# Clear OpenAPI schema cache to ensure latest schema is generated
app.openapi_schema = None

# Request correlation middleware (must be first for request ID to be available)
app.add_middleware(RequestIDMiddleware)

# Security headers middleware (production hardening)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - environment-based origins
cors_origins = ["*"] if settings.environment == "development" else settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for enforcing tier-based request limits.

    Checks rate limit and adds headers to response:
    - X-RateLimit-Limit: Requests allowed per minute
    - X-RateLimit-Used: Requests used this minute
    - X-RateLimit-Remaining: Requests remaining
    - X-RateLimit-Reset: When counter resets (ISO format)
    - Retry-After: Seconds until limit resets (if rate limited)
    """
    import os

    # Skip rate limiting in tests
    disable_rl = os.getenv("DISABLE_RATE_LIMITING", "false").lower()
    if disable_rl == "true":
        logger.info(
            "Rate limiting disabled for request",
            extra={"method": request.method, "path": request.url.path},
        )
        return await call_next(request)

    # Skip rate limiting for health, public endpoints, and static assets
    if request.url.path in [
        "/health",
        "/ready",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    ] or request.url.path.startswith(("/static/", "/assets/", "/favicon.ico")):
        return await call_next(request)

    # Extract user context from request (added by auth middleware)
    # In production, this comes from JWT token
    user_id = getattr(request.state, "user_id", None)
    user_tier = getattr(request.state, "user_tier", "free")

    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                token_user_id = payload.get("sub")
                if token_user_id:
                    user_id = token_user_id
                    request.state.user_id = token_user_id

                tier_claim = payload.get("tier")
                if isinstance(tier_claim, str) and tier_claim:
                    normalized_tier = tier_claim.lower()
                    user_tier = normalized_tier
                    request.state.user_tier = normalized_tier
            except JWTError:
                logger.debug("Invalid Authorization token supplied; using anonymous rate limit")

    if not user_id:
        # No user context, use default
        user_id = "anonymous"
        user_tier = "free"

    # Check rate limit
    limiter = get_rate_limiter()
    if not limiter.is_allowed(user_id, user_tier):
        # Rate limited - return 429 Too Many Requests
        limit_info = limiter.get_limit_info(user_id, user_tier)
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded. Maximum {limit_info['limit']} requests per minute for {user_tier} tier.",
                "limit": limit_info["limit"],
                "used": limit_info["used"],
                "remaining": limit_info["remaining"],
                "reset_at": limit_info["reset_at"],
            },
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Used": str(limit_info["used"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": limit_info["reset_at"] or "",
                "Retry-After": "60",  # Retry after 60 seconds
            },
        )

    # Request allowed - call the endpoint
    response = await call_next(request)

    # Add rate limit headers to response
    limit_info = limiter.get_limit_info(user_id, user_tier)
    response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
    response.headers["X-RateLimit-Used"] = str(limit_info["used"])
    response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
    if limit_info["reset_at"]:
        response.headers["X-RateLimit-Reset"] = limit_info["reset_at"]

    return response


app.include_router(user.router)

# Legacy endpoints (backward compatibility)
app.include_router(sessions.router)  # /sessions
app.include_router(documents.router)  # /sessions/{id}/documents
app.include_router(files.router)  # /files
app.include_router(agent.router)  # /agent
app.include_router(workspace.router)  # /workspace

# Shared/utility endpoints
app.include_router(tools.router)
app.include_router(auth.router)
app.include_router(oauth.router)  # OAuth for Google Workspace
app.include_router(jobs.router)
app.include_router(rate_limit.router)
app.include_router(dashboard.router)

# V4.0.0: Universal Object Model routes
app.include_router(usersessions.router)  # /usersessions (workspace root)
app.include_router(definitions.router)  # /definitions (agent/tool/source registry)
app.include_router(containers.router)  # /containers (unified instance CRUD)
app.include_router(query.router)  # /query (unified data access)

# V5.0.0: Unified Container API with SSE events
app.include_router(v5_containers.router)  # /api/v5/containers, /api/v5/events

# Phase 5: New API routes
app.include_router(session_resources.router)
app.include_router(resources.router)
app.include_router(events.router)

# Note: Legacy HTML dashboards removed - frontend now serves new webui
# Mount /static kept for any remaining static assets
app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness probe - checks if service is alive.

    **No authentication required.**

    Used by Cloud Run/Kubernetes to restart unhealthy containers.
    Always returns 200 unless the process is completely broken.
    """
    return HealthResponse(
        status="healthy",
        service="my-tiny-data-collider",
        version="2.0.0",
        checks={"api": "healthy"},
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check():
    """
    Readiness probe - checks if service can handle traffic.

    **No authentication required.**

    Used by Cloud Run/Kubernetes to determine if container is ready.
    Checks critical dependencies: Firestore, rate limiter.

    Returns:
    - 200 if all dependencies are healthy
    - 503 if any dependency is unavailable
    """
    from src.core.container import get_container

    checks = {}
    overall_status = "healthy"

    # Check Firestore connectivity
    try:
        container = get_container()
        firestore = container.firestore_client
        # Try a lightweight operation
        await firestore.collection("_health_check").limit(1).get()
        checks["firestore"] = "healthy"
    except Exception as e:
        logger.error("Firestore health check failed", extra={"error": str(e)})
        checks["firestore"] = "unhealthy"
        overall_status = "unhealthy"

    # Check rate limiter
    try:
        limiter = get_rate_limiter()
        tracked_users = limiter.get_tracked_user_count()
        checks["rate_limiter"] = f"healthy ({tracked_users} tracked users)"
    except Exception as e:
        logger.error("Rate limiter health check failed", extra={"error": str(e)})
        checks["rate_limiter"] = "unhealthy"
        overall_status = "unhealthy"

    # Check tools registry
    try:
        from src.core.tool_registry import get_tool_registry

        registry = get_tool_registry()
        tool_count = len(registry._tools)
        checks["tools"] = f"healthy ({tool_count} registered)"
    except Exception as e:
        logger.error("Tools health check failed", extra={"error": str(e)})
        checks["tools"] = "unhealthy"
        overall_status = "degraded"

    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "service": "my-tiny-data-collider",
            "version": "2.0.0",
            "checks": checks,
        },
    )


@app.get("/docs", tags=["Documentation"], include_in_schema=False)
async def get_swagger_docs():
    """Interactive API documentation (Swagger UI)."""
    from fastapi.openapi.docs import get_swagger_ui_html

    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


@app.get("/redoc", tags=["Documentation"], include_in_schema=False)
async def get_redoc_docs():
    """Alternative API documentation (ReDoc)."""
    from fastapi.openapi.docs import get_redoc_html

    return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")


@app.get("/api", tags=["Root"])
async def api_root():
    """
    API root endpoint with service information.

    **No authentication required.**

    Returns available endpoints and documentation links.
    """
    return {
        "message": "My Tiny Data Collider API",
        "version": "2.0.0",
        "status": "running",
        "fun_fact": "🎮 Try the Konami code on /dashboard.html for a surprise!",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "web_interfaces": {
            "object_oriented_ui": "/webui.html",
            "tables_ui": "/tables.html",
            "dashboard": "/dashboard.html",
        },
        "endpoints": {
            "user_info": "GET /user/info",
            "create_session": "POST /sessions",
            "list_sessions": "GET /sessions",
            "run_agent": "POST /agent/run",
            "list_tools": "GET /tools/available",
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "header": "Authorization: Bearer <token>",
            "note": "MVP uses mock authentication (user_dev_mock_123456)",
        },
        "building_blocks": {
            "user_context": "Identity, permissions, quota from JWT",
            "sessions": "Conversation containers with metadata",
            "agent": "PydanticAI agent for executing requests",
            "tools": "Functions agent can call (permission-filtered)",
            "messages": "Conversation history (user/assistant/tool)",
        },
    }


@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint - Backend service information.

    **No authentication required.**

    Frontend is deployed separately. For local development:
    ```bash
    cd frontend
    npm install
    npm run dev  # http://localhost:5173
    ```
    """
    return {
        "message": "My Tiny Data Collider API - Backend Only",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.environment,
        "frontend": {
            "local_dev": "http://localhost:5173",
            "production": "Deploy to Vercel/Netlify separately",
            "note": "Frontend no longer bundled with backend",
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "legacy_dashboards": {
            "tables_ui": "/tables.html",
            "dashboard": "/dashboard.html",
            "webui": "/webui.html",
        },
        "endpoints": {
            "user_info": "GET /user/info",
            "create_session": "POST /sessions",
            "list_sessions": "GET /sessions",
            "run_agent": "POST /agent/run",
            "list_tools": "GET /tools/available",
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "header": "Authorization: Bearer <token>",
        },
    }


# Startup/shutdown events

if __name__ == "__main__":
    import uvicorn
    import multiprocessing

    # Development: 8000, Production (Cloud Run): 8080
    port = int(os.getenv("PORT", "8000"))
    host = "127.0.0.1" if settings.environment == "development" else "0.0.0.0"

    # Performance tuning for concurrent workloads
    # Workers: 0 = auto-detect, n = explicit workers
    workers = int(os.getenv("UVICORN_WORKERS", "0"))  # 0 = auto
    if workers == 0 and settings.environment == "production":
        workers = (multiprocessing.cpu_count() or 1) + 1
    elif settings.environment == "development":
        workers = 1  # Single worker for easier debugging

    loop = os.getenv("UVICORN_LOOP", "auto")  # auto, asyncio, uvloop

    logger.info(
        "Starting server with performance tuning",
        extra={
            "host": host,
            "port": port,
            "environment": settings.environment,
            "workers": workers,
            "loop_type": loop,
            "max_connections": 1000,
            "keep_alive": 30,
        },
    )

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        workers=workers,
        limit_concurrency=1000,  # Max concurrent connections
        limit_max_requests=10000,  # Restart worker after N requests to prevent memory leaks
        timeout_keep_alive=30,  # Keep-alive timeout (seconds)
    )  # nosec B104
