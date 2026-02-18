# Backend Services

> Three FastAPI servers handle data persistence, graph processing, and semantic search.

## Service Map

| Service | Port | Stack | Database | Role |
|---------|------|-------|----------|------|
| ColliderDataServer | :8000 | FastAPI | SQLite (aiosqlite) | Primary API, auth, SSE, WebRTC signaling |
| ColliderGraphToolServer | :8001 | FastAPI | -- | WebSocket workflow + graph processing |
| ColliderVectorDbServer | :8002 | FastAPI | ChromaDB | Semantic search + embeddings |

All servers live under `FFS2_ColliderBackends_MultiAgentChromeExtension/`.

---

## ColliderDataServer (:8000)

**Path**: `ColliderDataServer/`
**Stack**: FastAPI + SQLAlchemy async + aiosqlite (SQLite)

### Registered Routers

Source: `src/main.py`

| Router | Module | Prefix | Purpose |
|--------|--------|--------|---------|
| health | `src.api.health` | -- | Health check endpoint |
| auth | `src.api.auth` | -- | Username/password + JWT auth |
| users | `src.api.users` | -- | User CRUD |
| apps | `src.api.apps` | -- | Application CRUD |
| nodes | `src.api.nodes` | -- | Node CRUD (tree operations) |
| context | `src.api.context` | -- | Context hydration endpoints |
| sse | `src.api.sse` | -- | Server-Sent Events stream |
| roles | `src.api.roles` | -- | System role assignment (SAD/CAD) |
| app_permissions | `src.api.app_permissions` | -- | Request/approve/reject app access |
| rtc | `src.api.rtc` | -- | WebRTC signaling WebSocket |

### CORS Configuration

```python
allow_origin_regex=r"^chrome-extension://.*$"
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

Allows any Chrome extension origin plus configured `cors_origins` from settings.

### Database Models

Source: `src/db/models.py`

#### User
```
users
├── id            (UUID, PK)
├── username      (unique, indexed)
├── password_hash (string)
├── display_name  (string, nullable)
├── system_role   (enum: superadmin, collider_admin, app_admin, app_user)
├── created_at
└── updated_at
```

The `system_role` field determines the user's platform-level access. Superadmin (SAD) and Collider Admin (CAD) can assign roles to other users.

#### Application
```
applications
├── id            (UUID, PK)
├── app_id        (unique, indexed)
├── owner_id      (FK → users, SET NULL)
├── display_name
├── config        (JSON)  ← domain, features, settings
├── root_node_id  (FK → nodes)
├── created_at
└── updated_at
```

The `config` JSON field contains the application's domain type and feature configuration. The `root_node_id` points to the top of the application's node tree.

#### AppPermission
```
app_permissions
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── role            (enum: app_admin, app_user)
├── created_at
└── UNIQUE(user_id, application_id)
```

#### AppAccessRequest
```
app_access_requests
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── message         (string, nullable)
├── status          (string: pending, approved, rejected)
├── requested_at
├── resolved_at     (nullable)
├── resolved_by     (FK → users, nullable)
└── INDEX(user_id), INDEX(application_id), INDEX(status)
```

#### Node
```
nodes
├── id              (UUID, PK)
├── application_id  (FK → applications, CASCADE)
├── parent_id       (FK → nodes, CASCADE, nullable)  ← self-referential tree
├── path            (string, indexed)
├── container       (JSON)  ← NodeContainer data
├── metadata        (JSON)
├── created_at
├── updated_at
├── UNIQUE(application_id, path)
└── INDEX(application_id), INDEX(parent_id), INDEX(path)
```

Nodes form a self-referential tree via `parent_id`. Each node carries a `container` (NodeContainer JSON) that defines its workspace context. The `path` field uses slash-separated addressing (e.g., `root/research/searcher`).

### Relationships

```
User (system_role) ──1:N──► Application (owner_id)──1:N──► Node
  │                                │                        │
  └──1:N──► AppPermission ◄──N:1───┘                        │
  │                                                          │
  └──1:N──► AppAccessRequest ◄──N:1──Application             │
                                                             │
                                               Node ──1:N──► Node (children)
```

### WebRTC Signaling

Source: `src/api/rtc.py`

WebSocket endpoint at `/ws/rtc/` for user-to-user P2P signaling:

```
Client → Server: { type: "join", userId, roomId }
Client → Server: { type: "offer", targetUserId, sdp }
Client → Server: { type: "answer", targetUserId, sdp }
Client → Server: { type: "ice", targetUserId, candidate }
```

Room-based architecture: users join rooms, signaling messages route to target users within rooms. The server is a relay only --- actual media flows P2P via WebRTC.

---

## ColliderGraphToolServer (:8001)

**Path**: `ColliderGraphToolServer/`
**Stack**: FastAPI + WebSocket

### WebSocket Endpoints

| Endpoint | Handler | Purpose |
|----------|---------|---------|
| `/ws/workflow` | WorkflowHandler | Execute multi-step workflows |
| `/ws/graph` | GraphHandler | Graph operations (create nodes, edges) |

The GraphToolServer processes workflows submitted by AI agents. When a workflow executes, it can create new subnodes in the application graph, which are persisted via the DataServer API.

**Workflow execution flow:**
1. Agent submits workflow via WebSocket
2. Server-side Pydantic AI graph processes steps
3. New nodes/subnodes created if permitted
4. Results streamed back via WebSocket
5. DataServer notified via REST to persist changes
6. SSE event broadcast to connected clients

---

## ColliderVectorDbServer (:8002)

**Path**: `ColliderVectorDbServer/`
**Stack**: FastAPI + ChromaDB

### REST Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/search` | POST | Semantic similarity search |
| `/api/v1/embed` | POST | Generate embeddings for text |
| `/api/v1/index` | POST | Index documents into ChromaDB |

Used by agents for semantic tool search (`TOOL_SEARCH` message type) and knowledge retrieval. Documents are indexed from NodeContainer `knowledge` and `tools` fields.

---

## Startup

All servers auto-create database tables on startup via SQLAlchemy's `Base.metadata.create_all`. No migration tool is required for development.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```
