---
description: Protocol standards connecting FFS2 (Backend/Extension) and FFS3
(Frontend) — REST, SSE, WebSocket, gRPC, Native Messaging activation:
model_decision
---

# Communication Architecture

> The "Nervous System" connecting FFS2 (Backend/Extension) and FFS3 (Frontend).

---

## 1. Inter-Service Communication

### FFS3 (Frontend) <-> FFS2 (Data Server)

- **Primary Protocol**: **REST (JSON over HTTP)**
  - **Why**: Simple, well-supported, Pydantic v2 serialization.
  - **Transport**: HTTP/1.1 with CORS allowlist.
- **Streams**: **Server-Sent Events (SSE)**
  - **Why**: Efficient one-way stream for real-time data updates and notifications.
  - **Handling**: `EventSource` API in browser, `StreamingResponse` in FastAPI.

### FFS3 (Frontend) <-> FFS2 (Graph Server)

- **Primary Protocol**: **WebSockets**
  - **Why**: Full duplex required for graph manipulation (layout updates, node dragging sync).
  - **Optimization**: Use **SharedWorker** to maintain a _single_ socket connection across multiple tabs.

### FFS2 Backend <-> Backend (gRPC)

- **Primary Protocol**: **gRPC** (HTTP/2)
  - **Why**: Typed protobuf contracts, streaming, high-performance inter-service calls.
  - **Routes**:
    - DataServer / AgentRunner -> GraphToolServer (:50052): tool execution, discovery
    - GraphToolServer -> VectorDbServer (:8002): semantic search, indexing

### Chrome Extension <-> AgentRunner

- **Primary Protocol**: **REST** (HTTP)
  - **Why**: Session composition is request/response (POST /agent/session).
  - **Port**: :8004

### Chrome Extension <-> NanoClawBridge

- **Primary Protocol**: **WebSocket**
  - **Why**: Bidirectional streaming for agent chat (text_delta, tool_use, tool_result events).
  - **Port**: :18789
  - **Auth**: Token-authenticated WebSocket URL returned by AgentRunner.

---

## 2. Browser Extension Internal (FFS2)

### Content Script <-> Background

- **Protocol**: **Chrome Messaging (Port API)**
  - **Standard**: Long-lived ports for session context.
  - **One-off**: `chrome.runtime.sendMessage` for simple commands.

### Inter-Tab Synchronization

- **Protocol**: **Broadcast Channel API**
  - **Purpose**: Sync "Active Agent" state across tabs without hitting the backend.
  - **Scope**: Same-origin only (Extension pages).

### Offline & Resilience

- **Service Workers**: Mandatory for all Background Scripts (MV3).
- **Background Sync API**:
  - **Usage**: Queue analytical events or drafts when offline.
  - **Retry**: Exponential backoff managed by browser.

---

## 3. External Integrations

### WebRTC

- **Status**: **Implemented** (ffs5 PiP).
- **Use Case**: Peer-to-peer tab capture streaming via Picture-in-Picture.
- **Transport**: SimplePeer (WebRTC), signaling via DataServer WebSocket (/rtc).

### MCP/SSE (IDE Tool Access)

- **Status**: **Live**.
- **Use Case**: IDE clients (Claude Code, Copilot, Cursor) access Collider tools via MCP protocol.
- **Endpoint**: GraphToolServer `GET /mcp/sse`, `POST /mcp/messages/`.

### Native Messaging

- **Status**: **Live**.
- **Use Case**: FILESYST domain — local file read/write/sync.
- **Host**: `com.collider.agent_host` (stdio JSON protocol).

---

## 4. Security Boundaries

- **CORS**: `allow_origin_regex` for chrome-extension:// IDs and FFS3 origin.
- **CSP**: Content Security Policy allows WebSocket (NanoClawBridge) and local server access.
- **Auth**: Bearer Tokens (JWT) passed in HTTP headers and gRPC metadata.
- **NanoClaw**: Session tokens scoped to composed context; expire after TTL (4h/24h).
