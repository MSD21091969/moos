# FFS3 Frontend Appnodes

> Nx monorepo in `FFS3_ColliderApplicationsFrontendServer/`. Vite + React 19, Next.js optional.

## Core Concept: Workspace = Application

**Every workspace IS an application.** When an app admin creates an application:

1. A root node is created with a **NodeContainer** carrying workspace context (tools, instructions, rules, knowledge, skills, workflows, configs)
2. The node's `metadata_.frontend_app` field points to the correct frontend code (`ffs4`, `ffs5`, or `ffs6`)
3. The application's `config` JSON carries a **"domain" config** — a label for the set of permitted backend APIs (e.g. FILESYST = native messaging + sync APIs, CLOUD = REST + SSE, ADMIN = user management APIs)

This is NOT an abstract concept — the node-container literally IS the workspace's `.agent/` directory, serialized into the database.

---

## Nx Workspace Structure

```
FFS3_ColliderApplicationsFrontendServer/   ← Nx workspace root
├── apps/
│   ├── ffs4/       ← Sidepanel appnode       (port 4201)
│   ├── ffs5/       ← PiP appnode             (port 4202)
│   └── ffs6/       ← IDE viewer appnode      (port 4200, default)
├── libs/
│   └── shared-ui/  ← @collider/shared-ui
├── nx.json         ← @nx/vite plugin, defaultProject: ffs6
├── package.json    ← React 19, Vite 7, Vitest 4
└── tsconfig.base.json ← Path aliases
```

### Each App Structure

```
apps/ffs6/
├── src/
│   ├── app/
│   │   ├── app.tsx           ← Root component + router
│   │   └── app.module.css
│   ├── components/           ← App-specific components
│   ├── hooks/                ← Custom hooks
│   ├── stores/               ← Zustand stores
│   ├── types/                ← TypeScript interfaces
│   ├── main.tsx              ← Entry point
│   └── styles.css            ← Global styles
├── index.html
├── vite.config.mts           ← Vite config
├── project.json              ← Nx targets (build, serve, test, lint)
└── tsconfig.json
```

---

## Appnodes

| App    | Name               | Purpose                                                          | Default Port |
| ------ | ------------------ | ---------------------------------------------------------------- | ------------ |
| `ffs4` | Sidepanel Appnode  | Agent seat, app tree browser, workspace navigator                | 4201         |
| `ffs5` | PiP Appnode        | Picture-in-Picture communication window (WebRTC P2P)             | 4202         |
| `ffs6` | IDE Viewer Appnode | Renders the selected workspace node's view — **default project** | 4200         |

Each appnode is a standalone Vite + React 19 app that receives workspace context from the extension and renders the appropriate view.

### How Appnodes Are Selected

```
1. User selects a node in the sidepanel
2. Extension reads node.metadata_.frontend_app
3. Extension routes to the correct appnode:
   - "ffs4" → Sidepanel app
   - "ffs5" → PiP window
   - "ffs6" → IDE viewer
4. Appnode receives node context + renders workspace view
```

### ffs4 — Sidepanel Appnode

The sidepanel that lives inside the Chrome extension's side panel:

- Application selector (switch between user's apps)
- Node tree browser (navigate workspace hierarchy)
- Agent chat interface (query the active agent)
- Status bar (SSE, auth, connection indicators)

### ffs5 — PiP Appnode

Picture-in-Picture floating window for communication:

- WebRTC P2P video/audio
- Shared data channel for collaboration
- Always-on-top window via Chrome PiP API

### ffs6 — IDE Viewer Appnode

The main workspace view — renders whatever the selected node represents:

- XYFlow graph visualization of node trees
- Code/content viewer for individual nodes
- Node editor for modifying container content
- This is the **default project** in `nx.json`

---

## Shared Library: libs/shared-ui

```typescript
import { SharedUi, NodeGraph } from "@collider/shared-ui";
```

Path alias in `tsconfig.base.json`:

```json
{
  "paths": {
    "@collider/shared-ui": ["libs/shared-ui/src/index.ts"]
  }
}
```

Contents:

- **Common components**: Button, Input, Modal, Toast, etc.
- **XYFlow graph components**: NodeGraph, WorkspaceNode, etc.
- **Layout components**: Sidebar, Panel, Toolbar
- **Hooks**: useTheme, useMediaQuery
- **Utilities**: formatPath, classNames, etc.

---

## Backend API Configs ("Domains")

> **Not an architectural concept** — just a label for a set of permitted backend APIs.

When an application is created, its `config.domain` field picks from:

| Config Label | Permitted APIs                               | Use Case             |
| ------------ | -------------------------------------------- | -------------------- |
| `FILESYST`   | Native Messaging, sync APIs, file operations | Local workspace apps |
| `CLOUD`      | REST API, SSE, WebSocket workflows           | Cloud-hosted apps    |
| `ADMIN`      | User management, role assignment, secrets    | System management    |

The node-container carries this config. The frontend reads it to know which API clients to initialize and which tools the agent can use.

**This is a frontend developer concern**, not a top-level architecture decision. The extension reads the domain config from the node and initializes the appropriate tools.

---

## Two-Graph Architecture

The system maintains two parallel graph structures:

### Graph 1: Container-Nodes (Database)

```
Application (root)
├── workspace-node-a (NodeContainer: tools, instructions, rules)
│   ├── sub-node-a1
│   └── sub-node-a2
└── workspace-node-b (NodeContainer: different context)
    └── sub-node-b1
```

Stored in `nodes` table. Agent creates/modifies these via DataServer REST. Each node's container IS the workspace's `.agent/` equivalent.

### Graph 2: View-Components (Frontend)

```
AppShell
├── NodeGraph (XYFlow — visual representation of Graph 1)
├── NodeViewer (renders selected node's content)
└── NodeEditor (modifies selected node's container)
```

Lives in the frontend appnode. Reads `metadata_` to know which component to render. The two graphs stay synchronized via SSE events.

---

## Routing

### Appnode Selection

The extension determines which appnode to serve based on `metadata_.frontend_app` from the node-container:

```typescript
// In Service Worker
const frontendApp = selectedNode.metadata?.frontend_app || "ffs6"; // default
const appPort = { ffs4: 4201, ffs5: 4202, ffs6: 4200 }[frontendApp];
// Navigate to or open the correct appnode
```

### Within an Appnode (React Router)

```tsx
<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/workspace/:nodeId" element={<WorkspaceView />} />
  <Route path="/graph" element={<GraphView />} />
</Routes>
```

The `frontendRoute` from `metadata_` can specify which route within the appnode to navigate to.

---

## Build & Dev

```bash
# Dev
nx serve ffs6          # default project (port 4200)
nx serve ffs4          # sidepanel app
nx run-many -t serve   # all apps

# Build
nx build ffs6          # production build
nx run-many -t build   # build all

# Test
nx test ffs6           # Vitest
nx run-many -t test    # test all

# Add new app
nx g @nx/react:app apps/ffs7       # Vite + React
nx g @nx/next:app apps/ffs-next    # Next.js alternative
```
