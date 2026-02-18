# Agent System

> AI agents run in two environments: LangGraph.js in the browser service worker and Pydantic AI Graph on the backend GraphToolServer.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BROWSER (Service Worker)                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                    LangGraph.js                          │       │
│  │                                                          │       │
│  │  ┌──────────────┐ ┌─────────────┐ ┌────────────────┐   │       │
│  │  │ CloudAgent   │ │ DomAgent    │ │ FilesystAgent  │   │       │
│  │  │              │ │             │ │                │   │       │
│  │  │ REST + SSE   │ │ Content     │ │ Native         │   │       │
│  │  │ + WebSocket  │ │ Scripts     │ │ Messaging      │   │       │
│  │  └──────────────┘ └─────────────┘ └────────────────┘   │       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (GraphToolServer :8001)                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                  Pydantic AI Graph                       │       │
│  │                                                          │       │
│  │  WorkflowHandler ── processes multi-step workflows      │       │
│  │  GraphHandler    ── creates/modifies node graph          │       │
│  │                                                          │       │
│  └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Browser Agents

Three specialized agents run in the service worker, each handling a specific domain of operations.

### CloudAgent

**Source**: `src/background/agents/cloud-agent.ts`
**Exports**: `initCloudAgent`, `searchForTools`, `executeWorkflow`

The primary AI agent. Uses LangGraph.js to orchestrate multi-step reasoning.

| Function                     | Description                                      |
| ---------------------------- | ------------------------------------------------ |
| `initCloudAgent()`           | Initialize the LangGraph.js agent graph          |
| `searchForTools(query)`      | Semantic search for tools via VectorDbServer     |
| `executeWorkflow(id, steps)` | Execute a workflow via GraphToolServer WebSocket |

**Connects to:**
- DataServer (:8000) via REST for context and state
- GraphToolServer (:8001) via WebSocket for workflow execution
- VectorDbServer (:8002) via REST for semantic search

### DomAgent

**Source**: `src/background/agents/dom-agent.ts`
**Exports**: `handleDomQuery`

Handles DOM interaction in the active browser tab.

| Function                          | Description                             |
| --------------------------------- | --------------------------------------- |
| `handleDomQuery(tabId, selector)` | Execute CSS selector query in tab's DOM |

**Connects to**: Content scripts via `chrome.tabs.sendMessage`

### FilesystAgent

**Source**: `src/background/agents/filesyst-agent.ts`
**Exports**: `readFile`, `writeFile`, `listDir`

Handles local filesystem operations for the FILESYST domain.

| Function                   | Description                           |
| -------------------------- | ------------------------------------- |
| `readFile(path)`           | Read file from local `.agent/` folder |
| `writeFile(path, content)` | Write file to local `.agent/` folder  |
| `listDir(path)`            | List directory contents               |

**Connects to**: Chrome Native Messaging Host

---

## Agent Routing

The service worker's message router determines which agent handles each request:

| Message Type       | Agent         | Backend                  |
| ------------------ | ------------- | ------------------------ |
| `WORKFLOW_EXECUTE` | CloudAgent    | GraphToolServer :8001    |
| `TOOL_SEARCH`      | CloudAgent    | VectorDbServer :8002     |
| `DOM_QUERY`        | DomAgent      | Content Script (tab)     |
| `NATIVE_MESSAGE`   | FilesystAgent | Native Host (filesystem) |

---

## Server-Side Processing

### Pydantic AI Graph (GraphToolServer)

The GraphToolServer runs Python-based Pydantic AI graphs that process workflows submitted by browser agents.

**WebSocket endpoints:**

| Endpoint       | Handler         | Purpose                       |
| -------------- | --------------- | ----------------------------- |
| `/ws/workflow` | WorkflowHandler | Multi-step workflow execution |
| `/ws/graph`    | GraphHandler    | Graph structure operations    |

### Workflow Lifecycle

Both LangGraph.js (browser) and Pydantic AI Graph (server) operate on the same NodeContainer:

```
┌────────────────────────────────────────────────────────────────────┐
│                      NODE CONTAINER                                │
│                                                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │
│  │ instructions/ │  │ workflows/    │  │ tools/        │         │
│  └───────────────┘  └───────────────┘  └───────────────┘         │
│         ▲                   │ ▲               │                    │
│         │                   │ │               │                    │
│  ┌──────┴──────┐            ▼ │            ┌──┴───────────┐      │
│  │ LANGGRAPH.JS│────────────┘ └────────────│ PYDANTIC AI  │      │
│  │ (Browser)   │                           │ GRAPH        │      │
│  │             │                           │ (Server)     │      │
│  │ Reads:      │                           │              │      │
│  │ • context   │                           │ Processes:   │      │
│  │ • tools     │                           │ • workflows  │      │
│  │             │                           │ • creates    │      │
│  │ Writes:     │                           │   subnodes   │      │
│  │ • workflows │                           │              │      │
│  └─────────────┘                           └──────────────┘      │
└────────────────────────────────────────────────────────────────────┘
```

**Execution steps:**

1. Agent (LangGraph.js) reads context from the active NodeContainer
2. Agent generates a workflow (code, instructions, parameters)
3. Agent writes workflow to container via DataServer REST API
4. Agent submits workflow execution request via GraphToolServer WebSocket
5. Server (Pydantic AI Graph) processes workflow steps
6. If permitted (`can_spawn: true`): server creates new subnodes with new containers
7. DataServer persists new nodes
8. SSE event notifies service worker of changes
9. Service worker updates cache, UI refreshes

---

## Template Topology

A "Template" is not a separate class of object. It is a **pre-configured NodeContainer** (or cluster of them) hydrated with a specific context.

### Topology vs. Hierarchy

- **Hierarchy** (Foundation) = Parent/Child relationships (ownership, permissions)
- **Topology** (Templates) = The functional graph of how nodes connect and interact

### Hydration Context

The behavior of a container is determined by how it is **hydrated** (loaded with context):

| Context Setting    | Behavior                                       |
| ------------------ | ---------------------------------------------- |
| `can_spawn: true`  | Agent can create new subnodes (growth)         |
| `can_spawn: false` | Agent is fixed, can only execute tools         |
| `domain: FILESYST` | Hydrates from local `.agent` folder (IDE mode) |
| `domain: CLOUD`    | Hydrates from database container (App mode)    |

### Template Clusters

A template often defines a **cluster** of nodes, not just one:

```
Researcher (Head)
├── Searcher (Tool-focused, specific search tools)
└── Writer (Tool-focused, specific writing tools)
```

- **Topology**: Head controls two subordinates
- **Hydration**:
  - `Researcher`: Full agency, can spawn sub-tasks
  - `Searcher`: Restricted context, read-only tools
  - `Writer`: Restricted context, write-only tools

### ApplicationGraph

The **ApplicationGraph** is the instantiated topology of a specific application:

- Starts with a **Root Node** (Application's root_node_id)
- Unfolds based on the templates used
- Evolving topology as agents create new nodes (if can_spawn is true)

### Hydration Paradigm

```
Definition → Injection → Hydration → Execution

1. Definition:  Unhydrated template (static .agent/ files or JSON)
2. Injection:   User/System injects configuration (secrets, goals)
3. Hydration:   System loads definition + config into a running Container
4. Execution:   The Container becomes a Node in the ApplicationGraph
```
