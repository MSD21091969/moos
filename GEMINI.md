# GEMINI.md — FFS0 Factory (Antigravity)

> Project instructions for the Gemini CLI and Gemini-powered agents.
> The Collider platform uses Gemini as its **default LLM provider** (`COLLIDER_AGENT_PROVIDER=gemini`).
> Knowledge base: `~/.gemini/antigravity/brain/`

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## What Is Antigravity?

**Antigravity** is the Collider-powered AI code-assist system:

- **Gemini 2.5 Flash** is the active LLM (via `GEMINI_API_KEY` in `secrets/api_keys.env`)
- The Chrome extension sidepanel has three tabs:
  1. **WorkspaceBrowser (Compose)** — pick nodes from the app tree, compose ContextSet
  2. **AgentSeat (Chat)** — stream responses from the composed context
  3. **Root Agent** — auto-boots from `Application.root_node_id`, has 15 Collider tools,
     can create/modify nodes, and controls browser DOM via content scripts
- All registered tools are exposed via **MCP** at `http://localhost:8001/mcp/sse`

## Context System

Every workspace has an `.agent/` folder. **Always read `.agent/index.md` first**.

- `.agent/index.md` — workspace identity and purpose
- `.agent/rules/` — coding standards and constraints
- `.agent/knowledge/architecture/` — layered architecture docs (FFS1)

## Workspace Map

```text
FFS0_Factory/                  Python agent-factory (UV, pyproject.toml)
├── sdk/
│   ├── seeder/                .agent/ filesystem → DataServer node sync
│   └── tools/collider_tools/  Atomic tool implementations (importlib targets)
└── workspaces/
    ├── FFS1_ColliderDataSystems/
    │   ├── FFS2_...ChromeExtension/
    │   │   ├── ColliderDataServer/         ← :8000 REST + SSE + NanoClaw
    │   │   ├── ColliderGraphToolServer/    ← :8001 WebSocket + gRPC + MCP
    │   │   ├── ColliderVectorDbServer/     ← :8002 ChromaDB
    │   │   ├── ColliderAgentRunner/        ← :8004 Gemini agent (default provider)
    │   │   └── NanoClawBridge/skills/       ← NanoClaw skill (gRPC tools)
    │   └── FFS3_...FrontendServer/         Nx + Vite 7 + React 19 appnodes
    └── maassen_hochrath/                   IADORE personal workspace (Ollama)
```

## Tech Stack

**Python**: Python 3.12+, UV, FastAPI, Pydantic v2, SQLAlchemy async, aiosqlite, ChromaDB,
pydantic-ai, Ruff, Mypy strict, Pytest

**TypeScript**: Nx, Vite 7, React 19, TS 5+, XYFlow, Zustand, React Router, CSS Modules

**Chrome Extension**: Plasmo MV3, React + TypeScript, Zustand appStore

## Servers

| Service                 | Port         | Role                                                       |
| ----------------------- | ------------ | ---------------------------------------------------------- |
| ColliderDataServer      | 8000         | REST + SSE + Agent bootstrap (SQLite)                      |
| ColliderGraphToolServer | 8001 / 50052 | Tool registry + gRPC execution + **MCP/SSE**               |
| ColliderVectorDbServer  | 8002         | ChromaDB semantic search (gRPC)                            |
| **ColliderAgentRunner** | **8004**     | pydantic-ai, **Gemini 2.5 Flash**, ContextSet + Root Agent |
| **NanoClawBridge**      | **18789**    | **WebSocket agent chat**                                   |
| ffs6 Frontend           | 4200         | IDE viewer appnode (default)                               |

## Active LLM (Gemini)

```bash
# secrets/api_keys.env:
COLLIDER_AGENT_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
# Optional: override model
# COLLIDER_AGENT_MODEL=gemini-2.5-pro

# Alternative — Claude on Vertex AI (ADC, GCP billing):
# COLLIDER_AGENT_PROVIDER=google-vertex
# VERTEX_PROJECT_ID=mailmind-ai-djbuw
# VERTEX_REGION=us-east5
```

## Agent Bootstrap

`GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N` returns:

```json
{
  "agents_md": "# Agent identity...",
  "soul_md":   "# Rules / guardrails...",
  "tools_md":  "# Knowledge / reference...",
  "skills":    [{"name": "...", "markdown_body": "..."}],
  "tool_schemas": [{"function": {"name": "create_node", ...}}]
}
```

AgentRunner merges this into a pydantic-ai system prompt (leaf-wins strategy for tools/skills).

## ContextSet — Session Agent

```json
POST :8004/agent/session
{
  "role": "superadmin",
  "app_id": "c57ab23a-4a57-4b28-a34c-9700320565ea",
  "node_ids": ["9848b323-..."],
  "vector_query": "code generation tools",
  "inherit_ancestors": true
}
```

Then NanoClawBridge handles chat via WebSocket at `ws://127.0.0.1:18789?token=...`
(diagnostic fallback: `GET :8004/agent/chat?session_id=...&message=...` → SSE stream).

## Root Agent

```json
POST :8004/agent/root/session
{"app_id": "c57ab23a-4a57-4b28-a34c-9700320565ea"}
```

Returns `{"session_id":"...","preview":{"node_count":1,"tool_count":15,"role":"superadmin"}}`.
24h TTL. Has built-in `spawn_subagent` tool for orchestration.

## Collider MCP Tools

```bash
# 15 tools exposed at:
http://localhost:8001/mcp/sse

# Groups:
# nodes:       create_node, update_node, get_node, list_nodes, delete_node
# apps:        create_app, list_apps, get_app
# permissions: grant_permission, assign_role, list_access_requests, approve_request
# nanoclaw:    bootstrap_node, discover_skills, list_skills
# graph:       discover_tools, register_tool
```

## SDK Seeder

```bash
uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id <uuid>
# Syncs .agent/ hierarchy → DataServer nodes + registers tools in GraphToolServer
```

## App 2XZ (primary test app)

- ID: `c57ab23a-4a57-4b28-a34c-9700320565ea`
- Root node: `9848b323-5e65-4179-a1d6-5b99be9f8b87`
- Creds: Sam / Sam (superadmin)
- Full test plan: `TESTING.md`

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Python: Google docstrings, Ruff formatting, 80% test coverage on core
- TypeScript: TSDoc, strict mode, no `any`, Interfaces for props
- Only modify files under `D:\FFS0_Factory\`
- Check `.agent/` context before modifying any workspace
