# Copilot Instructions — FFS0 Factory (Collider Ecosystem)

## Project Overview

Monorepo at `D:\FFS0_Factory` for the **Collider** multi-agent AI workspace platform.

Four Python FastAPI services + a Chrome extension + a React frontend. Each workspace node carries a `NodeContainer` — a JSON manifest holding the tools, instructions, rules, skills, and workflows that define what an AI agent can do in that context.

**MVP state**: The OpenClaw agent (`ColliderAgentRunner`) is operational. The Chrome extension sidepanel hosts a **WorkspaceBrowser** — users compose a ContextSet (role + nodes + vector query), the AgentRunner bootstraps context via OpenClaw and streams LLM responses (claude-sonnet-4-6) via SSE.

Full architecture docs: `.agent/knowledge/architecture/` in `FFS1_ColliderDataSystems/`.

---

## Workspace Structure

```
FFS0_Factory/
├── CLAUDE.md               ← Claude Code context
├── GEMINI.md               ← Gemini CLI context
├── .mcp.json               ← Claude Code project MCP config
├── .vscode/mcp.json        ← VS Code Copilot MCP config
├── .agent/                 ← Root context (rules, configs, knowledge)
├── models/                 ← Shared Pydantic models
└── workspaces/
    ├── FFS1_ColliderDataSystems/
    │   ├── .agent/         ← Architecture docs, rules, dev workflows
    │   ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
    │   │   ├── ColliderDataServer/               ← :8000  REST + SSE + OpenClaw
    │   │   ├── ColliderGraphToolServer/          ← :8001  WebSocket + gRPC + MCP
    │   │   ├── ColliderVectorDbServer/           ← :8002  ChromaDB semantic search
    │   │   ├── ColliderAgentRunner/              ← :8004  pydantic-ai, ContextSet
    │   │   ├── proto/                            ← Protobuf definitions + stubs
    │   │   └── ColliderMultiAgentsChromeExtension/  ← Plasmo MV3, WorkspaceBrowser
    │   └── FFS3_ColliderApplicationsFrontendServer/
    │       ├── apps/ffs4/   ← Sidepanel appnode   (:4201)
    │       ├── apps/ffs5/   ← PiP appnode          (:4202)
    │       ├── apps/ffs6/   ← IDE viewer (default) (:4200)
    │       └── libs/shared-ui/
    └── maassen_hochrath/    ← Personal AI workspace (Ollama)
```

**Source code lives in:** `ColliderDataServer/src/`, `ColliderGraphToolServer/src/`, `ColliderVectorDbServer/src/`, `ColliderAgentRunner/src/`, `apps/ffs*/src/`, `libs/*/src/`

---

## Servers

| Server | Port | Stack | Role |
|---|---|---|---|
| ColliderDataServer | 8000 | FastAPI + SQLAlchemy + aiosqlite | Auth, node CRUD, SSE, OpenClaw bootstrap |
| ColliderGraphToolServer | 8001 | FastAPI + gRPC + MCP/SSE | Tool registry, workflow execution, MCP server |
| ColliderVectorDbServer | 8002 | FastAPI + ChromaDB | Semantic search + embeddings |
| **ColliderAgentRunner** | **8004** | **FastAPI + pydantic-ai** | **ContextSet sessions, LLM streaming** |
| ffs6 (IDE viewer) | 4200 | Nx + Vite 7 + React 19 | Default frontend appnode |

Secrets for AgentRunner: `D:\FFS0_Factory\secrets\api_keys.env`
(`ANTHROPIC_API_KEY`, `COLLIDER_USERNAME`, `COLLIDER_PASSWORD`, optional per-role credentials)

---

## Tech Stack

### Python — FFS0 / FFS2 backends

- Python 3.12+, **UV** package manager (`uv run`, `uv add`)
- FastAPI (async), Pydantic v2, SQLAlchemy async, **aiosqlite** (SQLite, not Postgres)
- **pydantic-ai** (AgentRunner), ChromaDB (vector store), gRPC (`grpcio`, `grpcio-tools`), MCP (`mcp>=1.0.0`)
- Linter: **Ruff**. Type checker: **Mypy strict**. Docstrings: Google-style.
- Testing: **Pytest** + `pytest-asyncio`. Target ≥80% coverage on core logic.

### TypeScript — FFS3 frontend

- **Nx** monorepo, **Vite 7**, **React 19**, TypeScript 5+
- XYFlow (`@xyflow/react`), Zustand, React Router, CSS Modules
- Package manager: **pnpm** (`pnpm nx serve ffs6`)
- Testing: **Vitest**. Linter: ESLint. `strict: true`.

### Chrome Extension — FFS2

- **Plasmo** framework, Manifest V3
- React + TypeScript, Zustand (`appStore`)
- Key component: `WorkspaceBrowser.tsx` — Context Composer + AgentSeat chat

---

## Code Quality Rules

- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:` — one logical change per commit
- **Python**: Google docstrings on public endpoints, Ruff formatting
- **TypeScript**: TSDoc on exported components, no `any` (use `unknown` or generics)
- **React**: Custom hooks for logic, components for view. Props via `interface`, not `type`.
- **No** direct secret values in code — use environment variables

---

## Key Architectural Concepts

### NodeContainer (the workspace atom)

Every node in the DB carries a `NodeContainer` JSON:

```json
{
  "kind": "workspace",
  "instructions": ["...agent role..."],
  "rules": ["...constraints..."],
  "knowledge": ["...reference docs..."],
  "tools": [{ "name": "...", "code_ref": "module:fn", "params_schema": {} }],
  "skills": [{ "name": "...", "skill_md": "...", "tool_ref": "..." }],
  "workflows": [{ "name": "...", "steps": [] }]
}
```

### OpenClaw Bootstrap

`GET /api/v1/openclaw/bootstrap/{node_id}` returns the full aggregated context
(skills, tools, instructions) for a node and all its descendants. Leaf entries win.

### ContextSet (MVP pattern)

`POST :8004/agent/session` accepts:

```json
{
  "role": "app_user",
  "app_id": "my-app",
  "node_ids": ["uuid-1", "uuid-2"],
  "vector_query": "find tools for data extraction",
  "visibility_filter": ["global", "group"]
}
```

AgentRunner bootstraps each node, merges contexts (leaf-wins), augments with vector-discovered tools, builds a system prompt, caches as session (4h TTL), returns `session_id`.

Then `GET :8004/agent/chat?session_id=...&message=...` streams LLM responses via SSE.

### MCP Server

GraphToolServer is the MCP server. All `group`/`global` visibility tools are exposed:

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

### gRPC

DataServer ↔ GraphToolServer communicate via gRPC (`:50051`).
Proto files: `proto/collider_graph.proto`. Compiled stubs: `proto/*_pb2*.py`.
Recompile with: `python -m proto.compile_protos` (from within a server venv).

---

## Data Flow

### ContextSet (preferred — session-based)

```
Chrome ext WorkspaceBrowser
  → POST :8004/agent/session (role, node_ids, vector_query)
  → AgentRunner: bootstrap each node via OpenClaw
  → merge contexts, vector-augment tools
  → cache session → session_id
  → GET :8004/agent/chat?session_id=...&message=...
  → pydantic-ai Agent streams SSE deltas to extension
```

### Tool execution (via session agent)

```
Agent invokes tool → POST :8000/execution/tool/{name}
  → DataServer → gRPC → GraphToolServer ExecuteTool RPC
  → ToolRunner.execute() → result returned to agent
```

### MCP (direct)

```
MCP client → GET /mcp/sse → POST /mcp/messages/ → ToolRunner.execute()
```

---

## Important: What NOT to Do

- Do NOT look for source code in `FFS1/` root, `.agent/` folders, or `models/` — those are metadata/schemas
- Do NOT use `PostgreSQL` — the project uses **SQLite** via aiosqlite
- Do NOT use `Next.js` — FFS3 uses **Vite 7 + React 19** (no SSR, no App Router)
- Do NOT use `npm` or `yarn` in FFS3 — use **pnpm**
- Do NOT commit `C:\Users\hp\.claude\` — that is Claude Code session state
- Do NOT commit `mailmind-ai-*.json` or other credential files
- Do NOT use port 8003 for new services — reserved for SQLite Web Viewer (dev only)
- Only modify files under `D:\FFS0_Factory\`

---

## Dev Commands

```powershell
# Start AgentRunner (fill secrets/api_keys.env first)
cd ColliderAgentRunner && uv run uvicorn src.main:app --reload --port 8004

# Start DataServer
cd ColliderDataServer && uv run uvicorn src.main:app --reload --port 8000

# Start other Python servers
uv run uvicorn src.main:app --reload --port 8001   # GraphToolServer
uv run python -m src.main                           # VectorDbServer

# Frontend
pnpm nx serve ffs6

# Seed DB
cd ColliderDataServer && uv run python seed.py

# Recompile protos
cd ColliderDataServer && uv run python -m proto.compile_protos

# Connect MCP
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```
