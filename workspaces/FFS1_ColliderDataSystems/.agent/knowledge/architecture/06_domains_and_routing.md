# Domains and Routing

> Three domains (FILESYST, CLOUD, ADMIN) determine how workspaces are stored, accessed, and displayed.

## Domain Definitions

Source: `.agent/configs/domains.yaml`

| Domain   | Backend          | Context Source              | Description                         |
| -------- | ---------------- | --------------------------- | ----------------------------------- |
| FILESYST | Native Messaging | `.agent/` folders on disk   | Local file-based IDE workspaces     |
| CLOUD    | Data Server REST | `node.container` JSON field | Cloud-hosted application workspaces |
| ADMIN    | Data Server REST | `user.container` JSON field | User account management             |

All three domains use the same NodeContainer structure. The difference is where the container data lives and how it's accessed.

---

## Domain Data Flow

### FILESYST Domain

```
Local Filesystem                  Chrome Extension              Data Server
.agent/ folder ──► Native Host ──► FilesystAgent (SW) ──► POST /api/v1/sync
                                                           │
                                   ◄────── SSE ◄──────────┘
```

- Data lives on disk as `.agent/` folder hierarchies
- Accessed via Chrome Native Messaging (read_file, write_file, list_dir)
- Synced to DataServer for cloud availability
- Displayed by `@collider/ide-viewer` (FFS6)

### CLOUD Domain

```
Data Server                       Chrome Extension
SQLite tables ──► REST API ──► CloudAgent (SW) ──► Sidepanel UI
  applications
  nodes (container JSON)
```

- Data lives in SQLite `nodes.container` JSON field
- Accessed via DataServer REST API
- Real-time updates via SSE
- Displayed by `@collider/cloud-viewer` (FFS8)

### ADMIN Domain

```
Data Server                       Chrome Extension
SQLite tables ──► REST API ──► ContextManager ──► Sidepanel UI
  users (system_role)
  app_permissions (role enum)
  app_access_requests
```

- User settings and preferences managed via DataServer API
- System roles control platform-level access
- Accessed via DataServer REST API
- Displayed by `@collider/admin-viewer` (FFS7)

---

## Context-Driven Routing

### How It Works

The service worker determines which frontend viewer to load based on the active application's domain:

```
User selects app
      │
      ▼
ContextManager.switchWorkspaceContext(appId)
      │
      ├── Update user.active_application
      ├── Persist to chrome.storage.session
      │
      ▼
ContextManager.getActiveWorkspaceType()
      │
      ├── Find app in applications list
      ├── Read app.config.domain
      │
      ▼
Broadcast: { type: "CONTEXT_CHANGED", payload: { appId, workspaceType } }
      │
      ▼
Sidepanel receives message
      │
      ▼
workspace-router.getAppRouteForContext(workspaceType)
      │
      ▼
Load appropriate viewer component
```

### Routing Table

| App Domain           | Workspace Type | Viewer Package           | FFS  |
| -------------------- | -------------- | ------------------------ | ---- |
| (none/default)       | SIDEPANEL      | `@collider/sidepanel-ui` | FFS4 |
| `domain: "FILESYST"` | FILESYST       | `@collider/ide-viewer`   | FFS6 |
| `domain: "ADMIN"`    | ADMIN          | `@collider/admin-viewer` | FFS7 |
| `domain: "CLOUD"`    | CLOUD          | `@collider/cloud-viewer` | FFS8 |

### Implementation

Source: `src/background/context-manager.ts`

```typescript
getActiveWorkspaceType(): string {
  const activeApp = this.context.applications.find(
    (app) => app.app_id === this.context.user?.active_application
  );
  if (!activeApp) return "SIDEPANEL";
  const domain = (activeApp.config as any)?.domain;
  return domain || "CLOUD";
}
```

Source: `ColliderAppFrontend/libs/workspace-router/src/index.ts`

```typescript
function getAppRouteForContext(domain: WorkspaceType): AppRoute {
  switch (domain) {
    case "FILESYST":  return { app: "FFS6", packageName: "@collider/ide-viewer" };
    case "ADMIN":     return { app: "FFS7", packageName: "@collider/admin-viewer" };
    case "CLOUD":     return { app: "FFS8", packageName: "@collider/cloud-viewer" };
    case "SIDEPANEL": return { app: "FFS4", packageName: "@collider/sidepanel-ui" };
  }
}
```

---

## Application Configuration vs. Workspace Context

Two separate configuration layers govern applications:

### Application Config (Backend)

Stored in `applications.config` JSON field. Managed by admin users. Determines:
- Domain type (`FILESYST`, `CLOUD`, `ADMIN`)
- Feature flags
- Access restrictions
- Backend behavior

### Workspace Context (.agent/)

Stored in `.agent/` folders or `node.container` JSON. Defines agent intelligence:
- Instructions (what agents should do)
- Rules (constraints on agent behavior)
- Tools (available capabilities)
- Knowledge (reference material)
- Workflows (multi-step plans)

**Key distinction**: Application config is *governance* (who can do what). Workspace context is *intelligence* (how agents behave).

---

## Application Ownership

```
User (system_role) ──owns──► Application ──permits──► User (via AppPermission)
                                 │
                                 ├── config.domain → determines viewer package
                                 └── root_node_id → top of node tree
```

- Users with `system_role >= app_admin` can create/modify applications
- `AppPermission` controls per-user access via `role` enum (`app_admin`, `app_user`)
- Formal request/approval flow: users request access → admins approve/reject → AppPermission created
- Domain type in config routes to the correct viewer
- Each application has a root node that starts its NodeContainer tree
