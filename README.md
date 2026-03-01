# Collider — FFS0 Factory

> A self-hosted multi-agent AI workspace platform. Each workspace node carries
> its own tools, instructions, rules, and skills — forming a recursive context
> tree that any AI agent can bootstrap from.

---

## MVP State — z440 Workstation

The NanoClaw agent is live. From the Chrome extension sidepanel you can:

1. Select an application and pick a **role** (superadmin / collider_admin / app_admin / app_user)
2. Check one or more **workspace nodes** from the tree
3. Optionally enable **Include parent context** to inherit ancestor node contexts
4. Type a natural-language task description to **discover tools** semantically via vector search
5. Hit **Compose & Start Session** — the AgentRunner merges all node contexts into workspace files for NanoClaw
6. Chat with the agent via **NanoClawBridge** (WebSocket at :18789) — the extension connects directly

Services running locally:

| Service                 | Port       | Purpose                                |
| ----------------------- | ---------- | -------------------------------------- |
| ColliderDataServer      | :8000      | REST + SSE + NanoClaw bootstrap        |
| ColliderGraphToolServer | :8001      | Tool registry + gRPC + MCP             |
| ColliderVectorDbServer  | :8002      | ChromaDB semantic search               |
| **ColliderAgentRunner** | **:8004**  | **Context composer → workspace files** |
| **NanoClawBridge**      | **:18789** | **WebSocket chat**                     |
| FFS3 Frontend (ffs6)    | :4200      | IDE appnode viewer                     |

---

## What Is This?

Collider is a platform for building and running AI-powered workspaces. The core
idea: **every workspace is a node in a tree**, and every node carries a
`NodeContainer` — a JSON manifest holding the tools, instructions, rules,
knowledge, skills, and workflows that define what an AI agent can do in that
context.

Four servers talk to each other. A Chrome extension bridges the browser to the
backend. A React frontend renders whichever "appnode" the current workspace node
points to. An AI model (Claude) bootstraps from any set of nodes in the tree,
composes their contexts into a unified session, and streams responses via SSE.

---

## Architecture

```text
FFS0_Factory/
├── workspaces/
│   └── FFS1_ColliderDataSystems/
│       ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
│       │   ├── ColliderDataServer/               ← Port 8000  (REST + SSE + NanoClaw)
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

The primary API server. Owns authentication, the node tree, and real-time event
broadcasting.

| What it does                              | How                                        |
| ----------------------------------------- | ------------------------------------------ |
| User auth (login → JWT)                   | `POST /api/v1/auth/login`                  |
| Application and node CRUD                 | `GET/POST/PUT/DELETE /api/v1/nodes`        |
| Real-time node change events              | `GET /api/v1/sse` (Server-Sent Events)     |
| NanoClaw agent bootstrap                  | `GET /api/v1/agent/bootstrap/{node_id}`    |
| Tool execution (via gRPC passthrough)     | `POST /execution/tool/{tool_name}`         |
| Workflow execution (via gRPC passthrough) | `POST /execution/workflow/{workflow_name}` |
| WebRTC signaling                          | `WS /ws/rtc/`                              |

Storage: async SQLite via aiosqlite + SQLAlchemy.

### ColliderGraphToolServer — :8001

The tool registry and execution engine. Owns the in-memory tool registry,
workflow executor, gRPC server, and the MCP server.

| Transport   | Endpoint                               | Purpose                                                |
| ----------- | -------------------------------------- | ------------------------------------------------------ |
| REST        | `GET /health`                          | Health + registry stats                                |
| REST        | `/api/v1/registry/tools`               | Register / list / delete tools                         |
| REST        | `POST /api/v1/registry/tools/discover` | Semantic tool discovery (proxies to VectorDb)          |
| WebSocket   | `/ws/workflow`                         | Stream multi-step workflow execution                   |
| WebSocket   | `/ws/graph`                            | Graph node operations                                  |
| gRPC        | `:50052`                               | `ExecuteTool`, `ExecuteSubgraph`, `DiscoverTools`      |
| **MCP/SSE** | `GET /mcp/sse`                         | AI client connects here (Claude Code, Copilot, Cursor) |
| MCP/SSE     | `POST /mcp/messages/`                  | JSON-RPC request body endpoint                         |

Every tool registered with `visibility: "group"` or `"global"` is automatically exposed as a native MCP tool — no restart required.

### ColliderVectorDbServer — :8002

Semantic search over NodeContainer content using ChromaDB.

| Endpoint              | Purpose                              |
| --------------------- | ------------------------------------ |
| `POST /api/v1/search` | Find tools / knowledge by similarity |
| `POST /api/v1/embed`  | Generate text embeddings             |
| `POST /api/v1/index`  | Index NodeContainer documents        |

### ColliderAgentRunner — :8004

Context hydration service — composes Collider node bootstraps into NanoClaw
workspace files.
**Chat is handled by NanoClawBridge directly** (ws://127.0.0.1:18789).

| Endpoint              | Method | Purpose                                                                              |
| --------------------- | ------ | ------------------------------------------------------------------------------------ |
| `/health`             | GET    | Liveness probe                                                                       |
| `/agent/session`      | POST   | Compose ContextSet → write workspace files → return `session_id` + `nanoclaw_ws_url` |
| `/agent/root/session` | POST   | Auto-compose from app `root_node_id` → superadmin context                            |
| `/tools/discover`     | GET    | Proxy to GraphToolServer discover (single CORS origin for ext)                       |

**ContextSet composition** (`POST /agent/session`):

1. Authenticate as the selected role (separate JWT per role, falls back to default)
2. Bootstrap each selected node via NanoClaw (`GET /api/v1/agent/bootstrap/{id}`)
3. Optionally prepend ancestor node context (root-first) when `inherit_ancestors=true`
4. Merge all bootstraps — leaf-wins: later nodes override earlier for skills/tools
5. If `vector_query`: discover additional tools via GraphToolServer vector search
6. Write workspace files (`CLAUDE.md`, `.mcp.json`, `skills/`) to `~/.nanoclaw/workspaces/collider/`
7. Return `session_id` + `nanoclaw_ws_url` (WebSocket URL with auth token)

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

When an agent bootstraps from a node, it receives the full aggregated context of
that node **plus all its descendants** — skills, tools, and instructions merged
from root to leaf. Leaf entries win (more-specific context overrides parent
context).

---

## NanoClaw Integration

Collider exposes a NanoClaw-compatible bootstrap endpoint:

```bash
GET /api/v1/agent/bootstrap/{node_id}?depth=3
Authorization: Bearer <jwt>
```

The response gives a NanoClaw agent its:

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

Collider GraphToolServer is a native **Model Context Protocol** server. Connect
any MCP-compatible client once the server is running:

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

After connecting, every registered group/global tool appears as a native tool in
Claude Code, VS Code Copilot, Cursor, Zed, or any other MCP client. The tool
list updates live — no restart needed when new tools are registered.

---

## Chrome Extension — Three Tabs

The sidepanel hosts three tabs for different agent contexts:

### WorkspaceBrowser (Compose + Chat)

```text
┌─────────────────────────────────┐
│ ▼ Context Composer              │  collapsible
│   Role   [app_user          ▼]  │  pick identity level
│   Nodes  [☑ root  ☐ tools  …]  │  multi-select from tree
│   [☑] Include parent context    │  inherit ancestors
│   Search [describe your task…]  │
│           [Discover Tools   🔍] │  → GET :8004/tools/discover
│   [Compose & Start Session  →]  │  → POST :8004/agent/session
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ Agent Chat                      │  WS → :18789
│  [messages…]                    │  NanoClawBridge
│  [input…           ]  [Send]    │
└─────────────────────────────────┘
```

### AgentSeat (Chat Only)

Inline chat panel — connects to NanoClawBridge once a session is composed.

### Root Agent

Auto-composes from `Application.root_node_id` with full subtree depth,
authenticates as superadmin. Has access to all 15 Collider domain tools +
Claude Code built-ins (file, exec, browser).

---

## Getting Started

### Prerequisites

- Python 3.12+ with [UV](https://docs.astral.sh/uv/)
- Node.js 22+ with [pnpm](https://pnpm.io/)
- Chrome (for the extension)
- NanoClawBridge (Node.js 20+, `npm install` in NanoClawBridge/)
- LLM API key (Gemini, Anthropic, or Google Vertex AI)

### 1 — Fill in secrets

Edit `D:\FFS0_Factory\secrets\api_keys.env`:

```bash
# LLM provider (gemini | anthropic | google-vertex)
COLLIDER_AGENT_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...

# Collider auth
COLLIDER_USERNAME=Sam
COLLIDER_PASSWORD=Sam
```

### 2 — Configure NanoClawBridge

Create `NanoClawBridge/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
COLLIDER_MCP_URL=http://localhost:8001/mcp/sse
COLLIDER_WORKSPACE=~/.nanoclaw/workspaces/collider
NANOCLAW_PORT=18789
NANOCLAW_AUTH_TOKEN=collider-dev-token-2026
COLLIDER_MCP_ENABLED=true
COLLIDER_MCP_HOST=localhost:8001
```

### 3 — Start all services

```powershell
# Terminal 1: DataServer (REST + SSE + NanoClaw bootstrap)
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run uvicorn src.main:app --reload --port 8000

# Terminal 2: GraphToolServer (tool registry + gRPC + MCP)
cd ..\ColliderGraphToolServer
uv run uvicorn src.main:app --reload --port 8001

# Terminal 3: AgentRunner (context composer)
cd ..\ColliderAgentRunner
uv run uvicorn src.main:app --reload --port 8004

# Terminal 4: NanoClawBridge
cd ..\NanoClawBridge
npm run dev
```

### 4 — Seed the database

```powershell
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run python -m src.seed
```

### 5 — Connect Claude Code to the MCP server

```powershell
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

### 6 — Load the Chrome extension

Load `ColliderMultiAgentsChromeExtension` as an unpacked extension in Chrome developer mode. Open the sidepanel, select an application, switch to **Agent** view.

### API docs (when running)

- DataServer: <http://localhost:8000/docs>
- GraphToolServer: <http://localhost:8001/docs>
- VectorDbServer: <http://localhost:8002/docs>
- AgentRunner: <http://localhost:8004/docs>
- SQL Viewer: <http://localhost:8003>

See [dev-start.md](workspaces/FFS1_ColliderDataSystems/.agent/workflows/dev-
start.md) for the full ordered startup workflow.

---

## Tech Stack

| Layer               | Stack                                                           |
| ------------------- | --------------------------------------------------------------- |
| Python backends     | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy async, aiosqlite |
| Agent runtime       | NanoClawBridge (Claude Code SDK), WebSocket                     |
| Context composition | ColliderAgentRunner → workspace files                           |
| Execution engine    | gRPC (protobuf), MCP (SSE transport)                            |
| Vector search       | ChromaDB                                                        |
| Chrome extension    | Plasmo, Manifest V3, React + TypeScript                         |
| Frontend            | Nx, Vite 7, React 19, TypeScript 5+, XYFlow, Zustand            |
| Tooling             | UV (Python), pnpm (Node), Ruff, Mypy, Vitest, Pytest            |

---

## Protocols

| Protocol         | Transport       | Used Between                                                      |
| ---------------- | --------------- | ----------------------------------------------------------------- |
| REST             | HTTP            | Extension / agents ↔ DataServer, AgentRunner                      |
| SSE              | HTTP long-lived | DataServer → Extension (live events)                              |
| WebSocket        | WS              | Extension ↔ NanoClawBridge (agent chat)                           |
| WebSocket        | WS              | Extension ↔ GraphToolServer (workflow streaming)                  |
| WebRTC           | P2P (STUN/TURN) | Browser ↔ Browser (ffs5 PiP)                                      |
| Native Messaging | stdio           | Extension ↔ local filesystem host                                 |
| gRPC             | HTTP/2          | DataServer ↔ GraphToolServer                                      |
| MCP/SSE          | HTTP SSE + POST | NanoClawBridge / Claude Code / Copilot / Cursor ↔ GraphToolServer |

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

Canonical docs for this repo:

- `CLAUDE.md`
- `.agent/index.md`
- `.agent/workflows/conversation-state-rehydration.md`

Every workspace directory has an `.agent/` folder:

```text
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

```text
FFS0_Factory/
├── CLAUDE.md               ← Claude Code project context
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
