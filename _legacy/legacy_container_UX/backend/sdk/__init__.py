"""collider-sdk: Type-safe Python client for Collider API.

Makes API consumption trivial for Python developers with:
- Typed client for all endpoints
- Automatic token refresh and retry logic
- Session manager with context handling
- Full Pydantic model support
- Local persistence with export/import/sync
- Offline mode for working without server

Example (with local persistence):
    ```python
    from sdk import ColliderClient, SQLiteSessionStore

    # Setup local storage
    store = SQLiteSessionStore("~/.collider/sessions.db")
    await store.initialize()

    # Use with local sync
    async with ColliderClient(
        api_url="http://localhost:8000",
        token="eyJ...",
        local_store=store
    ) as client:
        # Sessions auto-saved locally and synced to server
        session = await client.sessions.create(
            title="My Analysis",
            ttl_hours=48
        )
        result = await client.run_agent(
            message="Analyze this data",
            session_id=session.session_id
        )

        # Export for backup
        await client.export_sessions("~/backup.json")

        # Later sync to new server
        await client.sync_to_server()
    ```

Example (offline mode):
    ```python
    from sdk import ColliderClient, InMemorySessionStore

    store = InMemorySessionStore()

    # Work offline without server connection
    async with ColliderClient(
        api_url="http://localhost:8000",
        token="eyJ...",
        local_store=store,
        offline_mode=True
    ) as client:
        session = await client.sessions.create(title="Offline Work")
        result = await client.run_agent("Analyze data", session_id=session.session_id)

    # Later connect and sync
    async with ColliderClient(
        api_url="http://localhost:8000",
        token="eyJ...",
        local_store=store,
        offline_mode=False
    ) as client:
        await client.sync_to_server()
    ```
"""

from sdk.client import ClientError, ColliderClient, TokenExpiredError
from sdk.models import (
    AgentRunRequest,
    AgentRunResponse,
    ErrorDetail,
    ErrorResponse,
    Message,
    MessageHistory,
    Session,
    SessionCreateRequest,
    SessionList,
    SessionUpdateRequest,
    ToolInfo,
    ToolList,
    UserInfo,
)
from sdk.persistence import InMemorySessionStore, SessionStore, SQLiteSessionStore
from sdk.sessions import SessionManager

__version__ = "2.0.0"
__all__ = [
    "ColliderClient",
    "TokenExpiredError",
    "ClientError",
    "SessionManager",
    "UserInfo",
    "Session",
    "SessionCreateRequest",
    "SessionUpdateRequest",
    "SessionList",
    "AgentRunRequest",
    "AgentRunResponse",
    "ToolInfo",
    "ToolList",
    "Message",
    "MessageHistory",
    "ErrorResponse",
    "ErrorDetail",
    # Persistence
    "SessionStore",
    "SQLiteSessionStore",
    "InMemorySessionStore",
]
