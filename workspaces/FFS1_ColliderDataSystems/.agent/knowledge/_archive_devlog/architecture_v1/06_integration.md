# Integration

> How systems work together: LangGraph ↔ Pydantic AI, workflow execution, context loading.

## LangGraph.js ↔ Pydantic AI Graph

Both systems operate on the **same NodeContainer**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      NODE CONTAINER                              │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ instructions/ │  │ workflows/    │  │ tools/        │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│         ▲                   │ ▲               │                  │
│         │                   │ │               │                  │
│  ┌──────┴──────┐            ▼ │            ┌──┴───────────┐     │
│  │ LANGGRAPH.JS│────────────┘ └────────────│ PYDANTIC AI  │     │
│  │ (Browser)   │                           │ GRAPH        │     │
│  │             │                           │ (Server)     │     │
│  │ Reads:      │                           │              │     │
│  │ • context   │                           │ Processes:   │     │
│  │ • tools     │                           │ • workflows  │     │
│  │             │                           │ • creates    │     │
│  │ Writes:     │                           │   subnodes   │     │
│  │ • workflows │                           │              │     │
│  └─────────────┘                           └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow Lifecycle

```
1. Agent (LangGraph.js) reads context from container
2. Agent generates workflow (code, instructions)
3. Agent writes workflow to container via Data Server API
4. GraphTool Server receives workflow execution request
5. Server (Pydantic AI Graph) processes workflow
6. Server creates new subnode with new container
7. SSE notifies SW of new node
8. SW updates cache, UI refreshes
```

---

## Context Loading

### Startup Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         EXTENSION STARTUP                                   │
│                                                                             │
│  1. SW wakes up                                                             │
│                        │                                                    │
│                        ▼                                                    │
│  2. Check chrome.storage for cached auth                                    │
│                        │                                                    │
│          ┌─────────────┴─────────────┐                                     │
│          │                           │                                     │
│          ▼                           ▼                                     │
│     [CACHED]                    [NO CACHE]                                 │
│     Load from storage           Show login UI                              │
│          │                           │                                     │
│          ▼                           ▼                                     │
│  3. Hydrate Main Context        Wait for login                             │
│     (user, permissions)              │                                     │
│          │                           │                                     │
│          ▼                           ▼                                     │
│  4. Preload app configs         After login, hydrate                       │
│     (from Data Server)                                                     │
│          │                                                                  │
│          ▼                                                                  │
│  5. Ready for navigation                                                    │
└────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         NODE NAVIGATION                                     │
│                                                                             │
│  1. User clicks node in Sidepanel                                          │
│                        │                                                    │
│                        ▼                                                    │
│  2. Sidepanel → SW: { type: 'NAVIGATE', app, node }                        │
│                        │                                                    │
│                        ▼                                                    │
│  3. SW checks cache: context_manager.cache.nodeContexts[node]              │
│                        │                                                    │
│          ┌─────────────┴─────────────┐                                     │
│          │                           │                                     │
│          ▼                           ▼                                     │
│     [CACHE HIT]                 [CACHE MISS]                               │
│     Use cached                  Fetch from server                          │
│          │                           │                                     │
│          │                           ▼                                     │
│          │                 Data Server: GET /api/v1/context                │
│          │                           │                                     │
│          │                           ▼                                     │
│          │                 Store in cache                                  │
│          │                           │                                     │
│          └───────────┬───────────────┘                                     │
│                      ▼                                                      │
│  4. Update tab context: context_manager.tabs[tabId] = { app, node, ... }   │
│                      │                                                      │
│                      ▼                                                      │
│  5. Broadcast via chrome.storage.session                                    │
│                      │                                                      │
│                      ▼                                                      │
│  6. UI components re-render                                                 │
│                      │                                                      │
│                      ▼                                                      │
│  7. Agent ready with new merged context                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Real-Time Updates (SSE)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSE EVENT HANDLING                            │
│                                                                  │
│  Data Server ──────────────────────────► SW                     │
│                                           │                      │
│  Event Types:                             ▼                      │
│                                   ┌───────────────┐             │
│  PERMISSION_CHANGED ───────────►  │ Update main   │             │
│                                   │ context       │             │
│                                   └───────────────┘             │
│                                           │                      │
│  CONTEXT_UPDATED    ───────────►  ┌───────▼───────┐             │
│                                   │ Invalidate    │             │
│                                   │ cache, refetch│             │
│                                   └───────────────┘             │
│                                           │                      │
│  NODE_MODIFIED      ───────────►  ┌───────▼───────┐             │
│                                   │ Update tab    │             │
│                                   │ if viewing    │             │
│                                   └───────────────┘             │
│                                           │                      │
│  APP_CONFIG_CHANGED ───────────►  ┌───────▼───────┐             │
│                                   │ Reload app    │             │
│                                   │ config        │             │
│                                   └───────────────┘             │
│                                           │                      │
│                                           ▼                      │
│                                  chrome.storage.session         │
│                                           │                      │
│                                           ▼                      │
│                                  UI components react             │
└─────────────────────────────────────────────────────────────────┘
```

---

## FILESYST Sync

Bidirectional sync between local filesystem and server:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         FILESYST SYNC                                       │
│                                                                             │
│  LOCAL                    NATIVE HOST              DATA SERVER              │
│  .agent/                      │                        │                    │
│     │                         │                        │                    │
│  ───┼─────────────────────────┼────────────────────────┼───────────────    │
│     │                         │                        │                    │
│  FILE → SERVER (Daily/Manual)                                              │
│     │                         │                        │                    │
│     └──► Read .agent/ ───────►│                        │                    │
│                               └──► POST /api/v1/sync ──►│                   │
│                                                        │                    │
│  ───┼─────────────────────────┼────────────────────────┼───────────────    │
│     │                         │                        │                    │
│  SERVER → FILE (On-Demand)                                                 │
│     │                         │                        │                    │
│     │                         │◄── GET /api/v1/context─┘                   │
│     │◄── Write .agent/ ◄──────┘                                            │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

**Trigger:**

- Manual: User clicks "Sync" in extension
- Scheduled: Daily at configured time
- API: External system triggers via Data Server
