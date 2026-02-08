"""Rate limiting API endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_rate_limiter_instance, get_user_context
from src.core.logging import get_logger
from src.core.rate_limiter import RateLimiter
from src.models.context import UserContext

logger = get_logger(__name__)
router = APIRouter(prefix="/rate-limit", tags=["Rate Limiting"])


@router.get("/info", name="get_rate_limit_info")
async def get_rate_limit_info(
    user_ctx: UserContext = Depends(get_user_context),
    limiter: RateLimiter = Depends(get_rate_limiter_instance),
):
    """
    Get current rate limit information for authenticated user.

    **Authentication Required**: Yes

    **Returns**:
    - limit: Requests allowed per minute (-1 = unlimited)
    - used: Requests made this minute
    - remaining: Requests available this minute
    - reset_at: When counter resets (ISO 8601 format)
    - tier: User's subscription tier

    **Use Case**: Frontend displays rate limit status in UI

    **Example Response**:
    ```json
    {
      "limit": 60,
      "used": 23,
      "remaining": 37,
      "reset_at": "2025-10-28T12:01:30.123456Z",
      "tier": "pro"
    }
    ```
    """
    try:
        info = limiter.get_limit_info(user_ctx.user_id, user_ctx.tier)
        return info
    except Exception as e:
        logger.error("Failed to get rate limit info", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to get rate limit information")


@router.post("/reset", status_code=204, name="reset_rate_limit")
async def reset_rate_limit(
    user_ctx: UserContext = Depends(get_user_context),
    limiter: RateLimiter = Depends(get_rate_limiter_instance),
):
    """
    Reset rate limit for current user (admin-only operation).

    **Authentication Required**: Yes
    **Authorization**: User must have admin permissions (not yet implemented)

    **Use Case**: Admin tool to help users who hit rate limits

    **Note**: MVP doesn't enforce admin check yet - should be added in production
    """
    try:
        limiter.reset_user(user_ctx.user_id)
        logger.info("Rate limit reset for user", extra={"user_id": user_ctx.user_id})
        return None  # 204 No Content

    except Exception as e:
        logger.error("Failed to reset rate limit", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to reset rate limit")
