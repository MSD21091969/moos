# x1z Application

> The Collider system itself is an application — x1z. Self-hosting recursive tree.

---

## Concept

x1z is the first application seeded by the ColliderDataServer. It represents the Collider platform managing itself — admin panels, role assignment, permission granting are all x1z workspace nodes.

---

## Two-Graph Architecture

### Container-Nodes (Database)

Rows in the `nodes` table. Each has:
- `path` — slash-separated address (e.g., `/admin/assign-roles`)
- `container` — JSON holding manifest, instructions, rules, knowledge
- `metadata_` — JSON with `frontend_app` and `frontend_route`

These form a tree via `parent_id` self-reference.

### View-Components (Frontend)

Next.js pages/components in FFS6 (Filesystem IDE viewer). Each renders one or more container-nodes based on `metadata_.frontend_app` and `metadata_.frontend_route`.

### Key Distinction

These two graphs are **related but NOT 1:1**:
- Multiple container-nodes may share the same view-component
- A single view-component may render different content based on which node is active
- The DB does not know or care what the frontend looks like
- The frontend reads `metadata_` to know which component to render

---

## x1z Node Tree (Seed)

```
/                               <- Root node (app shell)
├── /admin                      <- Admin panel container
│   ├── /admin/assign-roles     <- Role assignment workspace
│   └── /admin/grant-permission <- Permission management workspace
```

Each node's `metadata_` links to a frontend:

| Path | frontend_app | frontend_route |
|------|-------------|----------------|
| `/` | `x1z` | `/` |
| `/admin` | `x1z` | `/admin` |
| `/admin/assign-roles` | `x1z` | `/admin/roles` |
| `/admin/grant-permission` | `x1z` | `/admin/permissions` |

---

## RBAC for x1z

Access to x1z nodes is controlled by:

1. **System roles** (on User): `superadmin` (SAD), `collider_admin` (CAD), `app_admin`, `app_user`
2. **App roles** (on AppPermission): `app_admin` (owner), `app_user` (member)
3. **Formal request/approval flow**: Users request access, admins approve/reject

Only SAD and CAD can assign system roles. CAD cannot assign `superadmin` or `collider_admin`.

---

## How Workspaces Proliferate

1. An `app_admin` creates a new Application
2. This creates a new FFS workspace on disk AND a root node in the DB
3. The workspace gets its own `.agent/` folder (FILESYST domain)
4. The root node gets a `container` JSON (CLOUD domain)
5. Both represent the same workspace — synced via the DataServer
6. Users request access → admin approves → AppPermission created with role

---

_v1.0.0 — 2026-02-17_
