# Codebase: FFS2 ColliderBackends

> Backend services and Chrome Extension source.

## Structure

```
FFS2_ColliderBackends/
├── ColliderDataServer/              <- FastAPI Data Server
│   ├── src/
│   │   ├── main.py                  <- App entrypoint, router registration
│   │   ├── api/
│   │   │   ├── auth.py              <- Login/signup, JWT, role deps
│   │   │   ├── users.py             <- User CRUD
│   │   │   ├── apps.py              <- Application CRUD
│   │   │   ├── nodes.py             <- Node CRUD (tree operations)
│   │   │   ├── roles.py             <- System role assignment (SAD/CAD)
│   │   │   ├── app_permissions.py   <- Request/approve/reject access
│   │   │   ├── permissions.py       <- Per-app permission checks
│   │   │   ├── context.py           <- Context hydration
│   │   │   ├── sse.py               <- Server-Sent Events
│   │   │   ├── rtc.py               <- WebRTC signaling WebSocket
│   │   │   └── health.py            <- Health check endpoint
│   │   ├── core/
│   │   │   ├── auth.py              <- JWT utilities
│   │   │   ├── config.py            <- pydantic-settings
│   │   │   └── database.py          <- SQLAlchemy async engine
│   │   ├── db/
│   │   │   └── models.py            <- SQLAlchemy models
│   │   ├── schemas/
│   │   │   ├── users.py             <- User DTOs
│   │   │   ├── apps.py              <- Application DTOs
│   │   │   └── nodes.py             <- Node/Permission DTOs
│   │   └── seed.py                  <- x1z tree seeder
│   └── collider.db                  <- SQLite database (dev)
│
├── ColliderGraphToolServer/         <- Workflow engine (Gemini AI)
│   ├── src/
│   │   ├── main.py
│   │   └── graphs/engine.py
│
├── ColliderVectorDbServer/          <- Semantic search (ChromaDB)
│
└── ColliderMultiAgentsChromeExtension/ <- Plasmo Source
    ├── src/
    │   ├── background/ (Service Worker)
    │   ├── contents/ (Content Scripts)
    │   ├── sidepanel/
    │   └── popup/
```

## Database Models

### Core Enums

- **SystemRole**: `superadmin`, `collider_admin`, `app_admin`, `app_user`
- **AppRole**: `app_admin`, `app_user`

### Tables

- **users**: `id`, `username`, `password_hash`, `display_name`, `system_role`
- **applications**: `id`, `app_id`, `owner_id` (FK users), `display_name`, `config` (JSON), `root_node_id`
- **nodes**: `id`, `application_id`, `parent_id` (self-ref), `path`, `container` (JSON), `metadata_` (JSON)
- **app_permissions**: `id`, `user_id`, `application_id`, `role` (AppRole enum)
- **app_access_requests**: `id`, `user_id`, `application_id`, `message`, `status`, `requested_at`, `resolved_at`, `resolved_by`

### x1z Seed Tree

Application x1z is seeded with 4 nodes:

- `/` — root (frontend_app: x1z, frontend_route: /)
- `/admin` — admin panel (frontend_app: x1z, frontend_route: /admin)
- `/admin/assign-roles` — role assignment (frontend_app: x1z, frontend_route: /admin/roles)
- `/admin/grant-permission` — permission management (frontend_app: x1z, frontend_route: /admin/permissions)

## Developer Guide

### Running Services

Start the DataServer:

```bash
cd ColliderDataServer
uv run uvicorn src.main:app --reload --port 8000
```

Seed the database:

```bash
cd ColliderDataServer
uv run python -m src.seed
```

### Chrome Extension Development

1. `cd ColliderMultiAgentsChromeExtension`
2. `pnpm dev`
3. Load `build/chrome-mv3-dev` in `chrome://extensions`

### Key Patterns

- **Native Host**: The Extension uses `native_messaging` to talk to the local python host.
- **SSE**: Data updates flow via Server-Sent Events from `DataServer/api/v1/sse`.
- **Auth**: Username/password login returns JWT; Chrome extension planned to use Firebase.
