# FFS2 Backend Services

> Four FastAPI services in `FFS2_ColliderBackends_MultiAgentChromeExtension/`.

## Service Map

| Service                 | Port  | Stack                          | Storage            | Role                                            |
| ----------------------- | ----- | ------------------------------ | ------------------ | ----------------------------------------------- |
| ColliderDataServer      | :8000 | FastAPI + SQLAlchemy async     | SQLite (aiosqlite) | Primary API, auth, SSE, WebRTC, agent bootstrap |
| ColliderGraphToolServer | :8001 | FastAPI + WebSocket + gRPC MCP | —                  | Tool registry, workflow execution, MCP server   |
| ColliderVectorDbServer  | :8002 | FastAPI + ChromaDB             | ChromaDB           | Semantic search + embeddings                    |
| ColliderAgentRunner     | :8004 | FastAPI + pydantic-ai          | —                  | ContextSet sessions, LLM streaming (claude-s46) |

---

## ColliderDataServer (:8000)

**Path**: `ColliderDataServer/`
**Stack**: FastAPI + SQLAlchemy async + aiosqlite

### Source Structure

```text
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
│   │   ├── agent_bootstrap.py  ← Agent bootstrap endpoint
│   │   ├── execution.py       ← Tool/workflow execution proxy
│   │   ├── templates.py       ← Node templates
│   │   ├── sse.py             ← Server-Sent Events stream
│   │   ├── rtc.py             ← WebRTC signaling WebSocket
│   │   └── health.py          ← Health check endpoint
│   ├── core/
│   │   ├── auth.py            ← JWT utilities
│   │   ├── config.py          ← pydantic-settings
│   │   ├── database.py        ← SQLAlchemy async engine
│   │   ├── agent_bootstrap.py  ← Bootstrap render/merge logic
│   │   ├── grpc_client.py     ← gRPC client to GraphToolServer
│   │   ├── boundary.py        ← Context boundary helpers
│   │   └── templates.py       ← Template logic
│   ├── db/
│   │   └── models.py          ← SQLAlchemy models
│   └── schemas/
│       ├── users.py           ← Pydantic request/response schemas
│       ├── apps.py            ← Application schemas
│       ├── nodes.py           ← Node schemas
│       ├── agent_bootstrap.py  ← AgentBootstrap, SkillEntry, ToolSchema
│       └── templates.py       ← Template DTOs
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
| agent_bootstrap | `api.agent_bootstrap` | `GET /api/v1/agent/bootstrap/{node_id}` — agent bootstrap   |
| execution       | `api.execution`       | `POST /api/v1/execution/tool/{name}` — tool/workflow proxy  |
| templates       | `api.templates`       | `GET /api/v1/templates` — node templates                    |

### Database Models

#### User

```text
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

```text
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

```text
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

```text
app_permissions
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── role            (enum: app_admin, app_user)
├── UNIQUE(user_id, application_id)
```

#### AppAccessRequest

```text
app_access_requests
├── id              (UUID, PK)
├── user_id         (FK → users, CASCADE)
├── application_id  (FK → applications, CASCADE)
├── message         (string, nullable)
├── status          (string: pending, approved, rejected)
├── requested_at, resolved_at, resolved_by
```

### Relationships

```text
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

```text
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
Per-role credentials for AgentRunner stored in `secrets/api_keys.env`.

### How Agent Controls DataServer

```text
Agent (NanoClaw / Chrome Extension) → REST call (create/modify/delete node)
         → DataServer persists to SQLite
         → DataServer emits SSE event (node_modified)
         → Extension SW receives SSE → updates cache
         → Sidepanel UI re-renders with new data
```

---

## ColliderGraphToolServer (:8001)

**Path**: `ColliderGraphToolServer/`
**Stack**: FastAPI + WebSocket + gRPC + MCP/SSE

### Endpoints

| Transport | Endpoint                 | Purpose                                           |
| --------- | ------------------------ | ------------------------------------------------- |
| WebSocket | `/ws/workflow`           | Execute multi-step agent workflows (streamed)     |
| WebSocket | `/ws/graph`              | Graph operations (create/modify nodes)            |
| REST      | `/api/v1/registry/tools` | Register / list / delete tools                    |
| gRPC      | `:50052`                 | `ExecuteSubgraph`, `ExecuteTool`, `DiscoverTools` |
| MCP/SSE   | `/mcp/sse`               | SSE stream — AI client connects here              |
| MCP/SSE   | `/mcp/messages/`         | JSON-RPC POST body endpoint                       |
| REST      | `/health`                | Health + registry stats                           |

### MCP Integration

GraphToolServer is the authoritative **MCP server** for the Collider ecosystem.
Every `ToolDefinition` registered in the in-memory `ToolRegistry` with
`visibility: "group"` or `"global"` is exposed as a native MCP tool.

```bash
# Connect any MCP-compatible client (Claude Code, VS Code Copilot, Cursor…)
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

The `list_tools` handler queries the registry on every request (pull-based),
so tools registered after server start appear immediately.

### gRPC Service (`ColliderGraph`)

| RPC                     | Request / Response                               | Purpose                         |
| ----------------------- | ------------------------------------------------ | ------------------------------- |
| `RegisterTool`          | `RegisterToolRequest` → `RegisterToolResponse`   | Register a tool in the registry |
| `DiscoverTools`         | `ToolDiscoveryRequest` → `ToolDiscoveryResponse` | Semantic tool search            |
| `ExecuteSubgraph`       | `SubgraphRequest` → `SubgraphResponse`           | Run a workflow by name          |
| `ExecuteSubgraphStream` | `SubgraphRequest` → `stream SubgraphProgress`    | Streaming workflow execution    |
| `ExecuteTool`           | `ToolExecutionRequest` → `ToolExecutionResponse` | Execute a single tool by name   |

### Workflow Execution Flow

```text
Agent submits workflow via WebSocket / gRPC
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
**Stack**: gRPC + ChromaDB

### gRPC Service

| RPC           | Method | Purpose                    |
| ------------- | ------ | -------------------------- |
| `IndexTool`   | Unary  | Index tool into ChromaDB   |
| `SearchTools` | Unary  | Semantic similarity search |

Also exposes REST fallback endpoints:

| Endpoint         | Method | Purpose                       |
| ---------------- | ------ | ----------------------------- |
| `/api/v1/search` | POST   | Semantic similarity search    |
| `/api/v1/embed`  | POST   | Generate embeddings for text  |
| `/api/v1/index`  | POST   | Index documents into ChromaDB |

Documents are indexed from NodeContainer `knowledge` and `tools` fields. Used by agents for semantic tool discovery (`TOOL_SEARCH` message type).

---

## ColliderAgentRunner (:8004)

**Path**: `ColliderAgentRunner/`
**Stack**: FastAPI + pydantic-ai + httpx
**Model**: configurable via `COLLIDER_AGENT_PROVIDER` — default `gemini-2.5-flash` (Gemini) or `claude-sonnet-4-6` (Anthropic/Vertex)
**Config**: `D:/FFS0_Factory/secrets/api_keys.env`

### AgentRunner API

| Endpoint              | Method | Purpose                                                |
| --------------------- | ------ | ------------------------------------------------------ |
| `/health`             | GET    | Liveness probe                                         |
| `/agent/session`      | POST   | Compose ContextSet → cache session → return session_id |
| `/agent/root/session` | POST   | Auto-compose from app root_node_id → root orchestrator |
| `/agent/chat`         | GET    | SSE stream: LLM response (works for all session types) |
| `/tools/discover`     | GET    | Proxy to GraphToolServer tool discovery                |

### ContextSet (`POST /agent/session`)

```python
class ContextSet(BaseModel):
    role: Literal["superadmin", "collider_admin", "app_admin", "app_user"]
    app_id: str                        # ACL boundary
    node_ids: list[str]                # nodes to compose (leaf-wins merge)
    vector_query: str | None = None    # semantic tool discovery
    visibility_filter: list[Literal["local", "group", "global"]] = ["global", "group"]
    depth: int | None = None           # bootstrap depth per node (None = full subtree)
    inherit_ancestors: bool = False    # prepend ancestor contexts root-first
```

Compose flow:

1. `get_token_for_role(ctx.role)` — per-role JWT cache, falls back to default credentials
2. If `inherit_ancestors`: fetch ancestor chain via `GET /api/v1/apps/{app_id}/nodes/{id}/ancestors`, bootstrap each (depth=0) root-first
3. `get_bootstrap(node_id, token, depth)` for each `node_id` (agent bootstrap endpoint)
4. Merge: agents_md/soul_md/tools_md concatenated with node-path headers; skills + tool_schemas by name dict (leaf-wins: later node_id wins)
5. If `vector_query`: `POST /api/v1/registry/tools/discover` on GraphToolServer → extend tool map (add only, don't override bootstrap tools)
6. Build system prompt → `SessionStore.create()` → return `session_id`

### Root Agent (`POST /agent/root/session`)

Auto-composes the full application context:

1. Fetches `Application.root_node_id` from DataServer
2. Calls `compose_context_set()` with `role="superadmin"`, full subtree depth
3. Injects a built-in `spawn_subagent` tool — delegates sub-tasks to child-node context agents
4. Caches with 24h TTL (vs 4h for regular sessions)

### Multi-Provider Model Selection

`_build_model()` in `runner.py` selects the LLM based on `COLLIDER_AGENT_PROVIDER`:

| Provider        | Env var             | Default model       |
| --------------- | ------------------- | ------------------- |
| `gemini`        | `GEMINI_API_KEY`    | `gemini-2.5-flash`  |
| `anthropic`     | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| `google-vertex` | ADC (gcloud)        | `claude-sonnet-4-6` |

Override with `COLLIDER_AGENT_MODEL`. Uses `COLLIDER_AGENT_*` prefix to avoid collision with the FFS2 shared `AGENT_MODEL` env var.

### Session Cache

```python
class SessionStore:
    """In-memory: session_id → {system_prompt, tool_schemas, created_at}. TTL: 4h (24h for root)."""
```

### Per-Role Auth

```python
_ROLE_CREDENTIAL_MAP = {
    "superadmin":      ("collider_superadmin_username", "collider_superadmin_password"),
    "collider_admin":  ("collider_collider_admin_username", "collider_collider_admin_password"),
    "app_admin":       ("collider_app_admin_username", "collider_app_admin_password"),
    "app_user":        ("collider_app_user_username", "collider_app_user_password"),
}
```

Each role maps to optional env credentials in `secrets/api_keys.env`. Falls back to `COLLIDER_USERNAME`/`COLLIDER_PASSWORD`.

### AgentRunner Source Structure

```text
ColliderAgentRunner/
└── src/
    ├── main.py                  ← FastAPI app + routes
    ├── api/
    │   └── root.py              ← POST /agent/root/session (root orchestrator)
    ├── schemas/
    │   └── context_set.py       ← ContextSet, SessionPreview, SessionResponse
    ├── core/
    │   ├── config.py            ← Settings (COLLIDER_AGENT_PROVIDER, COLLIDER_AGENT_MODEL, ...)
    │   ├── auth_client.py       ← Per-role JWT cache + login
    │   ├── collider_client.py   ← GET /agent/bootstrap, GET ancestors, POST /execution/tool
    │   ├── graph_tool_client.py ← POST /registry/tools/discover (vector proxy)
    │   └── session_store.py     ← In-memory session cache (4h / 24h TTL)
    └── agent/
        ├── runner.py            ← _build_model(), compose_context_set(), run_session_stream()
        └── tools.py             ← build_tools() → pydantic-ai Tool wrappers
```

### SDK Tool Pipeline

Tools registered in `NodeContainer.tools` flow through:

```text
.agent/tools/*.json  →  sdk/seeder (agent_walker reads, node_upserter registers)
    ↓
ColliderDataServer (NodeContainer stored in DB)
    ↓
ColliderGraphToolServer /api/v1/registry/tools  (in-memory ToolRegistry)
    ↓
ToolRunner.execute() → importlib.import_module(code_ref) → actual Python function
    ↑
sdk/tools/collider_tools/ (nodes.py, apps.py, permissions.py, agent_bootstrap.py, graph.py)
```

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

```text
Layer 3: ADMIN Context     ← Secrets, global permissions (user.container)
Layer 2: APP Context       ← App-specific rules, API config (application.config)
Layer 1: NODE Context      ← Node-specific tools, instructions (node.container)
Layer 0: Base Agent        ← General capabilities (built-in)
```

Higher layers override lower layers.
