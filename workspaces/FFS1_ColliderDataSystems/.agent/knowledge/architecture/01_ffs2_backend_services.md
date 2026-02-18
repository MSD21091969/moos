# FFS2 Backend Services

> Three FastAPI servers in `FFS2_ColliderBackends_MultiAgentChromeExtension/`.

## Service Map

| Service                 | Port  | Stack                      | Storage            | Role                                     |
| ----------------------- | ----- | -------------------------- | ------------------ | ---------------------------------------- |
| ColliderDataServer      | :8000 | FastAPI + SQLAlchemy async | SQLite (aiosqlite) | Primary API, auth, SSE, WebRTC signaling |
| ColliderGraphToolServer | :8001 | FastAPI + WebSocket        | —                  | Workflow execution + graph processing    |
| ColliderVectorDbServer  | :8002 | FastAPI                    | ChromaDB           | Semantic search + embeddings             |

---

## ColliderDataServer (:8000)

**Path**: `ColliderDataServer/`
**Stack**: FastAPI + SQLAlchemy async + aiosqlite

### Source Structure

```
ColliderDataServer/
├── src/
│   ├── main.py                ← FastAPI app, CORS, lifespan
│   ├── api/
│   │   ├── auth.py            ← Login + JWT token generation
│   │   ├── users.py           ← User CRUD
│   │   ├── apps.py            ← Application CRUD
│   │   ├── nodes.py           ← Node CRUD (tree operations)
│   │   ├── roles.py           ← System role assignment (SAD/CAD)
│   │   ├── app_permissions.py ← Request/approve/reject app access
│   │   ├── permissions.py     ← Per-app permission checks
│   │   ├── context.py         ← Context hydration endpoints
│   │   ├── sse.py             ← Server-Sent Events stream
│   │   ├── rtc.py             ← WebRTC signaling WebSocket
│   │   └── health.py          ← Health check endpoint
│   ├── core/
│   │   ├── auth.py            ← JWT utilities
│   │   ├── config.py          ← pydantic-settings
│   │   └── database.py        ← SQLAlchemy async engine
│   ├── db/
│   │   └── models.py          ← SQLAlchemy models
│   └── schemas/
│       ├── users.py           ← Pydantic request/response schemas
│       ├── apps.py            ← Application schemas
│       └── nodes.py           ← Node schemas
└── requirements.txt
```

### API Routes

| Router          | Module                | Purpose                                                     |
| --------------- | --------------------- | ----------------------------------------------------------- |
| health          | `api.health`          | `GET /api/v1/health`                                        |
| auth            | `api.auth`            | `POST /api/v1/auth/login`, `POST /api/v1/auth/verify`       |
| users           | `api.users`           | User CRUD                                                   |
| apps            | `api.apps`            | Application CRUD, `GET /api/v1/apps`                        |
| nodes           | `api.nodes`           | Node CRUD, tree operations, `GET /api/v1/nodes?app_id=...`  |
| context         | `api.context`         | `GET /api/v1/context/:app_id/:node_path` — hydrated context |
| sse             | `api.sse`             | `GET /api/v1/sse` — persistent event stream                 |
| roles           | `api.roles`           | `POST /api/v1/users/{id}/assign-role`                       |
| app_permissions | `api.app_permissions` | Request/approve/reject app access                           |
| permissions     | `api.permissions`     | Per-app permission checks                                   |
| rtc             | `api.rtc`             | `WS /ws/rtc/` — WebRTC signaling                            |

### Database Models

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

#### Application

```
applications
├── id            (UUID, PK)
├── app_id        (unique, indexed)
├── owner_id      (FK → users, SET NULL)
├── display_name
├── config        (JSON) ← backend API config ("domain"), features, settings
├── root_node_id  (FK → nodes)
├── created_at
└── updated_at
```

The `config` JSON carries the application's permitted backend API set (the "domain" label — e.g. FILESYST, CLOUD, ADMIN) and feature configuration.

#### Node

```
nodes
├── id              (UUID, PK)
├── application_id  (FK → applications, CASCADE)
├── parent_id       (FK → nodes, CASCADE, nullable) ← self-referential tree
├── path            (string, indexed)
├── container       (JSON) ← NodeContainer: workspace context
├── metadata        (JSON) ← frontend_app, frontend_route
├── created_at
├── updated_at
├── UNIQUE(application_id, path)
└── INDEX(application_id), INDEX(parent_id), INDEX(path)
```

Nodes form a tree via `parent_id`. Each node's `container` JSON is a **NodeContainer** (manifest, instructions, rules, tools, knowledge, skills, workflows, configs). The `metadata` JSON includes `frontend_app` (which appnode renders this node) and `frontend_route`.

#### AppPermission

```
app_permissions
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── role            (enum: app_admin, app_user)
├── UNIQUE(user_id, application_id)
```

#### AppAccessRequest

```
app_access_requests
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── message         (string, nullable)
├── status          (string: pending, approved, rejected)
├── requested_at, resolved_at, resolved_by
```

### Relationships

```
User (system_role) ──1:N──► Application (owner_id) ──1:N──► Node
  │                                │                          │
  └──1:N──► AppPermission ◄──N:1───┘                          │
  │                                                            │
  └──1:N──► AppAccessRequest ◄──N:1──Application               │
                                                               │
                                                 Node ──1:N──► Node (children)
```

### SSE Event Types

| Event                | Trigger                      | Action                              |
| -------------------- | ---------------------------- | ----------------------------------- |
| `context_update`     | Node container modified      | Invalidate cache, notify sidepanel  |
| `node_modified`      | Node created/updated/deleted | Update tree if viewing affected app |
| `permission_changed` | Permissions modified         | Refresh permissions                 |
| `app_config_changed` | Application config modified  | Reload app config                   |
| `keepalive`          | Periodic                     | Maintain connection                 |

### WebRTC Signaling

WebSocket at `/ws/rtc/` for P2P signaling:

```
Client → Server: { type: "join", userId, roomId }
Client → Server: { type: "offer", targetUserId, sdp }
Client → Server: { type: "answer", targetUserId, sdp }
Client → Server: { type: "ice", targetUserId, candidate }
```

Room-based relay — actual media/data flows P2P via WebRTC.

### CORS

```python
allow_origin_regex=r"^chrome-extension://.*$"
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### Authentication

Current: Username/password + JWT (`POST /api/v1/auth/login`).
Planned: Firebase Auth (Google Sign-In → Firebase ID Token → exchange for DataServer JWT).

### How Agent Controls DataServer

```
Agent (LangGraph.js in SW) → REST call (create/modify/delete node)
         → DataServer persists to SQLite
         → DataServer emits SSE event (node_modified)
         → Extension SW receives SSE → updates cache
         → Sidepanel UI re-renders with new data
```

---

## ColliderGraphToolServer (:8001)

**Path**: `ColliderGraphToolServer/`
**Stack**: FastAPI + WebSocket + Pydantic AI

### WebSocket Endpoints

| Endpoint       | Handler         | Purpose                                |
| -------------- | --------------- | -------------------------------------- |
| `/ws/workflow` | WorkflowHandler | Execute multi-step agent workflows     |
| `/ws/graph`    | GraphHandler    | Graph operations (create/modify nodes) |

### Workflow Execution Flow

```
Agent submits workflow via WebSocket
    │
    ▼
Server processes steps (Pydantic AI Graph)
    │
    ├── Step results streamed back via WebSocket
    │
    ▼
If workflow creates new nodes:
    ├── Server calls DataServer REST to persist
    ├── DataServer emits SSE event
    └── Extension SW receives SSE, updates cache
```

### Node Creation

When a workflow step has `can_spawn: true`, the GraphToolServer can create sub-nodes in the application graph. Each new node gets its own NodeContainer with context defined by the workflow.

---

## ColliderVectorDbServer (:8002)

**Path**: `ColliderVectorDbServer/`
**Stack**: FastAPI + ChromaDB

### REST Endpoints

| Endpoint         | Method | Purpose                       |
| ---------------- | ------ | ----------------------------- |
| `/api/v1/search` | POST   | Semantic similarity search    |
| `/api/v1/embed`  | POST   | Generate embeddings for text  |
| `/api/v1/index`  | POST   | Index documents into ChromaDB |

Documents are indexed from NodeContainer `knowledge` and `tools` fields. Used by agents for semantic tool discovery (`TOOL_SEARCH` message type).

---

## Startup

All servers auto-create database tables on startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```

No migration tool required for development.

---

## Security

### System Roles

| Role                   | Level                | Can Assign Roles        |
| ---------------------- | -------------------- | ----------------------- |
| `superadmin` (SAD)     | Full platform access | All roles               |
| `collider_admin` (CAD) | Platform management  | `app_admin`, `app_user` |
| `app_admin`            | Per-app management   | —                       |
| `app_user`             | Per-app access       | —                       |

### Secrets Management

Secrets stored in user's ADMIN container (`users.container.secrets` JSON). Injected at runtime by tool executor middleware — agent never sees raw values.

### Context Security Layers

```
Layer 3: ADMIN Context     ← Secrets, global permissions (user.container)
Layer 2: APP Context       ← App-specific rules, API config (application.config)
Layer 1: NODE Context      ← Node-specific tools, instructions (node.container)
Layer 0: Base Agent        ← General capabilities (built-in)
```

Higher layers override lower layers.
