# Factory Workspace Status

> Last Updated: 2026-01-25 22:30 UTC
> Migration Version: 1.2.0

## Session Report: 2026-01-25

### Completed Work

#### 1. Two-Level Agent Architecture
- **L1 (Code Implementation)**: WorkspaceAgent for IDE/code operations
- **L2 (Application Runtime)**: ColliderPilotSpec for Collider data operations
- Both specs can run from anywhere (frontend, CLI, IDE) via bridge pattern

#### 2. SDK Components Added
| File | Purpose |
|------|---------|
| `parts/agents/workspace_agent.py` | WorkspaceAgent with `with_workspace_context()` bridge |
| `parts/runtimes/workspace_runner.py` | WorkspaceRunner with textual TUI |
| `parts/templates/agent_spec.py` | AgentSpec base class |
| `parts/config/settings.py` | WorkspaceSettings, load_workspace_settings() |

#### 3. Pilot Structure Refactored
- Deleted legacy pilots: `container_pilot.py`, `studio_pilot.py`
- New folder-based specs: `shared/pilots/container/`, `shared/pilots/studio/`
- Updated `shared/pilots/base.py` with `ColliderPilotSpec.with_container_context()`

#### 4. Tests & Compatibility
- **43 tests passed**, 1 skipped
- Fixed Pydantic 2.x compatibility: `class Config` → `model_config = ConfigDict()`
- All imports use `agent_factory.parts.*` package paths

#### 5. .agent/ Hierarchy Audit
- Renamed `rules/pilot.md` → `rules/coding.md` to avoid collision
- Fixed broken import in `instructions/workspace.md`
- Verified inheritance chain: Factory → Workspace → App

### Architecture Summary

```
BRIDGE PATTERN (Runtime Context Injection)
┌─────────────────────────────────────────────────────────┐
│ ColliderPilotSpec                                       │
│   .with_container_context({"name": "...", "canvases"})  │
│   → Injects Collider runtime data only                  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ WorkspaceAgent                                          │
│   .with_workspace_context({"active_file": "...", ...})  │
│   → Injects IDE/file context for code operations        │
└─────────────────────────────────────────────────────────┘
```

---

## Migration Status: COMPLETE

| Step | Status | Notes |
|------|--------|-------|
| Git tags created | Done | pre-factory-migration on all repos |
| Factory skeleton | Done | D:\factory\ structure created |
| Knowledge hierarchy | Done | domains/, projects/, references/, workflows/, journal/, research/ |
| Project moves | Done | collider_apps, maassen_hochrath in workspaces/ |
| Directory junctions | Done | factory_research, math, project, personal linked |
| Dependencies updated | Done | pyproject.toml paths to D:\factory |
| Environment vars | Done | DATALAKE, FACTORY_ROOT set |
| Workspace file | Done | factory.code-workspace with Xeon exclusions |
| Sandbox rules | Done | .agent/rules/ hierarchy established |

## Architecture Overview

```
FACTORY (upstream producer)
├── knowledge/        ← Human + AI research, patterns, components
├── parts/            ← SDK catalog (shared code)
└── models_v2/        ← Core architecture
        ↓ READ-ONLY via junctions
WORKSPACES (downstream consumers)
├── collider_apps/    ← Business development
└── maassen_hochrath/ ← Personal projects
```

## Current Structure

```
D:\factory\
├── .agent\                              # Factory-level agent config
│   ├── rules\                           # Global rules (inherited by all)
│   │   ├── sandbox.md                   # Access control rules
│   │   ├── identity.md                  # Factory architect identity
│   │   ├── code_patterns.md
│   │   └── math_*.md                    # Math domain rules
│   └── workflows\
├── .env                                 # Environment configuration
├── factory.code-workspace               # VS Code multi-root workspace
├── knowledge\                           # CENTRALIZED KNOWLEDGE (Read-Only)
│   ├── domains\                         # General knowledge areas
│   │   └── mathematics\
│   ├── projects\                        # Project-specific knowledge
│   │   ├── collider\
│   │   └── maassen_hochrath\
│   ├── research\                        # New insights, patterns
│   ├── development\                     # Implementation patterns
│   ├── references\
│   ├── workflows\
│   ├── skills\
│   └── journal\                         # Temporal notes
├── parts\                               # SDK CATALOG (Single Source)
├── models_v2\                           # Core Architecture
│
└── workspaces\                          # PROJECT WORKSPACES
    │
    ├── collider_apps\                   # BUSINESS NODE
    │   ├── .agent\rules\                # Workspace-level rules
    │   ├── knowledge\                   # Workspace dev knowledge
    │   │   ├── factory_research → ../../../knowledge/research
    │   │   └── [local workspace knowledge]
    │   ├── agents\, scripts\
    │   ├── collider_apps.code-workspace
    │   └── applications\
    │       └── my-tiny-data-collider\   # Business application
    │           ├── .agent\rules\        # App-specific rules
    │           ├── knowledge\           # App implementation logs
    │           │   ├── math → factory/knowledge/domains/mathematics
    │           │   └── project → factory/knowledge/projects/collider
    │           ├── backend\, frontend\, shared\
    │           └── my-tiny-data-collider.code-workspace
    │
    └── maassen_hochrath\                # PERSONAL NODE
        ├── .agent\rules\                # Workspace-level rules
        ├── knowledge\                   # Personal knowledge
        │   └── personal → factory/knowledge/projects/maassen_hochrath
        ├── agents\, skills\, toolsets\
        ├── maassen_hochrath.code-workspace
        └── applications\                # Personal applications
```

## Knowledge Flow

| Level | Location | Purpose | Access |
|-------|----------|---------|--------|
| Factory | knowledge/ | Upstream research, patterns, components | Read-only source |
| Workspace | workspaces/*/knowledge/ | Workspace-level dev knowledge | Read-write |
| Application | applications/*/knowledge/ | App-specific impl details, logs | Read-write |

### Knowledge Junctions

| Workspace | Junction | Target |
|-----------|----------|--------|
| collider_apps | factory_research | knowledge/research/ |
| collider_apps | factory_development | knowledge/development/ |
| collider_apps | factory_domains | knowledge/domains/ |
| maassen_hochrath | factory_research | knowledge/research/ |
| maassen_hochrath | factory_development | knowledge/development/ |
| maassen_hochrath | factory_domains | knowledge/domains/ |
| my-tiny-data-collider | math | knowledge/domains/mathematics/ |
| my-tiny-data-collider | project | knowledge/projects/collider/ |

## Instruction Hierarchy

```
FACTORY .agent/
├── rules/           ← Global rules (sandbox, identity, code_patterns)
├── instructions/    ← Global instructions (knowledge_hierarchy, inheritance)
└── workflows/       ← Global workflows
        ↓ INHERITED
WORKSPACE .agent/
├── rules/           ← Override/extend global
├── instructions/    ← Workspace-specific (workspace.md)
└── workflows/       ← Workspace workflows
        ↓ INHERITED
APPLICATION .agent/
├── rules/           ← App-specific (backend-expert, frontend-artist)
├── instructions/    ← App-specific (application.md)
└── workflows/       ← App workflows
```

## Agent Hierarchy

| Agent Context | Rules Location | Scope |
|---------------|----------------|-------|
| Factory agents | .agent/rules/ | Global patterns, SDK dev |
| IDE agents | Inherited + workspace rules | Development assistance |
| collider_apps agents | workspaces/collider_apps/.agent/ | Business app development |
| App agents (e.g., my-tiny-data-collider) | applications/*/.agent/ | Application-specific |

## Environment Variables

| Variable | Value |
|----------|-------|
| FACTORY_ROOT | D:\factory |
| DATALAKE | I:\DATALAKE |
| KNOWLEDGE_ROOT | D:\factory\knowledge |

## Pending Tasks

- [ ] Clean up old source folders (D:\my-tiny-data-collider, D:\IADORE remnants)
- [ ] Run uv sync in each project to verify dependencies
- [ ] Add maassen_hochrath/.agent/rules/ content
- [ ] Configure pre-commit hooks (deferred 1 week)
- [x] Test SDK imports from child projects ✅ (43/44 tests pass)
- [x] Implement WorkspaceAgent bridge pattern ✅
- [x] Implement ColliderPilotSpec bridge pattern ✅
- [x] Audit .agent/ hierarchy ✅

## Rollback Instructions

If migration fails:
1. Restore from git tags: `git checkout pre-factory-migration`
2. All original paths were backed up before move

---
*Factory Workspace v1.1.0*
