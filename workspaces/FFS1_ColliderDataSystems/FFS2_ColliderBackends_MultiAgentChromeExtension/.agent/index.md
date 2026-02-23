# FFS2 ColliderBackends - Agent Context

> Backend services and Chrome Extension implementation.

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\.agent\`

## Hierarchy

```text
FFS0_Factory                     (Root)
  └── FFS1_ColliderDataSystems   (IDE Context - Parent)
        └── FFS2_ColliderBackends (This Workspace - Backend/Extension)
```

## Purpose

Specific context for:

- **ColliderDataServer** (FastAPI on :8000) — REST, SSE, NanoClaw bootstrap, WebRTC signaling
- **ColliderGraphToolServer** (WebSocket/MCP on :8001) — Tool registry, workflow execution, MCP server
- **ColliderVectorDbServer** (ChromaDB on :8002) — Semantic search + embeddings
- **ColliderAgentRunner** (pydantic-ai on :8004) — ContextSet sessions + root orchestrator
- **ColliderMultiAgentsChromeExtension** (Plasmo, MV3) — Sidepanel with WorkspaceBrowser + RootAgentPanel

## SDK Components (at repo root `sdk/`)

- **`sdk/seeder/`** — Syncs `.agent/` filesystem hierarchy → DB nodes via DataServer REST
  - Run: `uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id <uuid>`
  - After each node upsert, registers tools from `NodeContainer.tools` to GraphToolServer
- **`sdk/tools/collider_tools/`** — Atomic Python tool implementations (code behind `ToolDefinition.code_ref`)
  - `nodes.py`, `apps.py`, `permissions.py`, `agent_bootstrap.py`, `graph.py`
  - Executed by GraphToolServer `ToolRunner` via `importlib`

## Contents

### [Instructions](instructions/)

- **[agent_system.md](instructions/agent_system.md)**: "Backend Systems Engineer" persona.

### [Rules](rules/)

- **[backend_api_design.md](rules/backend_api_design.md)**: FastAPI standards, Pydantic V2 usage.
- **context_loading.md**: Domain-specific context loading strategies.
- **extension_boundaries.md**: Security and communication boundaries for the extension.

### [Configs](configs/)

- **[servers.yaml](configs/servers.yaml)**: Service ports (8000, 8001, 8002, 8004) and protocols.
- **[extension.yaml](configs/extension.yaml)**: Extension permissions and capabilities.
- **[database.yaml](configs/database.yaml)**: DB connection templates.
- **[logging.yaml](configs/logging.yaml)**: Python logging config.

### [Skills](skills/)

- **[`api_client.py`](skills/api_client.py)**: Python client for testing the DataServer.

### [Tools](tools/)

- **[`run_migrations.py`](tools/run_migrations.py)**: Wrapper for Alembic migrations.
- **[`seed_db.py`](tools/seed_db.py)**: Wrapper for database seeding.

### [Workflows](workflows/)

- **dev-extension.md**: Chrome Extension dev guide.
- **sync-filesyst.md**: File sync guide.

## Component Folders

```text
ColliderDataServer/              # REST/SSE/NanoClaw API server (:8000)
ColliderGraphToolServer/         # Tool registry + MCP server (:8001)
ColliderVectorDbServer/          # ChromaDB semantic search (:8002)
ColliderAgentRunner/             # pydantic-ai orchestrator (:8004)
ColliderMultiAgentsChromeExtension/  # Plasmo MV3 extension
NanoClawBridge/skills/          # bootstrap.sh — hydrates NanoClaw workspace from Collider
```

## NanoClaw Bootstrap Skill (`NanoClawBridge/skills/bootstrap.sh`)

Hydrates an NanoClaw workspace directory from a Collider node:

- Writes `CLAUDE.md` + `.mcp.json`, per-skill `SKILL.md`, per-tool `SKILL.md`
- Supports `COLLIDER_WATCH=1` for SSE-driven re-sync on node changes
- Supports `COLLIDER_DEPTH=N` to limit subtree depth

Required env: `COLLIDER_URL`, `COLLIDER_NODE_ID`, `COLLIDER_TOKEN`
