# Communication Protocols

> All 10 protocols used across the Collider system.

## Protocol Matrix

| #   | Protocol               | Transport          | Direction               | Used Between                                                      |
| --- | ---------------------- | ------------------ | ----------------------- | ----------------------------------------------------------------- |
| 1   | **REST**               | HTTP               | Request/Response        | Extension ↔ DataServer, Extension ↔ VectorDbServer                |
| 2   | **SSE**                | HTTP (long-lived)  | Server → Client         | DataServer → Extension SW                                         |
| 3   | **WebSocket**          | WS                 | Bidirectional           | Extension ↔ GraphToolServer, Extension ↔ DataServer (RTC)         |
| 4   | **WebRTC**             | P2P (STUN/TURN)    | Peer-to-Peer            | Browser ↔ Browser (via ffs5 PiP)                                  |
| 5   | **Native Messaging**   | stdio              | Extension ↔ Host        | Extension SW ↔ Native Host binary                                 |
| 6   | **gRPC**               | HTTP/2             | Bidirectional streaming | DataServer ↔ GraphToolServer, VectorDbServer (live :50052, :8002) |
| 7   | **MCP/SSE**            | HTTP (SSE + POST)  | AI Client ↔ Server      | Claude Code / Copilot / Cursor ↔ GraphToolServer                  |
| 8   | **Internal Messaging** | `chrome.runtime.*` | Intra-extension         | SW ↔ Sidepanel ↔ Content Scripts                                  |
| 9   | **WebSocket**          | WS                 | Bidirectional streaming | AgentSeat ↔ NanoClawBridge (:18789)                               |
| 10  | **AgentRunner REST**   | HTTP               | Request/Response        | Extension ↔ ColliderAgentRunner (:8004)                           |

---

## 1. REST API

### Base URL

```text
http://localhost:8000/api/v1    ← DataServer
http://localhost:8002/api/v1    ← VectorDbServer
```

### Authentication

```text
Authorization: Bearer <JWT>
```

### Key Endpoints (DataServer)

| Method | Path                        | Purpose                           |
| ------ | --------------------------- | --------------------------------- |
| POST   | `/auth/login`               | Login → JWT                       |
| POST   | `/auth/verify`              | Verify JWT                        |
| GET    | `/apps`                     | List user's applications          |
| POST   | `/apps`                     | Create application                |
| GET    | `/nodes?app_id=...`         | Get node tree                     |
| POST   | `/nodes`                    | Create node                       |
| PUT    | `/nodes/:id`                | Update node (container, metadata) |
| DELETE | `/nodes/:id`                | Delete node + subtree             |
| GET    | `/context/:app_id/:path`    | Hydrated context for node         |
| GET    | `/health`                   | Health check                      |
| GET    | `/agent/bootstrap/:id`      | NanoClaw bootstrap for node       |
| POST   | `/execution/tool/:name`     | Execute tool via GraphToolServer  |
| POST   | `/execution/workflow/:name` | Execute workflow                  |
| GET    | `/templates`                | List node templates               |

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

```text
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

### Native Host Message Format

```text
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

```text
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

```text
WS ws://localhost:8000/ws/rtc/
```

See WebRTC section below.

---

## 4. WebRTC (P2P)

Used by **ffs5 PiP appnode** for real-time communication.

### Signaling Flow

```text
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

```text
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

```text
1. Agent triggers sync (TOOL_EXECUTE: sync_workspace)
2. Native host reads local .agent/ directory tree
3. Native host sends tree structure to SW
4. SW POSTs to DataServer to create/update nodes with container data
5. DataServer emits SSE event (node_modified)
6. Sidepanel refreshes tree view
```

---

## 6. gRPC

Live inter-service communication on dedicated ports.

### GraphToolServer (:50052)

```protobuf
service ColliderGraph {
  rpc ExecuteTool (ToolRequest) returns (ToolResponse);
  rpc ExecuteSubgraph (SubgraphRequest) returns (SubgraphResponse);
  rpc DiscoverTools (DiscoverRequest) returns (DiscoverResponse);
}
```

**Used by**: DataServer (`core/grpc_client.py`) and AgentRunner (`core/graph_tool_client.py`)
invoke tool execution. NanoClaw agents call tools through this path.

### VectorDbServer (:8002 gRPC)

```protobuf
service ColliderVectorDb {
  rpc IndexTool (IndexRequest) returns (IndexResponse);
  rpc SearchTools (SearchRequest) returns (SearchResponse);
}
```

**Used by**: GraphToolServer (`core/vector_client.py`) for semantic tool discovery.

### Proto definitions

Located in `proto/`:

- `collider_graph.proto` — tool + subgraph execution
- `collider_data.proto` — data sync, schema registration
- `collider_vectordb.proto` — index + search
- Generated stubs: `*_pb2.py`, `*_pb2_grpc.py`

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

## 9. WebSocket (NanoClawBridge)

### WebSocket Endpoint

```text
WS ws://127.0.0.1:18789?token=<session_token>
```

The NanoClawBridge is the agent execution runtime. Chrome Extension's `AgentSeat` component
connects via `nanoclaw-rpc.ts` to stream agent interactions.

### Protocol

JSON-RPC 2.0 over WebSocket with server-sent streaming events.

**Client → Server (request):**

```json
{
  "jsonrpc": "2.0",
  "method": "agent.request",
  "params": { "message": "List all nodes in the x1z app" },
  "id": 1
}
```

**Server → Client (streaming events):**

| Event            | Content                        |
| ---------------- | ------------------------------ |
| `text_delta`     | Incremental LLM text           |
| `tool_use_start` | Tool invocation (name, params) |
| `tool_result`    | Tool execution result          |
| `thinking`       | Agent reasoning (if enabled)   |
| `message_end`    | End of agent turn              |

### Session Lifecycle

1. WorkspaceBrowser composes a session via AgentRunner → gets `nanoclaw_ws_url`
2. AgentSeat opens WebSocket to the URL (includes session token)
3. Gateway reads workspace files from `~/.nanoclaw/workspaces/collider/`
4. Agent runs with composed context (CLAUDE.md + .mcp.json, skills/)
5. User sends messages → agent streams responses
6. Session expires after TTL (4h compose, 24h root)

---

## 10. AgentRunner REST

### AgentRunner Base URL

```text
http://localhost:8004
```

The ColliderAgentRunner is the context composer. It builds ContextSet sessions
by bootstrapping nodes from DataServer and writing workspace files for NanoClaw.

### Key Endpoints

| Method | Path                  | Purpose                                  |
| ------ | --------------------- | ---------------------------------------- |
| POST   | `/agent/session`      | Create ContextSet session (compose)      |
| POST   | `/agent/root/session` | Create root agent session (full subtree) |
| POST   | `/agent/chat`         | Direct chat (non-NanoClaw, diagnostic)   |
| GET    | `/tools/discover`     | Discover available tools from registry   |
| GET    | `/health`             | Health check                             |

### Session Request (Compose)

```json
{
  "role": "collider_admin",
  "app_id": "x1z",
  "node_ids": ["abc123", "def456"],
  "vector_query": "graph tools",
  "inherit_ancestors": true
}
```

### Session Response

```json
{
  "session_id": "sess_...",
  "preview": {
    "node_count": 3,
    "skill_count": 1,
    "tool_count": 15,
    "system_prompt_chars": 4200
  },
  "nanoclaw_ws_url": "ws://127.0.0.1:18789?token=..."
}
```

---

## End-to-End Flows

### Flow 1: Agent Creates Node

```text
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

```text
1. User opens extension → sidepanel mounts
2. Sidepanel → SW: LOGIN (cached credentials or prompt)
3. SW → DataServer: POST /auth/login → JWT
4. SW → DataServer: GET /apps → application list
5. SW → DataServer: GET /sse → persistent event stream
6. SW → Sidepanel: APPS_LOADED
7. Sidepanel renders AppSelector with app list
```

### Flow 3: Node Selection → Appnode Delivery

```text
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

```text
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

```text
1. Agent triggers sync tool
2. SW → Native Host: { action: "sync_workspace", payload: { localPath, nodeId, appId } }
3. Native Host reads .agent/ directory recursively
4. Native Host → SW: { success: true, data: { tree, files } }
5. SW → DataServer: POST/PUT /nodes (create/update nodes with container data)
6. DataServer → SSE: node_modified events
7. Sidepanel refreshes → workspace is now synced
```

### Flow 6: NanoClaw ContextSet Session

```text
1. User opens sidepanel → WorkspaceBrowser (Compose tab)
2. User selects role, picks nodes, optionally enters vector query
3. User clicks Compose
4. Sidepanel → POST :8004/agent/session { role, app_id, node_ids, vector_query }
5. AgentRunner:
   a. Authenticates as role via DataServer
   b. GET :8000/api/v1/agent/bootstrap/{id} for each node
   c. Merges contexts (leaf-wins) → ContextSet
   d. Optional: vector search for additional tools
   e. Writes workspace files → ~/.nanoclaw/workspaces/collider/
   f. Returns { session_id, preview, nanoclaw_ws_url }
6. User switches to AgentSeat (Chat tab)
7. AgentSeat connects ws://127.0.0.1:18789?token=... via nanoclaw-rpc.ts
8. User sends message → JSON-RPC agent.request
9. NanoClawBridge reads workspace files, runs agent
10. Agent streams response through WebSocket
11. Tool calls: Agent → gRPC :50052 → GraphToolServer → ToolRunner → result
```

### Flow 7: Root Agent Session

```text
1. User opens RootAgentPanel tab
2. Panel → POST :8004/agent/root/session { app_id }
3. AgentRunner fetches Application.root_node_id
4. Bootstraps full subtree (all descendants)
5. Writes to ~/.nanoclaw/workspaces/collider-root/
6. Returns { session_id, nanoclaw_ws_url }
7. Panel connects WebSocket, begins chat
8. 15 Collider tools + NanoClaw built-ins available
9. 24h session TTL
```
