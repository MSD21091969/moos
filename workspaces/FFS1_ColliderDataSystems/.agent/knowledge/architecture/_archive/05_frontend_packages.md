# Frontend Packages

> The frontend is organized as workspace-linked npm packages: 4 shared libraries + 5 application packages, all built with Vite + React 18 + TypeScript.

## Package Map

```
FFS3_ColliderApplicationsFrontendServer/
├── ColliderAppFrontend/libs/          # Shared libraries
│   ├── api-client/                    # @collider/api-client
│   ├── node-container/                # @collider/node-container
│   ├── shared-ui/                     # @collider/shared-ui
│   └── workspace-router/             # @collider/workspace-router
│
├── FFS4_.../app/                      # @collider/sidepanel-ui
├── FFS5_.../app/                      # @collider/pip-ui
├── FFS6_.../app/                      # @collider/ide-viewer
├── FFS7_.../app/                      # @collider/admin-viewer
└── FFS8_.../app/                      # @collider/cloud-viewer
```

All packages are linked via `pnpm-workspace.yaml` at the FFS1 root. Application packages reference shared libraries using the workspace protocol: `"@collider/shared-ui": "workspace:*"`.

---

## Shared Libraries

### api-client (`@collider/api-client`)

**Path**: `ColliderAppFrontend/libs/api-client/`
**Exports**: `DataServerClient`, `GraphServerClient`, `VectorServerClient`

HTTP/WebSocket client wrappers for the three backend services:

| Client               | Connects To                   | Protocol   |
| -------------------- | ----------------------------- | ---------- |
| `DataServerClient`   | ColliderDataServer :8000      | REST + SSE |
| `GraphServerClient`  | ColliderGraphToolServer :8001 | WebSocket  |
| `VectorServerClient` | ColliderVectorDbServer :8002  | REST       |

Also exports shared API types used across packages.

---

### node-container (`@collider/node-container`)

**Path**: `ColliderAppFrontend/libs/node-container/`
**Exports**: `ContainerMerger`, `emptyContainer`

Utilities for working with NodeContainer data:
- `ContainerMerger`: Merges parent + child containers following inheritance strategy
- `emptyContainer()`: Factory function returning a blank NodeContainer with all 8 fields initialized

---

### shared-ui (`@collider/shared-ui`)

**Path**: `ColliderAppFrontend/libs/shared-ui/`
**Exports**: `Button`, `Card`, `TreeView`, `getDomainColor`, `getDomainBgColor`

Reusable UI components and utilities:

| Export                     | Description                                            |
| -------------------------- | ------------------------------------------------------ |
| `Button`                   | Standard button component                              |
| `Card`                     | Container card component                               |
| `TreeView`                 | Generic recursive tree renderer (accepts `TreeNode[]`) |
| `getDomainColor(domain)`   | Returns text color for domain type                     |
| `getDomainBgColor(domain)` | Returns background color for domain type               |

**Domain color mapping:**

| Domain     | Color              | Background              |
| ---------- | ------------------ | ----------------------- |
| CLOUD      | `#60a5fa` (blue)   | `rgba(96,165,250,0.1)`  |
| FILESYST   | `#34d399` (green)  | `rgba(52,211,153,0.1)`  |
| ADMIN      | `#f472b6` (pink)   | `rgba(244,114,182,0.1)` |
| SIDEPANEL  | `#a78bfa` (purple) | `rgba(167,139,250,0.1)` |
| AGENT_SEAT | `#fbbf24` (amber)  | `rgba(251,191,36,0.1)`  |

---

### workspace-router (`@collider/workspace-router`)

**Path**: `ColliderAppFrontend/libs/workspace-router/`
**Exports**: `getAppRouteForContext`, `getDomainFromApp`, `WorkspaceType`, `AppRoute`

Maps domain types to their corresponding frontend application packages:

```typescript
type WorkspaceType = "FILESYST" | "CLOUD" | "ADMIN" | "SIDEPANEL";

interface AppRoute {
  app: string;        // FFS workspace name
  packageName: string; // npm package name
}

function getAppRouteForContext(domain: WorkspaceType): AppRoute;
function getDomainFromApp(app: Application): WorkspaceType;
```

**Routing table:**

| Domain    | FFS  | Package                  |
| --------- | ---- | ------------------------ |
| SIDEPANEL | FFS4 | `@collider/sidepanel-ui` |
| FILESYST  | FFS6 | `@collider/ide-viewer`   |
| ADMIN     | FFS7 | `@collider/admin-viewer` |
| CLOUD     | FFS8 | `@collider/cloud-viewer` |

---

## Application Packages

All application packages follow the same structure:

```
FFS{N}_.../
├── .agent/                  # Workspace context (manifest, knowledge, configs)
└── app/                     # npm package
    ├── package.json         # @collider/{name}
    ├── tsconfig.json
    ├── vite.config.ts       # Library mode build
    └── src/
        ├── index.tsx        # Public exports
        ├── components/      # React components
        ├── stores/          # Zustand stores (if needed)
        ├── hooks/           # Custom hooks (if needed)
        ├── nodes/           # Custom XYFlow nodes (FFS4 only)
        └── types/           # Local TypeScript types
```

### Build Configuration

Each package builds as an ES library via Vite:

```typescript
// vite.config.ts (common pattern)
export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.tsx"),
      formats: ["es"],
      fileName: "index",
    },
    rollupOptions: {
      external: ["react", "react-dom"],
    },
  },
});
```

Output: `dist/index.js` + `dist/index.d.ts`

### Import Strategy

Application packages are consumed via **static workspace protocol imports**, not dynamic loading:

```typescript
// In FFS2 Chrome extension sidepanel:
import { AppTree, AgentSeat } from "@collider/sidepanel-ui";
```

pnpm resolves `workspace:*` to the local package. Plasmo bundles the imported code into the extension build. This is a compile-time integration, not runtime dynamic loading.

---

### FFS4: `@collider/sidepanel-ui`

**Full name**: `FFS4_application00_ColliderSidepanelAppnodeBrowser`

| Export             | Description                                        |
| ------------------ | -------------------------------------------------- |
| `AppTree`          | Hierarchical node tree (domain-colored, clickable) |
| `AgentSeat`        | Agent chat/interaction interface                   |
| `WorkspaceBrowser` | XYFlow canvas with custom domain nodes             |

**Key dependency**: `@xyflow/react` ^12 (React Flow) for graph visualization

Custom XYFlow node types:
- `FilesystNode` -- Green-themed FILESYST domain node
- `CloudNode` -- Blue-themed CLOUD domain node
- `AdminNode` -- Pink-themed ADMIN domain node

---

### FFS5: `@collider/pip-ui`

**Full name**: `FFS5_application01_ColliderPictureInPictureMainAgentSeat`

| Export      | Description                           |
| ----------- | ------------------------------------- |
| `PiPWindow` | Complete PiP window component         |
| `useWebRTC` | React hook for WebRTC P2P connections |

**Key dependency**: `simple-peer` ^9 (WebRTC abstraction)

The `useWebRTC` hook connects to the DataServer's `/ws/rtc/` WebSocket endpoint for signaling, then establishes a P2P connection via SimplePeer.

---

### FFS6: `@collider/ide-viewer`

**Full name**: `FFS6_applicationx_FILESYST_ColliderIDE_appnodes`

| Export               | Description               |
| -------------------- | ------------------------- |
| `FileTree`           | Filesystem tree navigator |
| `AgentDirectoryView` | `.agent/` folder browser  |

Displays local workspace structure synced via Native Messaging.

---

### FFS7: `@collider/admin-viewer`

**Full name**: `FFS7_applicationz_ADMIN_ColliderAccount_appnodes`

| Export           | Description                       |
| ---------------- | --------------------------------- |
| `UserManagement` | User CRUD + permissions interface |

Admin domain workspace viewer for user account management.

---

### FFS8: `@collider/cloud-viewer`

**Full name**: `FFS8_application1_CLOUD_my-tiny-data-collider_appnodes`

| Export          | Description                            |
| --------------- | -------------------------------------- |
| `CloudNodeTree` | Cloud workspace node hierarchy browser |

CLOUD domain workspace viewer for deployed application management.
