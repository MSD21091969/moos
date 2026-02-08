"""Session management for collider-sdk.

Handles session lifecycle with automatic context management.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sdk.models import Session, SessionCreateRequest, SessionList, SessionUpdateRequest

if TYPE_CHECKING:
    from sdk.client import ColliderClient


class SessionManager:
    """Manage session lifecycle with context handling.

    Features:
    - CRUD operations for sessions
    - Active session tracking
    - Pagination support for listing
    - Filter by type/status/tags
    - Session sharing (ACL management)
    - Context manager for automatic cleanup

    **Usage Patterns**:

    1. **Basic Session Management**:
    ```python
    # Create and use session
    session = await client.sessions.create(
        title="Q4 Analysis",
        tags=["finance", "quarterly"]
    )

    result = await client.run_agent(
        "Analyze revenue",
        session_id=session.session_id
    )

    # Update metadata
    await client.sessions.update(
        session.session_id,
        title="Q4 Revenue Analysis (Complete)",
        status="archived"
    )
    ```

    2. **Session Sharing (ACL)**:
    ```python
    # Share session with teammates
    session = await client.sessions.share(
        session_id="sess_abc123def456",
        user_ids=["user_456", "user_789"]
    )

    # Shared users can now read the session
    # (Owner retains full control)

    # Revoke access
    await client.sessions.unshare(
        session_id="sess_abc123def456",
        user_ids=["user_789"]
    )
    ```

    3. **Session Discovery**:
    ```python
    # List all active sessions
    sessions = await client.sessions.list(
        status="active",
        page_size=50
    )

    # Filter by tags
    finance_sessions = await client.sessions.list(
        tags=["finance"],
        session_type="analysis"
    )

    # Pagination
    page1 = await client.sessions.list(page=1)
    if page1.has_more:
        page2 = await client.sessions.list(page=2)
    ```

    3. **Active Session Pattern**:
    ```python
    # Set active session (all messages go here)
    await client.sessions.set_active(session_id)

    # Run multiple messages in same session
    await client.run_agent("First question")  # Uses active session
    await client.run_agent("Follow-up")       # Same session

    # Get current active session
    current = client.sessions.get_active()
    ```

    4. **Cleanup**:
    ```python
    # Delete old sessions
    old_sessions = await client.sessions.list(
        status="archived",
        page_size=100
    )

    for session in old_sessions.sessions:
        await client.sessions.delete(session.session_id)
    ```
    """

    def __init__(self, client: "ColliderClient"):
        """Initialize session manager.

        Args:
            client: ColliderClient instance for API calls
        """
        self.client = client
        self._active_session: Optional[str] = None

    async def create(
        self,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        session_type: str = "chat",
        ttl_hours: int = 24,
    ) -> Session:
        """Create a new session.

        Args:
            title: Session title
            description: Optional description
            tags: Optional tags for filtering
            session_type: Type of session (chat, analysis, workflow)
            ttl_hours: Time-to-live in hours (1-8760)

        Returns:
            Created Session object

        Raises:
            ValueError: If parameters are invalid
            httpx.HTTPStatusError: If API call fails
        """
        req = SessionCreateRequest(
            title=title,
            description=description,
            tags=tags or [],
            session_type=session_type,
            ttl_hours=ttl_hours,
        )

        response = await self.client._post(
            "/sessions",
            json=req.model_dump(exclude_none=True),
        )
        session = Session(**response)
        self._active_session = session.session_id
        return session

    async def get(self, session_id: str) -> Session:
        """Get session details.

        Args:
            session_id: Session identifier

        Returns:
            Session object

        Raises:
            httpx.HTTPStatusError: If session not found or API fails
        """
        response = await self.client._get(f"/sessions/{session_id}")
        return Session(**response)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        session_type: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> SessionList:
        """List sessions with optional filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page (1-100)
            session_type: Filter by session type
            status: Filter by status
            tags: Filter by tags

        Returns:
            SessionList with pagination info

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if session_type:
            params["session_type"] = session_type
        if status:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)

        response = await self.client._get("/sessions", params=params)
        return SessionList(**response)

    async def update(
        self,
        session_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Session:
        """Update session metadata.

        Args:
            session_id: Session identifier
            title: New title
            description: New description
            tags: New tags
            status: New status

        Returns:
            Updated Session object

        Raises:
            httpx.HTTPStatusError: If session not found or API fails
        """
        req = SessionUpdateRequest(
            title=title,
            description=description,
            tags=tags,
            status=status,
        )

        response = await self.client._patch(
            f"/sessions/{session_id}",
            json=req.model_dump(exclude_none=True),
        )
        return Session(**response)

    async def delete(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session identifier

        Raises:
            httpx.HTTPStatusError: If session not found or API fails
        """
        await self.client._delete(f"/sessions/{session_id}")
        if self._active_session == session_id:
            self._active_session = None

    async def set_active(self, session_id: str) -> Session:
        """Set active session and verify it exists.

        Args:
            session_id: Session identifier to activate

        Returns:
            Session object

        Raises:
            httpx.HTTPStatusError: If session not found or API fails
        """
        session = await self.get(session_id)
        self._active_session = session_id
        return session

    def get_active(self) -> Optional[str]:
        """Get currently active session ID.

        Returns:
            Session ID or None if no active session
        """
        return self._active_session

    async def share(self, session_id: str, user_ids: List[str]) -> Session:
        """Share session with other users (grant read access).

        Only session owner can share.

        Args:
            session_id: Session to share
            user_ids: List of user IDs to grant access to

        Returns:
            Updated session with new ACL

        Raises:
            httpx.HTTPStatusError: If not owner or session not found
        """
        response = await self.client._post(
            f"/sessions/{session_id}/share",
            json={"user_ids": user_ids} if isinstance(user_ids, list) else user_ids,
        )
        return Session(**response)

    async def unshare(self, session_id: str, user_ids: List[str]) -> Session:
        """Revoke session access from users.

        Only session owner can unshare.

        Args:
            session_id: Session to unshare from
            user_ids: List of user IDs to revoke access from

        Returns:
            Updated session with modified ACL

        Raises:
            httpx.HTTPStatusError: If not owner or session not found
        """
        response = await self.client._post(
            f"/sessions/{session_id}/unshare",
            json={"user_ids": user_ids} if isinstance(user_ids, list) else user_ids,
        )
        return Session(**response)

    async def __aenter__(self) -> "SessionManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        pass
