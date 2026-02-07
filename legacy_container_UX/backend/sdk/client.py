"""Main collider-sdk client for API interaction.

Type-safe, async client with automatic token refresh, retry logic,
and session management with local persistence and offline support.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, AsyncGenerator

import httpx

from sdk.models import (
    AgentRunRequest,
    AgentRunResponse,
    MessageHistory,
    ToolList,
    UserInfo,
)
from sdk.persistence import SessionStore
from sdk.sessions import SessionManager

logger = logging.getLogger(__name__)


class TokenExpiredError(Exception):
    """Raised when access token has expired and cannot be refreshed."""

    pass


class ClientError(Exception):
    """Base exception for SDK errors."""

    pass


class ColliderClient:
    """Type-safe async client for Collider API.

    Production-grade SDK with enterprise features:
    - Automatic JWT token refresh with configurable buffer
    - Exponential backoff retry (5 attempts, 1s→16s)
    - Session lifecycle management
    - Connection pooling (100 max, 20 keepalive)
    - Structured error handling with typed exceptions
    - Request/response logging
    - User info caching (5min TTL)

    **Authentication Patterns**:

    1. **Simple Token** (development):
    ```python
    client = ColliderClient(
        api_url="http://localhost:8000",
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    ```

    2. **Auto-Refresh** (production):
    ```python
    client = ColliderClient(
        api_url="https://api.example.com",
        token="access_token",
        refresh_token="refresh_token",
        auto_refresh=True  # Automatically refresh before expiry
    )
    ```

    3. **Context Manager** (recommended):
    ```python
    async with ColliderClient(
        api_url="https://api.example.com",
        token=get_token(),
        timeout=60.0,  # Longer timeout for data operations
        max_retries=3   # Fewer retries for faster failures
    ) as client:
        user = await client.get_user_info()
        print(f"User: {user.email}, Quota: {user.quota_remaining}")
    # Auto-closes on exit
    ```

    **Usage Examples**:

    ```python
    # 1. One-off question (no session)
    result = await client.run_agent("What's the weather?")
    print(result.response)

    # 2. Conversational (with session)
    session = await client.sessions.create(
        title="Data Analysis",
        session_type="analysis",
        ttl_hours=48
    )

    # Multi-turn conversation
    r1 = await client.run_agent(
        "Load sales data",
        session_id=session.session_id
    )
    r2 = await client.run_agent(
        "Calculate Q4 revenue",
        session_id=session.session_id
    )

    # Get full history
    history = await client.get_message_history(session.session_id)
    for msg in history.messages:
        print(f"{msg.role}: {msg.content}")

    # 3. Tool discovery
    tools = await client.get_tools()
    for tool in tools.tools:
        print(f"{tool.name} (cost: {tool.quota_cost})")

    # 4. Usage monitoring
    user_info = await client.get_user_info(refresh_cache=True)
    if user_info.quota_remaining < 10:
        print("Warning: Low quota!")
    ```

    **Error Handling**:

    ```python
    from httpx import HTTPStatusError
    from sdk.client import TokenExpiredError, ClientError

    try:
        result = await client.run_agent(message)
    except HTTPStatusError as e:
        if e.response.status_code == 429:
            print("Quota exceeded")
        elif e.response.status_code == 403:
            print("Permission denied")
        elif e.response.status_code == 404:
            print("Session not found")
    except TokenExpiredError:
        print("Token expired, re-authenticate")
    except ClientError as e:
        print(f"SDK error: {e}")
    ```
    """

    def __init__(
        self,
        api_url: str,
        token: str,
        *,
        refresh_token: Optional[str] = None,
        auto_refresh: bool = True,
        timeout: float = 30.0,
        max_retries: int = 5,
        local_store: Optional[SessionStore] = None,
        offline_mode: bool = False,
    ):
        """Initialize Collider client.

        Args:
            api_url: Base API URL (e.g., http://localhost:8000)
            token: JWT access token
            refresh_token: Optional refresh token for automatic renewal
            auto_refresh: Automatically refresh token if expired
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            local_store: Optional SessionStore for local persistence (SQLite, in-memory, etc)
            offline_mode: If True, use only local storage and don't attempt API calls

        Raises:
            ValueError: If api_url or token is empty

        Usage:
            # With local SQLite persistence
            store = SQLiteSessionStore("~/.collider/sessions.db")
            await store.initialize()

            async with ColliderClient(
                api_url="http://localhost:8000",
                token=token,
                local_store=store
            ) as client:
                # Sessions auto-saved locally and synced to server
                session = await client.sessions.create(title="My Analysis")

            # Offline-only mode (no server connection needed)
            store = InMemorySessionStore()
            async with ColliderClient(
                api_url="http://localhost:8000",
                token=token,
                local_store=store,
                offline_mode=True
            ) as client:
                # Works without network connection
                session = await client.sessions.create(title="Local Session")
        """
        if not api_url or not token:
            raise ValueError("api_url and token are required")

        self.api_url = api_url.rstrip("/")
        self.token = token
        self.refresh_token = refresh_token
        self.auto_refresh = auto_refresh
        self.timeout = timeout
        self.max_retries = max_retries
        self.offline_mode = offline_mode
        self.local_store = local_store

        # Token expiry tracking
        self.token_expires_at: Optional[datetime] = None

        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(  # nosec B113
            base_url=self.api_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )

        # Session manager
        self.sessions = SessionManager(self)

        # User info cache
        self._user_cache: Optional[UserInfo] = None
        self._user_cache_time: Optional[datetime] = None

    async def get_user_info(self, *, refresh_cache: bool = False) -> UserInfo:
        """Get current user information.

        Caches user info for 5 minutes to reduce API calls.

        Args:
            refresh_cache: Force refresh from API

        Returns:
            UserInfo with permissions and quota

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        now = datetime.utcnow()

        if (
            not refresh_cache
            and self._user_cache
            and self._user_cache_time
            and (now - self._user_cache_time).total_seconds() < 300
        ):
            return self._user_cache

        response = await self._get("/user/info")
        user_info = UserInfo(**response)

        self._user_cache = user_info
        self._user_cache_time = now

        return user_info

    async def run_agent(
        self,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AgentRunResponse:
        """Execute agent with a message.

        Args:
            message: User message
            session_id: Existing session ID or None to create new
            model: Override default model (e.g., 'gpt-4')

        Returns:
            Agent response

        Raises:
            httpx.HTTPStatusError: If API call fails
            ValidationError: If response is invalid
        """
        req = AgentRunRequest(
            message=message,
            session_id=session_id,
            stream=False,
            model=model,
        )

        response = await self._post(
            "/agent/run",
            json=req.model_dump(exclude_none=True),
        )

        return AgentRunResponse(**response)

    async def get_tools(self) -> ToolList:
        """Get available tools.

        Returns:
            ToolList with accessible tools

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        response = await self._get("/tools/available")
        return ToolList(**response)

    async def get_tool(self, name: str) -> Dict[str, Any]:
        """Get details for a specific tool.

        Args:
            name: Tool name

        Returns:
            Tool information

        Raises:
            httpx.HTTPStatusError: If tool not found or API fails
        """
        return await self._get(f"/tools/{name}")

    async def get_message_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> MessageHistory:
        """Get message history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to retrieve (1-100)

        Returns:
            MessageHistory with messages and pagination info

        Raises:
            httpx.HTTPStatusError: If session not found or API fails
        """
        response = await self._get(
            f"/sessions/{session_id}/messages",
            params={"limit": limit},
        )
        return MessageHistory(**response)

    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities based on user tier.

        Returns:
            Agent capabilities with available models and features

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        return await self._get("/agent/capabilities")

    async def stream_agent(
        self,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute agent with streaming response.

        Streams tokens as they're generated by the model for real-time display.

        Args:
            message: User message
            session_id: Existing session ID or None to create new
            model: Override default model

        Yields:
            Individual tokens from the agent response

        Raises:
            httpx.HTTPStatusError: If API call fails
            TokenExpiredError: If token expired

        Example:
            ```python
            async with client:
                async for token in await client.stream_agent("What's the weather?"):
                    print(token, end="", flush=True)
            ```
        """
        req = AgentRunRequest(
            message=message,
            session_id=session_id,
            stream=True,
            model=model,
        )

        headers = self._get_headers()

        # Check token expiry before streaming
        if self._token_is_expired():
            if self.auto_refresh and self.refresh_token:
                await self._refresh_token()
            else:
                raise TokenExpiredError("Access token expired")

        async with self._client.stream(
            "POST",
            "/agent/stream",
            json=req.model_dump(exclude_none=True),
            headers=headers,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    token = line[6:]  # Strip "data: " prefix
                    if token and token != "[DONE]":
                        yield token

    async def stream_agent_to_file(
        self,
        message: str,
        filepath: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Stream agent response directly to file.

        Args:
            message: User message
            filepath: Path to save response
            session_id: Existing session ID
            model: Override model

        Returns:
            Metadata dict with token count, duration, etc.

        Example:
            ```python
            metadata = await client.stream_agent_to_file(
                message="Generate report",
                filepath="report.txt"
            )
            print(f"Saved {metadata['tokens']} tokens")
            ```
        """
        import time

        token_count = 0
        start_time = time.time()

        with open(filepath, "w") as f:
            async for token in await self.stream_agent(message, session_id, model):
                f.write(token)
                token_count += 1

        elapsed = time.time() - start_time

        return {
            "filepath": filepath,
            "tokens": token_count,
            "duration_seconds": elapsed,
            "tokens_per_second": token_count / elapsed if elapsed > 0 else 0,
        }

    async def export_messages(
        self,
        session_id: str,
        format: str = "json",
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """Export session messages.

        Args:
            session_id: Session identifier
            format: Export format (json, csv, txt)
            include_metadata: Include message metadata

        Returns:
            Export response with download URL or data

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        response = await self._post(
            f"/sessions/{session_id}/messages/export",
            json={
                "format": format,
                "include_metadata": include_metadata,
            },
        )
        return response

    async def trigger_job(
        self,
        job_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trigger a background job.

        Args:
            job_type: Type of job to trigger
            parameters: Job parameters

        Returns:
            Job trigger response with job ID and status

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        response = await self._post(
            "/jobs/trigger",
            json={
                "job_type": job_type,
                "parameters": parameters or {},
            },
        )
        return response

    async def export_session_job(
        self,
        session_id: str,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Trigger session export job.

        Args:
            session_id: Session to export
            format: Export format

        Returns:
            Job trigger response

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        response = await self._post(
            "/jobs/export-session",
            json={
                "session_id": session_id,
                "format": format,
            },
        )
        return response

    # ========================================================================
    # Internal HTTP Methods
    # ========================================================================

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make GET request with auth and retry logic.

        Args:
            path: API path (e.g., /user/info)
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If all retries fail
            TokenExpiredError: If token expired and cannot refresh
        """
        return await self._request(
            "GET",
            path,
            params=params,
        )

    async def _post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make POST request with auth and retry logic.

        Args:
            path: API path
            json: Request body

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If all retries fail
            TokenExpiredError: If token expired and cannot refresh
        """
        return await self._request(
            "POST",
            path,
            json=json,
        )

    async def _patch(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make PATCH request with auth and retry logic.

        Args:
            path: API path
            json: Request body

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If all retries fail
            TokenExpiredError: If token expired and cannot refresh
        """
        return await self._request(
            "PATCH",
            path,
            json=json,
        )

    async def _delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request with auth and retry logic.

        Args:
            path: API path

        Returns:
            Response JSON as dict (may be empty)

        Raises:
            httpx.HTTPStatusError: If all retries fail
            TokenExpiredError: If token expired and cannot refresh
        """
        return await self._request(
            "DELETE",
            path,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute HTTP request with auth, retry, and error handling.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: Request body

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If all retries fail
            TokenExpiredError: If token expired and cannot refresh
        """
        # Check if token expired and refresh if needed
        if self._token_is_expired():
            if self.auto_refresh and self.refresh_token:
                await self._refresh_token()
            else:
                raise TokenExpiredError("Access token expired")

        headers = self._get_headers()

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors (except 429 for rate limiting)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

                # Last attempt - raise
                if attempt == self.max_retries - 1:
                    raise

                # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                wait_time = 2**attempt
                logger.warning(
                    f"Request failed, retrying in {wait_time}s. "
                    f"Attempt {attempt + 1}/{self.max_retries}",
                    extra={"method": method, "path": path, "status": e.response.status_code},
                )
                await asyncio.sleep(wait_time)

            except httpx.RequestError as e:
                # Network errors - retry with backoff
                if attempt == self.max_retries - 1:
                    raise

                wait_time = 2**attempt
                logger.warning(
                    f"Network error, retrying in {wait_time}s. "
                    f"Attempt {attempt + 1}/{self.max_retries}",
                    extra={"error": str(e)},
                )
                await asyncio.sleep(wait_time)

        raise ClientError("Request failed after maximum retries")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "collider-sdk/1.0.0",
        }

    def _token_is_expired(self) -> bool:
        """Check if token is expired or about to expire (within 1 minute)."""
        if not self.token_expires_at:
            return False

        expiry_buffer = datetime.utcnow() + timedelta(minutes=1)
        return expiry_buffer >= self.token_expires_at

    async def _refresh_token(self) -> None:
        """Refresh access token using refresh token.

        Raises:
            TokenExpiredError: If refresh fails
        """
        if not self.refresh_token:
            raise TokenExpiredError("No refresh token available")

        try:
            # Call refresh endpoint (you'll need to implement this on backend)
            response = await self._client.post(
                "/auth/refresh",
                json={"refresh_token": self.refresh_token},
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            self.token = data["access_token"]

            # Parse token expiry from response if provided
            if "expires_in" in data:
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])

            logger.info("Token refreshed successfully")

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise TokenExpiredError("Failed to refresh access token")

    # ============================================================================
    # Session Persistence & Sync Methods
    # ============================================================================

    async def export_sessions(self, filepath: str) -> None:
        """Export all sessions to JSON file for backup or transfer.

        Useful for:
        - Backing up your analysis work
        - Switching to different server
        - Sharing session metadata with team
        - Offline archive

        Args:
            filepath: Path to export JSON file (e.g., ~/sessions_backup.json)

        Usage:
            # Export all sessions
            await client.export_sessions("~/my_sessions.json")

            # Later, import on different device
            new_client = ColliderClient(...)
            await new_client.import_sessions("~/my_sessions.json")
        """
        if not self.local_store:
            raise ValueError("Local store not configured. Initialize with local_store parameter.")

        await self.local_store.export(filepath)
        logger.info(f"Sessions exported to {filepath}")

    async def import_sessions(self, filepath: str) -> int:
        """Import sessions from JSON file.

        Allows you to:
        - Restore previous sessions
        - Move sessions between devices
        - Load a colleague's shared sessions

        Args:
            filepath: Path to JSON export file

        Returns:
            Number of sessions imported

        Usage:
            count = await client.import_sessions("~/sessions_backup.json")
            print(f"Imported {count} sessions")
        """
        if not self.local_store:
            raise ValueError("Local store not configured. Initialize with local_store parameter.")

        count = await self.local_store.import_sessions(filepath)
        logger.info(f"Imported {count} sessions from {filepath}")
        return count

    async def sync_to_server(self, session_ids: Optional[list] = None) -> int:
        """Sync local sessions to remote server.

        After working locally with offline_mode=True, sync back to server
        to make sessions available in web UI and share with team.

        Args:
            session_ids: Specific session IDs to sync, or None for all

        Returns:
            Number of sessions synced

        Usage:
            # Work locally (offline)
            store = SQLiteSessionStore()
            async with ColliderClient(..., local_store=store, offline_mode=True) as client:
                session = await client.sessions.create(title="Local Work")
                await client.run_agent("Analyze data", session_id=session.session_id)

            # Later, connect to server and sync
            async with ColliderClient(..., local_store=store, offline_mode=False) as client:
                synced = await client.sync_to_server()
                print(f"Synced {synced} sessions to server")
        """
        if not self.local_store:
            raise ValueError("Local store not configured")

        if self.offline_mode:
            logger.warning("Cannot sync in offline mode. Set offline_mode=False")
            return 0

        # Get sessions to sync
        all_sessions = await self.local_store.list(limit=10000)

        if session_ids:
            all_sessions = [s for s in all_sessions if s.session_id in session_ids]

        synced_count = 0

        for session in all_sessions:
            try:
                # Try to create or update on server
                await self._post(
                    "/sessions",
                    json={
                        "title": session.title,
                        "session_type": session.session_type,
                        "metadata": session.metadata,
                        "tags": session.tags,
                    },
                )

                # Mark as synced in local store
                await self.local_store.update(
                    session.session_id,
                    metadata={
                        **(session.metadata or {}),
                        "synced_to_server": True,
                        "synced_at": datetime.now().isoformat(),
                    },
                )

                synced_count += 1
                logger.info(f"Synced session {session.session_id} to server")

            except Exception as e:
                logger.warning(f"Failed to sync session {session.session_id}: {e}")

        logger.info(f"Synced {synced_count}/{len(all_sessions)} sessions to server")
        return synced_count

    async def sync_from_server(self) -> int:
        """Pull latest sessions from server and merge with local store.

        Useful for:
        - Switching devices/laptops
        - Collaborator shared sessions
        - Cloud backup recovery

        Returns:
            Number of sessions merged from server

        Usage:
            # Pull all sessions from server
            count = await client.sync_from_server()
            print(f"Synced {count} sessions from server")

            # Access merged sessions locally
            all_sessions = await client.local_store.list()
        """
        if not self.local_store:
            raise ValueError("Local store not configured")

        if self.offline_mode:
            logger.warning("Cannot sync from server in offline mode")
            return 0

        try:
            # Fetch all sessions from server
            response = await self._get("/sessions?limit=10000")
            server_sessions = response.get("sessions", [])

            merged_count = 0

            for session_data in server_sessions:
                try:
                    # Try to get existing local version
                    existing = await self.local_store.get(session_data["session_id"])

                    # Always keep local version if it's newer
                    if existing:
                        existing_updated = datetime.fromisoformat(existing.updated_at.isoformat())
                        server_updated = datetime.fromisoformat(session_data["updated_at"])

                        if existing_updated > server_updated:
                            continue  # Keep local version

                    # Otherwise, import/update with server version
                    from sdk.models import Session

                    session = Session(
                        session_id=session_data["session_id"],
                        user_id=session_data["user_id"],
                        title=session_data["title"],
                        session_type=session_data.get("session_type", "analysis"),
                        status=session_data.get("status", "active"),
                        created_at=datetime.fromisoformat(session_data["created_at"]),
                        updated_at=datetime.fromisoformat(session_data["updated_at"]),
                        ttl_hours=session_data.get("ttl_hours"),
                        metadata=session_data.get("metadata"),
                        tags=session_data.get("tags", []),
                    )

                    if existing:
                        await self.local_store.update(
                            session.session_id,
                            title=session.title,
                            status=session.status,
                            metadata=session.metadata,
                        )
                    else:
                        await self.local_store.create(session)

                    merged_count += 1

                except Exception as e:
                    logger.warning(f"Failed to merge session {session_data.get('session_id')}: {e}")

            logger.info(f"Synced {merged_count} sessions from server")
            return merged_count

        except Exception as e:
            logger.error(f"Failed to sync from server: {e}")
            return 0

    async def clear_local_cache(self) -> None:
        """Clear all local session data.

        Warning: This is permanent deletion of local data.

        Usage:
            # After syncing to cloud, optionally clear local cache
            await client.sync_to_server()
            await client.clear_local_cache()  # Free up disk space
        """
        if not self.local_store:
            return

        await self.local_store.clear()
        logger.info("Cleared all local session data")

        """Close HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self) -> "ColliderClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
