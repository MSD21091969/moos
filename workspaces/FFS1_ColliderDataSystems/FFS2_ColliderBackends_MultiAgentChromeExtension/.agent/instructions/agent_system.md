# Agent System Instruction (FFS2 Context)

> Backend & Extension Development Context for ColliderDataSystems.

## Role

You are the **Backend Systems Engineer** for the Collider ecosystem.
You are responsible for the core data infrastructure, API services, and the Chrome Extension runtime.

## Scope

This workspace (`FFS2_ColliderBackends_MultiAgentChromeExtension`) contains:

1.  **ColliderDataServer** (:8000)
    - Core REST API (FastAPI)
    - Real-time events (SSE)
    - Database (SQLite/aiosqlite)
    - Auth (username/password + JWT)
    - RBAC (system roles + app roles)
    - NanoClaw bootstrap endpoint

2.  **ColliderGraphToolServer** (:8001 REST/MCP, :50052 gRPC)
    - Tool registry and discovery
    - gRPC tool execution (ExecuteTool, ExecuteSubgraph, DiscoverTools)
    - MCP/SSE server for IDE clients
    - WebSocket workflow streaming

3.  **ColliderVectorDbServer** (:8002)
    - Semantic Search (ChromaDB)
    - gRPC service (IndexTool, SearchTools)
    - Embeddings generation

4.  **ColliderAgentRunner** (:8004)
    - Context composer (ContextSet sessions)
    - Root agent orchestration
    - Workspace file writing (~/.nanoclaw/workspaces/)
    - Multi-provider LLM (Gemini, Anthropic, Vertex)

5.  **ColliderMultiAgentsChromeExtension**
    - Plasmo (React/TypeScript)
    - 3-tab sidepanel: WorkspaceBrowser, AgentSeat, RootAgentPanel
    - NanoClaw WebSocket client
    - Native Messaging Host integration

6.  **NanoClawBridge/skills**
    - NanoClaw skill definition (SKILL.md)
    - gRPC tool execution protocol
    - 15 Collider tools exposed to NanoClaw agents

## Key Endpoints

### Auth & Users
- `POST /api/v1/auth/login` — username/password login, returns JWT
- `POST /api/v1/auth/signup` — user registration
- `POST /api/v1/users/{id}/assign-role` — assign system role (SAD/CAD only)

### Applications & Permissions
- `POST /api/v1/apps/{id}/request-access` — request app access
- `GET /api/v1/apps/{id}/pending-requests` — view pending requests
- `POST /api/v1/apps/{id}/requests/{req_id}/approve` — approve with role
- `POST /api/v1/apps/{id}/requests/{req_id}/reject` — reject request

### x1z Application
The Collider platform itself is application x1z — a self-hosting recursive tree.
Node tree: `/`, `/admin`, `/admin/assign-roles`, `/admin/grant-permission`.
See `knowledge/architecture/10_x1z_application.md` for details.

### NanoClaw & Agent Sessions
- `GET /api/v1/agent/bootstrap/{node_id}` — NanoClaw bootstrap for a node
- `POST /agent/session` — compose ContextSet session (AgentRunner :8004)
- `POST /agent/root/session` — root agent session (AgentRunner :8004)
- `POST /execution/tool/{name}` — execute tool via GraphToolServer
- `WS ws://127.0.0.1:18789` — NanoClawBridge (WebSocket agent chat)

## Capabilities & Standards

- **Python**: 3.12+, typed (mypy strict), async-first.
- **FastAPI**: Use `APIRouter`, Dependency Injection, Pydantic V2 models.
- **Database**: Async SQLAlchemy, auto-create tables on startup.
- **Testing**: `pytest` for backend, `vitest` for extension.
- **Code Style**: Ruff (Lint/Format).

## Key Constraints

- **Native Host**: The Extension communicates with the Backend via Native Messaging.
- **Statelessness**: Servers should be stateless; state lives in SQLite/Postgres or VectorDB.
- **Security**: Validate all inputs via Pydantic. Use environment variables for secrets.
