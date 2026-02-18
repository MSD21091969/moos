# Data Flow

> Communication protocols: internal messaging, external APIs, sync flows.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMMUNICATION MAP                                  │
│                                                                              │
│  CHROME EXTENSION                              EXTERNAL SERVERS              │
│  ┌─────────────────┐                                                        │
│  │ Service Worker  │◄────────────────────────► Native Host (FILESYST)      │
│  │ (Gateway)       │                           JSON/stdin/stdout            │
│  │                 │                                                        │
│  │                 │◄────────────────────────► Data Server                  │
│  │                 │                           REST + SSE                   │
│  │                 │                                                        │
│  │                 │◄────────────────────────► GraphTool Server             │
│  │                 │                           WebSocket                    │
│  │                 │                                                        │
│  │                 │◄────────────────────────► VectorDB Server              │
│  └────────┬────────┘                           REST/gRPC                    │
│           │                                                                  │
│    ┌──────┼───────┬────────────────┐                                        │
│    │      │       │                │                                        │
│    ▼      ▼       ▼                ▼                                        │
│  ┌────┐ ┌────┐ ┌────────┐    ┌──────────┐                                  │
│  │Tab │ │Side│ │Offscr  │    │ DocPiP   │                                  │
│  │CS  │ │Panl│ │Doc     │    │          │                                  │
│  └────┘ └────┘ └────────┘    └──────────┘                                  │
│                                                                              │
│  Internal: chrome.runtime / chrome.tabs / chrome.storage                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Principle:** Service Worker is the **sole gateway** to all external servers.

---

## Internal Communication

Within Chrome Extension:

| Channel             | Method                       | Use Case                |
| ------------------- | ---------------------------- | ----------------------- |
| SW ↔ Content Script | `chrome.tabs.sendMessage`    | Tab-specific operations |
| SW ↔ Sidepanel      | `chrome.runtime.sendMessage` | UI updates              |
| SW ↔ Offscreen      | `chrome.runtime.sendMessage` | Heavy compute           |
| SW ↔ DocPiP         | `chrome.runtime.sendMessage` | Agent seat updates      |
| Any ↔ Storage       | `chrome.storage.session`     | Reactive state sync     |

### Message Format

```typescript
interface Message {
  type: string; // e.g., 'ANALYZE_CLICKED', 'DOM_RESULT'
  payload: any; // Action-specific data
  tabId?: number; // Source tab (if from content script)
  windowId?: number; // Source window
}
```

---

## External Communication

SW → External Servers:

### Native Messaging (FILESYST)

**Protocol:** JSON over stdin/stdout

```
Extension ──► chrome.runtime.sendNativeMessage ──► Python Host
                                                        │
                                                        ▼
                                                   Filesystem
```

**Request:**

```json
{
  "action": "read_agent_context",
  "path": "D:\\FFS0_Factory\\workspaces\\FFS1\\.agent"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "manifest": "...",
    "instructions": ["..."],
    "rules": ["..."]
  }
}
```

### Data Server (CLOUD/ADMIN)

**Protocol:** REST + SSE

**REST Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/context` | GET/POST | Read/write nodecontainer |
| `/api/v1/nodes` | CRUD | Node operations |
| `/api/v1/users` | CRUD | User/account operations |
| `/api/v1/apps` | CRUD | Application management |

**SSE Stream:** `/api/v1/sse`

- Permission changes
- Context updates
- Node modifications

### GraphTool Server

**Protocol:** WebSocket

**Endpoints:**
| Endpoint | Purpose |
|----------|---------|
| `/ws/graph` | Graph queries, mutations |
| `/ws/workflow` | Workflow execution, streaming |

### VectorDB Server

**Protocol:** REST or gRPC

**Purpose:** Tool search, semantic matching

---

## Sync Flows

### FILESYST ↔ Server Sync

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ LOCAL FILE  │      │ NATIVE HOST │      │ DATA SERVER │
│ .agent/     │◄────►│             │◄────►│             │
└─────────────┘      └─────────────┘      └─────────────┘

File → Server: Daily/manual (extension triggers)
Server → File: On-demand (manual/API)
```

### Context Loading Flow

```
1. User navigates to node (click in Sidepanel)
2. Sidepanel → SW: { type: 'NAVIGATE', node: '/dashboard' }
3. SW checks cache
   - HIT: Use cached context
   - MISS: Fetch from server
4. SW updates: context_manager.tabs[tabId].node = '/dashboard'
5. SW updates: chrome.storage.session
6. UI reacts to storage change
7. Agent context is ready for next message
```

### SSE Event Handling

```
Data Server ──(SSE)──► SW
                        │
                        ▼
               ┌─────────────────┐
               │ Event Handler   │
               │                 │
               │ PERMISSION_CHANGED → Update main.permissions
               │ CONTEXT_UPDATED    → Invalidate cache, refetch
               │ NODE_MODIFIED      → Update tab context
               └─────────────────┘
                        │
                        ▼
               chrome.storage.session
                        │
                        ▼
                   UI re-renders
```
