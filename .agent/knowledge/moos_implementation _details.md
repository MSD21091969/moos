# mo:os — Developer Technical Brief

> Authority: Reference (proposal)
> Status: Non-canonical unless explicitly ratified into the foundations document
> Last reviewed: 2026-03

---

## What mo:os Is

mo:os (Multi-Object Operating System) is an open-source runtime kernel for compositional AI-human computation. It implements a single recursive data structure — the **Container** — as the universal primitive for users, tools, models, applications, memory, UI surfaces, and the OS itself. State mutates through exactly four typed graph operations (ADD, LINK, MUTATE, UNLINK). The kernel is written in Go. Persistence is PostgreSQL + pgvector. The model is provider-agnostic. The math is category theory.

This document is the technical developer brief. It covers every stack, language, protocol, and research field involved.

---

## Research Foundations

mo:os draws from six intersecting research areas. If you're contributing, these are the papers and fields that inform the design.

### 1. Category Theory & Functorial Semantics

**Core reference:** Lawvere's *Functorial Semantics of Algebraic Theories* (1963); Fong & Spivak's *Seven Sketches in Compositionality* (2018).

Containers are objects in a category. Morphisms (ADD/LINK/MUTATE/UNLINK) are arrows. The algebra guarantees:
- **Composition**: Sequential (`f ; g`) and parallel (`f ⊗ g`) composition of containers produces valid containers with correct interface types. Implemented as `composeSequential()` and `composeParallel()` with wire bridging and port prefixing.
- **Identity**: Every container has an identity morphism (passthrough wiring from inputs to outputs).
- **Functorial projection**: The UI is a functor `F: ContainerCat → ReactCat` mapping containers to components and morphisms to state updates. Structure-preserving, not ad-hoc.

The key insight from functorial semantics: the *syntax* (container schema) and the *semantics* (runtime execution) are related by a functor, which guarantees that any syntactically valid composition has well-defined runtime behavior.

### 2. Multi-Path DAG Reasoning (LogicGraph)

**Core reference:** *LogicGraph: Benchmarking Multi-Path Logical Reasoning* (2025).

Standard Chain-of-Thought (CoT) forces single-path sequential reasoning. LogicGraph demonstrates that structuring inference as Directed Acyclic Graphs — with multi-path branching, node reuse, and evaluation before commitment — significantly outperforms linear reasoning.

mo:os implements this as a first-class runtime feature:
- The **Active State Cache** is forkable (copy-on-write). When a model proposes multiple reasoning paths, the kernel forks the cache into parallel branches.
- Each branch gets its own goroutine. Morphisms are applied independently.
- Branches are scored (by the model, by heuristics, or by the user). The winning branch is committed to the Resting State (PostgreSQL). Losers are discarded or archived.
- The branching is visualized in real-time via XYFlow in the Chrome sidepanel.

**Implementation concern**: Forkable state requires immutable/persistent data structures. In Go, this means persistent hash-array mapped tries (HAMTs) or similar. The `hamt` package or custom implementation over Go's `sync.Map` patterns.

### 3. Graph Databases & JSONB Modeling

**Core references:** PostgreSQL JSONB documentation; pgvector extension; graph modeling in relational databases via recursive CTEs and adjacency lists.

mo:os does NOT use a dedicated graph database (Neo4j, TigerGraph, etc.). Instead:
- Containers are stored as **JSONB rows** in PostgreSQL with a `parent_urn` column for tree structure and a separate `wires` table for port-to-port edges.
- Tree traversal uses **recursive CTEs** (`WITH RECURSIVE`).
- Graph queries (find all containers reachable from X with permission Y) use recursive CTEs with join-based ACL filtering.
- Vector search (semantic queries against container kernels) uses **pgvector** with HNSW indexes.

**Why not Neo4j**: Operational simplicity. PostgreSQL is one dependency. JSONB + pgvector gives us document store + vector DB + relational + graph traversal in a single process. The container count per mo:os instance is in the thousands to low millions — PostgreSQL handles this trivially. If graph queries become a bottleneck at scale, we can add a materialized graph view or read replica. We do not start with architectural complexity we don't need.

### 4. Distributed Systems & Consensus

**Core references:** Raft (etcd), CRDT literature, optimistic concurrency control.

mo:os uses **optimistic concurrency** via monotonic version counters on containers. MUTATE_KERNEL includes `expected_version: uint64`. If the version has advanced since the caller read it, the mutation is rejected and must be retried.

**Future**: Federated mo:os instances (multiple kernels sharing state) will require either:
- CRDTs for conflict-free convergence of container state across instances
- Raft consensus for linearizable morphism ordering
- Or a hybrid: CRDTs for container kernels (data), Raft for structural morphisms (ADD/LINK/UNLINK)

This is Phase 5+ and explicitly deferred. Single-instance mo:os is the target.

### 5. Formal Type Systems & Interface Verification

**Core references:** Bidirectional type checking; JSON Schema specification (draft 2020-12); Protocol Buffers type system.

Container interfaces are typed via JSON Schema on ports:
```
Port { name: "user_query", schema: { type: "string", maxLength: 4096 } }
```

When LINK connects `from_port` to `to_port`, the kernel verifies schema compatibility. This is a form of **structural subtyping**: the output schema must be assignable to the input schema. In practice, this is JSON Schema containment checking.

**Implementation**: Go's `santhosh-tekuri/jsonschema` for validation; custom containment checker for LINK-time type verification. At MVP, we validate that output and input schemas are identical. Subtyping (output schema is a subtype of input schema) is a Phase 2 refinement.

### 6. Agent Memory Architecture

**Core reference:** The "Open Brain" architecture pattern (Hatch, 2026); MCP (Model Context Protocol, Anthropic, 2024-2026).

mo:os subsumes the open brain concept: every piece of user memory is a data container in the graph, vector-embedded at write time, queryable via MCP by any connected model or agent. The difference: mo:os memory has recursive structure (containers within containers), typed interfaces (ports), permissions (ACL), and compositional algebra (morphism-based mutation). Flat vector stores give you semantic search. mo:os gives you semantic search + structural navigation + composable reasoning over memory.

---

## Language & Stack Decisions

### Go — The Kernel

| Component   | Library / Tool                             | Purpose                                              |
| ----------- | ------------------------------------------ | ---------------------------------------------------- |
| HTTP server | `net/http` + `chi` router                  | Admin API (:8000), health checks                     |
| WebSocket   | `nhooyr.io/websocket`                      | Gateway (:18789), JSON-RPC 2.0 bidirectional         |
| gRPC        | `google.golang.org/grpc` + `protoc`        | Internal IPC (:50051), tool execution (:50052)       |
| PostgreSQL  | `jackc/pgx/v5`                             | Connection pooling, JSONB operations, recursive CTEs |
| Redis       | `redis/go-redis/v9`                        | Active State Cache, event pubsub, session state      |
| JSON        | `encoding/json` + `goccy/go-json` (perf)   | Container serialization, morphism parsing            |
| JSON Schema | `santhosh-tekuri/jsonschema/v6`            | Port schema validation, interface compatibility      |
| Protobuf    | `google.golang.org/protobuf`               | Wire format for gRPC services                        |
| Testing     | `testing` + `testify`                      | Unit + integration                                   |
| Logging     | `log/slog` (stdlib structured logging)     | Structured, leveled, JSON output                     |
| Config      | `caarlos0/env/v11`                         | Env-var based configuration                          |
| Docker      | `Dockerfile` (multi-stage, `scratch` base) | Single static binary, minimal image                  |

**Go version**: 1.23+ (for `slog`, improved generics, `maps`/`slices` packages).

**Build**: `go build -o moos-kernel ./cmd/kernel` → single ~20MB binary. Docker image: ~25MB (scratch base).

### TypeScript/React — Browser Surfaces

| Component | Library                                   | Purpose                                 |
| --------- | ----------------------------------------- | --------------------------------------- |
| Framework | React 19                                  | Component rendering                     |
| Build     | Vite 7                                    | Dev server + production build           |
| Monorepo  | Nx 22                                     | Workspace management for ffs4/ffs5/ffs6 |
| Graph viz | XYFlow (React Flow)                       | Container graph visualization           |
| State     | Zustand                                   | Client-side container graph store       |
| WebSocket | Native WebSocket + custom JSON-RPC client | Real-time kernel communication          |
| Styling   | TailwindCSS 4                             | Utility-first styling                   |
| Types     | TypeScript 5.9                            | Strict mode, shared type definitions    |

**Surface architecture**: Surfaces contain **zero business logic**. They are functorial projections:
1. Receive container state via WebSocket
2. Map containers to React components (by `kind`)
3. Map morphisms to Zustand state updates
4. Send user input to kernel via WebSocket JSON-RPC

If the kernel changes a container's kernel, the surface re-renders. That's it.

### Protocol Buffers — Wire Format

```protobuf
syntax = "proto3";
package moos.v1;

message Container {
  string urn = 1;
  uint64 version = 2;
  Interface interface = 3;
  ContainerKind kind = 4;
  bytes kernel = 5;           // Opaque payload, interpreted by kind
  string parent_urn = 6;
  repeated string children = 7;
  repeated Wire wiring = 8;
  string owner_urn = 9;
  repeated ACLEntry acl = 10;
  map<string, string> tags = 11;
  google.protobuf.Timestamp created_at = 12;
  google.protobuf.Timestamp updated_at = 13;
}

message Port {
  string name = 1;
  bytes schema = 2;           // JSON Schema as bytes
}

message Interface {
  repeated Port inputs = 1;
  repeated Port outputs = 2;
}

message Wire {
  string from_urn = 1;
  string from_port = 2;
  string to_urn = 3;
  string to_port = 4;
}

enum ContainerKind {
  DATA = 0;
  EXECUTABLE = 1;
  COMPOSITE = 2;
  SURFACE = 3;
  IDENTITY = 4;
}

// The four syscalls
message AddContainer {
  string urn = 1;
  string parent_urn = 2;
  ContainerKind kind = 3;
  Interface interface = 4;
  bytes kernel = 5;
  map<string, string> tags = 6;
}

message Link {
  string from_urn = 1;
  string from_port = 2;
  string to_urn = 3;
  string to_port = 4;
}

message MutateKernel {
  string urn = 1;
  bytes patch = 2;             // JSON Patch (RFC 6902) or full replacement
  uint64 expected_version = 3;
}

message Unlink {
  string from_urn = 1;
  string from_port = 2;
  string to_urn = 3;
  string to_port = 4;
}

message Morphism {
  oneof operation {
    AddContainer add = 1;
    Link link = 2;
    MutateKernel mutate = 3;
    Unlink unlink = 4;
  }
}

message MorphismEnvelope {
  string id = 1;
  string source_urn = 2;
  string session_id = 3;
  uint32 turn = 4;
  google.protobuf.Timestamp timestamp = 5;
  repeated Morphism morphisms = 6;
  repeated string causality = 7;   // Parent envelope IDs
}
```

### PostgreSQL — Schema

```sql
-- Containers: the one table
CREATE TABLE containers (
  urn         TEXT PRIMARY KEY,
  version     BIGINT NOT NULL DEFAULT 1,
  kind        TEXT NOT NULL CHECK (kind IN ('data','executable','composite','surface','identity')),
  interface   JSONB NOT NULL DEFAULT '{"inputs":[],"outputs":[]}',
  kernel      JSONB,                          -- Polymorphic payload
  parent_urn  TEXT REFERENCES containers(urn),
  children    TEXT[] NOT NULL DEFAULT '{}',    -- Ordered child URNs
  owner_urn   TEXT NOT NULL,
  acl         JSONB NOT NULL DEFAULT '[]',
  tags        JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Wires: port-to-port edges (separate table for efficient graph queries)
CREATE TABLE wires (
  id          BIGSERIAL PRIMARY KEY,
  from_urn    TEXT NOT NULL REFERENCES containers(urn),
  from_port   TEXT NOT NULL,
  to_urn      TEXT NOT NULL REFERENCES containers(urn),
  to_port     TEXT NOT NULL,
  UNIQUE (from_urn, from_port, to_urn, to_port)
);

-- Morphism log: append-only audit trail
CREATE TABLE morphism_log (
  id            BIGSERIAL PRIMARY KEY,
  envelope_id   TEXT NOT NULL,
  source_urn    TEXT NOT NULL,
  session_id    TEXT NOT NULL,
  turn          INTEGER NOT NULL,
  morphisms     JSONB NOT NULL,
  causality     TEXT[] NOT NULL DEFAULT '{}',
  applied_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vector embeddings for semantic search over container kernels
CREATE TABLE embeddings (
  urn         TEXT PRIMARY KEY REFERENCES containers(urn),
  embedding   vector(1536),                   -- OpenAI ada-002 / Anthropic embed
  content     TEXT,                            -- Plaintext extracted from kernel
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_containers_parent ON containers(parent_urn);
CREATE INDEX idx_containers_kind ON containers(kind);
CREATE INDEX idx_containers_owner ON containers(owner_urn);
CREATE INDEX idx_containers_tags ON containers USING gin(tags);
CREATE INDEX idx_wires_from ON wires(from_urn);
CREATE INDEX idx_wires_to ON wires(to_urn);
CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw(embedding vector_cosine_ops);
CREATE INDEX idx_morphism_log_session ON morphism_log(session_id);
CREATE INDEX idx_morphism_log_envelope ON morphism_log(envelope_id);
```

### Docker — Deployment

```yaml
# docker-compose.yml
version: "3.9"
services:
  kernel:
    build: ./kernel
    ports:
      - "8000:8000"      # HTTP admin API
      - "18789:18789"    # WebSocket gateway
      - "50051:50051"    # gRPC
    environment:
      - DATABASE_URL=postgres://moos:moos@postgres:5432/moos?sslmode=disable
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: moos
      POSTGRES_USER: moos
      POSTGRES_PASSWORD: moos
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U moos"]
      interval: 5s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  tool-runtime:
    build: ./tool-runtime
    ports: ["50052:50052"]

  ffs4:
    build: ./surfaces/ffs4
    ports: ["4201:4201"]

  ffs6:
    build: ./surfaces/ffs6
    ports: ["4200:4200"]

volumes:
  pgdata:
```

**Single command**: `docker compose up -d` → full mo:os stack.

---

## Model Provider Integration

mo:os is provider-agnostic. Each provider is an executable container registered in the graph. The kernel's model dispatcher routes to the appropriate container based on session configuration.

### Supported Providers

| Provider             | SDK / Protocol                 | Default Model             | Integration                                   |
| -------------------- | ------------------------------ | ------------------------- | --------------------------------------------- |
| **Anthropic**        | `anthropic-go` (Go SDK)        | Claude Opus 4.6           | Native streaming, tool use, extended thinking |
| **Google Gemini**    | `google.golang.org/genai`      | Gemini 2.5 Flash          | Native streaming, function calling            |
| **Google Vertex AI** | `cloud.google.com/go/vertexai` | Claude on GCP (via ADK)   | Service account auth, regional endpoints      |
| **OpenAI**           | `sashabaranov/go-openai`       | GPT-5.x                   | Streaming, tool calls, structured output      |
| **Ollama**           | HTTP API (`localhost:11434`)   | Llama 3.x, Mistral, etc.  | Local inference, no API key needed            |
| **Google ADK**       | Agent Development Kit          | Multi-agent orchestration | ADK agents as executable containers           |

### The Provider Adapter Pattern

Each provider adapter implements one Go interface:

```go
type ModelAdapter interface {
    // Stream a completion from a prompt. Yields chunks.
    Complete(ctx context.Context, prompt *Prompt) (<-chan *Chunk, error)

    // Name returns the adapter identifier.
    Name() string
}

type Prompt struct {
    System   string
    Messages []*Message
    Tools    []*ToolSchema
    Config   *ModelConfig   // temperature, max_tokens, etc.
}

type Chunk struct {
    Text       string
    ToolCalls  []*ToolCall
    Morphisms  []*Morphism    // Parsed from structured output
    StopReason StopReason
    Usage      *Usage
}
```

**Switching providers** = MUTATE the model container's kernel to point at a different adapter. No code change. No restart.

---

## Tool Execution Architecture

Tools are executable containers. The kernel dispatches tool calls to a sandboxed runtime via gRPC.

### Tool Runtime (Go Sidecar)

```go
service ToolRuntime {
    rpc Execute(ToolRequest) returns (stream ToolResponse);
    rpc Register(ToolDefinition) returns (RegistrationResult);
    rpc List(Empty) returns (ToolList);
}
```

### Isolation Policies

| Policy             | Default                | Purpose                                                 |
| ------------------ | ---------------------- | ------------------------------------------------------- |
| `max_input_bytes`  | 16 KB                  | Prevent payload bombs                                   |
| `max_execution_ms` | 5000 ms                | Prevent runaway tools                                   |
| `blocked_prefixes` | `internal_`, `system_` | Protect system tools                                    |
| `sandbox_mode`     | `process`              | `process` (fork), `container` (Docker), `wasm` (future) |
| `network_access`   | `restricted`           | Tools can't call arbitrary URLs by default              |

### Tool Ecosystem

Tools can be written in any language. The tool runtime communicates via gRPC:

| Language            | Integration                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| **Go**              | Native — compile into tool-runtime binary                                      |
| **Python**          | Subprocess via `exec` or gRPC sidecar (UV-managed)                             |
| **TypeScript/Node** | gRPC sidecar or MCP-over-SSE bridge                                            |
| **Rust**            | Compiled into WASM, executed in WASM sandbox (future)                          |
| **MCP servers**     | Bridge via `mcp-to-grpc` adapter — any MCP tool becomes a mo:os tool container |

---

## Protocol Interfaces

### WebSocket Gateway (External — Surfaces, Extensions, CLI)

JSON-RPC 2.0 over WebSocket at `:18789`.

```
→ {"jsonrpc":"2.0","id":1,"method":"session.create","params":{"app_urn":"urn:moos:app:research-assistant"}}
← {"jsonrpc":"2.0","id":1,"result":{"session_id":"s_abc123","root_urn":"urn:moos:session:s_abc123"}}

→ {"jsonrpc":"2.0","id":2,"method":"session.send","params":{"session_id":"s_abc123","text":"Find papers on DAG reasoning"}}
← {"jsonrpc":"2.0","method":"stream.thinking","params":{"session_id":"s_abc123","text":"Searching..."}}
← {"jsonrpc":"2.0","method":"stream.morphism","params":{"session_id":"s_abc123","morphism":{"add":{"urn":"urn:moos:session:s_abc123:result:1",...}}}}
← {"jsonrpc":"2.0","method":"stream.text_delta","params":{"session_id":"s_abc123","text":"Found 3 relevant papers..."}}
← {"jsonrpc":"2.0","method":"stream.end","params":{"session_id":"s_abc123","stop_reason":"end_turn"}}
```

### gRPC (Internal — Tool Runtime, Future Federation)

Protobuf-defined services with bidirectional streaming. See protobuf schema above.

### MCP Server (External — Agent Interop)

mo:os exposes an MCP-compliant endpoint at `:8000/mcp/sse`:
- `tools/list` — Exposes all executable containers as MCP tools
- `tools/call` — Routes to kernel's tool executor
- `resources/list` — Exposes data containers as MCP resources
- `resources/read` — Returns container kernel content

This means any MCP client (Claude Desktop, Claude Code, Cursor, VS Code, etc.) can connect to a running mo:os instance and access its entire container graph as tools + resources.

### HTTP Admin API (External — Management)

REST at `:8000/api/v1/`:
- `POST /auth/login` — Token-based auth
- `GET /containers/{urn}` — Read container
- `POST /containers` — Create container (wraps ADD morphism)
- `GET /containers/{urn}/tree` — Recursive tree traversal
- `POST /morphisms` — Submit morphism envelope
- `GET /morphisms/log` — Query append-only audit trail
- `GET /search?q=...` — Semantic vector search over container kernels

---

## Directory Structure (Target)

```
moos/
├── cmd/
│   └── kernel/
│       └── main.go                 # Entry point
├── internal/
│   ├── container/
│   │   ├── store.go               # PostgreSQL container CRUD
│   │   ├── tree.go                # Recursive CTE traversal
│   │   ├── compose.go             # Sequential/parallel composition
│   │   └── validate.go            # Interface compatibility checking
│   ├── morphism/
│   │   ├── executor.go            # ADD/LINK/MUTATE/UNLINK execution
│   │   ├── validator.go           # Schema validation, version checking
│   │   └── log.go                 # Append-only morphism log
│   ├── session/
│   │   ├── manager.go             # Session lifecycle
│   │   ├── cache.go               # Active State Cache (Redis-backed)
│   │   └── fork.go                # Cache forking for multi-path DAG
│   ├── loop/
│   │   ├── loop.go                # Main event loop (goroutine per session)
│   │   ├── evaluator.go           # Decides which morphisms to fire
│   │   └── dispatcher.go          # Routes to model/tool/surface
│   ├── model/
│   │   ├── adapter.go             # ModelAdapter interface
│   │   ├── anthropic.go           # Claude adapter
│   │   ├── gemini.go              # Gemini adapter
│   │   ├── openai.go              # OpenAI adapter
│   │   ├── ollama.go              # Local model adapter
│   │   └── resolver.go            # Config-based provider selection
│   ├── tool/
│   │   ├── runner.go              # gRPC client to tool-runtime
│   │   ├── policy.go              # Isolation policy enforcement
│   │   └── mcp_bridge.go          # MCP tool → gRPC adapter
│   ├── gateway/
│   │   ├── websocket.go           # JSON-RPC 2.0 WebSocket server
│   │   ├── http.go                # Admin REST API
│   │   └── mcp.go                 # MCP SSE endpoint
│   ├── auth/
│   │   ├── token.go               # JWT/bearer token management
│   │   └── acl.go                 # Container ACL enforcement
│   └── embed/
│       └── embedder.go            # Vector embedding (OpenAI/Anthropic embed API)
├── proto/
│   └── moos/v1/
│       ├── container.proto
│       ├── morphism.proto
│       ├── session.proto
│       └── tool.proto
├── migrations/
│   ├── 001_containers.up.sql
│   ├── 001_containers.down.sql
│   ├── 002_wires.up.sql
│   ├── 003_morphism_log.up.sql
│   └── 004_embeddings.up.sql
├── tool-runtime/
│   ├── cmd/runtime/main.go
│   └── internal/
│       ├── registry.go
│       ├── sandbox.go
│       └── executor.go
├── surfaces/
│   ├── ffs4/                      # React sidepanel (existing, TypeScript)
│   ├── ffs5/                      # React PiP (stub)
│   └── ffs6/                      # React IDE viewer (existing, TypeScript)
├── extension/
│   ├── manifest.json              # Chrome MV3
│   ├── service_worker.js
│   └── sidepanel.html
├── docker-compose.yml
├── Dockerfile                     # Multi-stage Go build
├── Makefile
├── go.mod
└── go.sum
```

---

## Relevant Research & Prior Art

### Papers

| Paper                                                          | Relevance                                                                                                   |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Lawvere, *Functorial Semantics of Algebraic Theories* (1963)   | Foundation: syntax-semantics duality via functors. Container schema = syntax, kernel execution = semantics. |
| Fong & Spivak, *Seven Sketches in Compositionality* (2018)     | Applied category theory for engineering. Wiring diagrams, compositional design patterns.                    |
| *LogicGraph: Benchmarking Multi-Path Logical Reasoning* (2025) | DAG reasoning outperforms linear CoT. Validates multi-path cache forking design.                            |
| Anthropic, *Model Context Protocol Specification* (2024-2026)  | Transport standard for tool/resource access. mo:os implements MCP natively.                                 |
| Wei et al., *Chain-of-Thought Prompting* (2022)                | Baseline that mo:os explicitly extends/rejects (single-path → multi-path).                                  |
| Yao et al., *Tree of Thoughts* (2023)                          | Intermediate step: tree search over reasoning. mo:os generalizes to arbitrary DAGs.                         |
| CockroachDB, *Architecture of CockroachDB*                     | Distributed JSONB storage patterns. Raft consensus for future federation.                                   |

### Open-Source Systems

| System                     | Relation to mo:os                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Docker / containerd**    | Execution model inspiration: containers as isolated units of computation. Go kernel pattern.                                   |
| **Kubernetes**             | Declarative state reconciliation loop (desired state → actual state). mo:os main loop is similar but for AI reasoning state.   |
| **etcd**                   | Raft consensus, watch-based event system. Potential future dependency for federated mo:os.                                     |
| **OpenClaw** (Claude Code) | Agent runtime. mo:os provides the persistent state layer that agent runtimes lack.                                             |
| **LangGraph**              | Graph-based agent orchestration. mo:os subsumes: containers ARE the graph AND the agents AND the state.                        |
| **Supabase / pgvector**    | PostgreSQL + vector embeddings. mo:os uses the same stack but with structured container schema instead of flat rows.           |
| **MCP ecosystem**          | Transport layer. mo:os is an MCP server AND client — it exposes containers as tools/resources and consumes external MCP tools. |

---

## Contributing Areas

If you're looking to contribute, here's where different specializations apply:

| Specialty                  | Area                                                              | What to Work On                                                     |
| -------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Go systems programming** | `internal/loop/`, `internal/session/`                             | Main loop, cache forking, goroutine lifecycle                       |
| **Database / SQL**         | `internal/container/store.go`, `migrations/`                      | JSONB queries, recursive CTEs, schema evolution                     |
| **gRPC / distributed**     | `proto/`, `internal/tool/`, `internal/gateway/`                   | Service definitions, streaming, backpressure                        |
| **React / TypeScript**     | `surfaces/ffs4/`, `surfaces/ffs6/`                                | Graph visualization, real-time WebSocket rendering                  |
| **LLM integration**        | `internal/model/`                                                 | Provider adapters, structured output parsing, morphism extraction   |
| **Security / auth**        | `internal/auth/`                                                  | ACL enforcement, token management, permission traversal             |
| **Category theory**        | `internal/container/compose.go`, `internal/container/validate.go` | Composition algebra, interface compatibility, functorial properties |
| **DevOps / infra**         | `Dockerfile`, `docker-compose.yml`, `Makefile`                    | Build pipeline, health checks, monitoring                           |
| **Chrome extension**       | `extension/`                                                      | MV3 lifecycle, sidepanel management, surface registration           |
| **Vector search / ML**     | `internal/embed/`                                                 | Embedding strategies, semantic search tuning, hybrid retrieval      |

---

## Getting Started (After Phase 1)

```bash
# Clone
git clone https://github.com/collider/moos
cd moos

# Start infrastructure
docker compose up -d postgres redis

# Run migrations
go run ./cmd/migrate up

# Start kernel
go run ./cmd/kernel

# Start surfaces (separate terminal)
cd surfaces/ffs4 && pnpm dev

# Open Chrome, load extension from ./extension/
# Open sidepanel → connected to mo:os kernel
```

---

## License & Governance

Open-source. The `.agent` governance chain (manifest inheritance, workspace conventions) is the project's self-documenting configuration system — read `.agent/index.md` at each workspace level for context.

---

---

# PHASED IMPLEMENTATION STRATEGY

---

## Overview

6 phases, each with: scope, deliverables, quality gate, testing strategy, risks, contingency plan, estimated duration. No phase starts until the previous phase's quality gate passes.

**Total estimated timeline**: 16–22 weeks for Phases 0–4. Phase 5 is ongoing/open-ended.

**Principles**:
- Every phase produces a runnable artifact (even if limited)
- Tests are written WITH the code, not after
- Each phase has an explicit rollback strategy
- Dependencies are minimized between phases — each phase adds capability, doesn't break previous
- Feature flags gate new behavior until validated
- All phases maintain backward compatibility with existing TypeScript surfaces

---

## Phase 0 — Specification & Ontology Wiring

**Duration**: 1–2 weeks
**Goal**: Formalize all contracts before writing kernel code. Eliminate ambiguity.

### Deliverables

| #   | Deliverable                                                        | Output                                                                      |
| --- | ------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 0.1 | Wire `superset_ontology_v1.json` into `.agent/manifest.yaml` chain | Manifest includes at FFS0 level, exports to all children                    |
| 0.2 | Fix broken reference in `rules/versioning.md`                      | Either create `repo-split-superrepo.md` or remove dead reference            |
| 0.3 | Triage 7 orphaned knowledge files                                  | Decide: wire into manifest, archive, or delete each                         |
| 0.4 | Publish protobuf schemas (`proto/moos/v1/*.proto`)                 | `container.proto`, `morphism.proto`, `session.proto`, `tool.proto`          |
| 0.5 | Publish PostgreSQL migration scripts (`migrations/001-004`)        | 4 tables: containers, wires, morphism_log, embeddings                       |
| 0.6 | Publish JSON Schema for Container (for LLM structured output)      | JSON Schema draft 2020-12, validates container payload                      |
| 0.7 | Write ADR (Architecture Decision Records)                          | ADR-001: Go kernel, ADR-002: PostgreSQL over graph DB, ADR-003: 4 morphisms |
| 0.8 | Define MorphismEnvelope JSON format for WebSocket                  | JSON-RPC 2.0 method + params spec for all 4 morphisms                       |

### Testing Strategy

- **Schema validation tests**: Generate test containers from JSON Schema, validate against protobuf, confirm round-trip fidelity
- **Migration tests**: Apply migrations to a test PostgreSQL instance, verify table creation, indexes, constraints
- **Manifest audit**: Automated script that walks `.agent/manifest.yaml` chain and confirms all `includes` and `exports` resolve to existing files

### Quality Gate

- [ ] All `.agent` manifest paths resolve (zero broken references)
- [ ] Protobuf compiles with `protoc` without errors
- [ ] Migrations apply cleanly to fresh PostgreSQL 16
- [ ] JSON Schema validates 10+ sample containers without false positives
- [ ] ADRs reviewed and merged

### Risks & Contingencies

| Risk                                            | Probability | Impact | Contingency                                                                               |
| ----------------------------------------------- | ----------- | ------ | ----------------------------------------------------------------------------------------- |
| Schema design requires revision in later phases | HIGH        | LOW    | Schemas are versioned (`moos.v1`). Breaking changes get `v2` namespace.                   |
| Protobuf ↔ JSON Schema divergence               | MEDIUM      | MEDIUM | Generate JSON Schema FROM protobuf using `protoc-gen-jsonschema`. Single source of truth. |
| Team disagreement on morphism naming            | LOW         | LOW    | ADR-003 records the decision. Rename is a grep-and-replace.                               |

### Rollback

No code changes to runtime. If schemas are wrong, regenerate. No production risk.

---

## Phase 1 — Go Kernel Foundation

**Duration**: 3–4 weeks
**Goal**: Replace the TypeScript data-server with a Go kernel that persists containers in PostgreSQL and executes the 4 morphisms.

### Deliverables

| #   | Deliverable                  | Output                                                                       |
| --- | ---------------------------- | ---------------------------------------------------------------------------- |
| 1.1 | Go project scaffold          | `cmd/kernel/main.go`, `internal/` package structure, `go.mod`, `Makefile`    |
| 1.2 | Container store (PostgreSQL) | CRUD operations: Create, Read, Update, Delete, ListChildren, TreeTraversal   |
| 1.3 | Morphism executor            | `ADD_CONTAINER`, `LINK`, `MUTATE_KERNEL`, `UNLINK` — applied to PostgreSQL   |
| 1.4 | Morphism log (append-only)   | Every envelope written to `morphism_log` table                               |
| 1.5 | HTTP admin API               | REST endpoints matching current data-server interface (backward compatible)  |
| 1.6 | WebSocket gateway (basic)    | JSON-RPC 2.0 server at `:18789`, receives morphism envelopes, broadcasts     |
| 1.7 | Auth (basic)                 | Bearer token, user lookup, role-based access                                 |
| 1.8 | Seed data migration          | SQL seed script replacing in-memory JS seed (App 2XZ, users, root node)      |
| 1.9 | Docker setup                 | `Dockerfile` (multi-stage, scratch base), `docker-compose.yml` with postgres |

### Testing Strategy

**Unit tests** (`go test ./internal/...`):
- Container store: CRUD operations, tree traversal, concurrent access
- Morphism executor: Each morphism type independently. Edge cases: duplicate URN, missing parent, version conflict, broken interface
- Auth: Token validation, role hierarchy, ACL enforcement

**Integration tests** (`go test -tags=integration ./...`):
- Full morphism cycle: ADD → LINK → MUTATE → UNLINK → verify PostgreSQL state
- WebSocket round-trip: Connect, send envelope, receive broadcast
- API compatibility: Run existing FFS4 test suite against Go kernel endpoints (drop-in replacement test)

**Benchmark tests** (`go test -bench=. ./...`):
- Container creation throughput: target 1000 containers/sec
- Tree traversal latency: target <50ms for 1000-node tree
- Morphism execution latency: target <10ms per morphism

**Test infrastructure**:
- PostgreSQL test container via `testcontainers-go`
- Parallel test execution with isolated databases
- Golden file tests for API response shapes

### Quality Gate

- [ ] 90%+ code coverage on `internal/container/` and `internal/morphism/`
- [ ] All integration tests pass
- [ ] FFS4 React app connects to Go kernel and renders graph (drop-in replacement)
- [ ] FFS6 IDE viewer connects and displays tree (drop-in replacement)
- [ ] No regression: existing Chrome extension sidepanel works unchanged
- [ ] Container creation benchmark: ≥500 containers/sec
- [ ] Docker image builds and starts in <5 seconds
- [ ] `go vet`, `staticcheck`, `golangci-lint` pass with zero warnings

### Risks & Contingencies

| Risk                                                         | Probability | Impact | Contingency                                                                                                                                                                |
| ------------------------------------------------------------ | ----------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API shape mismatch breaks existing frontends                 | MEDIUM      | HIGH   | **Compatibility shim**: Go kernel serves both old REST format AND new format behind content negotiation. Feature flag `COMPAT_MODE=true` (default) maps old shapes to new. |
| PostgreSQL performance worse than in-memory for dev workflow | LOW         | MEDIUM | Connection pool tuning (pgx defaults are conservative). If still slow: SQLite mode for local dev with `--dev` flag.                                                        |
| JSONB query complexity for deep trees                        | MEDIUM      | MEDIUM | Pre-compute `path` column (materialized path pattern) for O(1) subtree queries. Add in Phase 1.5 if needed.                                                                |
| Go ecosystem unfamiliarity for team                          | MEDIUM      | MEDIUM | Pair programming first 2 weeks. Go's stdlib is sufficient for 80% of needs — minimize third-party deps.                                                                    |

### Rollback

TypeScript data-server remains in the repository. `docker-compose.yml` has profiles: `--profile=go` starts Go kernel, `--profile=ts` starts TypeScript stack. Switch back with one flag.

---

## Phase 2 — Persistent Main Loop

**Duration**: 3–4 weeks
**Goal**: Replace the one-shot engine with a persistent, event-driven main loop running as a goroutine per session.

### Deliverables

| #    | Deliverable             | Output                                                                          |
| ---- | ----------------------- | ------------------------------------------------------------------------------- |
| 2.1  | Session manager         | Create/destroy/list sessions. Redis-backed session state.                       |
| 2.2  | Active State Cache      | In-memory container graph per session, loaded from PostgreSQL on session create |
| 2.3  | Event loop              | Goroutine per session: wait for event → evaluate → dispatch → apply → broadcast |
| 2.4  | Model dispatcher        | Route to provider adapter based on session/container config                     |
| 2.5  | Anthropic adapter       | Claude Opus 4.6 via `anthropic-go` SDK. Streaming completion.                   |
| 2.6  | Gemini adapter          | Gemini 2.5 Flash via Google GenAI Go SDK. Streaming completion.                 |
| 2.7  | Morphism parser         | Extract morphisms from model structured output (JSON in markdown fences)        |
| 2.8  | Tool dispatch stub      | Forward tool_calls to gRPC tool runtime (Phase 3 builds the runtime)            |
| 2.9  | Cache → Store commit    | On end_turn, compute delta between cache and store, apply to PostgreSQL         |
| 2.10 | Session timeout/cleanup | Configurable TTL, garbage collection of expired sessions                        |

### Testing Strategy

**Unit tests**:
- Session lifecycle: create → send message → receive events → close → verify cleanup
- Cache operations: load from store, apply morphism, compute delta, commit
- Model adapter: mock HTTP responses, verify prompt construction, verify morphism extraction
- Event loop: state machine tests — each event type produces expected side effects

**Integration tests**:
- Full conversation: create session → send user message → model responds → morphisms applied → cache committed → verified in PostgreSQL
- Multi-session concurrency: 10 simultaneous sessions, verify isolation (no state leakage between sessions)
- Provider failover: Primary provider timeout → verify graceful error, session survives

**Load tests** (`k6` or `vegeta`):
- 100 concurrent sessions, 5 messages each
- Target: <500ms p99 latency per message (excluding model API time)
- Target: <100MB memory per 100 sessions

**Chaos tests**:
- Kill Redis mid-session → verify session recovers from PostgreSQL
- Model API returns 500 → verify retry with exponential backoff, session error state
- PostgreSQL commit fails → verify cache rolls back, user notified

### Quality Gate

- [ ] End-to-end conversation works: user message → model response → morphisms applied → graph updated in FFS4
- [ ] 50 concurrent sessions without memory leak (measure with `runtime.MemStats`)
- [ ] Session survives Redis restart (reload from PostgreSQL)
- [ ] Model response latency overhead <50ms (excluding provider API time)
- [ ] Graceful degradation: model timeout returns user-friendly error, session remains usable
- [ ] Zero goroutine leaks (verified with `goleak` in tests)

### Risks & Contingencies

| Risk                                             | Probability | Impact | Contingency                                                                                                                                                                                                    |
| ------------------------------------------------ | ----------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Provider SDK Go bindings are immature/buggy      | MEDIUM      | HIGH   | **HTTP fallback**: All providers have REST APIs. Write raw HTTP adapter as fallback. Provider SDKs are convenience, not dependency.                                                                            |
| Cache-store consistency bugs                     | HIGH        | HIGH   | **Write-ahead log**: Before applying to cache, write morphism envelope to Redis stream. On crash, replay from stream. Eventual consistency guaranteed by morphism log in PostgreSQL.                           |
| Goroutine leak under error conditions            | MEDIUM      | HIGH   | **Context cancellation**: Every goroutine receives `context.Context` with timeout. `goleak` test package in ALL test files. CI fails on leak.                                                                  |
| Morphism extraction from model output unreliable | HIGH        | MEDIUM | **Structured output**: Use provider-specific structured output modes (Anthropic tool_use, Gemini function_calling, OpenAI function_call). If model returns free-text, fall back to JSON extraction with retry. |
| Redis adds operational complexity                | LOW         | LOW    | **In-process fallback**: `--cache=memory` flag uses Go `sync.Map` instead of Redis. Loses persistence on kernel restart but simplifies dev setup.                                                              |

### Rollback

Phase 1 kernel remains functional without the loop. Sessions are additive — if the loop breaks, the kernel still serves containers via REST/WebSocket. Feature flag `ENABLE_LOOP=false` disables session management.

---

## Phase 3 — Tool Runtime & Surface Integration

**Duration**: 3–4 weeks
**Goal**: Replace the TypeScript tool-server with a gRPC tool runtime. Connect surfaces as first-class graph objects.

### Deliverables

| #    | Deliverable                       | Output                                                                                    |
| ---- | --------------------------------- | ----------------------------------------------------------------------------------------- |
| 3.1  | gRPC tool runtime service         | `tool-runtime/` binary, `ToolRuntime.Execute` streaming RPC                               |
| 3.2  | Tool registry (PostgreSQL-backed) | Executable containers in graph, discovered by kernel                                      |
| 3.3  | Isolation sandbox                 | Process-level isolation, input size limits, execution timeout, network restrictions       |
| 3.4  | MCP bridge                        | Adapter: external MCP tools → mo:os tool containers. `mcp-to-grpc` shim.                  |
| 3.5  | Built-in tools                    | `echo`, `search` (semantic vector search over containers), `list_children`, `read_kernel` |
| 3.6  | Surface container registration    | FFS4/FFS5/FFS6 register as surface containers on WebSocket connect                        |
| 3.7  | SYNC_ACTIVE_STATE projection      | When cache mutates, push delta to all subscribed surface containers                       |
| 3.8  | FFS4 WebSocket client update      | Replace REST polling with WebSocket subscription + morphism-driven state                  |
| 3.9  | FFS6 WebSocket client update      | Same: replace REST with WebSocket                                                         |
| 3.10 | MCP server endpoint               | `:8000/mcp/sse` exposing containers as tools + resources                                  |

### Testing Strategy

**Unit tests**:
- Tool execution: each built-in tool with valid/invalid input
- Isolation: blocked prefixes, size limits, timeout enforcement
- MCP bridge: mock MCP server, verify tool discovery and invocation
- Surface registration: connect/disconnect lifecycle, subscription management

**Integration tests**:
- Full tool cycle: model requests tool → kernel dispatches to runtime → runtime executes → result returned to model → next turn
- MCP interop: Connect Claude Desktop to mo:os MCP endpoint, call tool, verify response
- Surface sync: Mutate container via API → verify FFS4 WebSocket receives update within 100ms

**Contract tests**:
- gRPC: `buf` lint + breaking change detection on `.proto` files
- WebSocket: JSON Schema validation on every message type
- REST API: OpenAPI spec generated from Go handlers, validated against

**Security tests**:
- Tool escaping: Attempt command injection via tool input → verify blocked
- Size bomb: Send 100MB tool input → verify rejected at policy layer
- Unauthorized tool access: Request execution of blocked tool → verify denied

### Quality Gate

- [ ] Model can call tool → receive result → continue conversation
- [x] MCP endpoint passes `mcp-inspector` validation (against :8080 kernel surface)
- [ ] FFS4 renders real-time updates via WebSocket (no polling)
- [ ] FFS6 renders real-time updates via WebSocket (no polling)
- [ ] Tool execution latency overhead <20ms (excluding tool logic)
- [ ] Surface sync latency <100ms from morphism application to UI update
- [ ] Zero security findings in tool sandbox tests

### Risks & Contingencies

| Risk                                                                   | Probability | Impact | Contingency                                                                                                                                            |
| ---------------------------------------------------------------------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| gRPC complexity slows frontend integration                             | MEDIUM      | MEDIUM | **gRPC-Web proxy**: Use `grpcwebproxy` or Envoy for browser-compatible gRPC. Or: keep WebSocket for surfaces (simpler), use gRPC only kernel-internal. |
| MCP spec changes (still evolving)                                      | MEDIUM      | LOW    | MCP adapter is isolated in `internal/tool/mcp_bridge.go`. Spec change = update one file.                                                               |
| Surface sync creates WebSocket storm under heavy load                  | LOW         | MEDIUM | **Batching**: Aggregate morphisms into 100ms windows, send batch update. **Throttling**: Per-surface rate limit (max 10 updates/sec).                  |
| Existing FFS4/FFS6 code requires significant refactoring for WebSocket | MEDIUM      | MEDIUM | **Dual mode**: Keep REST endpoints active (Phase 1). Add WebSocket subscription as opt-in. Remove REST in Phase 4 after validation.                    |

### Rollback

Tool-server TypeScript binary remains available. Feature flag `TOOL_RUNTIME=grpc|http` selects runtime. Surface WebSocket is additive — REST endpoints are not removed until Phase 4.

---

## Phase 4 — Dockerize & Production Readiness

**Duration**: 2–3 weeks
**Goal**: Single `docker compose up` for full stack. Production-grade observability, security, and documentation.

### Deliverables

| #    | Deliverable                            | Output                                                                                    |
| ---- | -------------------------------------- | ----------------------------------------------------------------------------------------- |
| 4.1  | Multi-stage Dockerfile                 | Go binary: <25MB image (scratch base). Tool runtime: separate image.                      |
| 4.2  | `docker-compose.yml` (production)      | kernel + postgres + redis + tool-runtime + ffs4 + ffs6                                    |
| 4.3  | `docker-compose.dev.yml` (development) | Hot-reload for Go (air), Vite dev servers for surfaces                                    |
| 4.4  | Health checks                          | `/health` endpoint on every service, Docker health checks, readiness probes               |
| 4.5  | Structured logging                     | `slog` JSON output, request tracing with `trace_id`, log levels                           |
| 4.6  | Metrics                                | Prometheus metrics: session count, morphism rate, model latency, tool latency, cache size |
| 4.7  | Database migrations CLI                | `go run ./cmd/migrate up                                                                  | down | status` — versioned, idempotent |
| 4.8  | Seed data command                      | `go run ./cmd/seed` — creates App 2XZ, users, root container                              |
| 4.9  | Configuration validation               | Startup fails fast with clear error if required env vars missing                          |
| 4.10 | Security hardening                     | Rate limiting, input validation, SQL injection prevention (parameterized queries), CORS   |
| 4.11 | Remove TypeScript stack                | Delete data-server, tool-server, engine TypeScript apps (keep surfaces)                   |
| 4.12 | README & getting-started docs          | Developer quickstart, architecture overview, API reference                                |

### Testing Strategy

**End-to-end tests**:
- `docker compose up` → wait for health → run full test suite → `docker compose down`
- Fresh database → seed → create session → full conversation → verify persistence → restart kernel → verify state recovered

**Smoke tests** (CI pipeline):
- Build all images
- Start compose stack
- Hit `/health` on all services
- Create container via API
- Send message via WebSocket
- Verify response
- Tear down

**Performance baseline**:
- 100 concurrent sessions, 10 messages each
- Measure: p50/p95/p99 latency, memory usage, CPU usage
- Record as baseline for future regression detection

**Disaster recovery tests**:
- Kill kernel → restart → verify all sessions recover
- Kill postgres → restart → verify data intact
- Kill redis → restart → verify sessions reload from postgres
- Corrupt morphism log → verify kernel detects and reports (but doesn't crash)

### Quality Gate

- [ ] `docker compose up` from clean state works in <60 seconds
- [ ] Full conversation works end-to-end in Docker
- [ ] Restart kernel: zero data loss
- [ ] Prometheus metrics scraping works
- [ ] JSON logs parseable by standard log aggregators
- [ ] No TypeScript runtime services remain (only surfaces)
- [ ] README enables new developer to get running in <15 minutes
- [ ] `golangci-lint`, `buf lint`, `eslint` all pass in CI
- [ ] Docker image CVE scan: zero critical/high vulnerabilities

### Risks & Contingencies

| Risk                                                                  | Probability | Impact | Contingency                                                                                                                               |
| --------------------------------------------------------------------- | ----------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Docker Compose networking issues across platforms (Windows/Mac/Linux) | MEDIUM      | MEDIUM | Test on all 3 platforms in CI. Provide `--network=host` fallback for local dev. Document platform-specific gotchas.                       |
| Removing TypeScript stack reveals hidden dependencies                 | LOW         | HIGH   | Phase 4.11 is last step. Run full test suite BEFORE deletion. Git branch: `pre-ts-removal` tagged for emergency rollback.                 |
| Performance regression under Docker overhead                          | LOW         | LOW    | Benchmark Phase 4 against Phase 2 bare-metal. Docker overhead should be <5%. If higher: tune cgroup limits, verify no unnecessary layers. |

### Rollback

Git tag `v0.4.0-pre-ts-removal` preserves the dual-stack state. `docker-compose.ts.yml` profile remains in repo for 30 days post-removal as escape hatch.

---

## Phase 5 — Advanced Capabilities

**Duration**: Ongoing (modular, each sub-feature is 2–4 weeks)
**Goal**: Features that differentiate mo:os from everything else. Each is independently deliverable.

### 5.1 Multi-Path DAG Reasoning

**Deliverables**:
- Forkable Active State Cache (copy-on-write HAMT or immutable tree)
- `session.fork` / `session.merge` / `session.discard` WebSocket methods
- Branch scoring (model-evaluated, heuristic, or user-selected)
- XYFlow branch visualization in FFS4 (parallel DAG paths rendered as lanes)

**Testing**:
- Fork cache → apply different morphisms to each branch → merge → verify correct state
- Concurrent branch evaluation (goroutine per branch) → verify no races (`-race` flag)
- 10 branches, 100 containers each → memory benchmark

**Contingency**: If HAMT implementation is complex, start with full-copy forking (expensive but correct). Optimize to COW in 5.1.1.

### 5.2 Federation (Multi-Instance mo:os)

**Deliverables**:
- gRPC federation protocol: one kernel discovers and syncs with others
- Container replication: `urn:moos:remote:{instance}:{path}` addressing
- Conflict resolution: CRDTs for data containers, Raft for structural morphisms

**Testing**:
- 2-instance cluster: create container on A → appears on B within 1 second
- Network partition: split A/B → both accept writes → rejoin → verify convergence

**Contingency**: This is research-grade. If CRDTs prove too complex, start with read-replica federation (one writer, N readers).

### 5.3 WebRTC Peer Surfaces

**Deliverables**:
- Surface-to-surface direct connection (bypassing kernel for UI sync)
- Collaborative editing: multiple users viewing/editing same container graph
- Signaling via kernel WebSocket, data via WebRTC DataChannel

**Testing**:
- 2 browsers, same session: user A mutates → user B sees update <200ms
- Network quality degradation: simulate packet loss → verify graceful degradation

**Contingency**: If WebRTC complexity is too high for surfaces, use kernel-relayed WebSocket (higher latency but simpler).

### 5.4 WASM Tool Sandbox

**Deliverables**:
- Tools compiled to WASM, executed in sandboxed WASM runtime (wazero in Go)
- Language-agnostic: Rust, AssemblyScript, C/C++ tools compile to WASM
- Memory/CPU limits enforced at WASM level

**Testing**:
- Rust tool → WASM → execute in sandbox → verify output
- Malicious WASM (infinite loop) → verify timeout
- Memory bomb WASM → verify limit enforcement

**Contingency**: If wazero has limitations, fall back to process-level sandbox with seccomp profiles.

### 5.5 Vector Search & Semantic Memory

**Deliverables**:
- Automatic embedding on container kernel write (via OpenAI/Anthropic embed API)
- `search` tool: semantic search across all accessible containers
- Hybrid retrieval: vector similarity + structural graph traversal
- MCP resource: expose semantic search as MCP resource for external agents

**Testing**:
- Create 1000 data containers with varied content → search → verify relevance ranking
- Permission-scoped search: user A's search doesn't return user B's containers
- Embedding pipeline latency: <500ms per container write

**Contingency**: If real-time embedding is too slow, batch embed every 60 seconds. Stale-but-available beats slow-but-fresh.

---

## Cross-Phase Practices

### CI/CD Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Lint        │ →  │   Test        │ →  │   Build       │ →  │   Deploy      │
│ golangci-lint │    │ go test       │    │ docker build  │    │ docker push   │
│ buf lint      │    │ -race -cover  │    │ multi-stage   │    │ compose up    │
│ eslint        │    │ integration   │    │ scratch base  │    │ smoke test    │
│ tsc --noEmit  │    │ e2e           │    │ CVE scan      │    │               │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**CI runs on**: Every PR, every push to main. Nightly: full integration + load tests.

### Branching Strategy

- `main` — always deployable, protected
- `phase/{N}/{feature}` — feature branches per phase deliverable
- `release/v{X}.{Y}` — release candidates
- Squash merge to main. No direct commits.

### Documentation

- **ADRs** (Architecture Decision Records): One per major decision. Stored in `docs/adr/`.
- **API docs**: Auto-generated from protobuf (buf) and Go handlers (swag).
- **Runbooks**: `docs/runbooks/` — operational procedures (restart, migrate, debug).
- **.agent chain**: Kept in sync — every Phase 0+ change updates relevant `.agent/manifest.yaml`.

### Dependency Management

- **Go**: `go mod tidy` enforced in CI. Dependabot for security patches.
- **TypeScript**: `pnpm` lockfile. Renovate for dependency updates.
- **Docker**: Pin image tags (e.g., `pgvector/pgvector:pg16-v0.7.0`, not `latest`).
- **Protobuf**: `buf.lock` for schema registry. Breaking change detection in CI.

### Monitoring & Alerting (Phase 4+)

| Metric                                 | Target                  | Alert Threshold           |
| -------------------------------------- | ----------------------- | ------------------------- |
| Morphism execution latency (p99)       | <50ms                   | >200ms for 5 minutes      |
| Active sessions                        | <1000 (single instance) | >800 (scale warning)      |
| PostgreSQL connection pool utilization | <70%                    | >90% for 2 minutes        |
| Redis memory usage                     | <256MB                  | >200MB                    |
| Goroutine count                        | <5000                   | >10000 (likely leak)      |
| Model API error rate                   | <1%                     | >5% for 5 minutes         |
| WebSocket connection count             | <5000                   | >4000 (approaching limit) |

---

## Phase Dependency Graph

```
Phase 0 (Specification)
    │
    ▼
Phase 1 (Go Kernel Foundation) ← Can start immediately after Phase 0 QG passes
    │
    ├─► Phase 2 (Main Loop) ← Requires Phase 1 container store + WebSocket
    │       │
    │       ├─► Phase 3 (Tools + Surfaces) ← Requires Phase 2 session/loop
    │       │       │
    │       │       └─► Phase 4 (Dockerize) ← Requires Phase 3 for full stack
    │       │               │
    │       │               └─► Phase 5.x (Advanced) ← All independent, require Phase 4
    │       │
    │       └─► Phase 5.5 (Vector Search) ← Can start after Phase 2 (needs container store)
    │
    └─► Phase 5.4 (WASM Sandbox) ← Can start after Phase 1 (needs tool interface definition)
```

**Parallelizable work**:
- Phase 5.4 (WASM sandbox) can begin during Phase 2 (only needs tool interface from Phase 1)
- Phase 5.5 (vector search) can begin during Phase 3 (only needs container store from Phase 1)
- Surface TypeScript work (3.8, 3.9) can begin during Phase 2 once WebSocket contract is defined

---

---

# INVESTOR PITCH (Separate Section)

---

## The One-Liner

**mo:os is an open-source operating system for AI-human computation — where every user, tool, model, application, and interaction is the same recursive data structure, persisted in a graph database that any AI agent can read, write, and reason over.**

---

## The Problem

### 1. AI memory is siloed and proprietary

Claude has memory. ChatGPT has memory. Gemini has memory. None of them talk to each other. Every platform has built a walled garden: your context is trapped inside their product, their retention funnel, their pricing tier. Switch tools and you start from zero. The "open brain" concept has proven this demand exists — people want agent-readable, cross-platform, self-owned memory infrastructure.

### 2. Agent frameworks have no operating system

LangChain, CrewAI, AutoGen, OpenClaw — they orchestrate model calls but share no persistent state, no typed mutation protocol, no compositional structure. Every agent session starts from nothing. Every tool integration is bespoke glue code. There is no kernel managing concurrent agent processes, no filesystem where reasoning is persisted, no permission system governing who sees what. These are scripting languages without an OS underneath.

### 3. The "skill" interface is broken

Providers treat tools as discrete Python functions appended to prompts. This creates an interface collision: every provider's tool format is different, every multi-agent framework defines its own calling convention, and none of them compose. MCP (Model Context Protocol) standardized *transport* but not *semantics*. The industry has USB-C but no filesystem.

### 4. Single-path reasoning is a dead end

Chain-of-Thought forces AI into linear single-path thinking. Research (LogicGraph, 2025) demonstrates that multi-path DAG reasoning — where the model explores parallel branches and collapses to the best — dramatically outperforms sequential chains. But no runtime exists that natively supports forking, branching, and committing reasoning paths as structured graph state.

---

## The Vision

mo:os is an operating system, not a framework. It runs like an OS:

| Traditional OS | mo:os                                                                                          |
| -------------- | ---------------------------------------------------------------------------------------------- |
| Kernel         | Go binary — manages the main loop, dispatches morphisms, enforces permissions                  |
| Process        | Container execution — a model call, a tool run, a surface render                               |
| Filesystem     | PostgreSQL + pgvector — persistent, versioned graph of all containers                          |
| RAM            | Active State Cache — in-memory container graph per session, forkable for multi-path evaluation |
| Syscalls       | 4 graph morphisms: ADD, LINK, MUTATE, UNLINK — the only mutations the system understands       |
| IPC            | gRPC (internal), WebSocket JSON-RPC (surfaces), MCP (external agents)                          |
| Shell          | Runtime Surfaces — Chrome sidepanel, browser tabs, PiP windows, CLI, any MCP client            |
| Users          | Identity containers with permission-bounded graph traversal                                    |

**The foundational axiom: Everything is a Container.**

A user is a container. A tool is a container. A workflow is a container of containers. An AI model is a container. An application is a tree of containers. The OS itself is the root container. There is one data structure, one schema, one persistence layer. Content is context is the application.

---

## The Core Innovation: The Recursive Container Model

### One Universal Primitive

```
Container {
  urn         — globally unique identity (urn:moos:{scope}:{path})
  interface   — typed input/output ports (what it accepts, what it produces)
  kind        — data | executable | composite | surface | identity
  kernel      — the actual content/state/logic (JSONB, interpreted by kind)
  children    — ordered list of sub-containers (recursive)
  wiring      — directed connections between ports (dataflow graph)
  permissions — ACL with read/write/execute/admin/traverse operations
  version     — monotonic counter for optimistic concurrency
}
```

This single schema replaces every ad-hoc abstraction in the AI tooling ecosystem:

| Industry Concept            | mo:os: It's a Container                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------ |
| "Tool" / "Function"         | Container with executable kernel and typed I/O ports                                       |
| "Workflow" / "Pipeline"     | Composite container — children are tools, wiring defines dataflow                          |
| "Knowledge base" / "Memory" | Data container with vector-indexed kernel, searchable via output ports                     |
| "Prompt template"           | Data container whose output feeds prompt composition                                       |
| "Application"               | Tree of containers (an AppTemplate is read-only; an AppInstance is a user's hydrated copy) |
| "Agent"                     | Composite container wiring model + tools + knowledge into a loop                           |
| "User profile"              | Identity container owning a permission-bounded sub-graph                                   |
| "Chat session"              | Active State Cache snapshot — a mutable fork of the container graph                        |
| "UI component"              | Surface container projecting other containers into a browser context                       |

### Four Syscalls

The entire system mutates through exactly four operations:

1. **ADD** — insert a new container into the graph
2. **LINK** — connect two ports (create dataflow edge)
3. **MUTATE** — patch a container's kernel (with optimistic concurrency)
4. **UNLINK** — disconnect two ports

LLMs don't "call tools." LLMs output a JSON array of these morphisms. The kernel validates them against container interfaces (type-checks the ports), applies them to the active state, and broadcasts changes to all subscribed surfaces. This is category theory applied to AI: the model operates on graph structure using typed, composable, verifiable operations.

### Why Category Theory Matters Here

Category theory provides three guarantees conventional AI frameworks lack:

1. **Composability** — Containers compose sequentially (chain outputs → inputs) and in parallel (run side-by-side). The algebra guarantees that composed containers have valid interfaces. You can build complex workflows from simple containers and know they'll type-check.

2. **Functorial projection** — The UI is a functor: it maps containers (objects) and morphisms (mutations) from the graph category to the React category, preserving structure. The frontend contains zero business logic. It reads JSONB and renders components. Change the graph, the UI updates. Automatically.

3. **Provider agnosticism** — The LLM is an object in the graph, not a privileged caller. Pre-flight configuration (model selection, parameter tuning, context composition) is itself a morphism. Swapping Anthropic for Gemini or a local Ollama instance is a MUTATE on the model container's kernel. No code change. No migration.

---

## Architecture

### The Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Chrome Extension (MV3)                                      │
│  ├── Sidepanel → FFS4 (React + XYFlow graph visualization)  │
│  ├── Tab → FFS6 (IDE viewer, admin dashboard)               │
│  └── PiP → FFS5 (floating overlay, future)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket JSON-RPC
┌───────────────────────────▼─────────────────────────────────┐
│  mo:os Kernel (Go, single binary)                            │
│  ├── Main Loop (goroutine per session, event-driven)         │
│  ├── Morphism Executor (ADD/LINK/MUTATE/UNLINK)             │
│  ├── Model Dispatcher (Anthropic, Gemini, OpenAI, Ollama)   │
│  ├── Tool Runtime (gRPC to sandboxed executors)             │
│  ├── WebSocket Gateway (:18789)                              │
│  ├── HTTP Admin API (:8000)                                  │
│  ├── gRPC Internal (:50051)                                  │
│  └── MCP Server (SSE, for external agent access)            │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL 16 + pgvector                                    │
│  ├── Container store (JSONB — one table, one schema)        │
│  ├── Morphism log (append-only, immutable history)          │
│  └── Vector embeddings (semantic search, MCP-queryable)     │
├─────────────────────────────────────────────────────────────┤
│  Redis                                                       │
│  ├── Active State Cache (per-session, forkable)             │
│  └── Event queue (morphism dispatch)                        │
└─────────────────────────────────────────────────────────────┘
```

### Why Go

The kernel is a long-running daemon managing concurrent AI sessions. It needs:
- **Goroutines** for per-session main loops (thousands of concurrent sessions, not single-threaded event loop)
- **Channels** for internal IPC (zero-copy morphism dispatch)
- **Single binary** deployment (no node_modules, no runtime, `docker build` → done)
- **Native gRPC/protobuf** (first-class, not bolted-on)
- Battle-tested for exactly this class of system (Docker, Kubernetes, etcd, CockroachDB are all Go)

Browser surfaces stay TypeScript/React — the right tool for UI projection.

### Multi-Path DAG Reasoning

When a model produces morphisms, the kernel can fork the Active State Cache into parallel branches:

```
User asks: "Design a deployment strategy"
                    │
              ┌─────┴─────┐
              ▼           ▼
        Branch A      Branch B
     (Kubernetes)   (Serverless)
          │               │
     ADD containers  ADD containers
     LINK edges      LINK edges
          │               │
     Score: 0.82     Score: 0.91
              │           │
              └─────┬─────┘
                    ▼
            Commit Branch B
            to Resting State
```

The user sees this branching in real-time via XYFlow in the Chrome sidepanel. This is not chain-of-thought. This is structured, visual, explorable multi-path reasoning persisted as graph state.

---

## The User Experience

### For End Users (AppUsers)

1. Install Chrome extension. Open sidepanel.
2. Your mo:os root container loads — your "desktop." It shows your apps, your memory, your active sessions.
3. Select an app (e.g., "Research Assistant"). It's an AppTemplate hydrated into your personal container graph.
4. Chat with the agent. It sees your full context — not because the model has memory, but because your container graph IS the context. Switch to Gemini mid-conversation. Same graph. Same context. Different model.
5. The agent's reasoning appears as a live DAG in the graph view. You can see it branch, evaluate, and commit. You can fork a branch yourself, edit it, merge it back.
6. Everything persists. Close the browser. Come back next week. The graph is exactly where you left it.

### For App Builders (AppAdmins)

1. Open the IDE viewer (FFS6). Create an AppTemplate — a tree of containers.
2. Wire containers together: knowledge → prompt composition → model → tool → output.
3. Publish the template. Users can hydrate it into their personal graph.
4. Every tool, every workflow, every piece of knowledge is a container. The same schema. The same editor. The same persistence.

### For Infrastructure Engineers (SuperAdmins)

1. `docker compose up` — kernel, postgres, redis, tool-runtime, surfaces.
2. Single Go binary. Single JSONB table. Single morphism log.
3. Add model providers by registering container nodes. Add tools by registering executable containers.
4. Monitor via admin API. Every mutation is logged. Every state transition is auditable.

---

## Why Now

1. **MCP went mainstream** (Q1 2026) — Every major AI provider speaks the protocol. mo:os is the first OS built on it natively, not as a bolt-on.

2. **Agents crossed the threshold** — OpenClaw passed 190K GitHub stars. Anthropic, Google, OpenAI all shipping agent products. But none of them have persistent, user-owned state infrastructure. They're all building agents without an OS.

3. **The memory problem is proven** — The "open brain" movement demonstrated massive demand for self-owned, agent-readable memory. mo:os is the operating system that gives that memory structure, composability, and multi-agent access.

4. **Multi-path reasoning is validated** — LogicGraph benchmarks show DAG reasoning outperforms linear CoT. mo:os is the first runtime that natively supports it with forkable state and visual exploration.

5. **Provider lock-in backlash is growing** — Users are frustrated that Claude's memory doesn't work in ChatGPT, that ChatGPT's memory doesn't work in Cursor. mo:os makes your context portable by design — one graph, any model, any surface.

---

## Competitive Landscape

| Category             | Examples                     | What They Do                    | What They Miss                                                                                            |
| -------------------- | ---------------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Agent Frameworks** | LangChain, CrewAI, AutoGen   | Orchestrate model calls         | No persistent state, no typed mutations, no user-owned graph                                              |
| **Agent Runtimes**   | OpenClaw, Devin, Claude Code | Run agents in sandboxes         | Proprietary state, no compositional algebra, single-path                                                  |
| **Memory Products**  | MemSync, OneContext, Mem0    | Cross-platform memory           | Flat key-value, no recursive structure, no morphism protocol                                              |
| **Knowledge Graphs** | Neo4j, TigerGraph            | Graph databases                 | No AI-native mutation protocol, no main loop, no surfaces                                                 |
| **AI IDEs**          | Cursor, Windsurf, Cline      | Code-focused AI                 | Single-domain (code), no universal container model                                                        |
| **mo:os**            | —                            | **OS for AI-human computation** | **Recursive containers, 4 typed syscalls, forkable multi-path state, any model, any surface, user-owned** |

mo:os sits at an intersection no one else occupies: it's the **kernel** that agent frameworks, memory products, and AI surfaces all need but none of them build.

---

## Differentiation Summary

1. **One primitive** — The recursive container. Not 15 different object types. Not a different schema per feature. One JSONB shape that IS the user, the tool, the model, the app, the memory, the UI.

2. **Four syscalls** — ADD, LINK, MUTATE, UNLINK. Not an ever-growing REST API. Not a different RPC per feature. Four typed graph operations that compose into everything.

3. **Your graph, any model** — Context lives in PostgreSQL you control. Plug in Claude, Gemini, GPT, Ollama, whatever ships next month. The model is a replaceable container in the graph, not the platform.

4. **Multi-path reasoning as infrastructure** — Not a research paper. Not a prompt technique. A forkable in-memory cache with visual DAG exploration and structured commit-to-DB semantics.

5. **Category-theoretic guarantees** — Container composition is algebraically verified. Interface compatibility is checked at the type level. Functorial UI projection is structural, not ad-hoc. This isn't "we use fancy math words" — it's "composition is guaranteed to produce valid systems."

---

## Current State & Roadmap

### What Exists (Prototype)

- **TypeScript compatibility runtime** — 5 services (data-server, tool-server, engine, 2 React surfaces) proving the data model and morphism protocol
- **Chrome Extension** — MV3 sidepanel wrapper loading the React graph UI
- **Container algebra** — Sequential/parallel composition with interface validation
- **Morphism schema** — Zod-validated discriminated union (ADD/LINK/MUTATE/UNLINK)
- **Multi-provider support** — Anthropic, Gemini, OpenAI adapter functors
- **MCP tool server** — JSON-RPC 2.0 compliant tool registry with isolation sandbox
- **Live graph visualization** — XYFlow + Zustand + WebSocket real-time morphism application
- **Governance chain** — 4-level `.agent` manifest inheritance for workspace configuration

### Phase 0 — Specification (Current)
Wire ontology into manifests. Publish protobuf schemas for Container + Morphisms. Formalize the superset.

### Phase 1 — Foundation
Build Go kernel with PostgreSQL-backed container store, morphism executor, WebSocket gateway, gRPC tool interface.

### Phase 2 — Main Loop
Persistent event-driven goroutine per session. Model dispatch. Morphism validation + application + broadcast.

### Phase 3 — Surfaces
Connect React UIs to Go kernel. Surface containers registered in graph. Real-time SYNC projection.

### Phase 4 — Dockerize
`docker compose up` → full stack. kernel + postgres + redis + tool-runtime + surfaces.

### Phase 5 — Advanced
Multi-path DAG evaluation with forkable cache. Federated mo:os instances. WebRTC peer surfaces. MCP server for external agent access.

---

## The Tagline Options

- *"The operating system for AI-human computation."*
- *"One container. Any model. Your graph."*
- *"Content is context is the application."*
- *"Four syscalls. Infinite composition."*

---

---

# APPENDIX: Architecture Critique (Internal Reference)

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
| OS Concept  | mo:os Equivalent                                           |
| ----------- | ---------------------------------------------------------- |
| Kernel      | Root Container + Main Loop                                 |
| Process     | Container execution (model call, tool run, surface render) |
| Filesystem  | Resting State DB (PostgreSQL + JSONB + pgvector)           |
| RAM         | Active State Cache (in-memory container graph per session) |
| Syscalls    | Graph Morphisms (ADD, LINK, UPDATE, DELETE)                |
| IPC         | gRPC streams + WebSocket channels                          |
| Shell       | Runtime Surfaces (Chrome sidepanel, tab, PiP, CLI)         |
| Users       | AuthUser containers with permission-bounded traversal      |
| Permissions | ACL on containers (OWNS morphism = traversal right)        |

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

| Old Concept    | Container Specialization                                           |
| -------------- | ------------------------------------------------------------------ |
| Tool           | Container with executable kernel, typed I/O                        |
| Workflow       | Container whose wiring composes child tool containers              |
| Knowledge      | Container whose kernel holds data, outputs expose it               |
| Instruction    | Container whose output feeds prompt composition                    |
| Skill          | **Deprecated** — was a semantic alias for "composed tool template" |
| AppTemplate    | Container whose children define application structure (read-only)  |
| AppInstance    | Hydrated copy of AppTemplate with user-specific state              |
| User           | Container with identity kernel, permission ACL, personal sub-graph |
| RuntimeSurface | Container projecting other containers into a browser context       |
| mo:os itself   | The root container containing all other containers                 |

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

| Kind         | Kernel Contains                             | Behavior                                                  |
| ------------ | ------------------------------------------- | --------------------------------------------------------- |
| `data`       | JSON document, text, binary blob            | Passive storage. Read via output ports.                   |
| `executable` | Code reference or inline logic              | Invoked via input ports, produces on output ports.        |
| `composite`  | Nothing (structure is in children + wiring) | Composition of child containers. Wiring defines dataflow. |
| `surface`    | Render configuration (url, component ref)   | Projects container state into a UI context.               |
| `identity`   | User profile, credentials, preferences      | Authentication anchor. Owns other containers.             |

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

| System                           | Identity                           | Responsibility                                                                                          |
| -------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Kernel** (was RootContainer)   | `urn:moos:system:kernel`           | The mo:os runtime. Hosts the main loop. Owns system containers.                                         |
| **Loop** (was MainLoop)          | Internal to Kernel                 | Event-driven scheduler: receives events → evaluates state → dispatches morphisms → applies results      |
| **Store** (was RestingStateDB)   | PostgreSQL + pgvector              | Persistent, versioned container graph. Source of truth. Immutable history via append-only morphism log. |
| **Cache** (was ActiveStateCache) | In-memory (Redis or process-local) | Hot working set per session. Morphisms applied here first, then committed to Store.                     |

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

| Criterion                     | TypeScript                       | Go                                    | Rust                                 |
| ----------------------------- | -------------------------------- | ------------------------------------- | ------------------------------------ |
| Concurrency model             | Event loop (single-threaded)     | Goroutines + channels (native)        | Async/await + tokio (complex)        |
| GC behavior                   | V8 GC pauses (unpredictable)     | Low-latency GC (designed for servers) | No GC (manual/ownership)             |
| Deployment                    | node_modules + bundler + runtime | Single static binary                  | Single static binary                 |
| gRPC/protobuf                 | Third-party, heavy deps          | First-class (google.golang.org/grpc)  | Mature but verbose (tonic)           |
| Development speed             | Fast (dynamic)                   | Fast (simple language, fast compiler) | Slow (borrow checker, compile times) |
| Long-running daemon           | Memory leaks common              | Battle-tested (Docker, K8s, etcd)     | Excellent but over-engineered        |
| WebSocket                     | ws library                       | gorilla/websocket, nhooyr             | tokio-tungstenite                    |
| JSON/JSONB handling           | Native                           | encoding/json (good enough)           | serde_json (excellent)               |
| Community for OS-like systems | None                             | Docker, K8s, CockroachDB, etcd        | Linux kernel, Servo                  |

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

| Path                         | Protocol                       | Why                                                  |
| ---------------------------- | ------------------------------ | ---------------------------------------------------- |
| Kernel ↔ Store (PostgreSQL)  | SQL/pgx                        | Direct DB access, no intermediate layer              |
| Kernel ↔ Cache               | In-process (Go maps/channels)  | Zero-copy, maximum speed                             |
| Kernel ↔ Tool Runtime        | gRPC (bidirectional streaming) | Typed, efficient, supports streaming tool output     |
| Kernel ↔ Model Providers     | HTTPS (provider SDKs) or gRPC  | Provider-dependent, abstracted by model container    |
| Kernel ↔ Surfaces            | WebSocket (JSON-RPC 2.0)       | Browser-compatible, bidirectional, real-time         |
| Kernel ↔ External Agents     | gRPC or MCP over SSE           | Interoperability with Claude, other agent frameworks |
| Surface ↔ Surface            | WebRTC (future)                | Peer-to-peer for collaborative editing               |
| Kernel ↔ Kernel (federation) | gRPC (future)                  | Multi-instance mo:os federation                      |

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

| Component                                 | Fate                                                                                              |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `@moos/core` Container algebra            | **Keep & port to Go** — composition/validation logic is sound                                     |
| `@moos/core` superset.ts morphism schemas | **Keep & port to protobuf** — morphism types are correct (rename only)                            |
| `@moos/functors` provider pattern         | **Keep & port to Go** — but make it a real functor (map containers + morphisms, not just prompts) |
| `@moos/store` interface-based queries     | **Port to PostgreSQL** — replace Map with JSONB queries                                           |
| FFS4 React UI (graph + chat)              | **Keep as-is** — surface container, works correctly                                               |
| FFS6 React UI (IDE viewer)                | **Keep as-is** — surface container                                                                |
| Chrome Extension MV3 wrapper              | **Keep** — thin shell, does its job                                                               |
| `.agent` governance chain                 | **Keep** — inheritance model is clean                                                             |
| Superset ontology JSON                    | **Wire into manifest chain** and **extend to full spec**                                          |

### 7.2 What Gets Replaced

| Component                                   | Replacement                                              |
| ------------------------------------------- | -------------------------------------------------------- |
| `data-server/main.ts` (1140-line monolith)  | Go kernel with PostgreSQL-backed container store         |
| `tool-server/main.ts` (HTTP tool execution) | Go kernel's gRPC tool dispatcher                         |
| `engine/main.ts` (one-shot bootstrap)       | Go kernel's persistent main loop (goroutine per session) |
| `InMemoryCategoryStore` (JavaScript Map)    | PostgreSQL JSONB + in-process Go cache                   |
| `SessionState` (message array)              | Redis-backed session with container graph snapshot       |
| All HTTP inter-service calls                | gRPC with protobuf (kernel-internal: channels)           |
| Seed data (hardcoded JS objects)            | PostgreSQL migrations + seed SQL                         |
| NanoClaw bridge (WebSocket echo stub)       | Go kernel's WebSocket gateway (real streaming)           |

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
