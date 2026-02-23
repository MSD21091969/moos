# Copilot Instructions — FFS0 Factory (Collider Ecosystem)

## Project Overview

Monorepo at `D:\FFS0_Factory` for the **Collider** multi-agent AI workspace platform — an
"Antigravity" code-assist system that combines a Chrome extension sidepanel,
four Python FastAPI services, and a React frontend. The active LLM provider is
**Gemini 2.5 Flash**.

Each workspace node carries a `NodeContainer` JSON — tools, instructions, rules, skills, and
workflows that define what an AI agent can do in that context. The **Root
Agent** has 15 live Collider tools and DOM capabilities via Chrome extension
content scripts.

Full architecture: `.agent/knowledge/architecture/` in `FFS1_ColliderDataSystems/`.

---

## Workspace Structure

```text
FFS0_Factory/
├── CLAUDE.md               ← Claude Code context
├── GEMINI.md               ← Gemini CLI (Antigravity) context
├── README.md               ← Project documentation
├── .mcp.json               ← Claude Code project MCP config
├── .vscode/mcp.json        ← VS Code Copilot MCP config
├── .agent/                 ← Root context (rules, configs, knowledge)
├── sdk/
│   ├── seeder/             ← .agent/ filesystem → DB sync
│   └── tools/
│       └── collider_tools/ ← Atomic tool implementations
└── workspaces/
    ├── FFS1_ColliderDataSystems/
    │   ├── .agent/         ← Architecture docs, rules, dev workflows
    │   ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
    │   │   ├── ColliderDataServer/               ← :8000  REST + SSE + NanoClaw
    │   │   ├── ColliderGraphToolServer/          ← :8001  WebSocket + gRPC + MCP
    │   │   ├── ColliderVectorDbServer/           ← :8002  ChromaDB semantic search
    │   │   ├── ColliderAgentRunner/              ← :8004  pydantic-ai + Gemini
    │   │   ├── ColliderMultiAgentsChromeExtension/  ← Plasmo MV3, 3-tab sidepanel
    │   │   └── NanoClawBridge/skills/            ← bootstrap.sh (SSE watch mode)
    │   └── FFS3_ColliderApplicationsFrontendServer/
    │       ├── apps/ffs4/   ← Sidepanel appnode   (:4201)
    │       ├── apps/ffs5/   ← PiP appnode          (:4202)
    │       ├── apps/ffs6/   ← IDE viewer (default) (:4200)
    │       └── libs/shared-ui/
    └── maassen_hochrath/    ← Personal AI workspace (Ollama)
```

**Source code lives in:** `ColliderDataServer/src/`, `ColliderGraphToolServer/src/`,
`ColliderVectorDbServer/src/`, `ColliderAgentRunner/src/`, `sdk/seeder/`, `sdk/tools/`,
`apps/ffs*/src/`, `libs/*/src/`

---

## Servers

| Server | Port | Stack | Role |
| --- | --- | --- | --- |
| ColliderDataServer | 8000 | FastAPI + SQLAlchemy + aiosqlite | Auth, node CRUD, SSE, NanoClaw |
| ColliderGraphToolServer | 8001 | FastAPI + gRPC + MCP/SSE | Tool registry, execution, MCP server |
| ColliderVectorDbServer | 8002 | FastAPI + ChromaDB | Semantic search + embeddings |
| **ColliderAgentRunner** | **8004 / 50051** | **FastAPI + gRPC** | **Context composer, gRPC streaming** |
| **NanoClawBridge** | **18789** | **Node.js + Anthropic SDK + WS** | **SDK agent sessions, teams** |
| ffs4 (sidepanel) | 4201 | Nx + Vite 7 + React 19 + XYFlow | Graph workspace browser + agent chat |
| ffs6 (IDE viewer) | 4200 | Nx + Vite 7 + React 19 | Default frontend appnode |

**Secrets**: `D:\FFS0_Factory\secrets\api_keys.env`
(`COLLIDER_AGENT_PROVIDER=gemini`, `GEMINI_API_KEY`, `COLLIDER_USERNAME`, `COLLIDER_PASSWORD`)

**MCP endpoint** (connect Copilot, Claude Code, Gemini):

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
# .vscode/mcp.json already configures this for VS Code Copilot
```

---

## Tech Stack

### Python — FFS0 / FFS2 backends

- Python 3.12+, **UV** package manager (`uv run`, `uv add`)
- FastAPI (async), Pydantic v2, SQLAlchemy async, **aiosqlite** (SQLite, NOT Postgres)
- **pydantic-ai** (AgentRunner), ChromaDB (vector), gRPC (`grpcio`, `grpcio-tools`), MCP (`mcp>=1.0.0`)
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
- Three sidepanel tabs: WorkspaceBrowser, AgentSeat, RootAgentPanel

---

## Code Quality Rules

- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:` — one logical change per commit
- **Python**: Google docstrings on public endpoints, Ruff formatting, `# type: ignore` with explanation
- **TypeScript**: TSDoc on exported components, no `any` (use `unknown` or generics)
- **React**: Custom hooks for logic, `interface` for props (not `type`)
- **No** secret values in code — environment variables only

---

## Key Architectural Concepts

### NodeContainer (the workspace atom)

Every node in the DB carries a `NodeContainer` JSON:

```json
{
  "kind": "workspace",
  "instructions": ["...agent role..."],
  "rules":        ["...constraints..."],
  "knowledge":    ["...reference docs..."],
  "tools": [{
    "name": "create_node",
    "description": "...",
    "code_ref": "sdk.tools.collider_tools.nodes:create_node",
    "params_schema": {},
    "visibility": "global"
  }],
  "skills": [{"name": "...", "skill_md": "...", "tool_ref": "..."}],
  "workflows": []
}
```

### Agent Bootstrap

`GET /api/v1/agent/bootstrap/{node_id}?depth=N` returns the aggregated context
(agents_md, soul_md, tools_md, skills, tool_schemas) for a node and all its
descendants. Leaf entries win on name collision.

### ContextSet (session agent)

```json
POST :8004/agent/session
{
  "role": "superadmin",
  "app_id": "c57ab23a-4a57-4b28-a34c-9700320565ea",
  "node_ids": ["uuid-1", "uuid-2"],
  "vector_query": "find tools for data extraction",
  "visibility_filter": ["global", "group"],
  "inherit_ancestors": true
}
```

AgentRunner bootstraps each node, optionally prepends ancestor contexts (root-
first), merges (leaf-wins), augments with vector-discovered tools, writes
workspace files to
`~/.nanoclaw/workspaces/collider/`, and returns `session_id` + `nanoclaw_ws_url`.
Chat is handled by **NanoClawBridge** (WebSocket at `:18789`).

### Root Agent

`POST :8004/agent/root/session` — auto-composes from `Application.root_node_id`:

- Authenticates as `superadmin`
- Full subtree depth, writes to `~/.nanoclaw/workspaces/collider-root/`
- 15 Collider tools + Claude Code built-ins (file, exec, browser)
- 24h session TTL
- Returns `nanoclaw_ws_url` for direct WebSocket chat

### Multi-Provider LLM

`COLLIDER_AGENT_PROVIDER` in `secrets/api_keys.env`:

| Value | Auth | Default model |
| --- | --- | --- |
| `gemini` *(active)* | `GEMINI_API_KEY` | `gemini-2.5-flash` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| `google-vertex` | ADC (gcloud) | `claude-sonnet-4-6` |

### SDK Tool Pipeline

```text
.agent/tools/*.json  →  sdk/seeder (node_upserter)  →  DataServer nodes
                                                     →  GraphToolServer registry
                                                     →  ToolRunner.execute() via importlib
                                                     →  sdk/tools/collider_tools/*.py
```

### MCP Server

GraphToolServer is the MCP server. All `group`/`global` visibility tools are exposed at `:8001/mcp/sse`.
`.vscode/mcp.json` configures this for VS Code Copilot automatically.

---

## Data Flow

### Context Delivery (Dual Mode)

**Mode 1 — Filesystem (Legacy, `USE_SDK_AGENT=false`):**

```text
Chrome ext / FFS4
  → POST :8004/agent/session (role, node_ids, vector_query)
  → AgentRunner: bootstrap + merge + write CLAUDE.md + .mcp.json + skills/*.SKILL.md
  → NanoClawBridge spawns Claude CLI with workspace context
```

**Mode 2 — SDK + gRPC (Current, `USE_SDK_AGENT=true`, `USE_GRPC_CONTEXT=true`):**

```text
Chrome ext / FFS4
  → POST :8004/agent/session (role, node_ids, vector_query)
  → NanoClawBridge: gRPC GetBootstrap(:50051) → ContextChunks
  → Creates Anthropic SDK session → skills as JSON, tools via MCP SSE
  → SSE delta subscription for live context hot-reload
```

**Agent Teams:** Select multiple nodes → each node becomes a teammate with isolated context. Leader gets merged context. Communication via mailbox.

### Tool execution

```text
Agent invokes tool → POST :8000/execution/tool/{name}
  → DataServer → gRPC → GraphToolServer ExecuteTool RPC
  → ToolRunner.execute() → importlib → sdk/tools/collider_tools/*.py
  → result returned to agent → agent includes in response
```

### MCP (direct from IDE)

```text
VS Code Copilot / Claude Code → GET /mcp/sse → POST /mcp/messages/
  → ToolRunner.execute() → same Python functions
```

---

## What NOT to Do

- Do NOT look for source code in `FFS1/` root or `.agent/` folders — those are metadata
- Do NOT use `PostgreSQL` — the project uses **SQLite** via aiosqlite
- Do NOT use `Next.js` — FFS3 uses **Vite 7 + React 19** (no SSR)
- Do NOT use `npm` or `yarn` in FFS3 — use **pnpm**
- Do NOT use `AGENT_MODEL` env var for AgentRunner — use **`COLLIDER_AGENT_MODEL`**
  (FFS2 shared `.env` has `AGENT_MODEL=claude-sonnet-4-6` which would override)
- Do NOT commit `C:\Users\hp\.claude\` — Claude Code session state
- Do NOT commit `mailmind-ai-*.json` or `secrets/api_keys.env` — credentials
- Do NOT use port 8003 — reserved for SQLite Web Viewer (dev only)
- Only modify files under `D:\FFS0_Factory\`

---

## Dev Commands

```bash
# Start services (from their respective directories)
cd ColliderDataServer      && uv run uvicorn src.main:app --reload --port 8000
cd ColliderGraphToolServer && uv run uvicorn src.main:app --reload --port 8001
cd ColliderAgentRunner     && uv run uvicorn src.main:app --reload --port 8004

# Start NanoClawBridge (after configuring ~/.nanoclaw/nanoclaw.json)
cd NanoClawBridge && npm run dev

# Seed DB from .agent/ filesystem
uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id <uuid>

# Chrome extension (from ColliderMultiAgentsChromeExtension/)
pnpm plasmo dev

# Frontend
pnpm nx serve ffs6

# Connect MCP
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse

# Recompile protos
cd ColliderDataServer && uv run python -m proto.compile_protos
```

---

## App 2XZ (primary test app — z440)

- App ID: `c57ab23a-4a57-4b28-a34c-9700320565ea`
- Root node: `9848b323-5e65-4179-a1d6-5b99be9f8b87`
- Default creds: Sam / Sam (superadmin)
