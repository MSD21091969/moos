# Factory Workspace Status

> Last Updated: 2026-01-26 15:00 UTC  
> Migration Version: 1.3.0

## Session Report: 2026-01-26

### Completed Work

#### 1. Knowledge Folder Restructure ✅
Moved all `knowledge/` folders INTO `.agent/knowledge/` for workspace agents:
- `factory/knowledge/` → `factory/.agent/knowledge/`
- `collider_apps/knowledge/` → `collider_apps/.agent/knowledge/`
- `my-tiny-data-collider/knowledge/` → `my-tiny-data-collider/.agent/knowledge/`
- Fixed all junctions to point to new `.agent/knowledge/` locations
- Updated all `manifest.yaml` files to include knowledge reference

#### 2. Pilots Moved to collider_sdk ✅
- Moved `shared/pilots/` → `shared/collider_sdk/pilots/`
- Updated backend imports and paths
- Updated SDK exports to include `load_pilot`, `ColliderPilotSpec`

#### 3. Architecture Clarification
- **PilotConfig** = App capability envelope (what the app exposes to pilot as tools)
- **PilotSpec** = Agent behavior definition (instructions, rules, knowledge)
- **Pilot uses App as Tool** — pilot is user-facing, persistent through journey
- Backend SERVES spec data, never runs agents — agents run in frontend or local UX
- `FrontendClientId` to be renamed → `AppId` (includes local UX)

---

## Two Agent Systems

### 1. Workspace Agents (IDE/Local CLI)

**Config Location**: `.agent/` folder hierarchy  
**Runner**: `parts/runtimes/workspace_runner.py` (Textual TUI)  
**Context**: `WorkspaceContext` (active_file, git_branch, cwd, diagnostics)

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

### 2. Application Pilots (Frontend/Local UX)

**Config Location**: `shared/collider_sdk/pilots/{pilot_id}/`  
**Runner**: `pilotService.ts` (frontend) or `pilot_runner.py` (local)  
**Context**: `ContainerContext` (container_name, canvases, permissions, user)

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

---

## Architecture Overview

```
FACTORY (upstream producer)
├── .agent/
│   └── knowledge/    ← Moved here (was factory/knowledge/)
├── parts/            ← SDK catalog (shared code)
└── models_v2/        ← Core architecture
        ↓ READ-ONLY via junctions
WORKSPACES (downstream consumers)
├── collider_apps/
│   └── .agent/knowledge/  ← Moved here (was collider_apps/knowledge/)
└── maassen_hochrath/
```

---

## Detailed Structure

### Factory Level

```
D:\factory\
├── .agent\                              # Factory-level agent config
│   ├── manifest.yaml                    # Root manifest (no parent)
│   ├── configs\
│   │   ├── api_providers.yaml
│   │   ├── users.yaml                   # Test users (superuser, lola, menno)
│   │   └── workspace_defaults.yaml
│   ├── instructions\
│   │   ├── knowledge_hierarchy.md       # Downstream flow rules
│   │   └── instruction_inheritance.md   # Rule cascade defined
│   ├── rules\
│   │   ├── sandbox.md                   # Access control (READ-ONLY knowledge, parts)
│   │   ├── identity.md                  # Factory Architect persona
│   │   ├── code_patterns.md             # Container, Link, Definition, Wire
│   │   ├── math_coding_style.md
│   │   ├── math_maintenance.md
│   │   └── math_testing.md
│   ├── workflows\
│   │   └── screenshots\
│   └── knowledge\                       # ← MOVED FROM factory/knowledge/
│       ├── domains\
│       │   ├── architectures\
│       │   ├── infrastructure\
│       │   ├── languages\
│       │   └── mathematics\             # Category theory, tensor graphs
│       ├── projects\
│       │   ├── collider\                # MANIFESTO, progress, roadmap
│       │   └── maassen_hochrath\
│       ├── references\
│       │   ├── papers\
│       │   ├── snippets\
│       │   └── specs\
│       ├── research\
│       ├── journal\
│       │   └── decisions\
│       └── workflows\
│
├── parts\                               # SDK CATALOG
│   ├── catalog.py                       # Part definitions
│   ├── agents\
│   │   ├── workspace_agent.py           # L1: with_workspace_context()
│   │   ├── collider_pilot.py            # Graph-context pilot
│   │   └── tracer.py
│   ├── runtimes\
│   │   ├── runner.py                    # Base runner
│   │   └── workspace_runner.py          # Textual TUI runner
│   ├── templates\
│   │   ├── agent_spec.py                # AgentSpec base (DeepAgent pattern)
│   │   └── deep_agent.py                # DeepAgent class
│   ├── toolsets\
│   │   └── filesystem.py
│   └── skills\
│       ├── filesystem.py
│       ├── google.py
│       ├── shell.py
│       └── system.py
│
├── models_v2\                           # Core Architecture
├── docs\
├── secrets\                             # Gitignored credentials
│
└── workspaces\
    ├── collider_apps\
    └── maassen_hochrath\
```

### Collider Apps Workspace

```
D:\factory\workspaces\collider_apps\
├── .agent\                              # Workspace agent config
│   ├── manifest.yaml                    # Includes factory rules
│   ├── instructions\
│   │   └── workspace.md                 # Business app development context
│   ├── rules\
│   │   └── coding.md                    # Python 3.12+, Pydantic v2
│   ├── workflows\
│   │   ├── add-knowledge.md
│   │   ├── add-tool.md
│   │   ├── gmail-sync.md
│   │   └── test.md
│   └── knowledge\                       # ← MOVED FROM collider_apps/knowledge/
│       ├── factory_domains → ../../.agent/knowledge/domains     # Junction
│       ├── factory_research → ../../.agent/knowledge/research   # Junction
│       ├── collider\
│       ├── collider.md                  # Tech stack overview
│       ├── COLLIDER_MANIFESTO.md        # Vision document
│       ├── pilot_behaviors.md
│       ├── pydantic_v2.md
│       ├── rebuild_plan_v1.md
│       └── tool_examples.md
│
├── agents\
│   ├── collider_pilot.py                # Workspace pilot runner
│   ├── debug_import.py
│   ├── debug_resolution.py
│   └── verify_kit.py
├── scripts\
├── sync_logs\
│
├── collider_apps.code-workspace
├── pyproject.toml
│
└── applications\
    └── my-tiny-data-collider\
```

### My-Tiny-Data-Collider Application

```
D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\
├── .agent\                              # Application agent config
│   ├── manifest.yaml                    # Includes factory + workspace
│   ├── configs\
│   │   └── notion_map.json
│   ├── instructions\
│   │   └── application.md               # Full-stack app context
│   ├── rules\
│   │   ├── backend-expert.md            # 3-tier, Logfire, security
│   │   ├── frontend-artist.md           # React 18, Zustand, ReactFlow
│   │   ├── collider.md                  # Master controller identity
│   │   └── environment.md               # dev.ps1 startup rules
│   ├── workflows\
│   │   ├── architecture-update.md
│   │   ├── dev.md                       # Tri-server startup
│   │   ├── docker.md
│   │   ├── graph-audit.md
│   │   ├── lint.md
│   │   ├── subgraph-resolution.md
│   │   └── test.md
│   └── knowledge\                       # ← MOVED FROM my-tiny-data-collider/knowledge/
│       ├── math → ../../../../.agent/knowledge/domains/mathematics    # Junction
│       └── project → ../../../../.agent/knowledge/projects/collider   # Junction
│
├── backend\                             # FastAPI Control Plane (port 8000)
│   ├── main.py                          # REST API, SSE, WebSocket bridge
│   ├── db.py                            # SQLite persistence (NOT YET WIRED)
│   ├── auth.py                          # JWT, seed users, RBAC
│   ├── storage.py                       # File staging on I: drive
│   └── cache.py
│
├── frontend\                            # React User Plane (port 5173)
│   └── src\
│       ├── components\
│       │   ├── ColliderPilot.tsx        # PRIMARY pilot component
│       │   ├── PilotSidebar.tsx         # LEGACY - to be deleted
│       │   └── ...
│       └── pilot\
│           ├── pilotService.ts          # Gemini SDK integration
│           └── index.ts
│
├── runtime\                             # Execution Plane (port 8001)
│
├── shared\                              # Source of Truth for Contracts
│   └── collider_sdk\                    # ← SDK PACKAGE
│       ├── types.py                     # PilotConfig, User, Container, Canvas
│       └── pilots\                      # ← MOVED FROM shared/pilots/
│           ├── base.py                  # ColliderPilotSpec (extends AgentSpec)
│           ├── container\               # Container Pilot
│           └── studio\                  # Studio Pilot
│
└── tests\
```

---

## Knowledge Junctions

| Workspace | Junction | Target |
|-----------|----------|--------|
| collider_apps | `factory_domains` | `factory/.agent/knowledge/domains` |
| collider_apps | `factory_research` | `factory/.agent/knowledge/research` |
| my-tiny-data-collider | `math` | `factory/.agent/knowledge/domains/mathematics` |
| my-tiny-data-collider | `project` | `factory/.agent/knowledge/projects/collider` |

---

## MVP Status Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| **Factory .agent** | ✅ Complete | 6 rules, 2 instructions, rich knowledge |
| **Collider Apps .agent** | ✅ Complete | Inherits factory, coding rules |
| **Application .agent** | ✅ Complete | 4 role-specific rules, full chain |
| **Backend API** | ⚠️ Partial | CRUD works but uses in-memory store |
| **Backend Persistence** | 🔴 NOT WIRED | `db.py` has SQLite, not used by API |
| **Frontend UI** | ✅ Ready | Container/Canvas views functional |
| **Frontend Pilot** | ⚠️ Dual | ColliderPilot (primary), PilotSidebar (legacy) |
| **SDK Types** | ✅ Complete | PilotConfig, User, Container, Canvas |
| **Pilots** | ✅ Complete | container, studio with full folder structure |

---

## Pending Tasks (MVP Graduation)

### Critical (Blockers)
- [ ] Wire `db.py` SQLite to `main.py` endpoints
- [ ] Delete `PilotSidebar.tsx` (legacy)
- [ ] Rename `FrontendClientId` → `AppId`, add `LOCAL_UX`

### Runtime Interface
- [ ] Add `ToolManifest`, `ModelConfig`, `RuntimeEndpoints`, `RuntimeFeatures` types
- [ ] Update `PilotConfig` with runtime fields

### Context Bridge
- [ ] Implement pydantic-ai `deps_type` in DeepAgent
- [ ] Create typed `ContainerContext`, `WorkspaceContext` models

### Local UX
- [ ] Create `collider_sdk/runners/pilot_runner.py`
- [ ] Create `collider_apps/agents/run.py` entry point
- [ ] Create `factory/agents/run.py` entry point

### Cleanup
- [ ] Move `ColliderPilot.tsx`, `pilotService.ts` to `collider_sdk/components/`
- [ ] Run full test suite
- [ ] Tag `v0.1.0-mvp` baseline

---

## Completed Tasks

- [x] Knowledge folders moved to `.agent/knowledge/` ✅ (2026-01-26)
- [x] Pilots moved to `collider_sdk/pilots/` ✅ (2026-01-26)
- [x] Junction paths fixed ✅ (2026-01-26)
- [x] Manifest files updated ✅ (2026-01-26)
- [x] Backend imports updated ✅ (2026-01-26)
- [x] Test SDK imports from child projects ✅ (43/44 tests pass)
- [x] Implement WorkspaceAgent bridge pattern ✅
- [x] Implement ColliderPilotSpec bridge pattern ✅
- [x] Audit .agent/ hierarchy ✅

---

## Environment Variables

| Variable | Value |
|----------|-------|
| FACTORY_ROOT | D:\factory |
| DATALAKE | I:\DATALAKE |
| KNOWLEDGE_ROOT | D:\factory\.agent\knowledge |

---

*Factory Workspace v1.3.0*
