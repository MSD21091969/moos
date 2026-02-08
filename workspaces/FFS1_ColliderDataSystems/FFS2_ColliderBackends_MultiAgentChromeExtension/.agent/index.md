# FFS2 ColliderBackends - Agent Context

> Backend services and Chrome Extension implementation.

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\.agent\`

## Hierarchy

```
FFS0_Factory                     (Root)
  └── FFS1_ColliderDataSystems   (IDE Context - Parent)
        └── FFS2_ColliderBackends (This Workspace - Backend/Extension)
```

## Purpose

Specific context for:

- **ColliderDataServer** (FastAPI on :8000)
- **ColliderGraphToolServer** (WebSocket on :8001 - Workflow Engine)
- **ColliderVectorDbServer** (Vector search on :8002)
- **ColliderMultiAgentsChromeExtension** (Plasmo)

## Contents

### [Instructions](instructions/)

- **[agent_system.md](instructions/agent_system.md)**: "Backend Systems Engineer" persona.

### [Rules](rules/)

- **[backend_api_design.md](rules/backend_api_design.md)**: FastAPI standards, Pydantic V2 usage.
- **context_loading.md**: Domain-specific context loading strategies.
- **extension_boundaries.md**: Security and communication boundaries for the extension.

### [Configs](configs/)

- **[servers.yaml](configs/servers.yaml)**: Service ports (8000, 8001, 8002) and protocols (gRPC/WS).
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

```
ColliderDataServer/              # REST/SSE API server
ColliderGraphToolServer/         # WebSocket Workflow Engine
ColliderVectorDbServer/          # Vector search server
ColliderMultiAgentsChromeExtension/  # Plasmo extension
```
