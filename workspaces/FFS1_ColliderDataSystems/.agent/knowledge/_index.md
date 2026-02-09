# Knowledge Base

> Architecture and domain knowledge for Collider Data Systems.

## Quick Start

- **[RUNNING.md](RUNNING.md)** - How to run the MVP stack

## Folders

| Folder        | Contents                          |
| ------------- | --------------------------------- |
| architecture/ | System architecture documentation |
| devlog/       | Development session logs          |

## Architecture Documents

| #   | Document                                            | Description                       |
| --- | --------------------------------------------------- | --------------------------------- |
| 1   | [01_foundation.md](architecture/01_foundation.md)   | NodeContainer, domains, hierarchy |
| 2   | [02_backend.md](architecture/02_backend.md)         | Servers, database, CORS setup     |
| 3   | [03_frontend.md](architecture/03_frontend.md)       | Chrome Extension, Portal UI       |
| 4   | [04_data_flow.md](architecture/04_data_flow.md)     | Protocols, messages, sync         |
| 5   | [05_security.md](architecture/05_security.md)       | Auth, permissions, secrets        |
| 6   | [06_integration.md](architecture/06_integration.md) | LangGraph ↔ Pydantic AI           |

## Development Log

| Date       | Entry                                                                | Status    |
| ---------- | -------------------------------------------------------------------- | --------- |
| 2026-02-09 | [Full Production Rebuild (Path B)](2026-02-09_full_production_rebuild.md) | **Completed** |
| 2026-02-05 | [Phase 2](devlog/2026-02-05_phase2.md)                               | Completed |
| 2026-02-05 | [Phase 3 Plan](devlog/2026-02-05_phase3_plan.md)                     | Completed |
| 2026-02-05 | [Phase 3 Implementation](devlog/2026-02-05_phase3_implementation.md) | Completed |
| 2026-02-05 | [MVP Debugging](devlog/2026-02-05_mvp_debugging.md)                  | Completed |

## Production Status

**Fully Operational (2026-02-09) - Path B Complete:**
- ColliderDataServer (FastAPI + SQLite :8000) ✅ — 11 apps seeded, 8/8 tests passing
- ColliderGraphToolServer (FastAPI + WebSocket :8001) ✅
- ColliderVectorDbServer (FastAPI + ChromaDB :8002) ✅
- Chrome Extension (Plasmo + React 18) ✅ — Built (18MB)
- Frontend Monorepo (Nx + Next.js :3000) ✅ — 3 shared libs + portal app
- **Total**: ~90 source files, 68,710 insertions (commit 4cf153c)

