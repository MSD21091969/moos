# Frontend

> Chrome Extension architecture: Service Worker, Context Manager, UI components.

## Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHROME EXTENSION (Plasmo)                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      SERVICE WORKER (Orchestrator)                       ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │                    CONTEXT MANAGER (Singleton)                      │ ││
│  │  │                                                                     │ ││
│  │  │  ┌──────────────┐     ┌──────────────────────────────────────────┐ │ ││
│  │  │  │ MAIN CONTEXT │     │           TAB/AGENT CONTEXTS              │ │ ││
│  │  │  │              │     │                                           │ │ ││
│  │  │  │ • User auth  │     │  tab_123: { app: cloud://app1, node: /x } │ │ ││
│  │  │  │ • Permissions│     │  tab_456: { app: filesyst://FFS1, ... }   │ │ ││
│  │  │  │ • Global cfg │     │  pip_789: { focuses: [tab_123, tab_456] } │ │ ││
│  │  │  │ • App index  │     │  window_2_tab_001: { ... }                │ │ ││
│  │  │  └──────────────┘     └──────────────────────────────────────────┘ │ ││
│  │  │         │                                    │                      │ ││
│  │  │         └──────────────┬─────────────────────┘                      │ ││
│  │  │                        ▼                                            │ ││
│  │  │              ┌─────────────────┐                                    │ ││
│  │  │              │   LOCAL CACHE   │  (IndexedDB / chrome.storage)      │ ││
│  │  │              │  • App configs  │  ← Loaded upfront at startup       │ ││
│  │  │              │  • Node contexts│  ← Cached on first access          │ ││
│  │  │              │  • Tool schemas │  ← From VectorDB                   │ ││
│  │  │              └─────────────────┘                                    │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │                      LANGGRAPH ROUTER                                │││
│  │  │  • Receives: (tab_id, message)                                      │││
│  │  │  • Looks up: context_manager.get(tab_id) → merged context           │││
│  │  │  • Routes to: FilesystAgent | CloudAgent | DomAgent                 │││
│  │  │  • Each agent sees: MAIN_CONTEXT + TAB_CONTEXT                      │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ CONTENT      │  │ SIDEPANEL    │  │ DocPiP       │  │ OFFSCREEN DOC   │  │
│  │ SCRIPTS      │  │ (Appnode     │  │ (User-to-User│  │                 │  │
│  │ (Per-tab)    │  │  Browser +   │  │  Comms)      │  │ • WebGPU        │  │
│  │              │  │  AI Pilot)   │  │              │  │ • Heavy compute │  │
│  │ • DOM access │  │ • Navigation │  │ • WebRTC     │  │                 │  │
│  │ • Tab agent  │  │ • Chat UI    │  │ • Video/Audio│  │                 │  │
│  │              │  │ • Agent Seat │  │ • Floats     │  │                 │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Context Manager

Central state management for multi-agent, multi-tab, multi-window architecture.

### Structure

```typescript
interface ContextManager {
  main: MainContext;
  tabs: Map<string, TabContext>; // key: `${windowId}_${tabId}`
  pip: PiPContext;
  cache: ContextCache;
}

interface MainContext {
  user: { id: string; email: string; profile: UserProfile };
  permissions: AppPermission[];
  secrets: Map<string, string>; // Encrypted, decrypted at tool execution
  apps: AppInfo[]; // Preloaded at startup
}

interface TabContext {
  app: AppAddress; // "cloud://app1" | "filesyst://FFS1"
  node: NodePath;
  domain: "FILESYST" | "CLOUD" | "ADMIN";
  container: NodeContainer | null;
  threadId: string;
  messages: Message[];
}

interface PiPContext {
  mode: "single" | "multi";
  focuses: string[];
  activeTabKey: string;
}

interface ContextCache {
  appConfigs: Map<string, AppConfig>;
  nodeContexts: Map<string, NodeContainer>;
  toolIndex: Map<string, ToolSchema>;
  policies: CachePolicies;
}

interface CachePolicies {
  nodeContextTTL: number; // ms, -1 = infinite (SSE invalidation)
  toolIndexRefresh: number;
  appConfigRefresh: number;
}
```

### Persistence

`tabs` Map persists across SW restarts via `chrome.storage.session`.

### SW Module Organization

```
service_worker/
├── index.ts                 # Entry, message router
├── context/
│   ├── manager.ts           # ContextManager singleton
│   ├── main.ts              # MainContext ops
│   ├── tab.ts               # TabContext ops
│   └── cache.ts             # ContextCache with policies
├── agents/
│   ├── router.ts            # LangGraph router
│   ├── filesyst.ts          # FILESYST agent
│   ├── cloud.ts             # CLOUD agent
│   └── dom.ts               # DOM agent
├── external/
│   ├── native.ts            # Native Messaging
│   ├── data_server.ts       # REST + SSE
│   ├── graphtool.ts         # WebSocket
│   └── vectordb.ts          # VectorDB
└── broadcast/
    └── storage.ts           # chrome.storage sync
```

### Secrets Handling

All tool execution is **client-side (SW)**:

1. Secrets stored in ADMIN container (DB)
2. Fetched to SW on login
3. Encrypted in `chrome.storage`
4. Decrypted by SW at tool execution
5. LLM never sees raw values

---

## Multi-Tab Routing

LangGraph.js uses `thread_id` = `{window_id}_{tab_id}`:

```javascript
const graph = compileGraph(...);

chrome.runtime.onMessage.addListener((msg, sender) => {
  const threadId = `${sender.tab.windowId}_${sender.tab.id}`;

  const state = await graph.invoke(
    { messages: [msg] },
    { configurable: { thread_id: threadId } }
  );
});
```

### Router Logic

```
┌─────────────────────────────────────────────────────────────┐
│                      ROUTER NODE                             │
│                                                              │
│  Input + Context → Decision                                  │
│                                                              │
│  IF context.app.domain == FILESYST → FilesystAgent          │
│  IF context.app.domain == CLOUD   → CloudAgent              │
│  IF input.type == DOM_ACTION      → DomAgent                │
└─────────────────────────────────────────────────────────────┘
```

---

## UI Components

### Sidepanel (Appnode Browser + AI Pilot/Agent Seat)

- **API:** `chrome.sidePanel`
- **Code Location:** FFS2 Chrome Extension (`sidepanel.tsx`, `src/components/sidepanel/`)
- **Context Documentation:** FFS4 (`.agent/` context only)
- **Context:** Tab-specific or Global
- **Use Case:**
  - Navigate appnode graph (Appnode Browser)
  - Interact with AI Pilot/Main Agent Seat
  - Contextual chat with agent
  - Quick actions on containers
- **Lifecycle:** Tied to browser window

Visual styles by domain:
| Domain   | Style                       |
| -------- | --------------------------- |
| FILESYST | Nested tree (File Explorer) |
| CLOUD    | 3D Force Graph              |
| ADMIN    | Filing Cabinet              |

### DocPiP (User-to-User Communications)

- **API:** `window.documentPictureInPicture`
- **Code Location:** FFS2 Chrome Extension (`pipWindow.tsx`, `src/components/pip/`)
- **Context Documentation:** FFS5 (`.agent/` context only)
- **Context:** Global, floats over OS
- **Use Case:**
  - User-to-user video/audio calls (WebRTC)
  - Screen sharing
  - Chat overlay during calls
  - Persistent communication window
- **Lifecycle:** Independent of browser window

Can support multi-party calls and collaborative features.

---

## State Synchronization

All UI components are **dumb views**. Logic lives in SW.

```
User Action → UI → chrome.runtime.sendMessage → SW
                                                 │
                                                 ▼
                                         Process (LangGraph)
                                                 │
                                                 ▼
                                         chrome.storage.session
                                                 │
                                                 ▼
                         UI ← onChanged listener ←
```

**Tech Stack:**

- React + Zustand (UI components)
- chrome.storage (reactive state broadcast)
- SW holds source of truth
