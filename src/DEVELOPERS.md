# mo:os Kernel — Developer Guide

**Audience:** Python developers joining the team.
**Language:** Go 1.23 — but the concepts map directly to Python thinking.

---

## Table of Contents

1. [The One-Sentence Pitch](#the-one-sentence-pitch)
2. [Why This Architecture](#why-this-architecture)
3. [The Mental Model (for Python devs)](#the-mental-model-for-python-devs)
4. [Package Map](#package-map)
5. [Core Concepts](#core-concepts)
   - [Nodes and Wires (the Graph)](#nodes-and-wires-the-graph)
   - [The Four Operations (Natural Transformations)](#the-four-operations-natural-transformations)
   - [Envelopes](#envelopes)
   - [Programs (Atomic Batches)](#programs-atomic-batches)
   - [The Morphism Log (Event Sourcing)](#the-morphism-log-event-sourcing)
   - [The Fold (Catamorphism)](#the-fold-catamorphism)
   - [The Registry (Type System)](#the-registry-type-system)
   - [Functors (Read-Path Projections)](#functors-read-path-projections)
6. [Package-by-Package Walkthrough](#package-by-package-walkthrough)
7. [Data Flow: Write Path](#data-flow-write-path)
8. [Data Flow: Read Path](#data-flow-read-path)
9. [HTTP API Reference](#http-api-reference)
10. [Configuration](#configuration)
11. [Running Locally](#running-locally)
12. [Testing](#testing)
13. [Common Tasks](#common-tasks)
14. [Glossary: Category Theory → Python](#glossary-category-theory--python)

---

## The One-Sentence Pitch

mo:os is a **typed graph database** whose entire state is derived by replaying
an append-only event log through a pure function — like a `functools.reduce()`
over a list of dicts.

---

## Why This Architecture

Traditional systems have tables, ORM models, migrations, and ad-hoc mutation
endpoints. mo:os replaces all of that with:

| Traditional          | mo:os equivalent                                |
| -------------------- | ----------------------------------------------- |
| SQL table rows       | **Nodes** in a typed graph                      |
| Foreign keys         | **Wires** (typed, directional edges)            |
| INSERT/UPDATE/DELETE | **4 operations**: ADD, LINK, MUTATE, UNLINK     |
| Migration history    | **Morphism log** — append-only, immutable       |
| Current DB state     | **Computed** by replaying the log (`reduce()`)  |
| Schema/validation    | **Operad registry** loaded from `ontology.json` |

**Key guarantee:** You can delete all state, replay the log, and get the
exact same graph. Always. This is the fundamental invariant.

---

## The Mental Model (for Python devs)

Think of the entire system as this Python pseudocode:

```python
from functools import reduce
from typing import TypedDict

# The state is a dict of nodes + a dict of wires
state = {"nodes": {}, "wires": {}}

# The log is a list of operations (events)
morphism_log: list[dict] = []

# Each operation is one of: ADD, LINK, MUTATE, UNLINK
def apply(state: dict, envelope: dict) -> dict:
    """Pure function. No side effects. Returns NEW state."""
    match envelope["type"]:
        case "ADD":     return {**state, "nodes": {**state["nodes"], urn: new_node}}
        case "LINK":    return {**state, "wires": {**state["wires"], key: new_wire}}
        case "MUTATE":  return {**state, "nodes": {**state["nodes"], urn: updated_node}}
        case "UNLINK":  # remove wire from state
    return state

# Replay: rebuild state from scratch
current_state = reduce(apply, morphism_log, {"nodes": {}, "wires": {}})
```

**That's it.** The entire kernel is an elaboration of this pattern.

The Go code adds: concurrency locks, persistence (JSONL or Postgres), type
validation (the operad), and an HTTP transport. But the core is always just
`reduce(apply, log, empty_state)`.

---

## Package Map

```
src/
├── cmd/kernel/main.go          # Boot: config → store → registry → runtime → seed → HTTP
├── internal/
│   ├── cat/                    # Value types: Node, Wire, Envelope, Program, GraphState
│   ├── fold/                   # Pure reduce: Evaluate(), Replay() — NO side effects
│   ├── operad/                 # Type system: which operations are allowed on which Kinds
│   ├── shell/                  # Runtime wrapper: locks + persistence + fold
│   ├── functor/                # Read-path projections (mocked): UI, embeddings, DAG
│   ├── provider/               # LLM adapter interface (mocked): echo provider
│   ├── transport/              # HTTP API: 14 endpoints + HTML explorer
│   ├── hydration/              # Batch materialization: declarative JSON → Program
│   └── config/                 # Environment variable configuration
└── go.mod
```

### Python analogy for each package

| Go package  | Python analogy                                                                   |
| ----------- | -------------------------------------------------------------------------------- |
| `cat`       | Your `models.py` — but these are immutable dataclasses, not ORM models           |
| `fold`      | A pure `reduce()` function. No DB calls, no network, no files                    |
| `operad`    | A schema validator (like Pydantic) that checks types before writes               |
| `shell`     | The "service layer" — wraps the pure function with threading locks and DB writes |
| `functor`   | Read-only transformers: `state → UI data`, `state → vector`, `state → DAG`       |
| `provider`  | An LLM client interface (like `openai.ChatCompletion`) — currently mocked        |
| `transport` | Your `views.py` / FastAPI routes                                                 |
| `hydration` | A batch import/seed tool: `JSON manifest → list of operations`                   |
| `config`    | `os.environ.get()` with defaults                                                 |

---

## Core Concepts

### Nodes and Wires (the Graph)

A **Node** is a vertex in the graph. Python equivalent:

```python
@dataclass(frozen=True)
class Node:
    urn: str              # "urn:moos:kernel:wave-0" — globally unique ID
    kind: str             # "Kernel", "Feature", "Agent", etc.
    stratum: str          # "S0"–"S4" (hydration level, default "S2")
    payload: dict         # arbitrary JSON data
    metadata: dict        # arbitrary JSON metadata
    version: int          # auto-incremented on mutation (CAS)
```

A **Wire** is a directed edge between two nodes, connecting specific **ports**:

```python
@dataclass(frozen=True)
class Wire:
    source_urn: str       # which node the wire leaves
    source_port: str      # which port on the source ("implements", "out", etc.)
    target_urn: str       # which node the wire enters
    target_port: str      # which port on the target ("implements", "in", etc.)
    config: dict          # optional wire metadata
```

Wires are uniquely identified by the 4-tuple `(source_urn, source_port, target_urn, target_port)`. Multiple wires between the same two nodes are allowed as long as ports differ — this makes it a **hypergraph**.

### The Four Operations (Natural Transformations)

**Every** mutation to the graph is one of exactly four operations. No exceptions.

| Operation  | What it does                                 | Python analogy                                               |
| ---------- | -------------------------------------------- | ------------------------------------------------------------ |
| **ADD**    | Create a new node                            | `nodes[urn] = Node(...)`                                     |
| **LINK**   | Create a wire between two existing nodes     | `wires[key] = Wire(...)`                                     |
| **MUTATE** | Update a node's payload (with version check) | `nodes[urn] = nodes[urn]._replace(payload=new, version=v+1)` |
| **UNLINK** | Remove a wire                                | `del wires[key]`                                             |

There is no DELETE for nodes. Nodes are permanent once added.
There is no UPDATE for wires. Remove and re-add instead.

### Envelopes

An **Envelope** is a single operation ready for execution:

```python
@dataclass
class Envelope:
    type: str             # "ADD" | "LINK" | "MUTATE" | "UNLINK"
    actor: str            # who is performing this operation (a URN)
    scope: str            # optional: which subgraph this belongs to
    add: AddPayload       # set when type="ADD"
    link: LinkPayload     # set when type="LINK"
    mutate: MutatePayload # set when type="MUTATE"
    unlink: UnlinkPayload # set when type="UNLINK"
```

Exactly one payload field is set per envelope. The `actor` is always required — every operation has a provenance.

### Programs (Atomic Batches)

A **Program** is a list of Envelopes executed atomically. If any envelope fails, the entire batch rolls back:

```python
@dataclass
class Program:
    actor: str            # inherited by all child envelopes
    scope: str            # inherited by all child envelopes
    envelopes: list[Envelope]
```

This is your transaction boundary. Use Programs when you need "create node A, create node B, link them" to succeed or fail as a unit.

### The Morphism Log (Event Sourcing)

Every successfully applied envelope is appended to the **morphism log** — a timestamped, immutable, append-only sequence:

```python
@dataclass
class PersistedEnvelope:
    envelope: Envelope
    issued_at: datetime
```

The log IS the source of truth. The current graph state is a **computed projection** of the log. If you understand event sourcing, you already understand this.

### The Fold (Catamorphism)

The fold is the pure function that replays the log into state:

```python
def replay(log: list[PersistedEnvelope]) -> GraphState:
    state = GraphState(nodes={}, wires={})
    for entry in log:
        state = evaluate(state, entry.envelope, entry.issued_at)
    return state
```

In the Go code, this lives in the `fold` package. **Critical rule:** the fold package has ZERO file I/O, ZERO network calls, ZERO concurrency primitives. It is a pure function. `state_in → state_out`, nothing else.

### The Registry (Type System)

The **operad registry** defines which Kinds exist and what operations are legal:

```python
registry = {
    "Kernel": {
        "mutable": True,
        "allowed_strata": ["S2"],
        "ports": {
            "implements": {"direction": "in", "targets": [("Feature", "implements")]},
            "exposes":    {"direction": "in", "targets": [("RuntimeSurface", "exposes")]},
        }
    },
    "Feature": {
        "mutable": True,
        "ports": {
            "implements": {"direction": "out"},
        }
    },
    # ... 13+ more kinds
}
```

It is loaded from `.agent/knowledge_base/registry/ontology.json` at boot. When present, the fold **rejects** operations that violate the type constraints (wrong Kind, wrong port direction, etc.).

### Functors (Read-Path Projections)

A **functor** transforms the graph state into a different representation for consumption. Functors are **read-only** — they never modify state.

| Functor          | What it produces                                          | Status                                      |
| ---------------- | --------------------------------------------------------- | ------------------------------------------- |
| **UI_Lens**      | `{nodes: [...], edges: [...]}` for rendering in a browser | Mocked (deterministic hash-based positions) |
| **Embedder**     | 1536-dim vectors for each node (for similarity search)    | Mocked (deterministic from URN hash)        |
| **StructureMap** | Topological sort / DAG layering                           | Mocked (alphabetical sort)                  |

**Key rule:** Functor output is NEVER ground truth. It's a disposable projection. You can always recompute it from the graph state.

---

## Package-by-Package Walkthrough

### `cat/` — Category Types

**7 files, 0 external dependencies.**

This is the data model — all value types, no behavior. Think of it as `models.py` if every model were a frozen dataclass with no database connection.

| File          | What it defines                                                                  |
| ------------- | -------------------------------------------------------------------------------- |
| `object.go`   | `URN`, `Kind`, `Port`, `Stratum`, `Node` — with S0–S4 constants                  |
| `wire.go`     | `Wire` struct + `WireKey()` composite key function                               |
| `envelope.go` | `MorphismType` (ADD/LINK/MUTATE/UNLINK), `Envelope` with `.Validate()`           |
| `payload.go`  | `AddPayload`, `LinkPayload`, `MutatePayload`, `UnlinkPayload`                    |
| `program.go`  | `Program`, `EvalResult`, `ProgramResult`, `PersistedEnvelope`                    |
| `state.go`    | `GraphState` (map of Nodes + map of Wires), with `.Clone()` deep copy            |
| `errors.go`   | 16 sentinel errors: `ErrNodeExists`, `ErrWireExists`, `ErrVersionConflict`, etc. |

### `fold/` — Pure Catamorphism

**3 source files, 2 test files.**

The mathematical core. Pure functions only — no I/O.

| Function                 | Signature (conceptual)                        | What it does                             |
| ------------------------ | --------------------------------------------- | ---------------------------------------- |
| `Evaluate()`             | `(state, envelope, time) → result`            | Apply one operation                      |
| `EvaluateWithRegistry()` | `(state, envelope, time, registry?) → result` | Apply one operation with type checking   |
| `EvaluateProgram()`      | `(state, program, time) → result`             | Atomic batch (rollback on failure)       |
| `Replay()`               | `(log) → state`                               | Full rebuild: `reduce(evaluate, log, ∅)` |

**Purity guarantee:** If you grep this package for `os.`, `net.`, `sync.`, or `http.` — you will find nothing. This guarantee is enforced at review time.

### `operad/` — Type System

**4 files.** Loaded from `ontology.json` at boot.

The operad validates operations against the type system:

- **ADD validation:** Is the Kind registered? Is the stratum allowed?
- **MUTATE validation:** Is the Kind mutable? Does the version match?
- **LINK validation:** Does the source port exist on the source Kind? Is the direction correct? Is the target Kind an admissible target?

The registry is derived from the Knowledge Base ontology using `DeriveFromOntology()`. It automatically injects `Kernel` and `Feature` Kinds if they're not explicitly defined in the ontology.

### `shell/` — Effect Boundary

**5 source files, 1 test file.** This is where purity ends and the real world begins.

The `Runtime` struct wraps the pure fold with:

- **`sync.RWMutex`** — concurrent reads, exclusive writes
- **`Store` interface** — abstract persistence
- **In-memory state cache** — the folded graph, always current

Key methods:

| Method                        | What it does                                   | Python analogy                    |
| ----------------------------- | ---------------------------------------------- | --------------------------------- |
| `NewRuntime(store, registry)` | Replays the log to reconstruct state           | `__init__` that calls `replay()`  |
| `Apply(envelope)`             | Fold → persist → update cache                  | `service.execute(command)`        |
| `ApplyProgram(program)`       | Atomic batch fold → persist                    | `service.execute_batch(commands)` |
| `SeedIfAbsent(envelope)`      | Like Apply but ignores "already exists" errors | Idempotent bootstrap              |
| `State()`                     | Returns a deep copy of current state           | `get_snapshot()`                  |
| `Node(urn)`                   | Lookup one node                                | `get_by_id(urn)`                  |
| `Nodes()`                     | All nodes                                      | `list_all()`                      |
| `OutgoingWires(urn)`          | Wires leaving a node                           | `get_edges_from(urn)`             |
| `IncomingWires(urn)`          | Wires entering a node                          | `get_edges_to(urn)`               |
| `Log()`                       | Full morphism log                              | `get_event_log()`                 |

Three Store implementations:

| Store           | Use case                                          |
| --------------- | ------------------------------------------------- |
| `MemStore`      | Tests — ephemeral, in-memory                      |
| `LogStore`      | Default — JSONL file at `data/morphism-log.jsonl` |
| `PostgresStore` | Production — Postgres table `morphism_log`        |

### `functor/` — Read-Path Projections

**4 source files, 1 test file.** All mocked for the MVP.

Each functor implements the `Projector` interface:

```go
type Projector interface {
    Name() string
    Project(state GraphState) (any, error)
}
```

Python equivalent:

```python
class Projector(Protocol):
    def name(self) -> str: ...
    def project(self, state: GraphState) -> Any: ...
```

The `MockUILens` produces `{nodes: [...], edges: [...]}` with deterministic positions based on URN hashes. This powers the `/explorer` HTML page and the `/functor/ui` JSON endpoint.

### `provider/` — LLM Adapter

**2 files.** The interface for AI model calls:

```python
class Provider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResult: ...
```

`MockProvider` echoes back the input with a `[mock:name]` prefix. No real API calls. When you integrate a real model, you'll implement this interface.

### `transport/` — HTTP API

**3 files.** All HTTP endpoints. Think FastAPI routes.

### `hydration/` — Batch Materialization

**1 source file, 1 test file.** Converts a declarative JSON manifest into a `Program`:

```python
# Input: "I want these nodes and wires to exist"
request = {
    "actor": "urn:moos:kernel:self",
    "nodes": [
        {"urn": "urn:a", "kind": "Node"},
        {"urn": "urn:b", "kind": "Node"},
    ],
    "wires": [
        {"source_urn": "urn:a", "source_port": "out", "target_urn": "urn:b", "target_port": "in"}
    ]
}

# Output: a Program with ADD + LINK envelopes
program = materialize(request)
```

### `config/` — Configuration

**1 file.** Reads environment variables:

| Variable                    | Default                   | Description                                             |
| --------------------------- | ------------------------- | ------------------------------------------------------- |
| `MOOS_KERNEL_STORE`         | `file`                    | Store backend: `file`, `postgres`, or `memory`          |
| `MOOS_KERNEL_LOG_PATH`      | `data/morphism-log.jsonl` | Path to JSONL file store                                |
| `MOOS_DATABASE_URL`         | _(none)_                  | Postgres connection string (required if store=postgres) |
| `MOOS_KERNEL_REGISTRY_PATH` | _(auto-detect)_           | Path to `ontology.json`                                 |
| `MOOS_KERNEL_ADDR`          | `:8000`                   | HTTP listen address                                     |

---

## Data Flow: Write Path

```
Client                 transport          shell              fold             store
  │                       │                 │                  │                │
  │  POST /morphisms      │                 │                  │                │
  │  {type: "ADD", ...}   │                 │                  │                │
  │──────────────────────►│                 │                  │                │
  │                       │  Apply(env)     │                  │                │
  │                       │────────────────►│                  │                │
  │                       │                 │  Lock()          │                │
  │                       │                 │  EvaluateWith    │                │
  │                       │                 │  Registry(       │                │
  │                       │                 │    state, env,   │                │
  │                       │                 │    now, reg)     │                │
  │                       │                 │─────────────────►│                │
  │                       │                 │                  │ clone state    │
  │                       │                 │                  │ validate       │
  │                       │                 │                  │ apply          │
  │                       │                 │  new_state       │                │
  │                       │                 │◄─────────────────│                │
  │                       │                 │                  │                │
  │                       │                 │  Append(entry)   │                │
  │                       │                 │─────────────────────────────────►│
  │                       │                 │                  │                │
  │                       │                 │  update cache    │                │
  │                       │                 │  Unlock()        │                │
  │                       │  EvalResult     │                  │                │
  │                       │◄────────────────│                  │                │
  │  200 OK {result}      │                 │                  │                │
  │◄──────────────────────│                 │                  │                │
```

**Key invariant:** The fold step (pure) happens _before_ persistence. If the fold rejects the operation, nothing is persisted. If persistence fails after a successful fold, the in-memory state is NOT updated (the operation is lost, which is safe because the log didn't record it).

---

## Data Flow: Read Path

```
Client                transport          shell            functor
  │                      │                 │                 │
  │  GET /functor/ui     │                 │                 │
  │─────────────────────►│                 │                 │
  │                      │  State()        │                 │
  │                      │────────────────►│                 │
  │                      │                 │ RLock()         │
  │                      │  clone(state)   │ clone           │
  │                      │◄────────────────│ RUnlock()       │
  │                      │                 │                 │
  │                      │  ProjectUI(state)                 │
  │                      │──────────────────────────────────►│
  │                      │                 │                 │ map nodes → UI
  │                      │                 │                 │ map wires → edges
  │                      │  UIProjection   │                 │
  │                      │◄──────────────────────────────────│
  │  200 OK {nodes, edges}                 │                 │
  │◄─────────────────────│                 │                 │
```

Reads use `RLock` (multiple concurrent readers allowed). The state is cloned before being passed to functors, so functor code cannot corrupt runtime state.

---

## HTTP API Reference

All endpoints return JSON. Port default: `8000`.

### Health & State

| Method | Path                          | Description                                                              |
| ------ | ----------------------------- | ------------------------------------------------------------------------ |
| `GET`  | `/healthz`                    | Health check: `{"status": "ok", "nodes": N, "wires": M, "log_depth": L}` |
| `GET`  | `/state`                      | Full graph state (all nodes + all wires)                                 |
| `GET`  | `/state/nodes`                | All nodes as a map `{urn: node}`                                         |
| `GET`  | `/state/nodes/{urn}`          | Single node by URN (404 if missing)                                      |
| `GET`  | `/state/wires`                | All wires as a map `{key: wire}`                                         |
| `GET`  | `/state/wires/outgoing/{urn}` | Wires leaving a node                                                     |
| `GET`  | `/state/wires/incoming/{urn}` | Wires entering a node                                                    |

### Write Operations

| Method | Path                     | Body                      | Description                |
| ------ | ------------------------ | ------------------------- | -------------------------- |
| `POST` | `/morphisms`             | `Envelope` JSON           | Apply a single operation   |
| `POST` | `/programs`              | `Program` JSON            | Apply an atomic batch      |
| `POST` | `/hydration/materialize` | `MaterializeRequest` JSON | Batch create nodes + wires |

### Introspection

| Method | Path                  | Description                     |
| ------ | --------------------- | ------------------------------- |
| `GET`  | `/log`                | Full morphism log (all events)  |
| `GET`  | `/semantics/registry` | The loaded operad registry      |
| `GET`  | `/functor/ui`         | UI_Lens projection (JSON)       |
| `GET`  | `/explorer`           | Interactive HTML graph explorer |

### Example: Create a node with curl

```bash
curl -X POST http://localhost:8000/morphisms \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ADD",
    "actor": "urn:dev:alice",
    "add": {
      "urn": "urn:myapp:service:auth",
      "kind": "Node",
      "stratum": "S2",
      "payload": {"label": "Auth Service", "version": "1.0"}
    }
  }'
```

### Example: Link two nodes

```bash
curl -X POST http://localhost:8000/morphisms \
  -H "Content-Type: application/json" \
  -d '{
    "type": "LINK",
    "actor": "urn:dev:alice",
    "link": {
      "source_urn": "urn:myapp:service:auth",
      "source_port": "depends_on",
      "target_urn": "urn:myapp:service:db",
      "target_port": "depends_on"
    }
  }'
```

### Example: Atomic batch (Program)

```bash
curl -X POST http://localhost:8000/programs \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "urn:dev:alice",
    "envelopes": [
      {"type": "ADD", "add": {"urn": "urn:a", "kind": "Node", "stratum": "S2"}},
      {"type": "ADD", "add": {"urn": "urn:b", "kind": "Node", "stratum": "S2"}},
      {"type": "LINK", "link": {
        "source_urn": "urn:a", "source_port": "out",
        "target_urn": "urn:b", "target_port": "in"
      }}
    ]
  }'
```

### Example: Batch materialize (Hydration)

```bash
curl -X POST http://localhost:8000/hydration/materialize \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "urn:dev:alice",
    "nodes": [
      {"urn": "urn:x", "kind": "Node"},
      {"urn": "urn:y", "kind": "Node"}
    ],
    "wires": [
      {"source_urn": "urn:x", "source_port": "out", "target_urn": "urn:y", "target_port": "in"}
    ]
  }'
```

Add `?dry_run=true` to validate without executing.

---

## Configuration

Set environment variables before starting the kernel:

```bash
# Defaults (file store, auto-detect registry, port 8000)
cd src && go run ./cmd/kernel

# Explicit file store path
MOOS_KERNEL_LOG_PATH=/path/to/morphism-log.jsonl go run ./cmd/kernel

# Postgres store
MOOS_KERNEL_STORE=postgres \
MOOS_DATABASE_URL="postgres://user:pass@localhost:5432/moos" \
go run ./cmd/kernel

# In-memory (ephemeral, for testing)
MOOS_KERNEL_STORE=memory go run ./cmd/kernel

# Custom listen address
MOOS_KERNEL_ADDR=":9000" go run ./cmd/kernel
```

The registry auto-detects `ontology.json` by walking up directories from cwd.
Override with: `MOOS_KERNEL_REGISTRY_PATH=/absolute/path/to/ontology.json`.

---

## Running Locally

```bash
# From the repository root (d:\FFS0_Factory\moos)
cd src

# Install dependencies (one-time)
go mod tidy

# Run the kernel
go run ./cmd/kernel
# → [boot] store=file addr=:8000
# → [boot] file store: D:\...\data\morphism-log.jsonl
# → [boot] registry loaded: 17 kinds from ...ontology.json
# → [shell] replayed 0 morphisms → 0 nodes, 0 wires
# → [seed] kernel identity seeded: 8 nodes, 6 wires
# → [transport] listening on :8000

# Open the explorer
# → http://localhost:8000/explorer

# Verify health
curl http://localhost:8000/healthz
# → {"status": "ok", "nodes": 8, "wires": 6, "log_depth": 14}
```

To **reset** state, delete the morphism log file:

```bash
rm data/morphism-log.jsonl
# Restart → clean slate, kernel re-seeds
```

---

## Testing

```bash
cd src

# Run all tests
go test ./...

# Verbose output
go test ./... -v

# Single package
go test ./internal/fold/ -v

# Specific test
go test ./internal/shell/ -v -run TestRuntimeSeedIfAbsent

# Static analysis
go vet ./...
```

### Test structure

Tests use Go's built-in `testing` package (no external framework):

```go
func TestSomething(t *testing.T) {
    // Arrange
    store := shell.NewMemStore()
    rt, err := shell.NewRuntime(store, nil)

    // Act
    result, err := rt.Apply(envelope)

    // Assert
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

Python equivalent: `pytest` with `assert` statements. No mocking frameworks — all stores and functors have in-memory implementations.

### What's tested (27 tests total)

| Package     | Tests | What they cover                                                             |
| ----------- | ----- | --------------------------------------------------------------------------- |
| `fold`      | 8     | All 4 operations, duplicate rejection, version conflicts, atomicity, replay |
| `functor`   | 3     | UILens projection, embedder determinism, structure map ordering             |
| `hydration` | 3     | Basic materialize, missing actor, dry run                                   |
| `operad`    | 2     | Loading from real ontology.json, ADD validation                             |
| `shell`     | 5     | Apply, SeedIfAbsent, replay on restart, programs, wire queries              |
| `transport` | 9     | All HTTP endpoints, error responses, content types                          |

---

## Common Tasks

### "I need to add a new Kind of node"

1. Add the Kind to `.agent/knowledge_base/registry/ontology.json`
2. Define its ports (connections to other Kinds)
3. Restart the kernel — the operad loader derives the new Kind automatically

### "I need to add a new HTTP endpoint"

1. Add a handler method on `*Server` in `transport/server.go`
2. Register the route in `registerRoutes()`
3. Add a test in `transport/server_test.go`

### "I need to integrate a real LLM"

1. Implement the `provider.Provider` interface
2. Wire it into `main.go` during boot
3. The mock remains available for tests

### "I need to add a new functor"

1. Implement the `functor.Projector` interface
2. Add a new handler in the transport layer
3. The mock version returns deterministic data for testing

### "I want to call this from Python"

The kernel is a JSON HTTP API. Use `requests` or `httpx`:

```python
import httpx

BASE = "http://localhost:8000"

# Create a node
resp = httpx.post(f"{BASE}/morphisms", json={
    "type": "ADD",
    "actor": "urn:dev:alice",
    "add": {
        "urn": "urn:myapp:widget:1",
        "kind": "Node",
        "stratum": "S2",
        "payload": {"name": "My Widget"}
    }
})
print(resp.json())

# Read the graph
state = httpx.get(f"{BASE}/state").json()
print(f"{len(state['nodes'])} nodes, {len(state['wires'])} wires")

# Batch create
resp = httpx.post(f"{BASE}/hydration/materialize", json={
    "actor": "urn:dev:alice",
    "nodes": [
        {"urn": "urn:a", "kind": "Node"},
        {"urn": "urn:b", "kind": "Node"},
    ],
    "wires": [
        {"source_urn": "urn:a", "source_port": "out",
         "target_urn": "urn:b", "target_port": "in"}
    ]
})
```

---

## Glossary: Category Theory → Python

You'll see category theory terms in code comments and documentation. Here's
what they mean in practical terms:

| Term                            | What it means here                            | Python analogy                        |
| ------------------------------- | --------------------------------------------- | ------------------------------------- |
| **Category C**                  | The typed graph (nodes + wires)               | A NetworkX DiGraph with typed nodes   |
| **Object / Ob(C)**              | A Node                                        | A vertex / dict entry                 |
| **Morphism / Hom(C)**           | A Wire                                        | A directed edge                       |
| **Natural Transformation (NT)** | One of ADD/LINK/MUTATE/UNLINK                 | An event type in an event store       |
| **Envelope**                    | An instance of an NT with data                | An event payload                      |
| **Catamorphism / Fold / Σ**     | `reduce(apply, log, ∅)`                       | `functools.reduce()`                  |
| **Initial Object**              | Empty state `{nodes: {}, wires: {}}`          | The starting accumulator              |
| **Carrier Algebra**             | The current GraphState                        | The computed result of reduce         |
| **Free Monoid**                 | The morphism log (append-only)                | A Python list you only `.append()` to |
| **Operad**                      | The type system (which ops on which types)    | Pydantic validators                   |
| **Functor**                     | A read-only transform: `state → something`    | A pure function from state to view    |
| **Kind**                        | A node type classification                    | A string enum or union type           |
| **Port**                        | A named connection point                      | A specific field in a relationship    |
| **Stratum**                     | Hydration level (S0–S4)                       | A processing stage / maturity label   |
| **URN**                         | Unique identifier                             | A string primary key                  |
| **Program**                     | An atomic batch of envelopes                  | A database transaction                |
| **Wire Key**                    | 4-tuple composite key for wires               | A tuple used as a dict key            |
| **Hypergraph**                  | Multiple edges between same nodes (via ports) | A multigraph                          |

---

## Architecture Invariants

These rules are always true. If code violates any of them, it's a bug:

1. **The fold is pure.** The `fold/` package makes zero I/O calls. Ever.
2. **State is reconstructible.** `replay(log) == current_state`. Always.
3. **Only four operations.** ADD, LINK, MUTATE, UNLINK. Nothing else modifies state.
4. **Actor is required.** Every operation has a provenance — who did this.
5. **Functor output is never truth.** It's a disposable projection. Recompute anytime.
6. **Programs are atomic.** All-or-nothing. Partial application is impossible.
7. **The log is append-only.** You never edit, delete, or reorder log entries.
8. **Reads don't block writes (mostly).** RWMutex: concurrent reads, exclusive writes.
9. **Seeds are idempotent.** Restarting the kernel re-seeds; no duplicates, no errors.
10. **The registry is loaded, not hardcoded.** Type rules come from `ontology.json`, not Go code.
