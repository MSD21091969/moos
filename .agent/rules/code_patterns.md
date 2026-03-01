# Code Patterns

> Active patterns for FFS0 Factory (v3)

---

## Status

**Current state**: `models/`, `sdk/`, and workspace-local implementations are active.

**Historical transitions**: tracked through git history/tags and workflow runbooks.

---

## Core Concepts

| Concept | Purpose |
| ---------- | --------------------------------- |
| Container | Workspace context holder in graph |
| Definition | Versioned I/O contract |
| Graph | Topology of nodes |
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
- **View-components**: Next.js pages/components (FFS6) — visual/UX graph
- These are related but NOT 1:1 — multiple nodes may share a view, or vice versa

### Role-Based Access

- System roles on User: `superadmin`, `collider_admin`, `app_admin`, `app_user`
- App roles on AppPermission: `app_admin`, `app_user`
- Formal request/approval flow for app access
