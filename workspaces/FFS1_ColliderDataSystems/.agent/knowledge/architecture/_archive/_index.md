# Architecture Documentation

> **Collider Data Systems v2.0** -- Workspace-driven package architecture
> Documentation regenerated: 2026-02-09

## Quick Reference

```
FFS1 (Root)
├── FFS2 (Backends + Chrome Extension)
│   ├── ColliderDataServer         FastAPI + SQLite     :8000
│   ├── ColliderGraphToolServer    WebSocket            :8001
│   ├── ColliderVectorDbServer     ChromaDB             :8002
│   └── Chrome Extension           Plasmo + React 18
│
└── FFS3 (Frontend Packages)
    ├── Shared libs: api-client, node-container, shared-ui, workspace-router
    ├── FFS4  @collider/sidepanel-ui    (graph viewer + agent seat)
    ├── FFS5  @collider/pip-ui          (WebRTC PiP communication)
    ├── FFS6  @collider/ide-viewer      (FILESYST domain)
    ├── FFS7  @collider/admin-viewer    (ADMIN domain)
    └── FFS8  @collider/cloud-viewer    (CLOUD domain)
```

## Documents

| #   | Document                                           | Topic                                                              |
| --- | -------------------------------------------------- | ------------------------------------------------------------------ |
| 01  | [System Overview](./01_system_overview.md)         | Core concepts, .agent pattern, NodeContainer, manifest inheritance |
| 02  | [Workspace Hierarchy](./02_workspace_hierarchy.md) | FFS0-8 directory map, workspace purposes, pnpm configuration       |
| 03  | [Backend Services](./03_backend_services.md)       | DataServer, GraphToolServer, VectorDbServer, database models       |
| 04  | [Chrome Extension](./04_chrome_extension.md)       | Service worker, ContextManager, sidepanel, message routing         |
| 05  | [Frontend Packages](./05_frontend_packages.md)     | Shared libraries, application packages, build configuration        |
| 06  | [Domains & Routing](./06_domains_and_routing.md)   | FILESYST/CLOUD/ADMIN domains, context-driven viewer routing        |
| 07  | [Data Flow](./07_data_flow.md)                     | 6 protocols, message types, SSE, sync flows                        |
| 08  | [Security](./08_security.md)                       | Firebase Auth, permissions, secrets, CORS, context layers          |
| 09  | [Agent System](./09_agent_system.md)               | LangGraph.js, Pydantic AI, 3 browser agents, templates             |

## Reading Order

**New to the system?** Read in this order:

1. **01 System Overview** -- Understand what Collider is and the `.agent/` pattern
2. **02 Workspace Hierarchy** -- See how the codebase is organized (FFS0-8)
3. **06 Domains & Routing** -- Understand the three domains and how routing works
4. **03 Backend Services** -- Learn the data model and API surface
5. **04 Chrome Extension** -- Understand the runtime environment
6. **05 Frontend Packages** -- See how UI packages connect
7. **09 Agent System** -- Learn how AI agents operate
8. **07 Data Flow** -- Deep dive into communication protocols
9. **08 Security** -- Authentication, authorization, secrets

## Core Principle

```
.agent/ folder = NodeContainer = workspace identity

  Everything is the same pattern at different scales:
  - A folder on disk (.agent/)
  - A JSON field in SQLite (node.container)
  - A user's context (user.container)

  Workspaces ARE the applications.
  Backend context determines frontend.
  Agents operate within workspace boundaries.
```

## Key Facts

- **Database**: SQLite (via SQLAlchemy async + aiosqlite)
- **Extension**: Plasmo + React 18 + TypeScript (Manifest V3)
- **Package Manager**: pnpm with workspace protocol
- **State**: Zustand 5 (sidepanel), chrome.storage.session (SW)
- **Auth**: Firebase Auth (Google sign-in)
- **Monorepo**: pnpm-workspace.yaml at FFS1 root links all packages

---

*Previous architecture docs archived to `_archive_devlog/architecture_v1/`*
