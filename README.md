# Collider — FFS0 Factory

> A self-hosted multi-agent AI workspace platform. Each workspace node carries its own tools, instructions, rules, and skills — forming a recursive context tree that any AI agent can bootstrap from.

---

## What Is This?

Collider is a platform for building and running AI-powered workspaces. The core idea: **every workspace is a node in a tree**, and every node carries a `NodeContainer` — a JSON manifest holding the tools, instructions, rules, knowledge, skills, and workflows that define what an AI agent can do in that context.

Three servers talk to each other. A Chrome extension bridges the browser to the backend. A React frontend renders whichever "appnode" the current workspace node points to. An AI model (Claude, GPT, Gemini) can bootstrap from any node in the tree and immediately know what tools it has, how to behave, and how to escalate.

---

## Architecture

```
FFS0_Factory/
├── workspaces/
│   └── FFS1_ColliderDataSystems/
│       ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
│       │   ├── ColliderDataServer/       ← Port 8000  (REST + SSE + OpenClaw)
│       │   ├── ColliderGraphToolServer/  ← Port 8001  (WebSocket + gRPC + MCP)
│       │   ├── ColliderVectorDbServer/   ← Port 8002  (ChromaDB semantic search)
│       │   ├── proto/                   ← Shared protobuf definitions + compiled stubs
│       │   └── ChromeExtension/         ← Plasmo, Manifest V3, LangGraph.js agents
│       └── FFS3_ColliderApplicationsFrontendServer/
│           ├── apps/ffs4/               ← Sidepanel appnode   (port 4201)
│           ├── apps/ffs5/               ← PiP appnode         (port 4202)
│           ├── apps/ffs6/               ← IDE viewer appnode  (port 4200, default)
│           └── libs/shared-ui/          ← Shared components + XYFlow
└── models/                              ← Shared Pydantic models
```

---

## The Three Servers

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

[OpenClaw](https://github.com/openclaw-ai/openclaw) is an open-source self-hosted agent gateway. Collider exposes an OpenClaw-compatible bootstrap endpoint:

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

This means any OpenClaw-compatible agent that connects to Collider gets a fully configured context from the workspace node tree, with no manual configuration.

---

## MCP Integration

Collider GraphToolServer is a native **Model Context Protocol** server. Connect any MCP-compatible client once the server is running:

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

After connecting, every registered group/global tool appears as a native tool in Claude Code, VS Code Copilot, Cursor, Zed, or any other MCP client. The tool list updates live — no restart needed when new tools are registered.

---

## Getting Started

### Prerequisites

- Python 3.12+ with [UV](https://docs.astral.sh/uv/)
- Node.js 20+ with [pnpm](https://pnpm.io/)
- (Optional) Chrome for the extension

### Start all services

```powershell
# 1. DataServer (REST + SSE)
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run uvicorn src.main:app --reload --port 8000

# 2. GraphToolServer (WebSocket + gRPC + MCP)
cd ..\ColliderGraphToolServer
uv run uvicorn src.main:app --reload --port 8001

# 3. VectorDbServer (ChromaDB)
cd ..\ColliderVectorDbServer
uv run python -m src.main

# 4. Frontend — ffs6 IDE viewer
cd ..\..\FFS3_ColliderApplicationsFrontendServer
pnpm nx serve ffs6

# 5. Connect Claude Code to the MCP server
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

See [dev-start.md](workspaces/FFS1_ColliderDataSystems/.agent/workflows/dev-start.md) for the full workflow including the SQLite viewer.

### Seed the database

```powershell
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run python seed.py
```

### API docs (when running)

- DataServer Swagger: http://localhost:8000/docs
- GraphToolServer Swagger: http://localhost:8001/docs
- VectorDbServer Swagger: http://localhost:8002/docs

---

## Tech Stack

| Layer | Stack |
|---|---|
| Python backends | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy async, aiosqlite |
| Execution engine | gRPC (protobuf), MCP (SSE transport), Pydantic AI |
| Vector search | ChromaDB |
| Chrome extension | Plasmo, Manifest V3, React + TypeScript, LangGraph.js |
| Frontend | Nx, Vite 7, React 19, TypeScript 5+, XYFlow, Zustand |
| Tooling | UV (Python), pnpm (Node), Ruff, Mypy, Vitest, Pytest |

---

## Protocols

| Protocol | Transport | Used Between |
|---|---|---|
| REST | HTTP | Extension / agents ↔ DataServer, VectorDbServer |
| SSE | HTTP long-lived | DataServer → Extension (live node change events) |
| WebSocket | WS | Extension ↔ GraphToolServer (workflow streaming) |
| WebRTC | P2P (STUN/TURN) | Browser ↔ Browser (ffs5 PiP) |
| Native Messaging | stdio | Extension ↔ local filesystem host |
| gRPC | HTTP/2 | DataServer ↔ GraphToolServer (tool/workflow RPCs) |
| MCP/SSE | HTTP SSE + POST | Claude Code / Copilot / Cursor ↔ GraphToolServer |

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

## Security

- JWT authentication on all DataServer endpoints
- System roles: `superadmin` → `collider_admin` → `app_admin` → `app_user`
- Per-application permissions (request / approve / revoke)
- MCP tool visibility: only `group` and `global` tools exposed — `local` tools remain owner-private
- Secrets injected at runtime by the tool executor — the agent never sees raw values

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
