# Chrome Extension Architecture

> The Chrome extension is the primary runtime environment. It hosts the service worker (agent orchestration), sidepanel (UI), and content scripts (DOM access).

## Overview

**Package**: `collider-chrome-extension`
**Framework**: Plasmo + React 18 + TypeScript
**Build**: Plasmo bundles to `build/chrome-mv3-dev/` (Manifest V3)
**Location**: `FFS2_.../ColliderMultiAgentsChromeExtension/`

### Chrome Permissions

| Permission        | Usage                                               |
| ----------------- | --------------------------------------------------- |
| `sidePanel`       | Sidepanel UI for workspace browsing + agent seat    |
| `activeTab`       | Access to current tab for DOM queries               |
| `tabs`            | Track tab state (URL, title, active tab)            |
| `storage`         | `chrome.storage.session` for context persistence    |
| `nativeMessaging` | FILESYST domain: read/write local `.agent/` folders |
| `scripting`       | Inject content scripts for DOM access               |

**Host permissions**: `http://localhost:8000/*`, `http://localhost:8001/*`, `http://localhost:8002/*`

### Key Dependencies

| Package                  | Version     | Purpose                           |
| ------------------------ | ----------- | --------------------------------- |
| `plasmo`                 | --          | Chrome extension framework        |
| `react`                  | ^18         | UI rendering                      |
| `zustand`                | ^5          | State management (sidepanel)      |
| `@collider/sidepanel-ui` | workspace:* | FFS4 package (AppTree, AgentSeat) |

---

## Source Structure

```
src/
├── background/                    # Service Worker
│   ├── index.ts                   # Entry point, message router, lifecycle
│   ├── context-manager.ts         # ContextManager singleton
│   ├── agents/
│   │   ├── cloud-agent.ts         # Cloud domain agent (LangGraph.js)
│   │   ├── dom-agent.ts           # DOM query agent
│   │   └── filesyst-agent.ts      # FILESYST domain agent (native messaging)
│   └── external/
│       ├── data-server.ts         # DataServer client (REST + SSE)
│       ├── graphtool.ts           # GraphToolServer client (WebSocket)
│       └── vectordb.ts            # VectorDbServer client (REST)
│
├── sidepanel/
│   ├── index.tsx                  # SidePanel component (entry point)
│   └── stores/
│       └── appStore.ts            # Zustand store
│
├── contents/
│   └── index.ts                   # Content script (DOM access)
│
├── types/
│   └── index.ts                   # Shared TypeScript interfaces
│
└── style.css                      # Tailwind CSS styles
```

---

## Service Worker

### Lifecycle

```
chrome.runtime.onInstalled  ──┐
chrome.runtime.onStartup   ──┤
                              ▼
                         initialize()
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              restore()  verifyAuth()  initCloudAgent()
              context    + fetchApps()  + connectSSE()
```

On install or startup, the service worker:
1. Restores persisted context from `chrome.storage.session`
2. Authenticates with DataServer and loads application list
3. Initializes the CloudAgent (LangGraph.js)
4. Connects SSE for real-time backend events

### Message Router

All extension components communicate with the service worker via `chrome.runtime.sendMessage()`. The service worker routes messages by type:

| Message Type       | Handler                           | Description                                |
| ------------------ | --------------------------------- | ------------------------------------------ |
| `AUTH_VERIFY`      | `verifyAuth()`                    | Verify Firebase auth, update user context  |
| `FETCH_APPS`       | `fetchApps()`                     | Load application list from DataServer      |
| `FETCH_TREE`       | `fetchTree(appId)`                | Load node tree for an application          |
| `DOM_QUERY`        | `handleDomQuery(tabId, selector)` | Query DOM in active tab via content script |
| `WORKFLOW_EXECUTE` | `executeWorkflow(id, steps)`      | Execute workflow via GraphToolServer       |
| `TOOL_SEARCH`      | `searchForTools(query)`           | Semantic tool search via VectorDbServer    |
| `NATIVE_MESSAGE`   | `readFile/writeFile/listDir`      | FILESYST operations via native messaging   |
| `CONTEXT_UPDATE`   | --                                | Return current serializable context        |

**Message format:**

```typescript
interface ColliderMessage {
  type: ColliderMessageType;
  payload?: unknown;
  tabId?: number;
  requestId?: string;
}

interface ColliderResponse {
  success: boolean;
  data?: unknown;
  error?: string;
  requestId?: string;
}
```

### Tab Tracking

The service worker monitors tab lifecycle events to maintain context:

- `chrome.tabs.onActivated` → updates `activeTabId` in ContextManager
- `chrome.tabs.onRemoved` → removes tab from context map
- `chrome.tabs.onUpdated` → updates tab URL/title in context

---

## ContextManager

**Source**: `src/background/context-manager.ts`

Singleton that manages all runtime state. Persists to `chrome.storage.session` on every mutation.

### State Shape

```typescript
interface MainContext {
  user: ColliderUser | null;
  applications: Application[];
  permissions: AppPermission[];
  activeTabId: number | null;
  tabs: Map<number, TabContext>;
}

interface TabContext {
  tabId: number;
  url: string;
  title: string;
  dom_snapshot?: string;
  active_app_id?: string;
  active_node_path?: string;
}
```

### Key Methods

| Method                            | Purpose                                      |
| --------------------------------- | -------------------------------------------- |
| `setUser(user)`                   | Store authenticated user, persist            |
| `setApplications(apps)`           | Store app list, persist                      |
| `setPermissions(perms)`           | Store permission set, persist                |
| `setActiveTab(tabId)`             | Track which tab is focused                   |
| `updateTabContext(tabId, update)` | Update tab metadata                          |
| `removeTab(tabId)`                | Clean up closed tab                          |
| `getActiveWorkspaceType()`        | Resolve domain from active app config        |
| `switchWorkspaceContext(appId)`   | Set active app + broadcast `CONTEXT_CHANGED` |
| `getSerializableContext()`        | Export context (converts Map to Object)      |
| `restore()`                       | Rehydrate from `chrome.storage.session`      |

### Context-Driven Routing

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

When `switchWorkspaceContext(appId)` is called, it broadcasts a `CONTEXT_CHANGED` message to all extension pages (sidepanel, popup). The sidepanel listens for this message and loads the appropriate domain-specific viewer component.

---

## Sidepanel

**Source**: `src/sidepanel/index.tsx`

The sidepanel is the primary user interface, displayed as a Chrome side panel.

### View Modes

| Mode  | Component       | Source                          |
| ----- | --------------- | ------------------------------- |
| Tree  | `<AppTree />`   | `@collider/sidepanel-ui` (FFS4) |
| Agent | `<AgentSeat />` | `@collider/sidepanel-ui` (FFS4) |

### UI Structure

```
┌────────────────────────┐
│ Collider    [Tree][Agent]│  ← Header + view mode toggle
├────────────────────────┤
│ [Select application ▼] │  ← App selector dropdown
├────────────────────────┤
│                        │
│   Tree View            │  ← AppTree (node hierarchy)
│   or                   │     or
│   Agent Seat           │     AgentSeat (chat interface)
│                        │
└────────────────────────┘
```

### Data Flow

1. On mount: sends `FETCH_APPS` to service worker
2. User selects app → sends `FETCH_TREE` with `app_id`
3. Tree renders with domain-specific styling
4. Node selection updates Zustand store + notifies service worker

### State Management

Zustand store (`stores/appStore.ts`) manages:
- `applications: Application[]`
- `selectedAppId: string | null`
- `tree: AppNodeTree[]`
- `selectedNodePath: string | null`
- `loading: boolean`
- `error: string | null`

---

## Content Scripts

**Source**: `src/contents/index.ts`

Injected into web pages. Responds to `DOM_QUERY` messages from the service worker to provide DOM access to agents. Used by the DomAgent for page analysis and interaction.

---

## Type System

**Source**: `src/types/index.ts`

Core interfaces shared across all extension components:

| Interface             | Description                                                                                               |
| --------------------- | --------------------------------------------------------------------------------------------------------- |
| `NodeContainer`       | 8-field workspace structure (manifest, instructions, rules, skills, tools, knowledge, workflows, configs) |
| `Application`         | App record (id, app_id, display_name, config, root_node_id)                                               |
| `AppNode`             | Single node with container and metadata                                                                   |
| `AppNodeTree`         | Recursive tree structure (node + children[])                                                              |
| `AppPermission`       | Per-user per-app permissions (can_read, can_write, is_admin)                                              |
| `ColliderUser`        | User record (email, firebase_uid, profile, container)                                                     |
| `TabContext`          | Per-tab tracking state                                                                                    |
| `MainContext`         | Full runtime context aggregate                                                                            |
| `ColliderMessage`     | Inbound message format                                                                                    |
| `ColliderResponse`    | Response format (success/error pattern)                                                                   |
| `ColliderMessageType` | Union of 10 message type strings                                                                          |
