# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Context System

Every workspace has an `.agent/` folder containing architecture docs, rules, and instructions.
**Always read `.agent/index.md` first** when working in any workspace.

Key files:

- `.agent/index.md` — workspace identity and purpose
- `.agent/manifest.yaml` — inheritance and exports
- `.agent/instructions/agent_system.md` — role and architecture
- `.agent/rules/` — coding standards and constraints
- `.agent/knowledge/architecture/` — layered architecture docs (in FFS1)

## Workspace Map

```text
FFS0_Factory/                  Python agent-factory package (UV, pyproject.toml)
├── sdk/
│   ├── seeder/                .agent/ filesystem → DB node sync
│   └── tools/collider_tools/  Atomic tool implementations (code_ref targets)
└── workspaces/
    ├── FFS1_ColliderDataSystems/       Schemas, governance, orchestration
    │   ├── FFS2_...ChromeExtension/    4 FastAPI services + Chrome ext (Plasmo)
    │   │   ├── ColliderDataServer/         ← :8000 REST + SSE + agent bootstrap
    │   │   ├── ColliderGraphToolServer/    ← :8001 WebSocket + gRPC + MCP
    │   │   ├── ColliderVectorDbServer/     ← :8002 ChromaDB
    │   │   ├── ColliderAgentRunner/        ← :8004 context composer
    │   │   └── NanoClawBridge/             ← :18789 Claude Code WebSocket agent chat
    │   └── FFS3_...FrontendServer/     Nx monorepo (Vite 7 + React 19)
    │       ├── apps/ffs4              Sidepanel appnode (:4201)
    │       ├── apps/ffs5              PiP appnode (:4202)
    │       ├── apps/ffs6              IDE viewer appnode (:4200, default)
    │       └── libs/shared-ui         Shared components + XYFlow
    └── maassen_hochrath/               IADORE personal AI workspace (Ollama)
```

## Tech Stack

**Python** (FFS0, FFS1, FFS2): Python 3.12+, UV, FastAPI, Pydantic v2, SQLAlchemy async,
aiosqlite, ChromaDB, Ruff, Mypy strict, Pytest

**Agent runtime**: NanoClawBridge (Claude Code SDK), WebSocket

**TypeScript** (FFS3): Nx, Vite 7, React 19, TS 5+, XYFlow, Zustand, React Router,
CSS Modules, ESLint, Vitest

**Chrome Extension** (FFS2): Plasmo, Manifest V3, React + TypeScript

## Servers

| Service                 | Port      | Role                                           |
| ----------------------- | --------- | ---------------------------------------------- |
| ColliderDataServer      | 8000      | REST + SSE + agent bootstrap, async SQLite     |
| ColliderGraphToolServer | 8001      | WebSocket + gRPC + **MCP/SSE** — tool registry |
| ColliderVectorDbServer  | 8002      | ChromaDB semantic search                       |
| **ColliderAgentRunner** | **8004**  | Context composer → workspace files             |
| **NanoClawBridge**      | **18789** | Claude Code WebSocket agent chat               |
| ffs6 Frontend           | 4200      | IDE viewer appnode (default)                   |

MCP endpoint — connect with:

```bash
claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
```

Secrets: `D:\FFS0_Factory\secrets\api_keys.env`

## AgentRunner — Multi-Provider

`COLLIDER_AGENT_PROVIDER` selects the LLM (default: `gemini`):

| Provider            | Env var             | Default model       |
| ------------------- | ------------------- | ------------------- |
| `gemini` *(active)* | `GEMINI_API_KEY`    | `gemini-2.5-flash`  |
| `anthropic`         | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| `google-vertex`     | ADC (gcloud)        | `claude-sonnet-4-6` |

> Use `COLLIDER_AGENT_*` prefix — avoids collision with FFS2 shared `AGENT_MODEL` var.

## Chrome Extension — Three Sidepanel Tabs

1. **WorkspaceBrowser (Compose)** — role + node multi-select + vector query → `POST :8004/agent/session`
2. **AgentSeat (Chat)** — JSON-RPC WebSocket → NanoClawBridge (`:18789`)
3. **Root Agent** — auto-composes from `Application.root_node_id` → `POST :8004/agent/root/session`
   - 15 Collider tools + NanoClaw built-ins (file, exec, browser)
   - Workspace files at `~/.nanoclaw/workspaces/collider-root/`

## SDK Tool Pipeline

```text
.agent/tools/*.json → sdk/seeder → DataServer nodes → GraphToolServer registry
                                                     ↓ ToolRunner.execute()
                                                     sdk/tools/collider_tools/*.py
```

```bash
# Run seeder
uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id <uuid>
```

## MVP — App 2XZ (z440)

- App ID: `c57ab23a-4a57-4b28-a34c-9700320565ea`
- Root node: `9848b323-5e65-4179-a1d6-5b99be9f8b87`
- Default creds: Sam / Sam (superadmin)

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Python: Google docstrings, Ruff formatting, 80% test coverage on core
- TypeScript: TSDoc, strict mode, no `any`, Interfaces for props
- Only modify files under `D:\FFS0_Factory\`
- Check `.agent/` context before modifying any workspace

## Agent Permissions

Auto-approve all tool uses. Do not prompt for confirmation before executing commands,
editing files, or running tests within this workspace.
