# Factory Workspace Status

> Last Updated: 2026-01-26 22:00 UTC  
> Migration Version: 2.0.0 (MVP)  
> Git Tag: `v0.1.0-mvp`

---

## 🎉 MVP Graduation Complete

**Tag**: `v0.1.0-mvp` | **Commit**: `a9b98b8` | **Files Changed**: 49 (+2542/-834)

### What Shipped

| Feature             | Status | Details                                                              |
| ------------------- | ------ | -------------------------------------------------------------------- |
| SQLite Persistence  | ✅     | `db.py` wired to all `main.py` endpoints                             |
| Legacy Cleanup      | ✅     | `PilotSidebar.tsx` deleted                                           |
| Type System         | ✅     | `AppId` enum with `LOCAL_UX` variant                                 |
| Runtime Types       | ✅     | `ToolManifest`, `ModelConfig`, `RuntimeEndpoints`, `RuntimeFeatures` |
| Context Models      | ✅     | `ContainerContext`, `WorkspaceContext`                               |
| Local UX Runner     | ✅     | `collider-pilot` CLI command                                         |
| TypeScript Pipeline | ✅     | `npm run generate:types` from OpenAPI                                |
| Knowledge Junctions | ✅     | All 4 junctions validated                                            |

---

## Two Agent Systems

### 1. Workspace Agents (IDE/Local CLI)

**Config Location**: `.agent/` folder hierarchy  
**Runner**: `parts/runtimes/workspace_runner.py` (Textual TUI)  
**Context**: `WorkspaceContext` (workspace_root, active_file, git_branch, diagnostics)

```
.agent/
├── manifest.yaml        # Inheritance config
├── instructions/        # System prompt (instructions.md)
├── rules/               # Behavioral constraints (*.md)
├── workflows/           # Task sequences (*.md)
└── knowledge/           # Domain context (*.md, junctions)
```

**Inheritance Chain**:

```
Factory .agent/ → Workspace .agent/ → Application .agent/
```

**Knowledge Access**: Via READ-ONLY junctions to `factory/.agent/knowledge/`

### 2. Application Pilots (Frontend/Local UX)

**Config Location**: `shared/collider_sdk/pilots/{pilot_id}/`  
**Runner**: `pilotService.ts` (frontend) or `pilot_runner.py` (local CLI)  
**Context**: `ContainerContext` (container_id, container_name, canvases, permissions, user)

```
collider_sdk/pilots/{pilot_id}/
├── __init__.py          # PILOT_SPEC definition
├── instructions.md      # System prompt
├── rules/               # Behavioral constraints
├── workflows/           # Task sequences
└── knowledge/           # Pilot-specific domain context
```

**Available Pilots**:
| Pilot | Capabilities | Use Case |
|-------|--------------|----------|
| `container` | Navigation, sharing, permissions | Container management |
| `studio` | File ops, staging, commit | Canvas editing |

**Local UX CLI**:

```bash
collider-pilot container   # Interactive container pilot
collider-pilot studio      # Interactive studio pilot
collider-pilot --help      # Show usage
```

---

## Architecture Overview

```
FACTORY (upstream producer)
├── .agent/
│   └── knowledge/         ← Domain knowledge (mathematics, projects)
├── parts/                 ← SDK catalog (agents, runtimes, skills)
└── models_v2/             ← Core graph architecture
        ↓ READ-ONLY via junctions
WORKSPACES (downstream consumers)
├── collider_apps/
│   ├── .agent/knowledge/  ← Junctions to factory knowledge
│   └── applications/
│       └── my-tiny-data-collider/
│           ├── backend/   ← FastAPI (port 8000) + SQLite
│           ├── frontend/  ← React/Vite (port 5173)
│           ├── runtime/   ← Mock execution (port 8001)
│           └── shared/collider_sdk/
│               ├── types.py     ← AppId, ContainerContext, etc.
│               ├── pilots/      ← container, studio
│               └── runners/     ← pilot_runner.py (CLI)
└── maassen_hochrath/
```

---

## SDK Type System (v0.1.0-mvp)

### Core Types (`shared/collider_sdk/types.py`)

```python
# Application Identity
class AppId(str, Enum):
    CONTAINER_APP = "container-app"
    STUDIO_APP = "studio-app"
    ADMIN_APP = "admin-app"
    VIEWER_APP = "viewer-app"
    LOCAL_UX = "local_ux"        # NEW: For CLI runner

# Runtime Interface
class ToolManifest(BaseModel):   # Tool capability declaration
class ModelConfig(BaseModel):     # AI model settings
class RuntimeEndpoints(BaseModel): # /execute, /status, /cancel
class RuntimeFeatures(BaseModel):  # streaming, tool_calling, etc.

# Context Models
class ContainerContext(BaseModel): # For pilots (container_id, canvases, permissions, user)
class WorkspaceContext(BaseModel): # For workspace agents (workspace_root, active_file, git_branch)

# Pilot Configuration
class PilotConfig(BaseModel):
    pilot_id: str
    app_id: AppId
    capabilities: list[PilotCapability]
    tools: list[ToolManifest]
    model: ModelConfig | None
    runtime: RuntimeEndpoints
    features: RuntimeFeatures
    ui_config: PilotUIConfig
```

### TypeScript Generation

```bash
# With backend running at localhost:8000
cd frontend && npm run generate:types
# Outputs: src/types/generated.ts
```

---

## Knowledge Junctions (All Verified ✅)

| Workspace             | Junction           | Target                                         |
| --------------------- | ------------------ | ---------------------------------------------- |
| collider_apps         | `factory_domains`  | `factory/.agent/knowledge/domains`             |
| collider_apps         | `factory_research` | `factory/.agent/knowledge/research`            |
| my-tiny-data-collider | `math`             | `factory/.agent/knowledge/domains/mathematics` |
| my-tiny-data-collider | `project`          | `factory/.agent/knowledge/projects/collider`   |

**Mathematics as AI Context First-Citizen**: The `tensor_graphs.md` in `factory/.agent/knowledge/domains/mathematics/` provides GPU-accelerated graph operations and category theory foundations—available to workspace agents via junction for advanced mathematical reasoning.

---

## Post-MVP Feature Tracking

| Issue                                                                   | Feature            | Scope                       | Priority |
| ----------------------------------------------------------------------- | ------------------ | --------------------------- | -------- |
| [#116](https://github.com/MSD21091969/my-tiny-data-collider/issues/116) | Auth Integration   | JWT wired to containers     | High     |
| [#117](https://github.com/MSD21091969/my-tiny-data-collider/issues/117) | Pilot Streaming    | SSE for real-time responses | High     |
| [#118](https://github.com/MSD21091969/my-tiny-data-collider/issues/118) | Canvas Persistence | File storage on DATALAKE    | High     |
| [#119](https://github.com/MSD21091969/my-tiny-data-collider/issues/119) | Graph View         | ReactFlow visualization     | Core     |

---

## Detailed Structure

### Factory Level

```
D:\factory\
├── .agent\                              # Factory-level agent config
│   ├── manifest.yaml                    # Root manifest (no parent)
│   ├── configs\
│   │   ├── api_providers.yaml
│   │   ├── users.yaml                   # Test users
│   │   └── workspace_defaults.yaml
│   ├── instructions\
│   │   ├── knowledge_hierarchy.md       # Downstream flow rules
│   │   └── instruction_inheritance.md   # Rule cascade
│   ├── rules\
│   │   ├── sandbox.md, identity.md, code_patterns.md
│   │   └── math_coding_style.md, math_maintenance.md, math_testing.md
│   └── knowledge\
│       ├── domains\mathematics\         # tensor_graphs, category_theory, etc.
│       └── projects\collider\           # MANIFESTO, progress, roadmap
│
├── parts\                               # SDK Catalog
│   ├── agents\workspace_agent.py        # with_workspace_context()
│   ├── runtimes\workspace_runner.py     # Textual TUI
│   └── templates\agent_spec.py          # AgentSpec base
│
└── workspaces\
    ├── collider_apps\
    └── maassen_hochrath\
```

### My-Tiny-Data-Collider (v0.1.0-mvp)

```
D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\
├── .agent\                              # Application agent config
│   ├── manifest.yaml                    # Inherits factory + workspace
│   ├── instructions\application.md
│   ├── rules\                           # backend-expert, frontend-artist, etc.
│   └── knowledge\
│       ├── math → factory/mathematics   # Junction
│       └── project → factory/collider   # Junction
│
├── backend\                             # FastAPI Control Plane (port 8000)
│   ├── main.py                          # REST API + SQLite via db.py ✅
│   ├── db.py                            # SQLite persistence (WIRED)
│   ├── auth.py                          # JWT, RBAC
│   └── storage.py                       # File staging
│
├── frontend\                            # React User Plane (port 5173)
│   └── src\
│       ├── components\ColliderPilot.tsx # ONLY pilot component ✅
│       ├── sdk\types.ts                 # AppId, ContainerContext
│       ├── types\generated.ts           # OpenAPI-generated
│       └── pilot\pilotService.ts        # Gemini SDK
│
├── runtime\                             # Execution Plane (port 8001) - MOCK
│
├── shared\collider_sdk\                 # Source of Truth
│   ├── types.py                         # AppId, *Context, *Config
│   ├── pilots\                          # container/, studio/
│   └── runners\pilot_runner.py          # CLI entry point ✅
│
└── pyproject.toml                       # collider-pilot script entry
```

---

## Component Status

| Component                | Status      | Notes                                           |
| ------------------------ | ----------- | ----------------------------------------------- |
| **Factory .agent**       | ✅          | 6 rules, 2 instructions, rich knowledge         |
| **Collider Apps .agent** | ✅          | Inherits factory, coding rules                  |
| **Application .agent**   | ✅          | 4 role-specific rules, full chain               |
| **Backend API**          | ✅          | Fixed `storage` import. Persistence verified.   |
| **Backend Persistence**  | ✅          | `data/collider.db`                              |
| **Frontend UI**          | ✅          | Verified reachable.                             |
| **SDK Types**            | ✅          | `AppId`, `ContainerContext`, `WorkspaceContext` |
| **Pilots**               | ✅          | container, studio with full folder structure    |
| **Local UX Runner**      | ✅          | `collider-pilot` operational via module         |
| **TypeScript Pipeline**  | ✅          | `npm run generate:types`                        |
| **Runtime Service**      | ⚠️ Degraded | Startup config issue (fixing now)               |

---

## MVP Graduation Changelog

### Session: 2026-01-26 (Verification)

**Fixes**:

- [x] Fixed `Backend` crash due to `import storage` path error in `main.py`.
- [x] Installed `pytest-env` to fix test configuration.
- [x] Verified `collider-pilot` module execution compatibility.

### Session: 2026-01-26 (Release)

**Breaking Changes**:

- `FrontendClientId` renamed to `AppId` (backward-compat alias provided)
- `PilotSidebar.tsx` deleted (use `ColliderPilot.tsx`)

**Backend**:

- [x] Wire SQLite `db.py` to `main.py` endpoints (replaces in-memory Store)
- [x] Update all CRUD operations to use `Database` class
- [x] Database persists to `data/collider.db`

**Type System**:

- [x] Rename `FrontendClientId` → `AppId` with `LOCAL_UX` variant
- [x] Add `ToolManifest`, `ModelConfig`, `RuntimeEndpoints`, `RuntimeFeatures`
- [x] Add `ContainerContext`, `WorkspaceContext` typed models
- [x] Update `PilotConfig` with runtime interface fields

**Local UX**:

- [x] Create `shared/collider_sdk/runners/pilot_runner.py`
- [x] Add `collider-pilot` CLI command via `pyproject.toml` entry point
- [x] Create `collider_apps/agents/run.py` workspace entry

**Frontend**:

- [x] Delete legacy `PilotSidebar.tsx`
- [x] Update TypeScript types to use `AppId`
- [x] Add `openapi-typescript` for type generation pipeline
- [x] Fix multiple TypeScript lint issues

**SDK**:

- [x] Move pilots to `shared/collider_sdk/pilots/`
- [x] Export `run_pilot`, `ContainerContext`, `WorkspaceContext`
- [x] Add backward-compat `FrontendClientId` alias

**Knowledge System**:

- [x] Add `.agent/` folder with `manifest.yaml` inheritance
- [x] Verify all 4 knowledge junctions resolve

---

## Environment Variables

| Variable       | Value                       |
| -------------- | --------------------------- |
| FACTORY_ROOT   | D:\factory                  |
| DATALAKE       | I:\DATALAKE                 |
| KNOWLEDGE_ROOT | D:\factory\.agent\knowledge |

---

## Quick Start

```bash
# Backend
cd my-tiny-data-collider
uv run python -m backend.main

# Frontend
cd frontend && npm run dev

# Local Pilot CLI
uv run collider-pilot container

# Generate TypeScript types (with backend running)
cd frontend && npm run generate:types

# Run tests
uv run python -m pytest tests/ -v
```

---

_Factory Workspace v2.0.0 (MVP) — Tagged 2026-01-26_
