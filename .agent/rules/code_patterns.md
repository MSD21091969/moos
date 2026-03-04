# Code Patterns

> Active patterns for FFS0 Factory (v4)

---

## Status

**Current state**: `models/`, `sdk/`, and workspace-local implementations are active.

**Active backend runtime**: MOOS (Go 1.23+) — category-theory morphism pipeline.

**Historical transitions**: tracked through git history/tags and workflow runbooks.

---

## Core Concepts

| Concept | Purpose |
| ---------- | --------------------------------- |
| Container | Workspace context holder in graph |
| Definition | Versioned I/O contract |
| Graph | Topology of nodes |
| Morphism | State mutation envelope (ADD/LINK/MUTATE/UNLINK) |
| Application | Self-hosting recursive tree (x1z) |

---

## Patterns

### NodeContainer Pattern

The same structure at all scales:

- `.agent/` folder on disk (FILESYST domain)
- `node.container` JSON field in DB (CLOUD domain)
- `user.container` JSON field in DB (ADMIN domain)

### Two-Graph Architecture

- **Container-nodes**: Rows in `nodes` table (DB) — data/workspace graph
- **View-components**: Vite+React components (FFS3 apps) — visual/UX graph
- These are related but NOT 1:1 — multiple nodes may share a view, or vice versa

### Morphism Pipeline

- LLM providers return morphism envelopes in ```json fenced blocks
- 4 operations: ADD (node), LINK (edge), MUTATE (update), UNLINK (remove edge)
- Backend parses, validates, and dispatches morphisms
- Frontend receives morphisms via WebSocket push and applies to Zustand store

### Role-Based Access

- System roles on User: `superadmin`, `collider_admin`, `app_admin`, `app_user`
- App roles on AppPermission: `app_admin`, `app_user`
- Formal request/approval flow for app access

### Phase 4 Architectural Lessons (Go Kernel Migration)

- **Do** rely purely on the Postgres Universal Graph Model (`dbStore containerStore`) for session/state persistence.
- **Do** use Go native testing constraints (e.g., `mockContainerStore` for DB outages/corrupted graph recovery).
- **Do** ensure Kubernetes/Docker compatibility by exposing Prometheus metrics at `/metrics` over standard HTTP muxes.
- **Do** run standalone standard `docker build` processes when profiling/caching the build stages instead of relying heavily on `docker compose` pipelined commands which may obfuscate logs/errors.
- **Don't** use Redis for active session/node storage in the cluster; architecture relies on universal Postgres nodes.
- **Don't** revert to or invoke legacy TypeScript implementation loops (`engine`, `data-server`, `tool-server`); they are purged and deprecated in favor of Go 1.23+ runtime execution.

