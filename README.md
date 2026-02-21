# Collider — FFS0 Factory

> A self-hosted multi-agent AI workspace platform. Each workspace node carries its own tools, instructions, rules, and skills — forming a recursive context tree that any AI agent can bootstrap from.

---

## MVP State — z440 Workstation

The OpenClaw agent is live. From the Chrome extension sidepanel you can:

1. Select an application and pick a **role** (superadmin / collider_admin / app_admin / app_user)
2. Check one or more **workspace nodes** from the tree
3. Type a natural-language task description to **discover tools** semantically via vector search
4. Hit **Compose & Start Session** — the AgentRunner merges all node contexts into a single system prompt, caches it as a session, and returns a `session_id`
5. Chat with the agent in the panel below — it streams responses via SSE, has access to all tools from the composed nodes, and knows its Collider role and ACL context

Services running locally:

| Service | Port | Purpose |
|---|---|---|
| ColliderDataServer | :8000 | REST + SSE + OpenClaw bootstrap |
| ColliderGraphToolServer | :8001 | Tool registry + gRPC + MCP |
| ColliderVectorDbServer | :8002 | ChromaDB semantic search |
| SQLite Web Viewer | :8003 | DB inspection (dev only) |
| **ColliderAgentRunner** | **:8004** | **pydantic-ai agent + ContextSet sessions** |
| FFS3 Frontend (ffs6) | :4200 | IDE appnode viewer |

---

## What Is This?

Collider is a platform for building and running AI-powered workspaces. The core idea: **every workspace is a node in a tree**, and every node carries a `NodeContainer` — a JSON manifest holding the tools, instructions, rules, knowledge, skills, and workflows that define what an AI agent can do in that context.

Four servers talk to each other. A Chrome extension bridges the browser to the backend. A React frontend renders whichever "appnode" the current workspace node points to. An AI model (Claude) bootstraps from any set of nodes in the tree, composes their contexts into a unified session, and streams responses via SSE.

---

## Architecture

```
FFS0_Factory/
├── workspaces/
│   └── FFS1_ColliderDataSystems/
│       ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
│       │   ├── ColliderDataServer/               ← Port 8000  (REST + SSE + OpenClaw)
│       │   ├── ColliderGraphToolServer/          ← Port 8001  (WebSocket + gRPC + MCP)
│       │   ├── ColliderVectorDbServer/           ← Port 8002  (ChromaDB semantic search)
│       │   ├── ColliderAgentRunner/              ← Port 8004  (pydantic-ai, ContextSet)
│       │   ├── proto/                            ← Shared protobuf definitions
│       │   └── ColliderMultiAgentsChromeExtension/  ← Plasmo, Manifest V3
│       └── FFS3_ColliderApplicationsFrontendServer/
│           ├── apps/ffs4/                        ← Sidepanel appnode  (port 4201)
│           ├── apps/ffs5/                        ← PiP appnode        (port 4202)
│           ├── apps/ffs6/                        ← IDE viewer appnode (port 4200)
│           └── libs/shared-ui/                  ← Shared components + XYFlow
└── models/                                      ← Shared Pydantic models
```

---

## The Services

### ColliderDataServer — :8000

The primary API server. Owns authentication, the node tree, and real-time event broadcasting.

| What it does | How |
|---|---|
| User auth (login → JWT) | `POST /api/v1/auth/login` |
| Application and node CRUD | `GET/POST/PUT/DELETE /api/v1/nodes` |
| Real-time node change events | `GET /api/v1/sse` (Server-Sent Events) |
| OpenClaw agent bootstrap | `GET /api/v1/openclaw/bootstrap/{node_id}` |
| Tool execution (via gRPC passthrough) | `POST /execution/tool/{tool_name}` |
| Workflow execution (via gRPC passthrough) | `POST /execution/workflow/{workflow_name}` |
| WebRTC signaling | `WS /ws/rtc/` |

Storage: async SQLite via aiosqlite + SQLAlchemy.

### ColliderGraphToolServer — :8001

The tool registry and execution engine. Owns the in-memory tool registry, workflow executor, gRPC server, and the MCP server.

| Transport | Endpoint | Purpose |
|---|---|---|
| REST | `GET /health` | Health + registry stats |
| REST | `/api/v1/registry/tools` | Register / list / delete tools |
| REST | `POST /api/v1/registry/tools/discover` | Semantic tool discovery (proxies to VectorDb) |
| WebSocket | `/ws/workflow` | Stream multi-step workflow execution |
| WebSocket | `/ws/graph` | Graph node operations |
| gRPC | `:50051` | `ExecuteTool`, `ExecuteSubgraph`, `DiscoverTools` |
| **MCP/SSE** | `GET /mcp/sse` | AI client connects here (Claude Code, Copilot, Cursor) |
| MCP/SSE | `POST /mcp/messages/` | JSON-RPC request body endpoint |

Every tool registered with `visibility: "group"` or `"global"` is automatically exposed as a native MCP tool — no restart required.

### ColliderVectorDbServer — :8002

Semantic search over NodeContainer content using ChromaDB.

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/search` | Find tools / knowledge by similarity |
| `POST /api/v1/embed` | Generate text embeddings |
| `POST /api/v1/index` | Index NodeContainer documents |

### ColliderAgentRunner — :8004

The local pydantic-ai agent. Composes ContextSets from OpenClaw bootstrap data, caches sessions, and streams LLM responses to the Chrome extension sidepanel.

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness probe |
| `/agent/session` | POST | Compose a ContextSet → cache as session → return `session_id` |
| `/agent/chat` | GET | SSE stream: chat against a session (or single node, legacy) |
| `/tools/discover` | GET | Proxy to GraphToolServer discover (single CORS origin for ext) |

**ContextSet composition** (`POST /agent/session`):

1. Authenticate as the selected role (separate JWT per role, falls back to default)
2. Bootstrap each selected node via OpenClaw (`GET /openclaw/bootstrap/{id}`)
3. Merge all bootstraps — leaf-wins: later nodes override earlier for skills/tools
4. If `vector_query`: discover additional tools via GraphToolServer vector search
5. Build unified system prompt (agents_md + soul_md + tools_md + skill playbooks + session context)
6. Cache as session (4h TTL), return `session_id`

---

## The NodeContainer

Every node in the workspace tree holds a `NodeContainer`:

```yaml
kind: workspace          # workspace | tool | workflow | skill | template
instructions: [...]      # WHO — agent role definition (markdown strings)
rules: [...]             # WHAT constraints — code standards, access rules
knowledge: [...]         # REFERENCE — docs, architecture notes
tools: [...]             # ToolDefinition list (code_ref, params_schema, visibility)
skills: [...]            # SkillDefinition list (SKILL.md playbooks for agents)
workflows: [...]         # WorkflowDefinition list (multi-step execution graphs)
```

When an agent bootstraps from a node, it receives the full aggregated context of that node **plus all its descendants** — skills, tools, and instructions merged from root to leaf. Leaf entries win (more-specific context overrides parent context).

---

## OpenClaw Integration

Collider exposes an OpenClaw-compatible bootstrap endpoint:

```bash
GET /api/v1/openclaw/bootstrap/{node_id}?depth=3
Authorization: Bearer <jwt>
```

The response gives an OpenClaw agent its:
- `agents_md` — system prompt context
- `soul_md` — constraints and rules
- `tools_md` — knowledge and reference docs
- `skills[]` — SKILL.md playbooks to inject into the agent's context
- `tool_schemas[]` — JSON function definitions for direct tool invocation
- `execute_tool_schema` — schema for `POST /execution/tool/{name}`

The **ColliderAgentRunner** uses this endpoint to bootstrap multi-node sessions:
it fetches each selected node's context, merges them (leaf-wins), augments with
vector-discovered tools, and builds a single system prompt for the pydantic-ai `Agent`.

---

## MCP Integration

Collider GraphToolServer is a native **Model Context Protocol** server. Connect any MCP-compatible client once the server is running:

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

After connecting, every registered group/global tool appears as a native tool in Claude Code, VS Code Copilot, Cursor, Zed, or any other MCP client. The tool list updates live — no restart needed when new tools are registered.

---

## Chrome Extension — WorkspaceBrowser

The ffs4 sidepanel hosts the **WorkspaceBrowser** — a two-panel UI:

```
┌─────────────────────────────────┐
│ ▼ Context Composer              │  collapsible
│   Role   [app_user          ▼]  │  pick identity level
│   Nodes  [☑ root  ☐ tools  …]  │  multi-select from tree
│   Search [describe your task…]  │
│           [Discover Tools   🔍] │  → GET :8004/tools/discover
│   Found  [3 tools matched]      │
│   [Compose & Start Session  →]  │  → POST :8004/agent/session
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ Agent Chat                      │  streaming SSE from :8004
│  [messages…]                    │
│  [input…           ]  [Send]    │
└─────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.12+ with [UV](https://docs.astral.sh/uv/)
- Node.js 20+ with [pnpm](https://pnpm.io/)
- Chrome (for the extension)
- Anthropic API key (for the AgentRunner LLM)

### 1 — Fill in secrets

Edit `D:\FFS0_Factory\secrets\api_keys.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
COLLIDER_USERNAME=your_seeded_user
COLLIDER_PASSWORD=your_password
```

Per-role credentials (optional — fall back to above if blank):

```bash
COLLIDER_SUPERADMIN_USERNAME=
COLLIDER_APP_USER_USERNAME=
# etc.
```

### 2 — Start all services

```powershell
# DataServer (REST + SSE + OpenClaw)
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run uvicorn src.main:app --reload --port 8000

# GraphToolServer (WebSocket + gRPC + MCP)
cd ..\ColliderGraphToolServer
uv run uvicorn src.main:app --reload --port 8001

# VectorDbServer (ChromaDB)
cd ..\ColliderVectorDbServer
uv run python -m src.main

# AgentRunner (pydantic-ai + ContextSet sessions)
cd ..\ColliderAgentRunner
uv run uvicorn src.main:app --reload --port 8004

# Frontend — ffs6 IDE viewer
cd ..\..\FFS3_ColliderApplicationsFrontendServer
pnpm nx serve ffs6

# SQLite Viewer (optional, dev only)
cd ..\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run sqlite_web collider.db -p 8003 -H 0.0.0.0
```

### 3 — Seed the database

```powershell
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run python seed.py
```

### 4 — Connect Claude Code to the MCP server

```powershell
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

### 5 — Load the Chrome extension

Load `ColliderMultiAgentsChromeExtension` as an unpacked extension in Chrome developer mode. Open the sidepanel, select an application, switch to **Agent** view.

### API docs (when running)

- DataServer: <http://localhost:8000/docs>
- GraphToolServer: <http://localhost:8001/docs>
- VectorDbServer: <http://localhost:8002/docs>
- AgentRunner: <http://localhost:8004/docs>
- SQL Viewer: <http://localhost:8003>

See [dev-start.md](workspaces/FFS1_ColliderDataSystems/.agent/workflows/dev-start.md) for the full ordered startup workflow.

---

## Tech Stack

| Layer | Stack |
|---|---|
| Python backends | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy async, aiosqlite |
| Agent | pydantic-ai, AnthropicModel (claude-sonnet-4-6) |
| Execution engine | gRPC (protobuf), MCP (SSE transport) |
| Vector search | ChromaDB |
| Chrome extension | Plasmo, Manifest V3, React + TypeScript |
| Frontend | Nx, Vite 7, React 19, TypeScript 5+, XYFlow, Zustand |
| Tooling | UV (Python), pnpm (Node), Ruff, Mypy, Vitest, Pytest |

---

## Protocols

| Protocol | Transport | Used Between |
|---|---|---|
| REST | HTTP | Extension / agents ↔ DataServer, AgentRunner |
| SSE | HTTP long-lived | DataServer → Extension (live events); AgentRunner → Extension (chat stream) |
| WebSocket | WS | Extension ↔ GraphToolServer (workflow streaming) |
| WebRTC | P2P (STUN/TURN) | Browser ↔ Browser (ffs5 PiP) |
| Native Messaging | stdio | Extension ↔ local filesystem host |
| gRPC | HTTP/2 | DataServer ↔ GraphToolServer; VectorDbServer ↔ GraphToolServer |
| MCP/SSE | HTTP SSE + POST | Claude Code / Copilot / Cursor ↔ GraphToolServer |

---

## Security

- JWT authentication on all DataServer endpoints
- System roles: `superadmin` → `collider_admin` → `app_admin` → `app_user`
- Per-role pre-seeded accounts used by AgentRunner; each role gets its own JWT cache
- Per-application permissions (request / approve / revoke)
- MCP tool visibility: only `group` and `global` tools exposed — `local` tools remain owner-private
- Secrets injected at runtime by the tool executor — the agent never sees raw values

---

## Workspace Context System

Every workspace directory has an `.agent/` folder:

```
.agent/
├── index.md          ← workspace identity and purpose
├── manifest.yaml     ← inheritance rules (which parent to merge from)
├── instructions/     ← WHO the agent is (role definitions)
├── rules/            ← WHAT constraints apply (code standards, policies)
├── skills/           ← HOW to do complex tasks (SKILL.md playbooks)
├── tools/            ← atomic action definitions
├── workflows/        ← multi-step sequences (e.g. dev-start.md)
├── configs/          ← environment-specific settings
└── knowledge/        ← reference docs and architecture
```

Context is inherited top-down: `FFS0 → FFS1 → FFS2 / FFS3`. Child workspaces extend and override parent context using `deep_merge`.

---

## Repository Layout

```
FFS0_Factory/
├── CLAUDE.md               ← Claude Code project context
├── GEMINI.md               ← Gemini CLI / Antigravity context
├── .mcp.json               ← Claude Code project-level MCP config
├── .vscode/
│   ├── mcp.json            ← VS Code Copilot MCP config
│   └── settings.json       ← Editor defaults + Copilot enable
├── .agent/                 ← Root agent context (exported to all workspaces)
├── models/                 ← Shared Pydantic models
├── sdk/                    ← SDK components
└── workspaces/
    ├── FFS1_ColliderDataSystems/
    │   ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
    │   └── FFS3_ColliderApplicationsFrontendServer/
    └── maassen_hochrath/   ← Personal AI workspace (Ollama)
```
