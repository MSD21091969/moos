# mo:os — First Principles Critique & Architecture Vision

---

## Part 1: Critique of the Current Codebase

### 1.1 The Fundamental Problem: Split Identity

The codebase has TWO models for the same concept — the NodeContainer:

- **`Container`** (`core.ts`) — algebraic, with `interface: {inputs, outputs}`, `layers`, `wiring: Wire[]`, composition operators (`composeSequential`, `composeParallel`)
- **`NodeRecord`** (`data-server/main.ts`) — flat CRUD row with `application_id`, `parent_id`, `path`, `container` (JSON blob), `metadata_`

These are the same thing described in two incompatible languages. The algebraic `Container` has no persistence. The `NodeRecord` has no algebra. Neither knows about the other at runtime. This is the source of nearly every downstream gap.

### 1.2 Schema Without Execution

The four graph morphisms (`ADD_NODE_CONTAINER`, `LINK_NODES`, `UPDATE_NODE_KERNEL`, `DELETE_EDGE`) are defined as Zod schemas in `superset.ts`. They are parsed from LLM output in `agent-loop.ts`. They are broadcast as events via WebSocket.

**But nothing applies them.** There is no executor. The schemas are syscall definitions for a kernel that doesn't exist. The frontend `graphStore.ts` applies them to XYFlow nodes — a visual projection pretending to be state mutation. The backend stores nothing.

### 1.3 Semantic Layer Bloat

The `.agent` system and `ContainerLayers` define five semantic categories:
```typescript
layers: { rules?, tools?, workflows?, instructions?, knowledge? }
```

But if the axiom is "content is context IS the application," then these categories are human convenience labels on the same underlying structure: **a container with an interface**. A "tool" is a container whose kernel is executable. A "workflow" is a container whose wiring composes child containers. "Knowledge" is a container whose output ports expose data. "Instructions" are containers that feed into prompt composition.

The current code treats these as fundamentally different things (separate directories, separate inheritance paths, separate runtime handling). This violates the recursive container axiom.

### 1.4 The "Functor" Is Not a Functor

`ProviderFunctor` maps `Prompt → Completion`. In category theory, a functor `F: C → D` must:
1. Map objects: `F(A)` for every object A in C
2. Map morphisms: `F(f: A → B) = F(f): F(A) → F(B)`
3. Preserve identity: `F(id_A) = id_{F(A)}`
4. Preserve composition: `F(g ∘ f) = F(g) ∘ F(f)`

The current implementation does none of this. It's a function call, not a functor. The naming imports categorical language without categorical behavior. A true functor in mo:os would map **containers** (objects) and **morphisms** (edges) from one category (e.g., the user's active state graph) to another (e.g., the LLM's prompt space), preserving the compositional structure.

### 1.5 No Persistent State

`InMemoryCategoryStore` is a `Map`. All seed data lives in JavaScript objects inside `data-server/main.ts`. There is no database. The ontology's "RestingStateDB" — the immutable record of finalized DAG reasoning — is literally absent. Every restart loses all state.

### 1.6 The Main Loop Is Not a Loop

`runAgentLoop` in `engine/main.ts` runs once on bootstrap with `ToolFirstProviderFunctor` (a test stub that always requests the first tool), then the process exits. The ontology describes an event-based execution cycle that monitors the Active State Cache and fires morphisms. What exists is a one-shot function call.

### 1.7 TypeScript as Kernel Language

The mo:os kernel — the main loop, container runtime, morphism dispatch, state management — needs:
- **True concurrency** for multi-path DAG evaluation (goroutines, not event loop)
- **Predictable latency** for real-time morphism dispatch (not V8 GC pauses)
- **Strong wire protocol** for inter-process communication (native protobuf/gRPC, not bolted-on)
- **Single-binary deployment** (not node_modules + bundler + runtime)
- **Long-running daemon stability** (not Node.js memory leaks over days)

TypeScript is the right language for browser surfaces (React/XYFlow). It is the wrong language for an operating system kernel.

### 1.8 HTTP for Internal Communication

Services communicate via HTTP REST:
- Engine → data-server: `POST /bootstrap`
- Engine → tool-server: `POST /execute`
- Engine → agent-compat: `POST /agent/morphisms`
- Frontend → data-server: `GET /api/v1/apps`

For an OS, internal IPC should be:
- **gRPC** with protobuf: typed, streaming, bidirectional, efficient
- **Channels/queues** for in-process: zero-copy, backpressure-aware
- HTTP/REST only for external-facing admin APIs

### 1.9 Chrome Extension Is Not a Graph Object

The extension is an iframe wrapper (`sidepanel.html` loads `http://localhost:4201`). A `RuntimeSurface` node is created in seed data, but it's inert — not linked to the actual extension lifecycle, not participating in morphism dispatch, not receiving SYNC_ACTIVE_STATE projections as a first-class subscriber.

### 1.10 Orphaned Ontology

The superset ontology (`superset_ontology_v1.json`) is not wired into any `.agent/manifest.yaml`. The architectural blueprint is a knowledge file sitting next to conversation logs and PDFs, unreferenced by the system it's supposed to govern. The code and the ontology have diverged into separate realities.

---

## Part 2: First Principles — What mo:os Actually Is

### 2.1 The Core Insight

**mo:os is not a web application. It is an operating system for compositional AI-human computation.**

An operating system has:
| OS Concept | mo:os Equivalent |
|---|---|
| Kernel | Root Container + Main Loop |
| Process | Container execution (model call, tool run, surface render) |
| Filesystem | Resting State DB (PostgreSQL + JSONB + pgvector) |
| RAM | Active State Cache (in-memory container graph per session) |
| Syscalls | Graph Morphisms (ADD, LINK, UPDATE, DELETE) |
| IPC | gRPC streams + WebSocket channels |
| Shell | Runtime Surfaces (Chrome sidepanel, tab, PiP, CLI) |
| Users | AuthUser containers with permission-bounded traversal |
| Permissions | ACL on containers (OWNS morphism = traversal right) |

### 2.2 The One Axiom

**Everything is a Container.**

A container is a typed, recursive, composable unit with:
- **Identity** (URN)
- **Interface** (typed input/output ports)
- **Kernel** (the actual content/state/logic)
- **Wiring** (connections to other containers)
- **Permissions** (who can read/write/execute)
- **Children** (recursive sub-containers)

There is no separate concept of "tool", "skill", "workflow", "instruction", "knowledge", "app", "user", "surface." These are all containers with different interface shapes and kernel types:

| Old Concept | Container Specialization |
|---|---|
| Tool | Container with executable kernel, typed I/O |
| Workflow | Container whose wiring composes child tool containers |
| Knowledge | Container whose kernel holds data, outputs expose it |
| Instruction | Container whose output feeds prompt composition |
| Skill | **Deprecated** — was a semantic alias for "composed tool template" |
| AppTemplate | Container whose children define application structure (read-only) |
| AppInstance | Hydrated copy of AppTemplate with user-specific state |
| User | Container with identity kernel, permission ACL, personal sub-graph |
| RuntimeSurface | Container projecting other containers into a browser context |
| mo:os itself | The root container containing all other containers |

### 2.3 "Content Is Context IS the Application"

This means:
- A NodeContainer's kernel IS the content (the data, the logic, the state)
- That same kernel IS the context (it's what gets composed into prompts, what the model sees)
- That same kernel IS the application (there's no separate "app" abstraction — the container tree IS the app)

Implication: There should be **one JSON schema** for the container, and the entire system reads from it. No ORM, no view models, no DTOs. One shape. Persisted as JSONB in PostgreSQL. Projected as-is into React. Composed as-is into prompts.

### 2.4 User Model

Each authenticated user has:
1. **A root container** — their mo:os instance (their "desktop")
2. **Permission-bounded top-level containers** — stored in a dedicated array in the user's DB record
3. These top-level containers are either:
   - AppInstances they've hydrated from templates
   - Shared containers they've been granted access to
4. Traversal from root → children is permission-gated at every edge

```
AuthUser Container (root)
├── AppInstance: "My Project" (hydrated from AppTemplate)
│   ├── Workspace Container
│   │   ├── Tool Container: "code_search"
│   │   ├── Knowledge Container: "project_docs"
│   │   └── Workflow Container: "deploy_pipeline"
│   └── RuntimeSurface Container: "ffs4-sidepanel"
├── AppInstance: "Shared Dashboard" (granted by another user)
└── Personal Context Container
    ├── Preferences
    └── Memory (vector-indexed, MCP-accessible)
```

---

## Part 3: Complete Superset Ontology Specification

### 3.1 The Container Schema (One Schema to Rule Them All)

```
Container {
  // Identity
  urn: string                    // "urn:moos:{scope}:{path}" — globally unique
  version: uint64                // Monotonic version for conflict detection

  // Interface (what this container accepts and produces)
  interface: {
    inputs:  Port[]              // Named, typed input slots
    outputs: Port[]              // Named, typed output slots
  }

  // Kernel (the actual content — polymorphic by container kind)
  kind: ContainerKind            // "data" | "executable" | "composite" | "surface" | "identity"
  kernel: bytes | JSON           // The payload. Interpreted based on kind.

  // Structure
  parent_urn: string?            // Parent container (null for root)
  children: string[]             // Child container URNs (ordered)
  wiring: Wire[]                 // Directed connections between ports

  // Permissions
  owner_urn: string              // URN of owning user/system container
  acl: ACLEntry[]                // Access control list

  // Metadata
  created_at: timestamp
  updated_at: timestamp
  tags: map<string, string>      // Arbitrary key-value (replaces "domain", "species", etc.)
}

Port {
  name: string
  schema: JSONSchema             // Validates data flowing through this port
  direction: "in" | "out"
}

Wire {
  from_urn: string               // Source container URN
  from_port: string              // Source port name
  to_urn: string                 // Target container URN
  to_port: string                // Target port name
}

ACLEntry {
  principal_urn: string          // Who (user, group, wildcard)
  operations: Operation[]        // What they can do
}

Operation = "read" | "write" | "execute" | "admin" | "traverse"
```

### 3.2 Container Kinds

| Kind | Kernel Contains | Behavior |
|---|---|---|
| `data` | JSON document, text, binary blob | Passive storage. Read via output ports. |
| `executable` | Code reference or inline logic | Invoked via input ports, produces on output ports. |
| `composite` | Nothing (structure is in children + wiring) | Composition of child containers. Wiring defines dataflow. |
| `surface` | Render configuration (url, component ref) | Projects container state into a UI context. |
| `identity` | User profile, credentials, preferences | Authentication anchor. Owns other containers. |

### 3.3 Morphisms (The Four Syscalls)

These are the ONLY mutations the system understands. Everything else is composed from these:

```
ADD_CONTAINER {
  urn: string                    // URN for the new container
  parent_urn: string             // Where to attach it
  kind: ContainerKind
  interface: Interface
  kernel: bytes | JSON
  tags: map<string, string>
}

LINK {
  from_urn: string
  from_port: string
  to_urn: string
  to_port: string
}

MUTATE_KERNEL {
  urn: string
  patch: JSONPatch | bytes       // RFC 6902 JSON Patch or full replacement
  expected_version: uint64       // Optimistic concurrency
}

UNLINK {
  from_urn: string
  from_port: string
  to_urn: string
  to_port: string
}
```

**Renamed from current ontology:**
- `ADD_NODE_CONTAINER` → `ADD_CONTAINER` (Node is implied; everything is a container)
- `LINK_NODES` → `LINK` (Nodes is implied)
- `UPDATE_NODE_KERNEL` → `MUTATE_KERNEL` (Update is vague; Mutate is precise)
- `DELETE_EDGE` → `UNLINK` (An edge IS a link between ports)

### 3.4 The Morphism Envelope

```
MorphismEnvelope {
  id: string                     // Unique envelope ID
  source_urn: string             // Who issued it (user, model, system)
  session_id: string             // Which session context
  turn: uint32                   // Turn number in conversation
  timestamp: timestamp
  morphisms: Morphism[]          // Ordered list of mutations
  causality: string[]            // IDs of envelopes that caused this one
}
```

### 3.5 Systems (Renamed/Clarified)

| System | Identity | Responsibility |
|---|---|---|
| **Kernel** (was RootContainer) | `urn:moos:system:kernel` | The mo:os runtime. Hosts the main loop. Owns system containers. |
| **Loop** (was MainLoop) | Internal to Kernel | Event-driven scheduler: receives events → evaluates state → dispatches morphisms → applies results |
| **Store** (was RestingStateDB) | PostgreSQL + pgvector | Persistent, versioned container graph. Source of truth. Immutable history via append-only morphism log. |
| **Cache** (was ActiveStateCache) | In-memory (Redis or process-local) | Hot working set per session. Morphisms applied here first, then committed to Store. |

---

## Part 4: The Root Container, Main Loop, and Identity of mo:os

### 4.1 mo:os IS the Root Container

```
urn:moos:system:kernel
├── urn:moos:system:loop          (the main loop — composite container)
│   ├── urn:moos:system:evaluator (reads cache, decides what fires)
│   ├── urn:moos:system:dispatcher (sends morphisms to executors)
│   └── urn:moos:system:committer (writes finalized state to store)
├── urn:moos:system:store         (resting state — surface over PostgreSQL)
├── urn:moos:system:cache         (active state — in-memory graph)
├── urn:moos:system:models        (provider registry)
│   ├── urn:moos:system:models:anthropic
│   ├── urn:moos:system:models:gemini
│   └── urn:moos:system:models:openai
├── urn:moos:system:tools         (system tool registry)
│   ├── urn:moos:system:tools:echo
│   └── urn:moos:system:tools:search
└── urn:moos:admin:users          (user identity containers)
    ├── urn:moos:admin:users:{userId1}
    │   ├── urn:moos:user:{userId1}:apps:...  (their app instances)
    │   └── urn:moos:user:{userId1}:memory:... (their persistent memory)
    └── urn:moos:admin:users:{userId2}
```

### 4.2 The Main Loop (Event-Driven)

```
forever {
  event = cache.waitForEvent()    // Block until: user input, model completion, tool result, timer, morphism

  switch event.type {
    case USER_INPUT:
      // Compose prompt from session context (traverse container graph)
      // Dispatch to model container (selected by session config)
      // Model returns: text + morphisms + tool_calls

    case MODEL_COMPLETION:
      // Parse morphisms from output
      // Validate against container interfaces (type-check ports)
      // Apply to cache (optimistic)
      // If tool_calls: dispatch to tool containers
      // If morphisms: broadcast SYNC to subscribed surfaces
      // If end_turn: commit cache delta to store

    case TOOL_RESULT:
      // Append result to session history
      // Continue model conversation (next turn)

    case MORPHISM_EXTERNAL:
      // Validate permissions (does source have write access?)
      // Apply to cache
      // Broadcast SYNC

    case SYNC_TICK:
      // Push cache state to all subscribed surface containers
      // Surfaces project state into their UI context
  }
}
```

This loop runs as a **goroutine per session**. Multiple sessions run concurrently. The kernel manages session lifecycle.

### 4.3 Multi-Path DAG Evaluation

The ontology axiom "Multi_Path_DAGs: Execution rejects single-path CoT" means:

When a model produces morphisms, the evaluator can fork the cache into parallel branches:
1. Branch A: Apply morphism set 1, continue evaluation
2. Branch B: Apply morphism set 2, continue evaluation
3. Score branches, select best, commit to store

This requires the cache to be **forkable** — a copy-on-write data structure where branching is cheap. This is trivially implementable with immutable data structures in Go (persistent maps/trees) but extremely difficult in JavaScript (mutable reference types everywhere).

---

## Part 5: The Principle Programming Language

### 5.1 Decision: **Go** for the Kernel

| Criterion | TypeScript | Go | Rust |
|---|---|---|---|
| Concurrency model | Event loop (single-threaded) | Goroutines + channels (native) | Async/await + tokio (complex) |
| GC behavior | V8 GC pauses (unpredictable) | Low-latency GC (designed for servers) | No GC (manual/ownership) |
| Deployment | node_modules + bundler + runtime | Single static binary | Single static binary |
| gRPC/protobuf | Third-party, heavy deps | First-class (google.golang.org/grpc) | Mature but verbose (tonic) |
| Development speed | Fast (dynamic) | Fast (simple language, fast compiler) | Slow (borrow checker, compile times) |
| Long-running daemon | Memory leaks common | Battle-tested (Docker, K8s, etcd) | Excellent but over-engineered |
| WebSocket | ws library | gorilla/websocket, nhooyr | tokio-tungstenite |
| JSON/JSONB handling | Native | encoding/json (good enough) | serde_json (excellent) |
| Community for OS-like systems | None | Docker, K8s, CockroachDB, etcd | Linux kernel, Servo |

**Go wins** because mo:os needs concurrent session handling (goroutines), efficient IPC (channels), fast iteration (simple language), and single-binary deployment. Rust's ownership model adds friction without proportional benefit for this use case (we're not writing a browser engine or OS kernel for hardware).

### 5.2 TypeScript Remains for Surfaces

FFS4/FFS5/FFS6 stay TypeScript/React. They are **surface containers** — UI projections of the container graph. React/XYFlow is the right tool for rendering interactive graphs in browsers. But they contain **zero business logic**. They read container state via WebSocket and render it. They send user input to the kernel via gRPC-Web or WebSocket. That's it.

### 5.3 Current TypeScript Apps as Containers

The current MOOS TypeScript services (data-server, tool-server, engine) are themselves containers in the mo:os graph:

```
urn:moos:system:services:data-server      (kind: executable, kernel: {runtime: "node", entry: "main.ts"})
urn:moos:system:services:tool-server      (kind: executable, kernel: {runtime: "node", entry: "main.ts"})
urn:moos:system:services:engine           (kind: executable, kernel: {runtime: "node", entry: "main.ts"})
urn:moos:system:surfaces:ffs4             (kind: surface, kernel: {url: "http://localhost:4201"})
urn:moos:system:surfaces:ffs5             (kind: surface, kernel: {url: "http://localhost:4202"})
urn:moos:system:surfaces:ffs6             (kind: surface, kernel: {url: "http://localhost:4200"})
```

During migration, these TypeScript services run as sidecar containers managed by the Go kernel. Eventually, the kernel subsumes their functionality (data-server → kernel's HTTP admin API, tool-server → kernel's tool executor, engine → kernel's main loop).

---

## Part 6: Data Flow Architecture

### 6.1 Wire Protocols

| Path | Protocol | Why |
|---|---|---|
| Kernel ↔ Store (PostgreSQL) | SQL/pgx | Direct DB access, no intermediate layer |
| Kernel ↔ Cache | In-process (Go maps/channels) | Zero-copy, maximum speed |
| Kernel ↔ Tool Runtime | gRPC (bidirectional streaming) | Typed, efficient, supports streaming tool output |
| Kernel ↔ Model Providers | HTTPS (provider SDKs) or gRPC | Provider-dependent, abstracted by model container |
| Kernel ↔ Surfaces | WebSocket (JSON-RPC 2.0) | Browser-compatible, bidirectional, real-time |
| Kernel ↔ External Agents | gRPC or MCP over SSE | Interoperability with Claude, other agent frameworks |
| Surface ↔ Surface | WebRTC (future) | Peer-to-peer for collaborative editing |
| Kernel ↔ Kernel (federation) | gRPC (future) | Multi-instance mo:os federation |

### 6.2 End-to-End Data Flow

```
[Chrome Extension / Browser Surface]
    │
    │  WebSocket JSON-RPC
    ▼
[mo:os Kernel — Go Binary]
    │
    ├─► [Active State Cache — In-Memory]
    │       • Mutable container graph per session
    │       • Forkable for multi-path evaluation
    │       • Committed to Store on logical conclusion
    │
    ├─► [Main Loop — Goroutine per Session]
    │       • Receives events from all sources
    │       • Evaluates which morphisms to fire
    │       • Dispatches to appropriate executor
    │       • Applies results to cache
    │       • Broadcasts SYNC to surfaces
    │
    ├─► [Model Dispatcher]
    │       │   Composes prompt from container graph
    │       │   Selects provider by session/container config
    │       ▼
    │   [Provider Adapter — gRPC/HTTPS]
    │       │   Anthropic: Claude Opus 4.6 (default)
    │       │   Google: Gemini 2.5 Flash / ADK
    │       │   OpenAI: GPT-5.x
    │       │   Local: Ollama
    │       ▼
    │   [Completion → Parse Morphisms → Validate → Apply]
    │
    ├─► [Tool Executor — gRPC to Sandboxed Runtime]
    │       │   Tool containers execute in isolation
    │       │   Input/output validated against container interface
    │       ▼
    │   [Tool Result → Append to Session → Continue Loop]
    │
    └─► [Store — PostgreSQL + pgvector]
            • Containers stored as JSONB
            • Morphism history as append-only log
            • Vector embeddings for semantic search (MCP-accessible)
            • Version tracking for optimistic concurrency
```

### 6.3 Docker Compose Topology

```yaml
services:
  moos-kernel:
    image: moos/kernel:latest          # Single Go binary
    ports:
      - "8000:8000"                    # HTTP admin API
      - "18789:18789"                  # WebSocket gateway
      - "50051:50051"                  # gRPC (internal)
    depends_on: [postgres, redis]

  postgres:
    image: pgvector/pgvector:pg16
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine              # Session cache + morphism queue

  tool-runtime:
    image: moos/tool-runtime:latest    # Sandboxed executor
    ports: ["50052:50052"]             # gRPC

  # Surfaces (dev mode — Vite dev servers)
  ffs4:
    image: node:22-alpine
    command: pnpm dev --port 4201
    volumes: [./ffs3/apps/ffs4:/app]

  ffs6:
    image: node:22-alpine
    command: pnpm dev --port 4200
    volumes: [./ffs3/apps/ffs6:/app]
```

---

## Part 7: What This Means for the Current Codebase

### 7.1 What Survives

| Component | Fate |
|---|---|
| `@moos/core` Container algebra | **Keep & port to Go** — composition/validation logic is sound |
| `@moos/core` superset.ts morphism schemas | **Keep & port to protobuf** — morphism types are correct (rename only) |
| `@moos/functors` provider pattern | **Keep & port to Go** — but make it a real functor (map containers + morphisms, not just prompts) |
| `@moos/store` interface-based queries | **Port to PostgreSQL** — replace Map with JSONB queries |
| FFS4 React UI (graph + chat) | **Keep as-is** — surface container, works correctly |
| FFS6 React UI (IDE viewer) | **Keep as-is** — surface container |
| Chrome Extension MV3 wrapper | **Keep** — thin shell, does its job |
| `.agent` governance chain | **Keep** — inheritance model is clean |
| Superset ontology JSON | **Wire into manifest chain** and **extend to full spec** |

### 7.2 What Gets Replaced

| Component | Replacement |
|---|---|
| `data-server/main.ts` (1140-line monolith) | Go kernel with PostgreSQL-backed container store |
| `tool-server/main.ts` (HTTP tool execution) | Go kernel's gRPC tool dispatcher |
| `engine/main.ts` (one-shot bootstrap) | Go kernel's persistent main loop (goroutine per session) |
| `InMemoryCategoryStore` (JavaScript Map) | PostgreSQL JSONB + in-process Go cache |
| `SessionState` (message array) | Redis-backed session with container graph snapshot |
| All HTTP inter-service calls | gRPC with protobuf (kernel-internal: channels) |
| Seed data (hardcoded JS objects) | PostgreSQL migrations + seed SQL |
| NanoClaw bridge (WebSocket echo stub) | Go kernel's WebSocket gateway (real streaming) |

### 7.3 Migration Path

**Phase 0 — Now**: Wire ontology into manifests. Fix broken references. Define protobuf schemas for Container + Morphisms. This is documentation + specification work.

**Phase 1 — Foundation**: Build Go kernel binary with:
- PostgreSQL container store (CRUD + tree traversal + JSONB queries)
- Morphism executor (the four syscalls actually mutating state)
- WebSocket gateway (replace NanoClaw bridge)
- gRPC tool execution interface

**Phase 2 — Loop**: Implement the main loop as persistent goroutine:
- Event-driven (not polling)
- Session lifecycle management
- Model dispatch via provider adapters (start with Anthropic)
- Morphism validation + application + broadcast

**Phase 3 — Surfaces**: Connect FFS4/FFS6 to Go kernel:
- Replace REST calls with WebSocket/gRPC-Web
- Surface containers registered in graph
- Real-time SYNC_ACTIVE_STATE projection

**Phase 4 — Dockerize**: Compose all services:
- kernel + postgres + redis + tool-runtime + surface-servers
- Single `docker compose up` for full stack

**Phase 5 — Advanced**: Multi-path DAG evaluation, federated mo:os instances, WebRTC peer surfaces, MCP server for external agent access.

---

## Part 8: Verification

After each phase, verify:
1. **Container CRUD**: Create/read/update/delete containers via gRPC/HTTP, confirm PostgreSQL persistence
2. **Morphism execution**: Issue ADD/LINK/MUTATE/UNLINK, confirm state mutation in store + cache
3. **Main loop**: Send user input, observe model call → morphism parse → state mutation → surface sync
4. **Surface rendering**: FFS4 graph updates in real-time when morphisms are applied
5. **Restart recovery**: Kill kernel, restart, confirm all state recovered from PostgreSQL
6. **Permission enforcement**: Attempt unauthorized traversal, confirm denial
