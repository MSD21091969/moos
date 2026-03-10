# mo:os Kernel — Developer Guide

**Audience:** Python developers crossing into typed FP / category theory.
**Language:** Go 1.23 — but the concepts map to any language with sum types and pure functions.

---

## Table of Contents

1. [The One-Sentence Pitch](#the-one-sentence-pitch)
2. [Why This Architecture](#why-this-architecture)
3. [The Mental Model (for Python devs)](#the-mental-model-for-python-devs)
4. [The Decoupled Design](#the-decoupled-design)
5. [Package Map](#package-map)
6. [Core Concepts](#core-concepts)
   - [Nodes and Wires (the Graph)](#nodes-and-wires-the-graph)
   - [The Four Operations (Natural Transformations)](#the-four-operations-natural-transformations)
   - [Envelopes](#envelopes)
   - [Programs (Atomic Batches)](#programs-atomic-batches)
   - [The Morphism Log (Event Sourcing)](#the-morphism-log-event-sourcing)
   - [The Fold (Catamorphism)](#the-fold-catamorphism)
   - [The Registry (Type System)](#the-registry-type-system)
   - [Functors (Read-Path Projections)](#functors-read-path-projections)
7. [Package-by-Package Walkthrough](#package-by-package-walkthrough)
8. [Data Flow: Write Path](#data-flow-write-path)
9. [Data Flow: Read Path](#data-flow-read-path)
10. [HTTP API Reference](#http-api-reference)
11. [Configuration](#configuration)
12. [Running Locally](#running-locally)
13. [Testing](#testing)
14. [Common Tasks](#common-tasks)
15. [Glossary: Category Theory → Python](#glossary-category-theory--python)

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

The Go code adds: concurrency locks, persistence (JSONL file), type
validation (the operad), and an HTTP transport. But the core is always just
`reduce(apply, log, empty_state)`.

---

## The Decoupled Design

The previous kernel (in `src/`) had coupling you'd find in a typical Go app:
env vars with hardcoded defaults, path-walking to find config files, seed data
baked into `main.go`, and Postgres imports in the binary.

The rewrite inverts these dependencies. The kernel is a **generic binary that
knows nothing about the workspace that runs it.**

| Old (src/)                                   | New (kernel/)                                         |
| -------------------------------------------- | ----------------------------------------------------- |
| `os.Getenv("MOOS_KERNEL_STORE")` with default `"file"` | Single JSON config file, no env vars, no defaults      |
| Auto-detect `ontology.json` by walking up dirs | Config specifies `registry_path` — or omits it         |
| Seed data hardcoded in `main.go` (13 morphisms) | Seed programs live in `config.json` as a JSON array    |
| `operad.LoadRegistry(path string)` reads files | `operad.LoadRegistry(data []byte)` — pure parse       |
| Explorer HTML as a Go string constant (`%s`)  | Explorer HTML as `embed.FS` template file             |
| Postgres store compiled in, pgx dependency     | Store interface preserved, Postgres deferred, 0 deps  |
| `config.Load()` — env vars + findRegistry()   | `config.LoadFromFile(path)` — fail-fast, no magic     |

**Consequence:** The installer (or you, manually) writes a `config.json` that
tells the kernel everything it needs. The kernel binary is generic. Same binary,
different config → different workspace. Config is never committed — it contains
absolute paths specific to *your* machine.

### The Three Zones

```
┌──────────────────────────────────────────────────────────────┐
│  INSTALLER / WORKSPACE (writes config.json)                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  config.json (gitignored)                               │ │
│  │  ├── store_type: "file"                                 │ │
│  │  ├── log_path: "/abs/path/to/morphism-log.jsonl"        │ │
│  │  ├── registry_path: "/abs/path/to/ontology.json"        │ │
│  │  ├── listen_addr: ":8000"                               │ │
│  │  └── seed: [ ... programs ... ]                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                     --config flag                             │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │  KERNEL BINARY (generic, workspace-unaware)             │ │
│  │  moos --config /path/to/config.json                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │  RUNTIME STATE (computed from morphism log)             │ │
│  │  morphism-log.jsonl → replay → GraphState               │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Package Map

```
kernel/
├── cmd/moos/main.go            # Boot: --config → load → store → registry → runtime → seed → HTTP
├── internal/
│   ├── cat/                    # Value types: Node, Wire, Envelope, Program, GraphState
│   ├── fold/                   # Pure reduce: Evaluate(), Replay() — NO side effects
│   ├── operad/                 # Type system: which operations are allowed on which Kinds
│   ├── shell/                  # Runtime wrapper: locks + persistence + fold
│   ├── functor/                # Read-path projections (mocked): UI, embeddings, DAG
│   ├── transport/              # HTTP API: 14 endpoints + embedded HTML explorer
│   ├── hydration/              # Batch materialization: declarative JSON → Program
│   └── config/                 # JSON config file parser — no env vars, no defaults
├── registry/                   # ontology.json + schema.json (public, committed)
└── go.mod                      # Module: moos, Go 1.23, zero external dependencies
```

### Python analogy for each package

| Go package  | Python analogy                                                                   |
| ----------- | -------------------------------------------------------------------------------- |
| `cat`       | Your `models.py` — but these are immutable dataclasses, not ORM models           |
| `fold`      | A pure `reduce()` function. No DB calls, no network, no files                    |
| `operad`    | A schema validator (like Pydantic) that checks types before writes               |
| `shell`     | The "service layer" — wraps the pure function with threading locks and DB writes |
| `functor`   | Read-only transformers: `state → UI data`, `state → vector`, `state → DAG`      |
| `transport` | Your `views.py` / FastAPI routes                                                 |
| `hydration` | A batch import/seed tool: `JSON manifest → list of operations`                   |
| `config`    | `json.load(open("config.json"))` with required field checks                      |

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

Wires are uniquely identified by the 4-tuple `(source_urn, source_port, target_urn, target_port)`. Multiple wires between the same two nodes are allowed as long as ports differ — this makes it a **hypergraph** (König-encoded: every wire IS a node in the mathematical sense, with typed half-edges called ports).

### The Four Operations (Natural Transformations)

**Every** mutation to the graph is one of exactly four operations. No exceptions.

| Operation  | What it does                                 | Python analogy                                               |
| ---------- | -------------------------------------------- | ------------------------------------------------------------ |
| **ADD**    | Create a new node                            | `nodes[urn] = Node(...)`                                     |
| **LINK**   | Create a wire between two existing nodes     | `wires[key] = Wire(...)`                                     |
| **MUTATE** | Update a node's payload (with version check) | `nodes[urn] = nodes[urn]._replace(payload=new, version=v+1)` |
| **UNLINK** | Remove a wire                                | `del wires[key]`                                             |

Why exactly four? These are the **natural transformations** of the graph category.
They correspond to the minimal complete set of structure-preserving operations on
a typed directed hypergraph. Any graph mutation decomposes into a sequence of
these four. You cannot express "swap two nodes" or "move a wire" — those are
programs (sequences of these primitives).

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

This is a **sum type** (tagged union / discriminated union). Exactly one payload
field is set per envelope, determined by `type`. In Haskell:
`data Envelope = Add AddPayload | Link LinkPayload | Mutate MutatePayload | Unlink UnlinkPayload`.
In Go, we model this with a struct + nil checks.

The `actor` is always required — every operation has provenance.

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

Formally, a Program is a morphism in the **free category** generated by the NTs. The atomic semantics means the fold either advances the state by the whole program or stays put — there's no observable intermediate state.

### The Morphism Log (Event Sourcing)

Every successfully applied envelope is appended to the **morphism log** — a timestamped, immutable, append-only sequence:

```python
@dataclass
class PersistedEnvelope:
    envelope: Envelope
    issued_at: datetime
```

The log IS the source of truth. The current graph state is a **computed projection** of the log.

Categorically, the log is the **free monoid** over the set of natural transformations.
"Free" means: you can only append. No edits, no deletes, no reordering.
"Monoid" means: the empty log is the identity element, and concatenation is the
binary operation. Replay is the unique homomorphism from the free monoid to the
carrier algebra (the graph state).

### The Fold (Catamorphism)

The fold is the pure function that replays the log into state:

```python
def replay(log: list[PersistedEnvelope]) -> GraphState:
    state = GraphState(nodes={}, wires={})
    for entry in log:
        state = evaluate(state, entry.envelope, entry.issued_at)
    return state
```

The name **catamorphism** (Greek: *cata-* = downward) means "a fold that
destructs a recursive data structure." Here the recursive structure is the log,
and the fold destructs it into a flat graph state. The symbol is **Σ** (sigma —
summation, accumulation).

Key property: **initial algebra**. The empty graph state `{nodes: {}, wires: {}}`
is the initial object in the category of algebras over the log's endofunctor.
The fold is the unique morphism from this initial algebra to the carrier. This
uniqueness guarantees determinism — there is exactly one way to replay a log.

In the Go code, this lives in the `fold` package. **Critical rule:** the fold package has ZERO file I/O, ZERO network calls, ZERO concurrency primitives. It is a pure function: `state_in → state_out`, nothing else.

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
    # ... more kinds derived from ontology.json
}
```

Why "operad"? An **operad** is a structure that describes multi-input operations
and how they compose. In mo:os, each Kind's ports define typed input/output
arities, and the registry's link validation rules define admissible compositions.
Think of it as: "which plugs fit into which sockets."

The registry is loaded from `ontology.json` at boot. The kernel ships a copy at
`kernel/registry/ontology.json` for tests and new contributors. In production,
the config points to wherever the registry lives.

When present, the fold **rejects** operations that violate the type constraints
(wrong Kind, wrong port direction, etc.). Without a registry, all operations are
permitted — the kernel runs "untyped."

### Functors (Read-Path Projections)

A **functor** transforms the graph state into a different representation for consumption.

| Functor          | What it produces                                          | Status                                      |
| ---------------- | --------------------------------------------------------- | ------------------------------------------- |
| **UI_Lens**      | `{nodes: [...], edges: [...]}` for rendering in a browser | Mocked (deterministic hash-based positions) |
| **Embedder**     | 1536-dim vectors for each node (for similarity search)    | Mocked (deterministic from URN hash)        |
| **StructureMap** | Topological sort / DAG layering                           | Mocked (alphabetical sort)                  |

Why "functor"? In category theory, a functor is a **structure-preserving map
between categories**: F: C → D. It maps objects to objects and morphisms to
morphisms while preserving composition and identities. Here, the UI_Lens maps
graph nodes to UI nodes and wires to UI edges, preserving connectivity.

**Key rule:** Functor output is NEVER ground truth. It's a disposable projection. You can always recompute it from the graph state. This is the **S4 invariant** — projections live at stratum S4 and are ephemeral by definition.

---

## Package-by-Package Walkthrough

### `cat/` — Category Types

**7 files, 0 external dependencies.**

This is the data model — all value types, no behavior. Think of it as `models.py` if every model were a frozen dataclass with no database connection.

| File          | What it defines                                                                  |
| ------------- | -------------------------------------------------------------------------------- |
| `object.go`   | `URN`, `Kind`, `Port`, `Stratum`, `Node` — with S0–S4 constants                 |
| `wire.go`     | `Wire` struct + `WireKey()` composite key function                               |
| `envelope.go` | `MorphismType` (ADD/LINK/MUTATE/UNLINK), `Envelope` with `.Validate()`           |
| `payload.go`  | `AddPayload`, `LinkPayload`, `MutatePayload`, `UnlinkPayload`                   |
| `program.go`  | `Program`, `EvalResult`, `ProgramResult`, `PersistedEnvelope`                    |
| `state.go`    | `GraphState` (map of Nodes + map of Wires), with `.Clone()` deep copy            |
| `errors.go`   | 15 sentinel errors: `ErrNodeExists`, `ErrWireExists`, `ErrVersionConflict`, etc. |

### `fold/` — Pure Catamorphism

**3 source files, 2 test files. 8 tests.**

The mathematical core. Pure functions only — no I/O.

| Function                       | Signature (conceptual)                        | What it does                             |
| ------------------------------ | --------------------------------------------- | ---------------------------------------- |
| `Evaluate()`                   | `(state, envelope, time) → result`            | Apply one operation                      |
| `EvaluateWithRegistry()`       | `(state, envelope, time, registry?) → result` | Apply one operation with type checking   |
| `EvaluateProgram()`            | `(state, program, time) → result`             | Atomic batch (rollback on failure)       |
| `EvaluateProgramWithRegistry()`| `(state, program, time, registry?) → result`  | Atomic batch with type checking          |
| `Replay()`                     | `(log) → state`                               | Full rebuild: `reduce(evaluate, log, ∅)` |
| `ReplayWithRegistry()`         | `(log, registry?) → state`                    | Full rebuild with type checking          |

**Purity guarantee:** If you grep this package for `os.`, `net.`, `sync.`, or `http.` — you will find nothing. This guarantee is enforced at review time.

### `operad/` — Type System

**4 files. 2 tests.** Loaded from `ontology.json` at boot.

The operad validates operations against the type system:

- **ADD validation:** Is the Kind registered? Is the stratum allowed?
- **MUTATE validation:** Is the Kind mutable? Does the version match?
- **LINK validation:** Does the source port exist on the source Kind? Is the direction correct? Is the target Kind an admissible target?

Key design decision: `LoadRegistry(data []byte)` takes raw bytes, not a file path.
The caller (main.go) reads the file; the operad package never touches the
filesystem. This means the operad is **testable with inline JSON** and has no
implicit dependency on the working directory.

The registry is derived from the Knowledge Base ontology using
`DeriveFromOntology()`. It automatically injects `Kernel` and `Feature` Kinds
if they're not explicitly defined in the ontology.

### `shell/` — Effect Boundary

**4 source files, 1 test file. 5 tests.** This is where purity ends and the real world begins.

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

Two Store implementations:

| Store      | Use case                                     |
| ---------- | -------------------------------------------- |
| `MemStore` | Tests — ephemeral, in-memory                 |
| `LogStore` | Default — JSONL file at configured log_path  |

The Store interface is preserved for future backends (Postgres, SQLite, etc.)
but the kernel ships with zero external dependencies.

### `functor/` — Read-Path Projections

**4 source files, 1 test file. 3 tests.** All mocked for the MVP.

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

### `transport/` — HTTP API

**3 source files, 1 HTML template, 1 test file. 9 tests.** All HTTP endpoints.

The explorer HTML is embedded at compile time via Go's `embed.FS` and rendered
with `html/template`. No Go string constants, no `fmt.Sprintf` with `%s`. The
template receives the UI_Lens projection as `template.JS` — properly escaped.

### `hydration/` — Batch Materialization

**1 source file, 1 test file. 3 tests.** Converts a declarative JSON manifest into a `Program`:

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

**1 source file, 1 test file. 8 tests.**

A pure JSON parser. No environment variables. No defaults. No path walking.

```go
func LoadFromFile(path string) (Config, error)  // read + parse + validate
func Parse(data []byte) (Config, error)          // parse + validate (testable)
```

The `Parse` function is exported so tests can validate config parsing without
touching the filesystem.

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

This is the **onion architecture** in practice: pure core (`fold`) wrapped by
effect shell (`shell`) wrapped by transport (`transport`). Side effects can only
flow inward through well-typed interfaces.

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

All endpoints return JSON. Port is specified in config.

### Health & State

| Method | Path                          | Description                                                               |
| ------ | ----------------------------- | ------------------------------------------------------------------------- |
| `GET`  | `/healthz`                    | Health check: `{"status": "ok", "nodes": N, "wires": M, "log_depth": L}` |
| `GET`  | `/state`                      | Full graph state (all nodes + all wires)                                  |
| `GET`  | `/state/nodes`                | All nodes as a map `{urn: node}`                                          |
| `GET`  | `/state/nodes/{urn}`          | Single node by URN (404 if missing)                                       |
| `GET`  | `/state/wires`                | All wires as a map `{key: wire}`                                          |
| `GET`  | `/state/wires/outgoing/{urn}` | Wires leaving a node                                                      |
| `GET`  | `/state/wires/incoming/{urn}` | Wires entering a node                                                     |

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
| `GET`  | `/explorer`           | Interactive HTML graph explorer  |

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

The kernel takes a single `--config` flag pointing to a JSON file.
**No environment variables. No defaults. No magic path detection.**

```json
{
  "store_type": "file",
  "log_path": "/absolute/path/to/morphism-log.jsonl",
  "registry_path": "/absolute/path/to/registry/ontology.json",
  "listen_addr": ":8000",
  "seed": [
    {
      "actor": "urn:moos:kernel:self",
      "envelopes": [
        {"type": "ADD", "add": {"urn": "urn:moos:kernel:wave-0", "kind": "Kernel", "stratum": "S2"}}
      ]
    }
  ]
}
```

| Field           | Required | Description                                                    |
| --------------- | -------- | -------------------------------------------------------------- |
| `store_type`    | Yes      | `"file"` or `"memory"`                                         |
| `log_path`      | If file  | Absolute path to JSONL morphism log                            |
| `registry_path` | No       | Absolute path to `ontology.json`. Omit to run without types.   |
| `listen_addr`   | Yes      | HTTP listen address (e.g. `":8000"`, `"127.0.0.1:9000"`)      |
| `seed`          | No       | Array of Program JSON objects. Applied idempotently on boot.   |

If any required field is missing, the kernel fails immediately with a clear error.
No partial boot. No "I'll guess what you meant."

---

## Running Locally

```bash
# From the repository root
cd kernel

# Create a config file (NOT committed — contains absolute paths)
cat > /tmp/moos-dev.json << 'EOF'
{
  "store_type": "file",
  "log_path": "/tmp/moos/morphism-log.jsonl",
  "registry_path": "/absolute/path/to/kernel/registry/ontology.json",
  "listen_addr": ":8000",
  "seed": [
    {
      "actor": "urn:moos:kernel:self",
      "envelopes": [
        {"type": "ADD", "add": {"urn": "urn:moos:kernel:self", "kind": "Actor", "stratum": "S2", "payload": {"label": "Kernel Self-Actor"}}},
        {"type": "ADD", "add": {"urn": "urn:moos:kernel:wave-0", "kind": "Kernel", "stratum": "S2", "payload": {"label": "mo:os Kernel — Wave 0"}}}
      ]
    }
  ]
}
EOF

# Run the kernel
go run ./cmd/moos --config /tmp/moos-dev.json
# → [boot] store=file addr=:8000
# → [boot] registry loaded: 17 kinds from .../ontology.json
# → [shell] replayed 0 morphisms → 0 nodes, 0 wires
# → [seed] applied 1 programs → 2 nodes, 0 wires
# → [transport] listening on :8000

# Open the explorer
# → http://localhost:8000/explorer

# Verify health
curl http://localhost:8000/healthz
# → {"status": "ok", "nodes": 2, "wires": 0, "log_depth": 2}
```

To **reset** state, delete the morphism log file:

```bash
rm /tmp/moos/morphism-log.jsonl
# Restart → clean slate, seeds re-apply
```

For ephemeral testing (state vanishes on exit):

```json
{"store_type": "memory", "listen_addr": ":8000"}
```

---

## Testing

```bash
cd kernel

# Run all tests (38 tests)
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

### What's tested (38 tests total)

| Package     | Tests | What they cover                                                             |
| ----------- | ----- | --------------------------------------------------------------------------- |
| `config`    | 8     | Valid parse, memory store, missing fields, invalid store type, seed, JSON   |
| `fold`      | 8     | All 4 operations, duplicate rejection, version conflicts, atomicity, replay |
| `functor`   | 3     | UILens projection, embedder determinism, structure map ordering             |
| `hydration` | 3     | Basic materialize, missing actor, dry run                                   |
| `operad`    | 2     | Loading from real ontology.json, ADD validation                             |
| `shell`     | 5     | Apply, SeedIfAbsent, replay on restart, programs, wire queries              |
| `transport` | 9     | All HTTP endpoints, error responses, content types                          |

---

## Common Tasks

### "I need to add a new Kind of node"

1. Add the Kind to `registry/ontology.json` (or your workspace's copy)
2. Define its ports (connections to other Kinds)
3. Restart the kernel — the operad loader derives the new Kind automatically

### "I need to add a new HTTP endpoint"

1. Add a handler method on `*Server` in `transport/server.go`
2. Register the route in `registerRoutes()`
3. Add a test in `transport/server_test.go`

### "I need to integrate a real LLM"

Implement a `Provider` interface in a new package, wire it into `main.go`.
The kernel doesn't ship a provider — it's an extension point.

### "I need to add a new functor"

1. Implement the `functor.Projector` interface
2. Add a new handler in the transport layer
3. The mock version returns deterministic data for testing

### "I want to add seed data for my workspace"

Add Programs to the `seed` array in your `config.json`. They're applied
idempotently — existing nodes/wires are silently skipped.

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
| **Initial Algebra**             | `(GraphState, evaluate)`                      | The reduce function + its zero value  |
| **Carrier Algebra**             | The current GraphState                        | The computed result of reduce         |
| **Free Monoid**                 | The morphism log (append-only)                | A Python list you only `.append()` to |
| **Operad**                      | The type system (multi-input typed ops)        | Pydantic validators with port arities |
| **Colored Operad**              | Operad where each input/output has a type     | Validators that match plug → socket   |
| **Functor**                     | A read-only transform: `state → something`    | A pure function from state to view    |
| **Kind**                        | A node type classification                    | A string enum or union type           |
| **Port**                        | A named, typed connection point on a Kind     | A specific field in a relationship    |
| **Stratum**                     | Hydration level (S0–S4)                       | A processing stage / maturity label   |
| **URN**                         | Unique identifier                             | A string primary key                  |
| **Program**                     | An atomic batch of envelopes                  | A database transaction                |
| **Wire Key**                    | 4-tuple composite key for wires               | A tuple used as a dict key            |
| **Hypergraph**                  | Multiple edges between same nodes (via ports) | A multigraph                          |
| **König encoding**              | Wires as nodes with half-edges (ports)        | Normalizing M:N → two 1:N tables      |
| **Sum type / tagged union**     | Envelope: one of four payload variants         | `Union[Add, Link, Mutate, Unlink]`    |

---

## Architecture Invariants

These rules are always true. If code violates any of them, it's a bug:

1. **The fold is pure.** The `fold/` package makes zero I/O calls. Ever.
2. **State is reconstructible.** `replay(log) == current_state`. Always.
3. **Only four operations.** ADD, LINK, MUTATE, UNLINK. Nothing else modifies state.
4. **Actor is required.** Every operation has provenance — who did this.
5. **Functor output is never truth.** It's a disposable projection. Recompute anytime.
6. **Programs are atomic.** All-or-nothing. Partial application is impossible.
7. **The log is append-only.** You never edit, delete, or reorder log entries.
8. **Reads don't block writes (mostly).** RWMutex: concurrent reads, exclusive writes.
9. **Seeds are idempotent.** Restarting the kernel re-seeds; no duplicates, no errors.
10. **The registry is loaded, not hardcoded.** Type rules come from `ontology.json`, not Go code.
11. **The kernel knows nothing.** No env vars, no path discovery, no workspace assumptions. Config in, behavior out.
12. **Zero external dependencies.** The `go.mod` has no `require` block. Stdlib only.
