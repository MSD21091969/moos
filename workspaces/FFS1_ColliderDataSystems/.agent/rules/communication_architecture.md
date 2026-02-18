---
description: Protocol standards connecting FFS2 (Backend/Extension) and FFS3 (Frontend) — REST, SSE, WebSocket, WebRTC, Native Messaging
activation: model_decision
---

# Communication Architecture

> The "Nervous System" connecting FFS2 (Backend/Extension) and FFS3 (Frontend).

---

## 1. Inter-Service Communication

### FFS3 (Frontend) <-> FFS2 (Data Server)

- **Primary Protocol**: **gRPC-Web**
  - **Why**: Strictly typed contracts, smaller payloads, auto-generated clients.
  - **Transport**: HTTP/2 (or HTTP/1.1 via Envoy wrapper if needed locally).
- **Streams**: **Server-Sent Events (SSE)**
  - **Why**: Efficient one-way stream for Agent "thought" updates and log tails.
  - **Handling**: `EventSource` API in browser, `StreamingResponse` in FastAPI.

### FFS3 (Frontend) <-> FFS2 (Graph Server)

- **Primary Protocol**: **WebSockets**
  - **Why**: Full duplex required for graph manipulation (layout updates, node dragging sync).
  - **Optimization**: Use **SharedWorker** to maintain a _single_ socket connection across multiple tabs.

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
  - **Usage**: Queue analytical events or "Draft" agent instructions when offline.
  - **Retry**: Exponential backoff managed by browser.

---

## 3. External Integrations

### WebRTC

- **Status**: **Evaluate/Defer**.
- **Use Case**: Peer-to-peer heavy lifting (e.g., streaming a tab capture to a remote analyzer).
- **Trigger**: Only implement if Relay Server bandwidth becomes a cost prohibitive bottleneck.

### GraphQL

- **Status**: **Secondary**.
- **Use Case**: Complex nested queries on the Knowledge Graph.
- **Trigger**: If REST/gRPC endpoints become too chatty (N+1 problem).

---

## 4. Security Boundaries

- **CORS**: Strict allowlist for FFS3 origin.
- **CSP**: Content Security Policy must allow gRPC-Web and WASM (if used for local embeddings).
- **Auth**: Bearer Tokens (JWT) passed in gRPC metadata / HTTP headers.
