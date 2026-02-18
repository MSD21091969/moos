# Workspace Hierarchy

> The FFS (Factory File System) naming convention maps workspace directories to their role in the system.

## Directory Structure

```
FFS0_Factory/
├── .agent/                                    # Factory-level rules and patterns
└── workspaces/
    └── FFS1_ColliderDataSystems/              # Project root workspace
        ├── .agent/                            # Root context (manifest, knowledge, configs)
        ├── package.json                       # pnpm root package
        ├── pnpm-workspace.yaml                # Links all packages below
        │
        ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
        │   ├── .agent/                        # Backend + extension context
        │   ├── ColliderDataServer/            # FastAPI + SQLite (:8000)
        │   ├── ColliderGraphToolServer/       # WebSocket server (:8001)
        │   ├── ColliderVectorDbServer/        # ChromaDB server (:8002)
        │   └── ColliderMultiAgentsChromeExtension/  # Plasmo Chrome extension
        │
        └── FFS3_ColliderApplicationsFrontendServer/
            ├── ColliderAppFrontend/           # Shared frontend libraries
            │   └── libs/
            │       ├── api-client/            # REST/WS/SSE client wrappers
            │       ├── node-container/        # Container merge utilities
            │       ├── shared-ui/             # Reusable UI components
            │       └── workspace-router/      # Domain-to-app routing logic
            │
            ├── FFS4_application00_ColliderSidepanelAppnodeBrowser/
            │   ├── .agent/                    # Sidepanel app context
            │   └── app/                       # @collider/sidepanel-ui package
            │
            ├── FFS5_application01_ColliderPictureInPictureMainAgentSeat/
            │   ├── .agent/                    # PiP app context
            │   └── app/                       # @collider/pip-ui package
            │
            ├── FFS6_applicationx_FILESYST_ColliderIDE_appnodes/
            │   ├── .agent/                    # IDE viewer context
            │   └── app/                       # @collider/ide-viewer package
            │
            ├── FFS7_applicationz_ADMIN_ColliderAccount_appnodes/
            │   ├── .agent/                    # Admin viewer context
            │   └── app/                       # @collider/admin-viewer package
            │
            └── FFS8_application1_CLOUD_my-tiny-data-collider_appnodes/
                ├── .agent/                    # Cloud viewer context
                └── app/                       # @collider/cloud-viewer package
```

---

## Workspace Reference

### FFS0 -- Factory

**Purpose**: Top-level factory containing shared rules and patterns inherited by all projects.

**`.agent/` exports**: `rules/sandbox.md`, `rules/code_patterns.md`, `instructions/knowledge_hierarchy.md`, `instructions/instruction_inheritance.md`

---

### FFS1 -- ColliderDataSystems (Root)

**Purpose**: Project root. Defines the Collider Data Systems product, its domain configuration, and shared agent instructions.

**Key files:**
- `manifest.yaml`: Inherits from FFS0, exports to FFS2/FFS3 children
- `configs/domains.yaml`: Defines FILESYST, CLOUD, ADMIN domains
- `knowledge/architecture/`: This documentation
- `pnpm-workspace.yaml`: Links all packages in the monorepo

**pnpm workspace configuration** (`pnpm-workspace.yaml`):
```yaml
packages:
  - "FFS2_.../ColliderMultiAgentsChromeExtension"
  - "FFS3_.../collider-frontend/libs/*"
  - "FFS3_.../FFS4_.../app"
  - "FFS3_.../FFS5_.../app"
  - "FFS3_.../FFS6_.../app"
  - "FFS3_.../FFS7_.../app"
  - "FFS3_.../FFS8_.../app"
```

---

### FFS2 -- Backends + Chrome Extension

**Purpose**: All runtime code. Three Python backend servers and the Chrome extension.

| Component | Technology | Port | Role |
|-----------|-----------|------|------|
| ColliderDataServer | FastAPI + SQLite | :8000 | REST API, SSE, Auth, WebRTC signaling |
| ColliderGraphToolServer | FastAPI + WebSocket | :8001 | Graph processing, workflow execution |
| ColliderVectorDbServer | FastAPI + ChromaDB | :8002 | Semantic search, embeddings |
| ColliderMultiAgentsChromeExtension | Plasmo + React 18 | -- | Browser extension (SW + sidepanel) |

**Package name**: `collider-chrome-extension`

---

### FFS3 -- Frontend Server (Shared Libraries)

**Purpose**: Houses shared libraries consumed by FFS4-8 application packages. The `ColliderAppFrontend/libs/` directory contains reusable code; the FFS4-8 subdirectories contain domain-specific applications.

**Shared libraries:**

| Library | Package | Purpose |
|---------|---------|---------|
| `api-client` | `@collider/api-client` | DataServer, GraphServer, VectorDB client classes |
| `node-container` | `@collider/node-container` | Container merging and factory utilities |
| `shared-ui` | `@collider/shared-ui` | Button, Card, TreeView, domain colors |
| `workspace-router` | `@collider/workspace-router` | Domain-to-package routing logic |

---

### FFS4 -- Sidepanel App (Graph Viewer + Agent Seat)

**Package**: `@collider/sidepanel-ui`
**Domain**: SIDEPANEL (default view)
**Exports**: `AppTree`, `AgentSeat`, `WorkspaceBrowser`
**Key dependency**: `@xyflow/react` (graph visualization)

The primary UI package imported by the Chrome extension's sidepanel. Provides the workspace node browser (tree + graph views) and the agent interaction interface.

---

### FFS5 -- Picture-in-Picture Communication

**Package**: `@collider/pip-ui`
**Domain**: Cross-domain (communication layer)
**Exports**: `PiPWindow`, `useWebRTC`
**Key dependency**: `simple-peer` (WebRTC)

Handles user-to-user real-time communication via WebRTC P2P connections, rendered in a Document Picture-in-Picture window.

---

### FFS6 -- IDE Workspace Viewer (FILESYST)

**Package**: `@collider/ide-viewer`
**Domain**: FILESYST
**Exports**: `FileTree`, `AgentDirectoryView`

Displays local filesystem workspaces synced via Native Messaging. Shows `.agent/` folder structure and sync status.

---

### FFS7 -- Admin Workspace Viewer (ADMIN)

**Package**: `@collider/admin-viewer`
**Domain**: ADMIN
**Exports**: `UserManagement`

User account management, permissions editing, and admin container browsing.

---

### FFS8 -- Cloud Application Viewer (CLOUD)

**Package**: `@collider/cloud-viewer`
**Domain**: CLOUD
**Exports**: `CloudNodeTree`

Displays cloud-hosted application workspaces. Hierarchical node tree browser with container configuration editing.

---

## Naming Convention

The FFS prefix follows a consistent pattern:

```
FFS{N}_{role}_{description}/
```

- **N**: Workspace number (0=factory, 1=root, 2=backends, 3=frontend, 4-8=apps)
- **Role**: `application{NN}` for apps with sequence numbers, or descriptive for infrastructure
- **Description**: Human-readable purpose

Application workspaces (FFS4-8) embed domain information in their names:
- `FILESYST` = FILESYST domain
- `ADMIN` = ADMIN domain
- `CLOUD` = CLOUD domain
