# Architecture Documentation

> Component-focused architecture docs for Collider Data Systems (Feb 17 rebuild).

## Quick Reference

```
FFS1_ColliderDataSystems/
├── FFS2 (Backends + Extension)
│   ├── ColliderDataServer (:8000) — REST, SSE, WebRTC signaling
│   ├── ColliderGraphToolServer (:8001) — WebSocket workflows
│   ├── ColliderVectorDbServer (:8002) — REST semantic search
│   └── ChromeExtension — Service Worker, agents, sidepanel
├── FFS3 (Frontend Monorepo — Nx + Vite + React 19)
│   ├── apps/ffs4 — Sidepanel appnode
│   ├── apps/ffs5 — PiP appnode
│   ├── apps/ffs6 — IDE viewer appnode (default)
│   └── libs/shared-ui — Shared components + XYFlow
└── Protocols: REST · SSE · WebSocket · WebRTC · Native Messaging · gRPC · Internal
```

## Core Principle

**Workspaces ARE applications.** When an app admin creates an application, its node-containers carry:

1. Workspace context (tools, instructions, rules, knowledge)
2. Frontend pointer (`metadata_.frontend_app` → ffs4/5/6)
3. Permitted backend API set ("domain" config)

**Core flow:** Agent controls DataServer (CRUD nodes) → SSE broadcasts changes → Frontend delivers the correct appnode (ffs4/5/6) based on the selected workspace node in DB.

## Documents

| #   | Document                                                                                                                                           | Covers                                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 01  | [FFS2 Backend Services](file:///D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/01_ffs2_backend_services.md)     | DataServer, GraphToolServer, VectorDbServer — APIs, DB models, protocols |
| 02  | [FFS2 Chrome Extension](file:///D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/02_ffs2_chrome_extension.md)     | Service Worker, agents, ContextManager, sidepanel, appnode delivery      |
| 03  | [FFS3 Frontend Appnodes](file:///D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/03_ffs3_frontend_appnodes.md)   | Nx monorepo, appnode concept, ffs4/5/6, routing, XYFlow                  |
| 04  | [Communication Protocols](file:///D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/04_communication_protocols.md) | All 7 protocols, end-to-end flows, message formats                       |

## Reading Order

1. Start with **01** for backend API surface
2. Read **02** for how the extension orchestrates everything
3. Read **03** for how frontends render workspace nodes
4. Reference **04** for protocol details and flow diagrams

## Key Technologies

| Layer     | Stack                                                       |
| --------- | ----------------------------------------------------------- |
| Backend   | FastAPI, SQLAlchemy async, aiosqlite, ChromaDB, Pydantic AI |
| Extension | Plasmo, React 18, Zustand, LangGraph.js, SimplePeer         |
| Frontend  | Nx, Vite 7, React 19, Vitest 4, XYFlow (`@xyflow/react`)    |

## Archived Docs

Previous architecture docs (Feb 9 structure) are preserved in [`_archive/`](file:///D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/_archive/).
