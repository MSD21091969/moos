"""ACL cache management for v4.0.0 Universal Object Model.

Redis cache strategy:
- Key pattern: `acl:user:{user_id}:sessions`
- TTL: Matches JWT token lifetime (configurable, default 24h)
- Content: Set of session IDs where user has owner/editor/viewer role
- Invalidation: On USER ResourceLink add/remove

This cache optimizes workspace queries by avoiding Firestore ACL scans.
"""

from src.core.logging import get_logger

logger = get_logger(__name__)


class ACLCache:
    """Cache for ACL-permitted sessions per user."""

    def __init__(self, default_ttl: int = 86400):  # 24 hours
        """Initialize ACL cache.
        
        Args:
            default_ttl: Default TTL in seconds (matches JWT lifetime)
        """
        self.default_ttl = default_ttl

    def _get_key(self, user_id: str) -> str:
        """Build Redis key for user's ACL cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            Redis key: acl:user:{user_id}:sessions
        """
        return f"acl:user:{user_id}:sessions"

    async def get_permitted_sessions(self, user_id: str) -> set[str] | None:
        """Get cached session IDs where user has access.
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of session IDs or None if cache miss
        """
        from src.core.redis_client import redis_client
        key = self._get_key(user_id)
        
        try:
            # Get from Redis (stored as JSON list)
            cached_data = await redis_client.get(key)
            
            if cached_data:
                session_ids = set(cached_data) if isinstance(cached_data, list) else set()
                logger.debug(
                    "ACL cache HIT",
                    extra={"user_id": user_id, "session_count": len(session_ids)}
                )
                return session_ids
            else:
                logger.debug("ACL cache MISS", extra={"user_id": user_id})
                return None
        except Exception as e:
            logger.warning(
                "ACL cache GET error",
                extra={"user_id": user_id, "error": str(e)}
            )
            return None

    async def set_permitted_sessions(
        self,
        user_id: str,
        session_ids: set[str],
        ttl: int | None = None
    ) -> None:
        """Cache session IDs where user has access.
        
        Args:
            user_id: User identifier
            session_ids: Set of permitted session IDs
            ttl: Optional TTL override (seconds)
        """
        from src.core.redis_client import redis_client
        key = self._get_key(user_id)
        cache_ttl = ttl or self.default_ttl
        
        try:
            if session_ids:
                # Store as JSON list with TTL
                await redis_client.set(key, list(session_ids), ttl=cache_ttl)
                
                logger.info(
                    "ACL cache SET",
                    extra={
                        "user_id": user_id,
                        "session_count": len(session_ids),
                        "ttl": cache_ttl
                    }
                )
            else:
                # Clear cache if no sessions
                await redis_client.delete(key)
        except Exception as e:
            logger.warning(
                "ACL cache SET error",
                extra={"user_id": user_id, "error": str(e)}
            )

    async def add_session(self, user_id: str, session_id: str) -> None:
        """Add session to user's ACL cache (incremental update).
        
        Called when USER ResourceLink is added to UserSession.
        
        Args:
            user_id: User identifier
            session_id: Session ID to add
        """
        from src.core.redis_client import redis_client
        
        try:
            # Get current cache
            current = await self.get_permitted_sessions(user_id)
            
            if current is not None:
                # Add to existing set and re-cache
                current.add(session_id)
                await self.set_permitted_sessions(user_id, current)
            # If cache miss, don't create partial cache - wait for full rebuild
            
            logger.info(
                "ACL cache ADD session",
                extra={"user_id": user_id, "session_id": session_id}
            )
        except Exception as e:
            logger.warning(
                "ACL cache ADD error",
                extra={"user_id": user_id, "session_id": session_id, "error": str(e)}
            )

    async def remove_session(self, user_id: str, session_id: str) -> None:
        """Remove session from user's ACL cache (incremental update).
        
        Called when USER ResourceLink is removed or ACL changes revoke access.
        
        Args:
            user_id: User identifier
            session_id: Session ID to remove
        """
        from src.core.redis_client import redis_client
        
        try:
            # Get current cache
            current = await self.get_permitted_sessions(user_id)
            
            if current is not None:
                # Remove from set and re-cache
                current.discard(session_id)
                await self.set_permitted_sessions(user_id, current)
            # If cache miss, nothing to remove
            
            logger.info(
                "ACL cache REMOVE session",
                extra={"user_id": user_id, "session_id": session_id}
            )
        except Exception as e:
            logger.warning(
                "ACL cache REMOVE error",
                extra={"user_id": user_id, "session_id": session_id, "error": str(e)}
            )

    async def invalidate_user(self, user_id: str) -> None:
        """Invalidate entire ACL cache for user.
        
        Called when:
        - ACL structure changes require full rebuild
        - User permissions change significantly
        - Manual cache clear needed
        
        Args:
            user_id: User identifier
        """
        from src.core.redis_client import redis_client
        key = self._get_key(user_id)
        
        try:
            await redis_client.delete(key)
            
            logger.info("ACL cache INVALIDATE", extra={"user_id": user_id})
        except Exception as e:
            logger.warning(
                "ACL cache INVALIDATE error",
                extra={"user_id": user_id, "error": str(e)}
            )

    async def refresh_from_firestore(
        self,
        user_id: str,
        firestore_session_ids: set[str]
    ) -> None:
        """Rebuild cache from Firestore query results.
        
        Called on cache miss or periodic refresh.
        
        Args:
            user_id: User identifier
            firestore_session_ids: Session IDs from Firestore ACL query
        """
        await self.set_permitted_sessions(user_id, firestore_session_ids)
        
        logger.info(
            "ACL cache REFRESH from Firestore",
            extra={"user_id": user_id, "session_count": len(firestore_session_ids)}
        )


# Global ACL cache instance
_acl_cache: ACLCache | None = None


def get_acl_cache(ttl: int = 86400) -> ACLCache:
    """Get global ACL cache instance.
    
    Args:
        ttl: Cache TTL in seconds (default 24h)
        
    Returns:
        ACLCache singleton
    """
    global _acl_cache
    if _acl_cache is None:
        _acl_cache = ACLCache(default_ttl=ttl)
    return _acl_cache
