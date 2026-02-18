# Data Flow and Communication

> Six communication protocols connect the browser extension to backend services and between extension components.

## Protocol Stack

| Protocol           | Endpoint                           | Direction        | Purpose                              |
| ------------------ | ---------------------------------- | ---------------- | ------------------------------------ |
| REST               | `http://localhost:8000/api/v1/*`   | Request/Response | CRUD operations, auth, context       |
| SSE                | `http://localhost:8000/api/v1/sse` | Server → Client  | Real-time event streaming            |
| WebSocket          | `ws://localhost:8001/ws/*`         | Bidirectional    | Workflow execution, graph operations |
| Native Messaging   | Chrome Native Host                 | Bidirectional    | FILESYST domain file I/O             |
| WebRTC P2P         | Peer-to-Peer                       | Bidirectional    | User-to-user media/data              |
| Internal Messaging | `chrome.runtime.*`                 | Intra-extension  | SW ↔ sidepanel ↔ content scripts     |

---

## Extension Internal Messaging

### chrome.runtime.sendMessage

Primary communication between extension components:

```
Sidepanel ──sendMessage──► Service Worker ──sendResponse──► Sidepanel
Content Script ──sendMessage──► Service Worker
Service Worker ──sendMessage──► All extension pages (broadcast)
```

**Message types** (from `ColliderMessageType`):

| Type               | Sender    | Handler                      | Description                         |
| ------------------ | --------- | ---------------------------- | ----------------------------------- |
| `INIT`             | --        | --                           | Reserved for initialization         |
| `AUTH_VERIFY`      | Sidepanel | `verifyAuth()`               | Authenticate with DataServer        |
| `FETCH_APPS`       | Sidepanel | `fetchApps()`                | Load application list               |
| `FETCH_TREE`       | Sidepanel | `fetchTree(appId)`           | Load node tree for app              |
| `DOM_QUERY`        | Agent     | `handleDomQuery()`           | Query DOM in tab via content script |
| `WORKFLOW_EXECUTE` | Agent     | `executeWorkflow()`          | Run workflow on GraphToolServer     |
| `TOOL_SEARCH`      | Agent     | `searchForTools()`           | Semantic search on VectorDbServer   |
| `CONTEXT_UPDATE`   | Any       | --                           | Return current context snapshot     |
| `NATIVE_MESSAGE`   | Agent     | `readFile/writeFile/listDir` | FILESYST file operations            |
| `SSE_EVENT`        | SW        | --                           | Forwarded SSE events                |

### chrome.storage.session

Used for context persistence across service worker restarts:

```
ContextManager ──persist()──► chrome.storage.session.set({ colliderContext })
                 restore()◄── chrome.storage.session.get("colliderContext")
```

The `colliderContext` key stores the serialized `MainContext` (user, apps, permissions, tab map).

### CONTEXT_CHANGED Broadcast

When the user switches applications, the service worker broadcasts:

```typescript
chrome.runtime.sendMessage({
  type: "CONTEXT_CHANGED",
  payload: { appId, workspaceType }
});
```

The sidepanel listens for this message and loads the appropriate domain viewer.

---

## REST API (DataServer :8000)

### Endpoint Groups

| Group       | Prefix                | Operations                        |
| ----------- | --------------------- | --------------------------------- |
| Health      | `/api/v1/health`      | GET health check                  |
| Auth        | `/api/v1/auth`        | POST verify (Firebase token)      |
| Users       | `/api/v1/users`       | CRUD user accounts                |
| Apps        | `/api/v1/apps`        | CRUD applications                 |
| Nodes       | `/api/v1/nodes`       | CRUD nodes (tree operations)      |
| Context     | `/api/v1/context`     | GET hydrated context for app/node |
| Permissions | `/api/v1/permissions` | CRUD app permissions              |

### Request Pattern

All REST calls from the extension go through `src/background/external/data-server.ts`:

```
Sidepanel → sendMessage("FETCH_APPS") → SW → data-server.ts → GET /api/v1/apps → Response
```

---

## SSE (DataServer :8000)

### Connection

The service worker maintains a persistent SSE connection established during `initialize()`:

```typescript
connectSSE(
  (event) => { /* handle event */ },
  (error) => { /* handle error */ }
);
```

### Event Types

| Event                | Trigger                      | Action                              |
| -------------------- | ---------------------------- | ----------------------------------- |
| `context_update`     | Node container modified      | Invalidate cache, notify sidepanel  |
| `node_modified`      | Node created/updated/deleted | Update tree if viewing affected app |
| `permission_changed` | Permissions modified         | Refresh permissions, update access  |
| `app_config_changed` | Application config modified  | Reload app configuration            |
| `keepalive`          | Periodic                     | Maintain connection                 |

---

## WebSocket (GraphToolServer :8001)

### Endpoints

| Endpoint       | Purpose                                |
| -------------- | -------------------------------------- |
| `/ws/workflow` | Execute multi-step agent workflows     |
| `/ws/graph`    | Graph operations (create/modify nodes) |

### Workflow Execution Flow

```
Agent decides to execute workflow
    │
    ▼
SW sends WORKFLOW_EXECUTE message
    │
    ▼
cloud-agent.ts opens WebSocket to :8001/ws/workflow
    │
    ▼
Send: { workflow_id, steps, context }
    │
    ▼
Server processes each step (Pydantic AI Graph)
    │
    ├── Step results streamed back via WebSocket
    │
    ▼
If workflow creates new nodes:
    │
    ├── Server calls DataServer REST to persist
    ├── DataServer emits SSE event
    └── SW receives SSE, updates cache
```

---

## Native Messaging (FILESYST Domain)

### Architecture

```
Chrome Extension ──► Native Host Process ──► Local Filesystem
   (SW)                (spawned by Chrome)      (.agent/ folders)
```

### Message Format

The `NATIVE_MESSAGE` handler in the service worker routes to three operations:

| Action       | Function                   | Description                           |
| ------------ | -------------------------- | ------------------------------------- |
| `read_file`  | `readFile(path)`           | Read file from local `.agent/` folder |
| `write_file` | `writeFile(path, content)` | Write file to local `.agent/` folder  |
| `list_dir`   | `listDir(path)`            | List directory contents               |

### Security

- `allowed_origins`: Only the registered extension ID can connect
- All messages are JSON (no arbitrary code execution)
- Windows requires registry entry at `HKCU\Software\Google\Chrome\NativeMessagingHosts\...`

---

## WebRTC P2P (User-to-User)

### Signaling Flow

```
User A                    DataServer :8000              User B
  │                       /ws/rtc/                        │
  ├── join(roomId) ──────►                                │
  │                       ◄────── join(roomId) ───────────┤
  │                                                       │
  ├── offer(sdp) ────────► relay ────────────────────────►│
  │                                                       │
  │◄─────────────────────── relay ◄──── answer(sdp) ──────┤
  │                                                       │
  ├── ice(candidate) ────► relay ────────────────────────►│
  │◄─────────────────────── relay ◄──── ice(candidate) ───┤
  │                                                       │
  ├═══════════════════ P2P Connection ═══════════════════►│
  │            (media/data flows directly)                │
```

- Signaling via DataServer WebSocket `/ws/rtc/`
- P2P connection via SimplePeer (`simple-peer` library)
- Used by FFS5 `@collider/pip-ui` for PiP communication window
- Room-based: users join rooms, signaling messages route to target users

---

## Context Loading Flows

### Startup Flow

```
Extension installs/starts
    │
    ▼
contextManager.restore()     ← Rehydrate from chrome.storage.session
    │
    ▼
verifyAuth()                 ← POST /api/v1/auth/verify
    │
    ├── Success: setUser(), fetchApps(), setApplications()
    └── Failure: Warn (servers offline), continue with cached data
    │
    ▼
initCloudAgent()             ← Initialize LangGraph.js agent
    │
    ▼
connectSSE()                 ← Open persistent SSE connection
    │
    ▼
Ready for user interaction
```

### Navigation Flow

```
User selects app in dropdown
    │
    ▼
Sidepanel sends FETCH_TREE { app_id }
    │
    ▼
SW calls fetchTree(appId) → GET /api/v1/nodes?app_id=...
    │
    ▼
Tree data returned → Sidepanel renders AppTree
    │
    ▼
User clicks node
    │
    ▼
Sidepanel updates Zustand store (selectedNodePath)
    │
    ▼
Agent context updated with node's container data
```

---

## FILESYST Sync

Bidirectional sync between local filesystem and cloud:

```
LOCAL → SERVER (sync upload)
.agent/ folder → Native Host → SW → POST /api/v1/sync

SERVER → LOCAL (on-demand)
Data Server → REST response → SW → Native Host → Write .agent/
```

**Triggers:**
- Manual: User clicks "Sync" in extension
- Scheduled: Daily at configured time
- API: External system triggers via Data Server
