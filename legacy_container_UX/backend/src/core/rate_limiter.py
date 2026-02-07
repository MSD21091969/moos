"""Rate limiting for API requests.

Provides:
- Per-user rate limiting
- Tier-based rate limits (FREE: 10/min, PRO: 60/min, ENTERPRISE: unlimited)
- In-memory tracking with automatic cleanup
- Sliding window rate limiting algorithm
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting tiers."""

    # Requests per minute for each tier
    # Increased for load testing: FREE 60→120, PRO 300→600, ENTERPRISE unlimited
    TIER_LIMITS = {
        "free": 120,  # Increased from 60
        "pro": 600,  # Increased from 300
        "enterprise": 0,  # 0 = unlimited
    }

    # Cleanup interval (remove entries older than 2 minutes)
    CLEANUP_INTERVAL = timedelta(minutes=2)
    WINDOW_SIZE = timedelta(minutes=1)


class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm.

    Tracks requests per user per minute, enforces tier-based limits.

    Example:
        >>> limiter = RateLimiter()
        >>> if limiter.is_allowed(user_id="user_123", tier="pro"):
        ...     # Allow request
        ...     pass
        >>> limit_info = limiter.get_limit_info(user_id="user_123", tier="pro")
        >>> print(f"Remaining: {limit_info['remaining']}/{limit_info['limit']}")
    """

    def __init__(self):
        """Initialize rate limiter."""
        # Structure: {user_id: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list[datetime]] = {}
        self.last_cleanup = datetime.now(timezone.utc)

    def is_allowed(self, user_id: str, tier: str) -> bool:
        """
        Check if request is allowed for user.

        Args:
            user_id: User identifier
            tier: User tier (free, pro, enterprise)

        Returns:
            True if request is allowed, False if rate limited

        Example:
            >>> if limiter.is_allowed("user_123", "pro"):
            ...     return await process_request()
            ... else:
            ...     raise HTTPException(status_code=429, detail="Rate limited")
        """
        # Enterprise tier has no limits
        limit = RateLimitConfig.TIER_LIMITS.get(tier, 0)
        if limit == 0:
            return True

        now = datetime.now(timezone.utc)

        # Cleanup old entries periodically
        if now - self.last_cleanup > RateLimitConfig.CLEANUP_INTERVAL:
            self._cleanup(now)

        # Get requests in current window
        if user_id not in self.requests:
            self.requests[user_id] = []

        # Filter requests within the sliding window (last 1 minute)
        window_start = now - RateLimitConfig.WINDOW_SIZE
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] if req_time > window_start
        ]

        # Check if limit exceeded
        request_count = len(self.requests[user_id])
        if request_count >= limit:
            tier_value = tier.value if hasattr(tier, "value") else tier
            logger.warning(
                "Rate limit exceeded for user",
                extra={"user_id": user_id, "tier": tier_value, "limit": limit},
            )
            return False

        # Record this request
        self.requests[user_id].append(now)
        return True

    def get_limit_info(self, user_id: str, tier: str) -> dict:
        """
        Get rate limit information for user.

        Args:
            user_id: User identifier
            tier: User tier

        Returns:
            Dictionary with:
            - limit: Requests allowed per minute
            - used: Requests made this minute
            - remaining: Requests available
            - reset_at: When counter resets (ISO format)

        Example:
            >>> info = limiter.get_limit_info("user_123", "pro")
            >>> print(f"{info['used']}/{info['limit']} requests")
        """
        limit = RateLimitConfig.TIER_LIMITS.get(tier, 0)

        if limit == 0:
            # Unlimited tier
            return {
                "limit": -1,  # Unlimited
                "used": 0,
                "remaining": -1,
                "reset_at": None,
                "tier": tier,
            }

        now = datetime.now(timezone.utc)

        # Get requests in current window
        if user_id not in self.requests:
            self.requests[user_id] = []

        window_start = now - RateLimitConfig.WINDOW_SIZE
        requests_in_window = [
            req_time for req_time in self.requests[user_id] if req_time > window_start
        ]

        used = len(requests_in_window)
        remaining = max(0, limit - used)

        # Next window starts when oldest request in window expires
        if requests_in_window:
            oldest_request = min(requests_in_window)
            reset_at = oldest_request + RateLimitConfig.WINDOW_SIZE
        else:
            reset_at = now

        return {
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "reset_at": reset_at.isoformat(),
            "tier": tier,
        }

    def reset_user(self, user_id: str) -> None:
        """
        Reset rate limit for specific user (admin operation).

        Args:
            user_id: User to reset

        Example:
            >>> limiter.reset_user("user_123")
        """
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info("Reset rate limit for user", extra={"user_id": user_id})

    def reset(self) -> None:
        """
        Reset all rate limit tracking (for testing).

        Example:
            >>> limiter.reset()
        """
        self.requests.clear()
        logger.debug("Reset all rate limits")

    def get_tracked_user_count(self) -> int:
        """Return how many users currently have rate limit entries."""
        return len(self.requests)

    def get_status(self, user_id: str, tier: str) -> dict:
        """
        Get current rate limit status for user (alias for get_limit_info).

        Args:
            user_id: User identifier
            tier: User tier

        Returns:
            Dictionary with rate limit status

        Note:
            This is an alias for get_limit_info() to match API expectations.
        """
        return self.get_limit_info(user_id, tier)

    def _cleanup(self, now: datetime) -> None:
        """
        Remove old entries outside the window.

        Args:
            now: Current time (for window calculation)
        """
        window_start = now - RateLimitConfig.CLEANUP_INTERVAL

        # Remove entries older than cleanup interval
        for user_id in list(self.requests.keys()):
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id] if req_time > window_start
            ]

            # Remove user if no requests left
            if not self.requests[user_id]:
                del self.requests[user_id]

        self.last_cleanup = now
        logger.debug("Cleaned up rate limiter", extra={"users_tracked": len(self.requests)})


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        Global RateLimiter instance

    Example:
        >>> limiter = get_rate_limiter()
        >>> if limiter.is_allowed(user_id, tier):
        ...     return await process_request()
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
