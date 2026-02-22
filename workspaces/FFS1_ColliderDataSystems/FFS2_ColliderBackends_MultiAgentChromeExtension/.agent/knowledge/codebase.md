# Codebase: FFS2 ColliderBackends

> Backend services, Chrome Extension, NanoClaw skill, and SDK source.

## Structure

```
FFS2_ColliderBackends/
├── ColliderDataServer/              <- FastAPI :8000 REST + SSE + NanoClaw bootstrap
│   ├── src/
│   │   ├── main.py                  <- App entrypoint, router registration
│   │   ├── api/
│   │   │   ├── auth.py              <- Login, JWT, role deps
│   │   │   ├── users.py             <- User CRUD
│   │   │   ├── apps.py              <- Application CRUD
│   │   │   ├── nodes.py             <- Node CRUD (tree operations)
│   │   │   ├── roles.py             <- System role assignment (SAD/CAD)
│   │   │   ├── app_permissions.py   <- Request/approve/reject access
│   │   │   ├── permissions.py       <- Per-app permission checks
│   │   │   ├── context.py           <- Context hydration
│   │   │   ├── agent_bootstrap.py          <- NanoClaw bootstrap endpoint
│   │   │   ├── execution.py         <- Tool/workflow execution proxy
│   │   │   ├── templates.py         <- Node templates
│   │   │   ├── sse.py               <- Server-Sent Events
│   │   │   ├── rtc.py               <- WebRTC signaling WebSocket
│   │   │   └── health.py            <- Health check endpoint
│   │   ├── core/
│   │   │   ├── auth.py              <- JWT utilities
│   │   │   ├── config.py            <- pydantic-settings
│   │   │   ├── database.py          <- SQLAlchemy async engine
│   │   │   ├── agent_bootstrap.py          <- Bootstrap render/merge logic
│   │   │   ├── grpc_client.py       <- gRPC client to GraphToolServer
│   │   │   ├── boundary.py          <- Context boundary helpers
│   │   │   └── templates.py         <- Template logic
│   │   ├── db/
│   │   │   └── models.py            <- SQLAlchemy models
│   │   ├── schemas/
│   │   │   ├── users.py             <- User DTOs
│   │   │   ├── apps.py              <- Application DTOs
│   │   │   ├── nodes.py             <- Node/Permission DTOs
│   │   │   ├── agent_bootstrap.py          <- AgentBootstrap, SkillEntry, ToolSchema
│   │   │   └── templates.py         <- Template DTOs
│   │   └── seed.py                  <- x1z tree seeder
│   └── collider.db                  <- SQLite database (dev)
│
├── ColliderGraphToolServer/         <- Tool registry + gRPC + MCP :8001
│   ├── src/
│   │   ├── main.py                  <- FastAPI app + gRPC server startup
│   │   ├── handlers/
│   │   │   ├── registry_api.py      <- REST /api/v1/registry/tools
│   │   │   ├── mcp_handler.py       <- MCP/SSE endpoints (/mcp/sse, /mcp/messages/)
│   │   │   ├── grpc_servicer.py     <- ColliderGraph gRPC service (:50052)
│   │   │   ├── workflow.py          <- WS /ws/workflow handler
│   │   │   └── graph.py             <- WS /ws/graph handler
│   │   ├── core/
│   │   │   ├── tool_registry.py     <- In-memory tool + workflow registry
│   │   │   ├── execution.py         <- ToolRunner — importlib exec of code_ref
│   │   │   ├── vector_client.py     <- gRPC client to VectorDbServer (:8002)
│   │   │   ├── model_factory.py     <- Dynamic Pydantic model from params_schema
│   │   │   └── config.py            <- Settings
│   │   ├── schemas/
│   │   │   └── registry.py          <- Tool/workflow registry DTOs
│   │   └── tools/
│   │       └── collider_management.py <- Built-in management tool wrappers
│
├── ColliderVectorDbServer/          <- gRPC :8002 ChromaDB semantic search
│   └── src/
│       ├── main.py                  <- Async gRPC server startup
│       ├── handlers/
│       │   └── grpc_servicer.py     <- IndexTool, SearchTools RPCs
│       ├── core/
│       │   ├── config.py            <- Settings
│       │   └── vector_store.py      <- Persistent vector store
│       ├── embeddings/
│       │   └── generator.py         <- Embedding generation
│       └── search/
│           └── engine.py            <- FAISS + ChromaDB semantic search
│
├── ColliderAgentRunner/             <- Context composer :8004
│   └── src/
│       ├── main.py                  <- FastAPI app + session/chat routes
│       ├── api/
│       │   └── root.py              <- POST /agent/root/session
│       ├── agent/
│       │   └── runner.py            <- compose_context_set(), _build_model()
│       ├── core/
│       │   ├── config.py            <- Settings (COLLIDER_AGENT_PROVIDER, MODEL)
│       │   ├── auth_client.py       <- Per-role JWT cache + login
│       │   ├── collider_client.py   <- HTTP client to DataServer (bootstrap, ancestors)
│       │   ├── graph_tool_client.py <- HTTP client to GraphToolServer (discover)
│       │   ├── session_store.py     <- In-memory session cache (4h / 24h TTL)
│       │   └── workspace_writer.py  <- Write CLAUDE.md + .mcp.json, skills/
│       └── schemas/
│           └── context_set.py       <- ContextSet, SessionPreview, SessionResponse
│
├── ColliderMultiAgentsChromeExtension/ <- Plasmo MV3 Extension
│   └── src/
│       ├── background/
│       │   ├── index.ts             <- SW entry: init, message routing
│       │   ├── context-manager.ts   <- ContextManager state machine
│       │   ├── agents/
│       │   │   ├── cloud-agent.ts   <- CLOUD domain agent
│       │   │   ├── dom-agent.ts     <- DOM interaction agent
│       │   │   └── filesyst-agent.ts <- FILESYST domain agent
│       │   └── external/
│       │       ├── data-server.ts   <- HTTP client to :8000
│       │       ├── graphtool.ts     <- HTTP client to :8001
│       │       └── vectordb.ts      <- Client to :8002
│       ├── sidepanel/
│       │   ├── index.tsx            <- Sidepanel entry (3-tab layout)
│       │   ├── components/
│       │   │   ├── WorkspaceBrowser.tsx <- Compose tab: role + node multi-select + vector query
│       │   │   ├── AgentSeat.tsx       <- Chat tab: NanoClaw WebSocket
│       │   │   ├── RootAgentPanel.tsx  <- Root agent tab: auto-compose from root_node_id
│       │   │   └── AppTree.tsx         <- App/node tree widget
│       │   ├── lib/
│       │   │   └── nanoclaw-rpc.ts  <- WebSocket RPC client to :18789
│       │   └── stores/
│       │       └── appStore.ts      <- Zustand store (sessions, apps, nodes)
│       ├── contents/
│       │   └── index.ts             <- Content script (page-level)
│       ├── popup/
│       │   └── index.tsx            <- Extension popup UI
│       ├── types/
│       │   └── index.ts             <- TypeScript type defs
│       └── style.css
│
├── NanoClawBridge/skills/         <- NanoClaw skill definition
│   ├── skills/
│   │   └── collider-mcp/
│   │       └── SKILL.md             <- gRPC tool execution protocol + 15 tools
│   ├── nanoclaw.example.json5       <- Example NanoClaw config
│   └── README.md                    <- Setup instructions
│
├── proto/                           <- gRPC proto definitions + generated stubs
│   ├── collider_graph.proto         <- ExecuteTool, ExecuteSubgraph, DiscoverTools
│   ├── collider_data.proto          <- Data sync, schema registration
│   ├── collider_vectordb.proto      <- IndexTool, SearchTools
│   ├── compile_protos.py            <- Proto compilation script
│   └── *_pb2.py, *_pb2_grpc.py     <- Generated Python stubs
│
└── sdk/ (at repo root D:\FFS0_Factory\sdk\)
    └── seeder/                      <- .agent/ filesystem → DB node sync
        ├── cli.py                   <- Click CLI (--root, --app-id, --data-server-url)
        ├── agent_walker.py          <- Discovers .agent/ dirs, parses manifest/tools
        └── node_upserter.py         <- Async API calls to DataServer for upsert
```

> **Note**: `sdk/tools/collider_tools/` is referenced in CLAUDE.md but does not yet exist
> on disk. Tool `code_ref` paths (e.g. `sdk.tools.collider_tools.nodes:create_node`) are
> defined in `.agent/tools/*.json` and registered in GraphToolServer, but the backing Python
> modules are pending implementation.

## Database Models

### Core Enums

- **SystemRole**: `superadmin`, `collider_admin`, `app_admin`, `app_user`
- **AppRole**: `app_admin`, `app_user`

### Tables

- **users**: `id`, `username`, `password_hash`, `display_name`, `system_role`
- **applications**: `id`, `app_id`, `owner_id` (FK users), `display_name`, `config` (JSON), `root_node_id`
- **nodes**: `id`, `application_id`, `parent_id` (self-ref), `path`, `container` (JSON), `metadata_` (JSON)
- **app_permissions**: `id`, `user_id`, `application_id`, `role` (AppRole enum)
- **app_access_requests**: `id`, `user_id`, `application_id`, `message`, `status`, `requested_at`, `resolved_at`, `resolved_by`

### x1z Seed Tree

Application x1z is seeded with 4 nodes:

- `/` — root (frontend_app: x1z, frontend_route: /)
- `/admin` — admin panel (frontend_app: x1z, frontend_route: /admin)
- `/admin/assign-roles` — role assignment (frontend_app: x1z, frontend_route: /admin/roles)
- `/admin/grant-permission` — permission management (frontend_app: x1z, frontend_route: /admin/permissions)

## Key Data Flows

### ContextSet Session

```text
Chrome ext WorkspaceBrowser
  → POST :8004/agent/session (role, node_ids, vector_query, inherit_ancestors)
  → AgentRunner: bootstrap nodes via DataServer NanoClaw
  → merge contexts (leaf-wins), vector-augment tools
  → write workspace files → ~/.nanoclaw/workspaces/collider/
  → return session_id + nanoclaw_ws_url
  → Chrome ext AgentSeat connects WebSocket → NanoClawBridge :18789
```

### Tool Execution

```text
NanoClaw agent invokes tool
  → gRPC :50052 ExecuteTool({name, params})
  → GraphToolServer ToolRunner.execute()
  → importlib → code_ref Python function
  → result returned to agent
```

## Developer Guide

### Running Services

```bash
# DataServer
cd ColliderDataServer && uv run uvicorn src.main:app --reload --port 8000

# GraphToolServer
cd ColliderGraphToolServer && uv run uvicorn src.main:app --reload --port 8001

# AgentRunner
cd ColliderAgentRunner && uv run uvicorn src.main:app --reload --port 8004

# NanoClawBridge (after configuring ~/.nanoclaw/nanoclaw.json)
nanoclaw start
```

Seed the database:

```bash
cd ColliderDataServer && uv run python -m src.seed
```

### Chrome Extension Development

1. `cd ColliderMultiAgentsChromeExtension`
2. `pnpm dev`
3. Load `build/chrome-mv3-dev` in `chrome://extensions`

### Key Patterns

- **NanoClaw sessions**: WorkspaceBrowser composes a ContextSet → AgentRunner writes workspace files → NanoClawBridge reads them and runs the agent.
- **SSE**: Data updates flow via Server-Sent Events from `DataServer/api/v1/sse`.
- **gRPC**: Tool execution flows `DataServer → gRPC → GraphToolServer → ToolRunner`.
- **MCP**: IDE clients connect at `GET :8001/mcp/sse` for tool access.
- **Auth**: Username/password login returns JWT. Per-role credentials in `secrets/api_keys.env`.
