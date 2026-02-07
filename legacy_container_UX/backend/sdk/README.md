# Collider SDK - Python Client Library

**Type-safe Python client** for the Collider API with local persistence, offline mode, and automatic sync.

## Installation

```bash
# From project root
pip install -e ./sdk

# Or add to requirements.txt
-e file:./sdk
```

## Quick Start

```python
from sdk import ColliderClient

async with ColliderClient(
    api_url="http://localhost:8000",
    token="your-jwt-token"
) as client:
    # Create session
    session = await client.sessions.create(
        title="My Analysis",
        ttl_hours=48
    )
    
    # Run agent
    result = await client.run_agent(
        message="Analyze this data",
        session_id=session.session_id
    )
    
    # List sessions
    sessions = await client.sessions.list()
    
    # Get user info
    user = await client.get_user_info()
    print(f"Quota: {user.remaining_quota}")
```

## Features

### 1. Type-Safe API Client

All endpoints return **Pydantic models** with full type hints:

```python
from sdk import Session, SessionCreateRequest, AgentRunResponse

# Create with validation
request = SessionCreateRequest(
    title="My Session",
    ttl_hours=24,
    tags=["analysis", "urgent"]
)

session: Session = await client.sessions.create(**request.model_dump())
```

### 2. Local Persistence

**SQLite** or **in-memory** storage for offline work:

```python
from sdk import ColliderClient, SQLiteSessionStore

# Setup local database
store = SQLiteSessionStore("~/.collider/sessions.db")
await store.initialize()

async with ColliderClient(
    api_url="http://localhost:8000",
    token="your-token",
    local_store=store
) as client:
    # Sessions auto-saved locally + synced to server
    session = await client.sessions.create(title="Local Work")
    
    # Export for backup
    await client.export_sessions("~/backup.json")
    
    # Import from backup
    await client.import_sessions("~/backup.json")
```

### 3. Offline Mode

Work without server connection, sync later:

```python
from sdk import InMemorySessionStore

store = InMemorySessionStore()

# Work offline
async with ColliderClient(
    api_url="http://localhost:8000",
    token="your-token",
    local_store=store,
    offline_mode=True
) as client:
    session = await client.sessions.create(title="Offline Work")
    result = await client.run_agent("Analyze", session_id=session.session_id)

# Later: sync to server
async with ColliderClient(
    api_url="http://localhost:8000",
    token="your-token",
    local_store=store,
    offline_mode=False
) as client:
    await client.sync_to_server()
```

### 4. Session Manager

High-level session operations:

```python
from sdk import SessionManager

async with SessionManager(
    api_url="http://localhost:8000",
    token="your-token"
) as mgr:
    # Get or create session
    session = await mgr.get_or_create(
        title="Daily Analysis",
        create_if_missing=True
    )
    
    # Auto-cleanup old sessions
    await mgr.cleanup_expired()
    
    # Batch operations
    await mgr.archive_completed()
```

### 5. Streaming Responses

Real-time agent responses:

```python
from sdk import StreamingResponse

async for chunk in client.run_agent_stream(
    message="Analyze this",
    session_id=session_id
):
    if chunk.type == "text":
        print(chunk.content, end="", flush=True)
    elif chunk.type == "tool_call":
        print(f"\n🔧 Tool: {chunk.tool_name}")
    elif chunk.type == "result":
        print(f"\n✓ Result: {chunk.result}")
```

## API Reference

### ColliderClient

**Core Methods**:
```python
client.sessions.list()                    # List all sessions
client.sessions.create(...)               # Create session
client.sessions.get(session_id)           # Get session by ID
client.sessions.update(session_id, ...)   # Update session
client.sessions.delete(session_id)        # Delete session

client.run_agent(message, session_id)     # Run agent (async)
client.run_agent_stream(...)              # Run agent (streaming)

client.get_user_info()                    # Get user profile
client.list_tools()                       # List available tools
client.upload_document(...)               # Upload file
client.list_documents(session_id)         # List documents
```

**Persistence Methods**:
```python
client.export_sessions(filepath)          # Export to JSON
client.import_sessions(filepath)          # Import from JSON
client.sync_to_server()                   # Push local changes to server
client.sync_from_server()                 # Pull server changes to local
```

### Error Handling

```python
from sdk import ClientError, TokenExpiredError

try:
    session = await client.sessions.get("invalid-id")
except TokenExpiredError:
    # Refresh token and retry
    new_token = await refresh_token()
    client.set_token(new_token)
except ClientError as e:
    print(f"API Error: {e.status_code} - {e.message}")
```

## Models

**Core Types**:
```python
Session                  # Session metadata + ACL
SessionCreateRequest     # Create session payload
SessionUpdateRequest     # Update session payload
SessionList              # List response with pagination

AgentRunRequest          # Agent execution request
AgentRunResponse         # Agent execution result

Message                  # Chat message (user/agent/tool)
MessageHistory          # List of messages

ToolInfo                # Tool metadata
ToolList                # Available tools

UserInfo                # User profile + quota

ErrorResponse           # API error details
```

## Configuration

**Environment Variables**:
```bash
COLLIDER_API_URL=http://localhost:8000
COLLIDER_TOKEN=your-jwt-token
COLLIDER_TIMEOUT=30
COLLIDER_MAX_RETRIES=3
```

**Client Options**:
```python
client = ColliderClient(
    api_url="http://localhost:8000",
    token="your-token",
    timeout=30,               # Request timeout (seconds)
    max_retries=3,            # Auto-retry failed requests
    local_store=store,        # Local persistence
    offline_mode=False,       # Work offline?
    auto_sync=True,           # Auto-sync to server?
    verify_ssl=True           # Verify SSL certs?
)
```

## Testing

**Unit Tests**:
```bash
# SDK tests included in main test suite
pytest tests/unit/ -k sdk -v
```

**Integration Tests**:
```bash
# Requires running backend
pytest tests/integration/test_sdk_client.py -v
```

## Examples

See `examples/` folder in project root:
- `examples/basic_usage.py` - Simple CRUD operations
- `examples/agent_chat.py` - Chat with agent
- `examples/offline_work.py` - Offline mode + sync
- `examples/batch_operations.py` - Bulk session management

## Development

**Type Checking**:
```bash
mypy sdk/ --ignore-missing-imports
```

**Linting**:
```bash
ruff check sdk/
ruff format sdk/
```

## Architecture

```
sdk/
├── __init__.py          # Public API exports
├── client.py            # ColliderClient (main class)
├── sessions.py          # SessionManager (high-level ops)
├── models.py            # Pydantic models (API types)
├── persistence.py       # Local storage (SQLite/in-memory)
└── streaming.py         # Streaming response handlers
```

**Design Philosophy**:
- **Type-safe**: Full Pydantic validation
- **Async-first**: All I/O is async/await
- **Offline-capable**: Work without server
- **Auto-sync**: Keep local + remote in sync
- **Ergonomic**: Pythonic API, minimal boilerplate

## Troubleshooting

**Import errors?**
```bash
pip install -e ./sdk
```

**Type errors?**
```bash
# Ensure Pydantic 2.x is installed
pip install "pydantic>=2.0"
```

**Connection errors?**
```bash
# Check backend is running
curl http://localhost:8000/health
```

**Offline sync issues?**
```bash
# Check local database
sqlite3 ~/.collider/sessions.db "SELECT * FROM sessions;"
```

---

**Version**: 2.0.0  
**Python**: 3.11+  
**License**: MIT
