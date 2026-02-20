# Communication Protocols

> All 8 protocols used across the Collider system.

## Protocol Matrix

| #   | Protocol               | Transport          | Direction               | Used Between                                              |
| --- | ---------------------- | ------------------ | ----------------------- | --------------------------------------------------------- |
| 1   | **REST**               | HTTP               | Request/Response        | Extension ↔ DataServer, Extension ↔ VectorDbServer        |
| 2   | **SSE**                | HTTP (long-lived)  | Server → Client         | DataServer → Extension SW                                 |
| 3   | **WebSocket**          | WS                 | Bidirectional           | Extension ↔ GraphToolServer, Extension ↔ DataServer (RTC) |
| 4   | **WebRTC**             | P2P (STUN/TURN)    | Peer-to-Peer            | Browser ↔ Browser (via ffs5 PiP)                          |
| 5   | **Native Messaging**   | stdio              | Extension ↔ Host        | Extension SW ↔ Native Host binary                         |
| 6   | **gRPC**               | HTTP/2             | Bidirectional streaming | DataServer ↔ GraphToolServer (tool execution, discovery)  |
| 7   | **MCP/SSE**            | HTTP (SSE + POST)  | AI Client ↔ Server      | Claude Code / Copilot / Cursor ↔ GraphToolServer          |
| 8   | **Internal Messaging** | `chrome.runtime.*` | Intra-extension         | SW ↔ Sidepanel ↔ Content Scripts                          |

---

## 1. REST API

### Base URL

```
http://localhost:8000/api/v1    ← DataServer
http://localhost:8002/api/v1    ← VectorDbServer
```

### Authentication

```
Authorization: Bearer <JWT>
```

### Key Endpoints (DataServer)

| Method | Path                     | Purpose                           |
| ------ | ------------------------ | --------------------------------- |
| POST   | `/auth/login`            | Login → JWT                       |
| POST   | `/auth/verify`           | Verify JWT                        |
| GET    | `/apps`                  | List user's applications          |
| POST   | `/apps`                  | Create application                |
| GET    | `/nodes?app_id=...`      | Get node tree                     |
| POST   | `/nodes`                 | Create node                       |
| PUT    | `/nodes/:id`             | Update node (container, metadata) |
| DELETE | `/nodes/:id`             | Delete node + subtree             |
| GET    | `/context/:app_id/:path` | Hydrated context for node         |
| GET    | `/health`                | Health check                      |

### Key Endpoints (VectorDbServer)

| Method | Path      | Purpose                    |
| ------ | --------- | -------------------------- |
| POST   | `/search` | Semantic similarity search |
| POST   | `/embed`  | Generate embeddings        |
| POST   | `/index`  | Index documents            |

### Error Format

```json
{
  "detail": "Not found",
  "status_code": 404
}
```

---

## 2. Server-Sent Events (SSE)

### Endpoint

```
GET /api/v1/sse
Authorization: Bearer <JWT>
```

Persistent connection from Extension SW to DataServer.

### Event Types

| Event                | Data                                                | Trigger                     |
| -------------------- | --------------------------------------------------- | --------------------------- |
| `context_update`     | `{ app_id, node_path, fields_changed }`             | Node container modified     |
| `node_modified`      | `{ app_id, node_id, action: create/update/delete }` | Any node CRUD               |
| `permission_changed` | `{ user_id, app_id, new_role }`                     | Permission change           |
| `app_config_changed` | `{ app_id, config }`                                | Application config modified |
| `keepalive`          | `{ timestamp }`                                     | Every 30s                   |

### Message Format

```
event: node_modified
data: {"app_id":"abc","node_id":"def","action":"create","node_path":"root/research"}

event: keepalive
data: {"timestamp":1708281600}
```

### Extension Handling

```typescript
// In sse-handler.ts
const eventSource = new EventSource(`${API_BASE}/api/v1/sse`, {
  headers: { Authorization: `Bearer ${jwt}` },
});

eventSource.addEventListener("node_modified", (e) => {
  const data = JSON.parse(e.data);
  // Update cached tree if viewing this app
  if (data.app_id === contextManager.selectedAppId) {
    contextManager.refreshTree();
  }
  // Forward to sidepanel
  chrome.runtime.sendMessage({ type: "NODE_MODIFIED", data });
});
```

---

## 3. WebSocket

### GraphToolServer Workflows

```
WS ws://localhost:8001/ws/workflow
```

**Client → Server:**

```json
{
  "type": "execute",
  "workflow_id": "generate_research_nodes",
  "context": {
    "app_id": "abc",
    "node_path": "root/research",
    "parameters": { "topic": "quantum computing" }
  }
}
```

**Server → Client (streamed):**

```json
{
  "type": "step_result",
  "step": 1,
  "total_steps": 3,
  "result": { "action": "create_node", "path": "root/research/quantum" }
}
```

```json
{
  "type": "workflow_complete",
  "results": [...]
}
```

### DataServer WebRTC Signaling

```
WS ws://localhost:8000/ws/rtc/
```

See WebRTC section below.

---

## 4. WebRTC (P2P)

Used by **ffs5 PiP appnode** for real-time communication.

### Signaling Flow

```
Peer A                    DataServer (/ws/rtc/)              Peer B
  │                           │                               │
  ├── join(roomId) ──────────►│                               │
  │                           │◄────────── join(roomId) ──────┤
  │                           │                               │
  │  create offer             │                               │
  ├── offer(sdp) ────────────►│── relay ──► offer(sdp) ──────►│
  │                           │                               │ create answer
  │◄── answer(sdp) ◄─── relay│◄────────── answer(sdp) ───────┤
  │                           │                               │
  ├── ice(candidate) ────────►│── relay ──► ice(candidate) ──►│
  │◄── ice(candidate) ◄ relay│◄────────── ice(candidate) ────┤
  │                           │                               │
  │═══════════ P2P Data/Media Channel Established ════════════│
```

### Message Types

```json
{ "type": "join", "userId": "...", "roomId": "..." }
{ "type": "offer", "targetUserId": "...", "sdp": "..." }
{ "type": "answer", "targetUserId": "...", "sdp": "..." }
{ "type": "ice", "targetUserId": "...", "candidate": "..." }
```

### Implementation

Extension uses `simple-peer` (SimplePeer) for WebRTC:

```typescript
const peer = new SimplePeer({ initiator: true, trickle: true });
peer.on("signal", (data) => {
  // Send via signaling WebSocket
  ws.send(JSON.stringify({ type: data.type, sdp: data.sdp, targetUserId }));
});
peer.on("data", (data) => {
  /* receive P2P data */
});
```

---

## 5. Native Messaging

Used by **FILESYST domain** for local file system operations.

### Architecture

```
Extension SW ──chrome.runtime.sendNativeMessage("collider_host", msg)──► Native Host
                                                                              │
                                                                        Read/Write FS
                                                                              │
Extension SW ◄────────────────── JSON response via stdout ────────────────────┘
```

### Native Host Manifest

```json
{
  "name": "collider_host",
  "description": "Collider file system bridge",
  "path": "path/to/native-host.exe",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://<extension-id>/"]
}
```

### Message Format

**Request:**

```json
{
  "action": "read_file",
  "payload": { "path": "D:/project/.agent/manifest.yaml" }
}
```

**Response:**

```json
{
  "success": true,
  "data": { "content": "name: my-workspace\n..." }
}
```

### Supported Actions

| Action           | Payload                        | Response                           |
| ---------------- | ------------------------------ | ---------------------------------- |
| `read_file`      | `{ path }`                     | `{ content }`                      |
| `write_file`     | `{ path, content }`            | `{ written: true }`                |
| `list_directory` | `{ path, recursive? }`         | `{ entries: [...] }`               |
| `sync_workspace` | `{ localPath, nodeId, appId }` | `{ synced: true, changes: [...] }` |
| `delete_file`    | `{ path }`                     | `{ deleted: true }`                |

### FILESYST Sync Flow

```
1. Agent triggers sync (TOOL_EXECUTE: sync_workspace)
2. Native host reads local .agent/ directory tree
3. Native host sends tree structure to SW
4. SW POSTs to DataServer to create/update nodes with container data
5. DataServer emits SSE event (node_modified)
6. Sidepanel refreshes tree view
```

---

## 6. gRPC (Planned)

Planned for inter-service communication between backend servers:

- DataServer ↔ GraphToolServer (workflow results → node creation)
- DataServer ↔ VectorDbServer (auto-indexing on node create)

Currently these use REST, but gRPC will replace for performance.

---

## 7. Internal Messaging (`chrome.runtime.*`)

All intra-extension communication uses Chrome's messaging APIs.

### APIs Used

| API                                               | Purpose                                  |
| ------------------------------------------------- | ---------------------------------------- |
| `chrome.runtime.sendMessage()`                    | One-shot message (sidepanel ↔ SW)        |
| `chrome.runtime.onMessage.addListener()`          | Receive messages                         |
| `chrome.runtime.connect()` / `port.postMessage()` | Long-lived channel (content script ↔ SW) |
| `chrome.tabs.sendMessage()`                       | SW → specific content script tab         |

### Message Envelope

```typescript
interface InternalMessage {
  type: string; // e.g. 'FETCH_APPS', 'AGENT_QUERY'
  payload?: unknown; // request data
  requestId?: string; // for correlating request/response
  source?: "sidepanel" | "content" | "background";
}
```

### Pattern: Request/Response

```typescript
// Sidepanel → SW (request)
const apps = await chrome.runtime.sendMessage({
  type: "FETCH_APPS",
  requestId: crypto.randomUUID(),
});

// SW listener (handler)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "FETCH_APPS") {
    apiClient.getApps().then(sendResponse);
    return true; // async response
  }
});
```

---

## End-to-End Flows

### Flow 1: Agent Creates Node

```
1. User sends query in sidepanel ChatPanel
2. Sidepanel → SW: { type: "AGENT_QUERY", payload: { query: "Create a research section" } }
3. SW routes to active agent (e.g. cloud-agent)
4. Agent decides to create node → REST POST /api/v1/nodes
5. DataServer creates node in SQLite
6. DataServer emits SSE: event: node_modified, data: { action: "create", ... }
7. SW receives SSE → updates cache → forwards to sidepanel
8. Sidepanel refreshes NodeTree
9. Agent responds → SW → Sidepanel ChatPanel shows result
```

### Flow 2: Startup

```
1. User opens extension → sidepanel mounts
2. Sidepanel → SW: LOGIN (cached credentials or prompt)
3. SW → DataServer: POST /auth/login → JWT
4. SW → DataServer: GET /apps → application list
5. SW → DataServer: GET /sse → persistent event stream
6. SW → Sidepanel: APPS_LOADED
7. Sidepanel renders AppSelector with app list
```

### Flow 3: Node Selection → Appnode Delivery

```
1. User clicks node in NodeTree
2. Sidepanel → SW: SELECT_NODE { nodeId, path }
3. SW ContextManager:
   a. GET /context/:app_id/:path → hydrated context
   b. Read metadata_.frontend_app ("ffs6")
   c. Layer context: Base → Node → App → User
4. SW routes to ffs6 appnode (port 4200)
5. ffs6 receives context, renders workspace view
6. Agent tools are now bound to this node's context
```

### Flow 4: Application Creation

```
1. App admin creates application via REST POST /api/v1/apps
2. DataServer creates Application row + root Node
3. Root node gets NodeContainer with workspace context:
   - tools, instructions, rules, knowledge from template
   - metadata_.frontend_app = "ffs6" (default)
4. Application.config.domain = "CLOUD" (permitted API set)
5. SSE emits app_config_changed
6. Extension refreshes app list
```

### Flow 5: FILESYST Sync

```
1. Agent triggers sync tool
2. SW → Native Host: { action: "sync_workspace", payload: { localPath, nodeId, appId } }
3. Native Host reads .agent/ directory recursively
4. Native Host → SW: { success: true, data: { tree, files } }
5. SW → DataServer: POST/PUT /nodes (create/update nodes with container data)
6. DataServer → SSE: node_modified events
7. Sidepanel refreshes → workspace is now synced
```
