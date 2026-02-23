# Collider Data Systems -- Knowledge Base Index

> Central documentation for the Collider Multi-Agent System architecture, implementation, and development history.

---

## Quick Start

**New to Collider?** Start here:

1. **[System Overview](architecture/01_system_overview.md)** - What Collider is, the `.agent/` pattern, NodeContainer
2. **[Workspace Hierarchy](architecture/02_workspace_hierarchy.md)** - FFS0-8 directory map and workspace roles
3. **[Domains & Routing](architecture/06_domains_and_routing.md)** - FILESYST/CLOUD/ADMIN domains and context routing
4. **[Architecture Index](architecture/_index.md)** - Full document listing and reading order

---

## Current System Status

**Latest Implementation**: Frontend Architecture Restructure (2026-02-09)

### Production Stack

| Component                   | Technology          | Port  | Status                              |
| --------------------------- | ------------------- | ----- | ----------------------------------- |
| **ColliderDataServer**      | FastAPI + SQLite    | :8000 | Running (11 apps seeded, 8/8 tests) |
| **ColliderGraphToolServer** | FastAPI + WebSocket | :8001 | Running                             |
| **ColliderVectorDbServer**  | FastAPI + ChromaDB  | :8002 | Running                             |
| **Chrome Extension**        | Plasmo + React 18   | -     | Built (381 kB sidepanel)            |
| **Frontend Packages**       | Vite + React 18     | -     | 7 packages (~165 kB)                |

### Application Packages (FFS4-FFS8)

| Package                         | Purpose                       | Size     | Domain    |
| ------------------------------- | ----------------------------- | -------- | --------- |
| **FFS4** @collider/sidepanel-ui | Workspace browser, agent seat | 25.04 kB | Sidepanel |
| **FFS5** @collider/pip-ui       | WebRTC user-user comms        | 24.57 kB | PiP       |
| **FFS6** @collider/ide-viewer   | File tree, .agent/ viewer     | 23.85 kB | FILESYST  |
| **FFS7** @collider/admin-viewer | User management               | 22.57 kB | ADMIN     |
| **FFS8** @collider/cloud-viewer | Cloud app viewer              | 22.74 kB | CLOUD     |

---

## Architecture Documentation

See **[architecture/_index.md](architecture/_index.md)** for the full index and
reading order.

| #   | Document                                                      | Topic                                                  |
| --- | ------------------------------------------------------------- | ------------------------------------------------------ |
| 01  | [System Overview](architecture/01_system_overview.md)         | .agent pattern, NodeContainer, manifest inheritance    |
| 02  | [Workspace Hierarchy](architecture/02_workspace_hierarchy.md) | FFS0-8 map, workspace purposes, pnpm workspace         |
| 03  | [Backend Services](architecture/03_backend_services.md)       | DataServer, GraphToolServer, VectorDbServer, DB models |
| 04  | [Chrome Extension](architecture/04_chrome_extension.md)       | Service worker, ContextManager, sidepanel, messaging   |
| 05  | [Frontend Packages](architecture/05_frontend_packages.md)     | Shared libraries, application packages, Vite build     |
| 06  | [Domains & Routing](architecture/06_domains_and_routing.md)   | FILESYST/CLOUD/ADMIN, context-driven viewer routing    |
| 07  | [Data Flow](architecture/07_data_flow.md)                     | 6 protocols, message types, SSE, sync flows            |
| 08  | [Security](architecture/08_security.md)                       | Firebase Auth, permissions, secrets, CORS              |
| 09  | [Agent System](architecture/09_agent_system.md)               | LangGraph.js, Pydantic AI, browser agents, templates   |

---

## Implementation Guides

### 2026-02-09: Frontend Architecture Restructure

**[Full Implementation Log](2026-02-09_frontend_architecture_restructure.md)** (728 lines)

**Summary**: Transformed from monolithic portal to modular, workspace-driven application packages.

**What Was Built**:

- 9 core components (FETCH_TREE fix, WebRTC endpoint, FFS3 restructure, FFS4-8 packages, context routing)
- 7 frontend packages (~165 kB total, gzipped: ~46 kB)
- Workspace-driven architecture: "workspaces ARE the applications"
- Context-aware routing (ContextManager + workspace-router)
- WebRTC signaling for user-user communication
- Fixed sharp native module build issue

**Key Files**:

- Backend: `FFS2_.../ColliderDataServer/src/api/rtc.py`
- Extension: `ColliderMultiAgentsChromeExtension/src/background/context-manager.ts`
- Packages: `FFS3_.../FFS4-8/app/`

---

### 2026-02-09: Architectural Design Notes

**[Rebuild Design Document](2026-02-09_rebuild_2.md)**

**Key Decisions**:

- Package imports (workspace protocol, NOT dynamic loading)
- XYFlow for graph visualization
- WebRTC architecture (SimplePeer + DataServer signaling)
- Protocol matrix (REST + SSE + WebSocket + Native Messaging + WebRTC P2P)
- **No gRPC**: Current stack is sufficient

> "The workspaces ARE the actual applications. The FFS3 code is just the visual to these applications."

---

## Development History

Archived development logs documenting the evolution of the system.

### Archive: Development Logs

Located in **[`_archive_devlog/`](_archive_devlog/)**

| Date           | Entry                                                                            | Description                   | Status                    |
| -------------- | -------------------------------------------------------------------------------- | ----------------------------- | ------------------------- |
| **2026-02-09** | [Full Production Rebuild](_archive_devlog/2026-02-09_full_production_rebuild.md) | Original Path B rebuild plan  | Superseded by restructure |
| **2026-02-05** | [Phase 3 Implementation](_archive_devlog/2026-02-05_phase3_implementation.md)    | Multi-agent extension build   | Completed                 |
| **2026-02-05** | [Phase 3 Plan](_archive_devlog/2026-02-05_phase3_plan.md)                        | Chrome extension architecture | Completed                 |
| **2026-02-05** | [Phase 2](_archive_devlog/2026-02-05_phase2.md)                                  | Backend servers setup         | Completed                 |
| **2026-02-05** | [MVP Debugging](_archive_devlog/2026-02-05_mvp_debugging.md)                     | Initial MVP fixes             | Completed                 |

Previous architecture docs (v1) archived to **[`_archive_devlog/architecture_v1/`](_archive_devlog/architecture_v1/)**

---

## Navigation Tips

### By Task

**Setting up the system?**

- Start with [System Overview](architecture/01_system_overview.md), then [Backend Services](architecture/03_backend_services.md)

**Understanding workspace-driven architecture?**

- Read [System Overview](architecture/01_system_overview.md), then [Workspace Hierarchy](architecture/02_workspace_hierarchy.md)

**Working on backend?**

- Check [Backend Services](architecture/03_backend_services.md) and [Data Flow](architecture/07_data_flow.md)

**Building frontend applications?**

- Review [Frontend Packages](architecture/05_frontend_packages.md) and [Domains & Routing](architecture/06_domains_and_routing.md)

**Working on the Chrome extension?**

- See [Chrome Extension](architecture/04_chrome_extension.md) and [Data Flow](architecture/07_data_flow.md)

**Implementing agents?**

- See [Agent System](architecture/09_agent_system.md) and [Chrome Extension](architecture/04_chrome_extension.md)

**Need security/permissions?**

- Consult [Security](architecture/08_security.md)

### By Domain

#### FILESYST Domain (IDE workspaces)

- [Domains & Routing](architecture/06_domains_and_routing.md) + [Frontend Packages (FFS6)](architecture/05_frontend_packages.md)

#### CLOUD Domain (deployed apps)

- [Domains & Routing](architecture/06_domains_and_routing.md) + [Frontend Packages (FFS8)](architecture/05_frontend_packages.md)

#### ADMIN Domain (user management)

- [Domains & Routing](architecture/06_domains_and_routing.md) + [Frontend Packages (FFS7)](architecture/05_frontend_packages.md)

---

## Directory Structure

```text
.agent/knowledge/
├── _index.md                                        # This file
├── _archive_devlog/                                 # Historical development logs
│   ├── _index.md
│   ├── architecture_v1/                             # Archived v1 architecture docs
│   ├── 2026-02-09_full_production_rebuild.md
│   └── 2026-02-05_*.md                              # Phase 2-3 logs
├── architecture/                                    # Core architecture docs (v2.0)
│   ├── _index.md                                    # Architecture quick reference
│   ├── 01_system_overview.md                        # .agent pattern, NodeContainer
│   ├── 02_workspace_hierarchy.md                    # FFS0-8 directory map
│   ├── 03_backend_services.md                       # DataServer, GraphTool, VectorDB
│   ├── 04_chrome_extension.md                       # SW, ContextManager, sidepanel
│   ├── 05_frontend_packages.md                      # Shared libs + app packages
│   ├── 06_domains_and_routing.md                    # FILESYST/CLOUD/ADMIN routing
│   ├── 07_data_flow.md                              # Protocols & sync
│   ├── 08_security.md                               # Auth & permissions
│   └── 09_agent_system.md                           # Agents & templates
├── 2026-02-09_frontend_architecture_restructure.md  # Implementation log (728 lines)
└── 2026-02-09_rebuild_2.md                          # Design decisions
```

---

## Version History

| Version  | Date       | Major Changes                                                            |
| -------- | ---------- | ------------------------------------------------------------------------ |
| **v2.0** | 2026-02-09 | Architecture docs rewritten; workspace-driven package architecture       |
| **v1.0** | 2026-02-09 | Production rebuild (Path B - 3 backends + extension + frontend monorepo) |
| **v0.x** | 2026-02-05 | MVP phases 2-3 (backend servers, multi-agent extension)                  |

---

## Key Concepts Quick Reference

**NodeContainer**: 8-field workspace structure (manifest, instructions, rules,
skills, tools, knowledge, workflows, configs). Isomorphic to `.agent/` folder
on disk.

**Domain Types**:

- **FILESYST** - Local filesystem workspaces (IDE) - backed by Native Messaging
- **CLOUD** - Cloud-deployed applications - backed by Data Server REST
- **ADMIN** - User management & security - backed by Data Server REST

**Workspace-Driven**: Applications are defined by `.agent/` metadata in
workspace directories. FFS4-8 packages provide domain-specific viewers. Backend
context determines which frontend to load.

**Service Worker Agents**:

- **CloudAgent** - Backend API calls, workflow execution, tool search
- **DomAgent** - Browser DOM manipulation via content scripts
- **FilesystAgent** - Native filesystem access via Native Messaging

**Protocol Stack**:

- REST (:8000) - CRUD operations
- SSE (:8000) - Real-time events
- WebSocket (:8001) - Workflow execution
- Native Messaging - File operations
- WebRTC P2P - User-user communication

**Context Routing**: `ContextManager.switchWorkspaceContext()` broadcasts `CONTEXT_CHANGED` -- sidepanel loads appropriate viewer (FFS6/7/8)

---

**Last Updated**: 2026-02-09
**Repository**: FFS1_ColliderDataSystems
