# Collider Data Systems — Knowledge Base Index

> Central documentation for the Collider Multi-Agent System architecture, implementation, and development history.

---

## 🚀 Quick Start

**New to Collider?** Start here:

1. **[Architecture Overview](architecture/00_overview.md)** - System architecture at a glance
2. **[Components Guide](architecture/01_components.md)** - Core components and their roles
3. **[Frontend Architecture Restructure (2026-02-09)](2026-02-09_frontend_architecture_restructure.md)** - Latest implementation (workspace-driven apps)
4. **[Workspace Strategy](architecture/08_workspace_strategy.md)** - How workspaces ARE the applications

---

## 📊 Current System Status

**Latest Implementation**: Frontend Architecture Restructure (2026-02-09)

### Production Stack ✅

| Component                   | Technology          | Port  | Status                                |
| --------------------------- | ------------------- | ----- | ------------------------------------- |
| **ColliderDataServer**      | FastAPI + SQLite    | :8000 | ✅ Running (11 apps seeded, 8/8 tests) |
| **ColliderGraphToolServer** | FastAPI + WebSocket | :8001 | ✅ Running                             |
| **ColliderVectorDbServer**  | FastAPI + ChromaDB  | :8002 | ✅ Running                             |
| **Chrome Extension**        | Plasmo + React 18   | -     | ✅ Built (381 kB sidepanel)            |
| **Frontend Packages**       | Vite + React 18     | -     | ✅ 7 packages (~165 kB)                |

### Application Packages (FFS3-FFS8)

| Package                         | Purpose                       | Size     | Domain    |
| ------------------------------- | ----------------------------- | -------- | --------- |
| **FFS4** @collider/sidepanel-ui | Workspace browser, agent seat | 25.04 kB | Sidepanel |
| **FFS5** @collider/pip-ui       | WebRTC user-user comms        | 24.57 kB | PiP       |
| **FFS6** @collider/ide-viewer   | File tree, .agent/ viewer     | 23.85 kB | FILESYST  |
| **FFS7** @collider/admin-viewer | User management               | 22.57 kB | ADMIN     |
| **FFS8** @collider/cloud-viewer | Cloud app viewer              | 22.74 kB | CLOUD     |

**Architecture**: Workspace-driven, where "workspaces ARE the applications"

---

## 📚 Architecture Documentation

### Foundation & Core Concepts

| Document                                                              | Description                   | Key Topics                            |
| --------------------------------------------------------------------- | ----------------------------- | ------------------------------------- |
| **[00_overview.md](architecture/00_overview.md)**                     | System architecture overview  | High-level design, data flow          |
| **[01_components.md](architecture/01_components.md)**                 | Core components guide         | Servers, extension, frontend packages |
| **[02_domains.md](architecture/02_domains.md)**                       | Domain system                 | FILESYST, CLOUD, ADMIN domains        |
| **[08_workspace_strategy.md](architecture/08_workspace_strategy.md)** | Workspace-driven architecture | `.agent/` metadata, context routing   |

### Backend & Data

| Document                                            | Description                  | Key Topics                                  |
| --------------------------------------------------- | ---------------------------- | ------------------------------------------- |
| **[02_backend.md](architecture/02_backend.md)**     | Backend servers              | DataServer, GraphToolServer, VectorDbServer |
| **[04_data_flow.md](architecture/04_data_flow.md)** | Data protocols & sync        | REST, WebSocket, SSE, Native Messaging      |
| **[05_security.md](architecture/05_security.md)**   | Authentication & permissions | JWT, role-based access, CORS                |

### Frontend & Integration

| Document                                                | Description           | Key Topics                   |
| ------------------------------------------------------- | --------------------- | ---------------------------- |
| **[03_frontend.md](architecture/03_frontend.md)**       | Frontend architecture | Chrome extension, React apps |
| **[06_integration.md](architecture/06_integration.md)** | Agent integration     | LangGraph ↔ Pydantic AI      |
| **[07_templates.md](architecture/07_templates.md)**     | Code templates        | Boilerplate patterns         |

---

## 🛠️ Implementation Guides

Recent major implementations with full technical details:

### 2026-02-09: Frontend Architecture Restructure

**[📄 Full Implementation Log](2026-02-09_frontend_architecture_restructure.md)** (728 lines)

**Summary**: Transformed from monolithic portal to modular, workspace-driven application packages.

**What Was Built**:
- ✅ 9 core components (FETCH_TREE fix, WebRTC endpoint, FFS3 restructure, FFS4-8 packages, context routing)
- ✅ 7 frontend packages (~165 kB total, gzipped: ~46 kB)
- ✅ Workspace-driven architecture: "workspaces ARE the applications"
- ✅ Context-aware routing (ContextManager + workspace-router)
- ✅ WebRTC signaling for user-user communication
- ✅ Fixed sharp native module build issue

**Key Files**:
- Backend: `FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/src/api/rtc.py`
- Extension: `ColliderMultiAgentsChromeExtension/src/background/context-manager.ts`
- Packages: `FFS3_ColliderApplicationsFrontendServer/FFS4-8/app/`

**Build Time**: 3.7 seconds for extension, all packages compile successfully

---

### 2026-02-09: Architectural Design Notes

**[📄 Rebuild Design Document](2026-02-09_rebuild_2.md)**

**Key Decisions**:
- Package imports (workspace protocol, NOT dynamic loading)
- XYFlow for graph visualization
- WebRTC architecture (SimplePeer + DataServer signaling)
- Protocol matrix (REST + SSE + WebSocket + Native Messaging + WebRTC P2P)
- **No gRPC**: Current stack is sufficient

**Architecture Insights**:
> "The workspaces ARE the actual applications. The FFS3 code is just the visual to these applications."

---

## 📖 Development History

Archived development logs documenting the evolution of the system:

### Archive: Development Logs

Located in **[`_archive_devlog/`](_archive_devlog/)**

| Date           | Entry                                                                            | Description                   | Status                      |
| -------------- | -------------------------------------------------------------------------------- | ----------------------------- | --------------------------- |
| **2026-02-09** | [Full Production Rebuild](_archive_devlog/2026-02-09_full_production_rebuild.md) | Original Path B rebuild plan  | ✅ Superseded by restructure |
| **2026-02-05** | [Phase 3 Implementation](_archive_devlog/2026-02-05_phase3_implementation.md)    | Multi-agent extension build   | ✅ Completed                 |
| **2026-02-05** | [Phase 3 Plan](_archive_devlog/2026-02-05_phase3_plan.md)                        | Chrome extension architecture | ✅ Completed                 |
| **2026-02-05** | [Phase 2](_archive_devlog/2026-02-05_phase2.md)                                  | Backend servers setup         | ✅ Completed                 |
| **2026-02-05** | [MVP Debugging](_archive_devlog/2026-02-05_mvp_debugging.md)                     | Initial MVP fixes             | ✅ Completed                 |

**Note**: These logs are preserved for historical context but reflect earlier system states. Refer to current implementation guides above for up-to-date architecture.

---

## 🧭 Navigation Tips

### By Task

**Setting up the system?**
→ Start with [Architecture Overview](architecture/00_overview.md), then [Components Guide](architecture/01_components.md)

**Understanding workspace-driven architecture?**
→ Read [Workspace Strategy](architecture/08_workspace_strategy.md), then [Frontend Architecture Restructure](2026-02-09_frontend_architecture_restructure.md)

**Working on backend?**
→ Check [Backend Guide](architecture/02_backend.md) and [Data Flow](architecture/04_data_flow.md)

**Building frontend applications?**
→ Review [Frontend Guide](architecture/03_frontend.md) and [Implementation Log](2026-02-09_frontend_architecture_restructure.md) Components 3-8

**Implementing agents?**
→ See [Integration Guide](architecture/06_integration.md) and [Components Guide](architecture/01_components.md)

**Need security/permissions?**
→ Consult [Security Guide](architecture/05_security.md)

### By Domain

**FILESYST Domain (IDE workspaces)**
→ [Domains](architecture/02_domains.md) + [FFS6 Implementation](2026-02-09_frontend_architecture_restructure.md#component-6-ffs6-ide-workspace-viewer-filesyst)

**CLOUD Domain (deployed apps)**
→ [Domains](architecture/02_domains.md) + [FFS8 Implementation](2026-02-09_frontend_architecture_restructure.md#component-8-ffs8-cloud-workspace-viewer)

**ADMIN Domain (user management)**
→ [Domains](architecture/02_domains.md) + [FFS7 Implementation](2026-02-09_frontend_architecture_restructure.md#component-7-ffs7-admin-workspace-viewer)

---

## 📁 Directory Structure

```
.agent/knowledge/
├── _index.md                                        # This file
├── _archive_devlog/                                 # Historical development logs
│   ├── 2026-02-09_full_production_rebuild.md
│   ├── 2026-02-05_*.md                              # Phase 2-3 logs
│   └── _index.md
├── architecture/                                    # Core architecture docs
│   ├── _index.md
│   ├── 00_overview.md                               # Start here
│   ├── 01_components.md                             # Component guide
│   ├── 02_backend.md & 02_domains.md                # Backend + domains
│   ├── 03_frontend.md                               # Frontend architecture
│   ├── 04_data_flow.md                              # Protocols & sync
│   ├── 05_security.md                               # Auth & permissions
│   ├── 06_integration.md                            # Agent integration
│   ├── 07_templates.md                              # Code templates
│   └── 08_workspace_strategy.md                     # Workspace-driven design
├── 2026-02-09_frontend_architecture_restructure.md  # Latest implementation (728 lines)
└── 2026-02-09_rebuild_2.md                          # Design decisions
```

---

## 🔄 Version History

| Version  | Date       | Major Changes                                                            |
| -------- | ---------- | ------------------------------------------------------------------------ |
| **v2.0** | 2026-02-09 | Frontend architecture restructure (9 components, workspace-driven)       |
| **v1.0** | 2026-02-09 | Production rebuild (Path B - 3 backends + extension + frontend monorepo) |
| **v0.x** | 2026-02-05 | MVP phases 2-3 (backend servers, multi-agent extension)                  |

---

## 💡 Key Concepts Quick Reference

**NodeContainer**: Hierarchical data structure with path-based addressing (`/parent/child`)

**Domain Types**:
- **FILESYST** - Local filesystem workspaces (IDE)
- **CLOUD** - Cloud-deployed applications
- **ADMIN** - User management & security

**Workspace-Driven**: Applications are defined by `.agent/` metadata in workspace directories. FFS4-8 packages provide domain-specific viewers.

**Service Worker Agents**:
- **DOMAgent** - Browser DOM manipulation
- **CloudAgent** - Backend API calls
- **FilesystAgent** - Native filesystem access

**Protocol Stack**:
- REST (:8000) - CRUD operations
- SSE (:8000) - Real-time events
- WebSocket (:8001) - Workflow execution
- Native Messaging - File operations
- WebRTC P2P - User-user communication

**Context Routing**: `ContextManager.switchWorkspaceContext()` → broadcasts `CONTEXT_CHANGED` → sidepanel loads appropriate viewer (FFS6/7/8)

---

**Last Updated**: 2026-02-09
**Maintainer**: Claude (Sonnet 4)
**Repository**: FFS1_ColliderDataSystems
