"""Dependency injection providers for FastAPI endpoints."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.container import AppContainer, get_container
from src.core.logging import get_logger
from src.core.rate_limiter import RateLimiter, get_rate_limiter
from src.models.context import SessionContext, UserContext
from src.models.permissions import Tier
from src.services.agent_service import AgentService
from src.services.auth_service import AuthService
from src.services.document_service import DocumentService
from src.services.session_service import SessionService
from src.services.storage_service import StorageService, FirestoreStorageProvider
from src.services.tool_service import ToolService

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


def get_app_container() -> AppContainer:
    """Get singleton AppContainer with all expensive resources."""
    return get_container()


def get_rate_limiter_instance() -> RateLimiter:
    """
    Get rate limiter instance for dependency injection.

    Provides global rate limiter for endpoints that need to check/enforce
    rate limits programmatically (beyond the middleware).

    Example in endpoint:
        >>> async def my_endpoint(
        ...     limiter: RateLimiter = Depends(get_rate_limiter_instance),
        ...     user_ctx: UserContext = Depends(get_user_context)
        ... ):
        ...     info = limiter.get_limit_info(user_ctx.user_id, user_ctx.tier)
        ...     return {"rate_limit": info}
    """
    return get_rate_limiter()


def get_auth_service(
    container: AppContainer = Depends(get_app_container),
) -> AuthService:
    """Get the authentication service."""
    return AuthService(container.firestore_client)


def get_tool_service() -> ToolService:
    """Get the tool service."""
    return ToolService()


def get_auth_service(
    container: AppContainer = Depends(get_app_container),
) -> AuthService:
    """Get the authentication service."""
    return AuthService(container.firestore_client)

def get_firestore_client(
    container: AppContainer = Depends(get_app_container),
):
    """Get raw Firestore client."""
    return container.firestore_client

def get_session_service(
    container: AppContainer = Depends(get_app_container),
) -> SessionService:
    """Get session service instance."""
    return SessionService(container.firestore_client)


def get_storage_service(
    container: AppContainer = Depends(get_app_container),
) -> StorageService:
    """Get storage service instance."""
    return StorageService(FirestoreStorageProvider(container.firestore_client))


async def get_document_service(
    container: AppContainer = Depends(get_app_container),
    session_service: SessionService = Depends(get_session_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> DocumentService:
    """Get document service instance with session validation."""
    return DocumentService(container.firestore_client, session_service, storage_service)


async def get_agent_service(
    session_service: SessionService = Depends(get_session_service),
    tool_service: ToolService = Depends(get_tool_service),
) -> AgentService:
    """Get the agent service."""
    return AgentService(session_service, tool_service)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    Get current user ID from JWT token.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        user_id: Unique user identifier

    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    if not credentials:
        # Check if auth bypass is enabled for testing
        from src.core.config import settings
        if settings.skip_auth_for_testing:
            logger.warning("Auth bypassed for testing (no credentials)", extra={"path": request.url.path})
            # Return a dummy user ID for tests
            request.state.user_id = "enterprise@test.com"
            return "enterprise@test.com"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        from jose import JWTError, jwt

        from src.core.config import settings

        # Check if auth bypass is enabled for testing (with invalid token)
        if settings.skip_auth_for_testing:
             logger.warning("Auth bypassed for testing (skipping signature check)", extra={"path": request.url.path})
             # Try to decode without verification to get user_id if possible, else default
             try:
                 # Decode without verification just to peek
                 unverified = jwt.get_unverified_claims(token)
                 user_id = unverified.get("sub") or "enterprise@test.com"
             except Exception:
                 user_id = "enterprise@test.com"
             
             request.state.user_id = user_id
             return user_id

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user_id = user_id
        logger.debug("Authenticated user", extra={"user_id": user_id})
        return user_id

    except JWTError as e:
        logger.error("JWT validation failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_context(
    request: Request,
    user_id: str = Depends(get_current_user),
    container: AppContainer = Depends(get_app_container),
) -> UserContext:
    """
    Get UserContext by fetching user data from Firestore.

    Retrieves user tier, email, and calculates remaining quota.
    """
    firestore = container.firestore_client

    # Fetch user from Firestore
    # Try to find by user_id field first, then by email as fallback
    users_ref = firestore.collection("users")
    
    # First try: query by user_id field
    query = users_ref.where("user_id", "==", user_id).limit(1)
    docs = query.stream()

    user_doc = None
    async for doc in docs:
        user_doc = doc
        break

    if not user_doc or not user_doc.exists:
        # Fallback for users not in Firestore (e.g., test tokens)
        logger.warning("User not found in Firestore, using defaults", extra={"user_id": user_id})
        # Check if user_id is already an email (contains @), otherwise append @example.com
        email = user_id if "@" in user_id else f"{user_id}@example.com"
        
        # Determine tier from user_id for test users
        # enterprise@test.com -> ENTERPRISE, pro@test.com -> PRO, else FREE
        if "enterprise" in user_id.lower():
            default_tier = Tier.ENTERPRISE
        elif "pro" in user_id.lower():
            default_tier = Tier.PRO
        else:
            default_tier = Tier.FREE
            
        user_ctx = UserContext(
            user_id=user_id,
            email=email,
            permissions=("read_data", "write_data", "execute_tools"),
            quota_remaining=1000,
            tier=default_tier,
        )
    else:
        user_data = user_doc.to_dict()

        # Parse tier (handle both string and Tier enum)
        tier_value = user_data.get("tier", "free")  # Default to "free"
        if isinstance(tier_value, str):
            # Tier enum expects lowercase values: "free", "pro", "enterprise"
            tier = Tier(tier_value.lower())
        else:
            tier = tier_value

        # Get quota remaining
        from src.services.quota_service import QuotaService

        quota_service = QuotaService(firestore)
        quota_remaining = await quota_service.get_remaining_quota(user_id, tier)

        # Determine permissions based on role
        role = user_data.get("role", "user")  # Default to "user"
        if role == "admin":
            # Admin gets all permissions including user management
            permissions = (
                "read_data",
                "write_data",
                "execute_tools",
                "manage_users",
                "view_logs",
                "manage_sessions",
                "manage_quotas",
            )
        else:
            # Regular users get basic permissions
            permissions = ("read_data", "write_data", "execute_tools")

        user_ctx = UserContext(
            user_id=user_id,
            email=user_data.get("email", f"{user_id}@example.com"),
            permissions=permissions,
            quota_remaining=quota_remaining,
            tier=tier,
        )

    request.state.user_id = user_ctx.user_id
    request.state.user_tier = user_ctx.tier.value

    return user_ctx


async def get_session_context(user_ctx: UserContext = Depends(get_user_context)) -> SessionContext:
    """
    Create SessionContext bridge for PydanticAI.

    Converts UserContext → SessionContext for use in RunContext[SessionContext].
    """
    return SessionContext.from_user_context(session_id="temp_session", user_ctx=user_ctx)
