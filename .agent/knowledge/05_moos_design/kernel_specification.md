# mo:os — Greenfield Kernel Specification

> Bridges normalization decisions → concrete implementation.
> Status: **Active design** — candidate material for promotion into `01_foundations` and `02_architecture`.
> Depends on: `normalization_and_migration.md`, `strata_and_authoring.md`, `semantic_layer_rebuild.md`.
>
> **Related**: `strata_and_authoring.md` Part 6 (hypergraph computation model),
> `hydration_lifecycle.md` §11 (multi-path evaluation), `papers/wolfram_hdc_digest.md`.
> **Cross-provider**: §14 (provider category mapping), `foundations.md` §9, `architecture.md` §12.
> **Category Registry**: `foundations.md` §21 (formalization levels for all named categories).

---

## §1 — Purpose

This document specifies what the greenfield `moos` kernel IS as a
concrete system, translating categorical foundations and normalization
decisions into implementable structures. It is the contract between
knowledge and code.

**Guiding constraint:** The kernel is a **pure morphism evaluator** with
explicit effect boundaries. Everything that is not morphism evaluation
is an effect adapter around the pure core.

---

## §2 — The Pure Core / Effect Boundary Split

The single most important architectural decision for the greenfield
kernel.

### Pure Core (zero side effects)

The pure core is a function:

```
evaluate : (Envelope, GraphState) → (GraphState', [Effect])
```

It takes a morphism envelope and the current graph state, and produces
the next graph state plus a list of effects to be interpreted by the
shell. The pure core:

- Validates envelope syntax (well-formed, correct type, required fields present)
- Checks version consistency (CAS for MUTATE)
- Checks permission reachability (wire existence = permission)
- Checks structural invariants (no duplicate 4-tuple for LINK, URN existence for MUTATE)
- Computes the state transition (what the graph looks like after this morphism)
- Emits effects (log append, cache invalidation, embedding recompute trigger, notification)

The pure core **never**:
- Touches the database
- Makes network calls
- Reads the filesystem
- Writes to stdout/stderr
- Accesses the clock (time is an input, not a side effect)

### Effect Shell (managed side effects)

The effect shell interprets the effect list produced by the pure core:

```
interpret : [Effect] → IO ()
```

Effect types the shell must handle:

| Effect | Interpretation |
| --- | --- |
| `LogAppend(entry)` | INSERT INTO morphism_log |
| `ContainerWrite(urn, state)` | UPSERT containers cache |
| `WireWrite(wire)` | INSERT INTO wires cache |
| `WireDelete(wire)` | DELETE FROM wires cache |
| `EmbeddingRecompute(urn)` | Queue for embedding functor |
| `Notify(channel, event)` | Push to WebSocket/SSE subscribers |
| `MetricIncrement(name, labels)` | Prometheus counter/histogram |

### Why This Split Matters

1. **Testability**: The pure core can be tested with zero infrastructure — pass in state, get back state.
2. **Replay correctness**: The pure core IS $\Sigma$ — the reducer that folds morphism log to state. If it's pure, replay is deterministic.
3. **Composition guarantee**: Pure functions compose. Effect-laden functions don't (their composition depends on execution order of side effects).
4. **Provider independence**: The effect shell is the ONLY place where concrete infrastructure appears. Swap Postgres for SQLite, swap Anthropic for Gemini — the pure core doesn't change.

### Categorical Interpretation

The pure core IS the evaluation functor $F_{\text{eval}} : \mathbf{Syn} \to \mathbf{Sem}$
from foundations §13 (Lawvere's functorial semantics). `Envelope` is a
morphism in the syntax category. `GraphState` is an object in the
semantics category. `Evaluate` is the functor's action on morphisms:

$$F_{\text{eval}}(e : S \to S') = \texttt{Evaluate}(e, S) = (S', [\text{effects}])$$

The effect list is the **free monoid** $\text{Free}(\Sigma)$ over the
effect alphabet $\Sigma = \{$ LogAppend, ContainerWrite, WireWrite,
WireDelete, EmbeddingRecompute, Notify, MetricIncrement $\}$. The shell
interpreter is the unique monoid homomorphism $h : \text{Free}(\Sigma) \to \texttt{IO}$
— the universal property guarantees that adding new effect types extends
the interpreter without modifying existing arms.

Composition of `Evaluate` over a sequence of envelopes is the `Program`
type (§8.1) — a catamorphism (fold) over the free monoid of morphisms.

### Go Realization

```go
// Pure core — no database, no network, no clock
package core

type EvalResult struct {
    NextState   GraphState
    Effects     []Effect
    Diagnostics []Diagnostic  // validation warnings, not errors
}

func Evaluate(env Envelope, state GraphState, now time.Time) (EvalResult, error) {
    // Returns error only for malformed envelopes (syntax failure)
    // Structural violations are Diagnostics, not panics
}

// Effect shell — interprets effects against real infrastructure
package shell

type Interpreter struct {
    db       persistence.Store
    notifier notify.Broadcaster
    metrics  prometheus.Registerer
    embedQ   chan<- string  // URN queue for async embedding
}

func (i *Interpreter) Run(ctx context.Context, effects []Effect) error {
    // Executes effects in order, wraps in transaction where needed
}
```

---

## §3 — GraphState: The In-Memory Evaluation Target

The pure core operates on `GraphState`, not raw SQL. This is the
materialized view of the graph that the reducer needs.

```go
type GraphState struct {
    Objects map[URN]*Object     // All known objects
    Wires   *WireIndex          // Indexed by source, target, port
    Clock   time.Time           // Injected, not read from OS
}

type Object struct {
    URN           URN
    Kind          Kind              // Typed, not raw string
    Stratum       Stratum           // 0, 1, 2 (stratum 3 is never stored)
    InterfaceSpec json.RawMessage   // Port vocabulary / schema
    Payload       json.RawMessage   // The state_payload (cache of log)
    Permissions   PermissionSet     // Resolved from wires, cached
    Version       int64
}

type WireIndex struct {
    bySource map[URN][]Wire         // Fan-out (coslice)
    byTarget map[URN][]Wire         // Fan-in (slice)
    by4Tuple map[Wire4Tuple]Wire    // Uniqueness check
}

type Wire struct {
    SourceURN  URN
    SourcePort Port
    TargetURN  URN
    TargetPort Port
    Config     json.RawMessage     // wire_config (temporal, env, conditions)
    Stratum    Stratum
}
```

### Loading Strategy

GraphState is not the entire database. It is a **scoped snapshot** loaded
for a specific evaluation context:

1. **Scope identification**: Determine which subcategory $\mathcal{C}_W$ the morphism operates within
2. **Transitive load**: Load all objects and wires within that subcategory (OWNS-recursive CTE)
3. **Permission expansion**: Load permission wires (CAN_HYDRATE) relevant to the actor
4. **Freeze**: The loaded GraphState is immutable during evaluation — the pure core cannot trigger additional loads

This scoped loading maps to the topological context requirement from
foundations §9 and §14: an evaluation is always performed within a
specific subgraph, and that subgraph is the evaluation's identity.

### Immutability Contract

`GraphState` produced by `Evaluate` is a **new value** — the function
MUST NOT mutate its input. In Go this means:

- **Objects map**: New map with shared `*Object` pointers for unchanged
  objects, fresh `*Object` for modified/created ones (structural sharing).
- **WireIndex**: New index maps for modified dimensions, shared slices
  for unchanged fan-out/fan-in sets.
- **No persistent data structure library** required — plain Go maps with
  copy-on-write discipline at the `Evaluate` boundary.

The shell MUST deep-copy `GraphState` at the API boundary before passing
to the pure core (go-defensive: copy slices and maps at boundaries). The
pure core returns a separate value; the shell never observes partial
mutation.

This is the Go realization of the FP principle: **immutability eliminates
entire categories of bugs** (referential transparency of `Evaluate`).

---

## §4 — Stratum Realization in Schema

The four strata from `strata_and_authoring.md` become concrete schema
discriminators.

### Stratum Column

```sql
ALTER TABLE containers ADD COLUMN stratum smallint NOT NULL DEFAULT 2;
-- 0 = bootstrap/evaluator substrate
-- 1 = canonical authoring syntax
-- 2 = user-visible operational graph
-- (3 = projection, never stored)

ALTER TABLE wires ADD COLUMN stratum smallint NOT NULL DEFAULT 2;
```

### Stratum 0 — Bootstrap Substrate

Seeded on first migration. Never created by user morphisms. Protected
from MUTATE/UNLINK by kernel policy (not permission wires — hard rule).

| Object | Kind | Purpose |
| --- | --- | --- |
| Morphism algebra declaration | `_S0_ALGEBRA` | Declares ADD/LINK/MUTATE/UNLINK as the invariant set |
| Log truth contract | `_S0_LOG_CONTRACT` | Declares morphism_log as ground truth |
| Identity primitive | `_S0_IDENTITY` | Declares URN as opaque identity |
| Version primitive | `_S0_VERSION` | Declares CAS version protocol |
| Evaluator reference | `_S0_EVALUATOR` | Points to the kernel reducer pipeline |

Stratum 0 is *about* 5-10 objects. It should never grow beyond ~20.

### Stratum 1 — Authoring Syntax

Created by the FP authoring pipeline or manual declaration. Validated
against Stratum 0 rules before materialization into Stratum 2.

| Object type | Kind pattern | Purpose |
| --- | --- | --- |
| Category declaration | `_S1_CATEGORY` | Declares a named category |
| Object inventory | `_S1_OBJECT_INV` | Lists objects in a category |
| Morphism signature | `_S1_MORPHISM_SIG` | Declares allowed morphism shapes |
| Functor declaration | `_S1_FUNCTOR` | Declares a structure-preserving map |
| Port vocabulary | `_S1_PORT_VOCAB` | Declares typed port names and schemas |
| Schema declaration | `_S1_SCHEMA` | JSON Schema for payload validation |
| Governance policy | `_S1_POLICY` | Permission/lifecycle rules |
| Bootstrap preset | `_S1_PRESET` | Platform/install configuration template |

Stratum 1 objects ARE the ontology in syntax form. They are *about* the
graph, not *in* the operational graph.

### Stratum 2 — Operational Graph

Created by user/agent morphisms. This is where workspaces, documents,
tools, sessions, agents, and all runtime objects live.

| Object type | Kind pattern | Purpose |
| --- | --- | --- |
| Purpose anchor | `purpose` | Root semantic anchor (replaces RootContainer) |
| Workspace | `workspace` | Scoped full subcategory (§6 of foundations) |
| Document | `document` | Content-bearing syntax object |
| Tool resource | `tool` | Code-bearing evaluable capability |
| Agent actor | `agent` | Evaluated semantic actor subgraph |
| Session | `session` | Conversation lifecycle container |
| Message | `message` | Single exchange within session |
| Provider | `provider` | Benchmarkable external capability source |
| Model | `model` | Provider-scoped evaluable coprocessor |
| Group | `group` | Governance/permission distribution |
| User identity | `identity` | Auth user as graph object |

Kind values in Stratum 2 are open — new kinds are created by promoting
Stratum 1 category declarations.

### Stratum 3 — Projection (Never Stored)

Computed by functors, held in memory or external systems:

- React virtual DOM (UI_Lens functor output)
- Embedding vectors (stored in `embeddings` table, not `containers`)
- Compressed DAGs (Structure functor output in GPU memory)
- Benchmark results (stored in evaluation-specific tables)
- API response bodies (transport serialization, ephemeral)

---

## §5 — The Envelope Contract

Every morphism enters the kernel as an Envelope. This is the syntax
object that the pure core evaluates.

```go
type Envelope struct {
    ID        string          `json:"id"`        // Client-generated idempotency key
    Type      MorphismType    `json:"type"`      // ADD | LINK | MUTATE | UNLINK
    ActorURN  URN             `json:"actor_urn"` // Who is performing this
    ScopeURN  URN             `json:"scope_urn"` // Which subcategory context
    IssuedAt  time.Time       `json:"issued_at"` // Client timestamp (kernel also records commit time)
    Stratum   Stratum         `json:"stratum"`   // Target stratum (default 2)

    Add    *AddPayload    `json:"add,omitempty"`
    Link   *LinkPayload   `json:"link,omitempty"`
    Mutate *MutatePayload `json:"mutate,omitempty"`
    Unlink *UnlinkPayload `json:"unlink,omitempty"`
}

type AddPayload struct {
    URN           URN             `json:"urn"`            // Optional: kernel generates if empty
    Kind          Kind            `json:"kind"`
    ParentURN     *URN            `json:"parent_urn"`     // Implicit LINK(parent, child, "owns", "owned_by")
    InterfaceSpec json.RawMessage `json:"interface_spec"`
    Payload       json.RawMessage `json:"payload"`
}

type LinkPayload struct {
    SourceURN  URN             `json:"source_urn"`
    SourcePort Port            `json:"source_port"`
    TargetURN  URN             `json:"target_urn"`
    TargetPort Port            `json:"target_port"`
    Config     json.RawMessage `json:"config,omitempty"` // wire_config
}

type MutatePayload struct {
    URN             URN             `json:"urn"`
    ExpectedVersion int64           `json:"expected_version"`
    Patch           json.RawMessage `json:"patch"`           // Merged into payload
}

type UnlinkPayload struct {
    SourceURN  URN  `json:"source_urn"`
    SourcePort Port `json:"source_port"`
    TargetURN  URN  `json:"target_urn"`
    TargetPort Port `json:"target_port"`
}
```

### Validation Rules (Pure Core)

| Rule | Morphism | Check |
| --- | --- | --- |
| Envelope has exactly one payload | All | `Add XOR Link XOR Mutate XOR Unlink` |
| URN exists | MUTATE, UNLINK | Object lookup in GraphState |
| URN does not exist | ADD | Uniqueness check in GraphState |
| Version matches | MUTATE | `state.Objects[urn].Version == expected` |
| 4-tuple unique | LINK | Wire not already in WireIndex |
| 4-tuple exists | UNLINK | Wire found in WireIndex |
| Actor has permission | LINK, MUTATE, UNLINK | CAN_HYDRATE wire from actor to scope |
| Stratum protection | All on Stratum 0 | Rejected unless actor is `_S0_EVALUATOR` |
| Kind registered | ADD | Kind exists as Stratum 1 `_S1_CATEGORY` or is a Stratum 0 kind |

---

## §6 — Module Layout for Greenfield Repo

```
moos/
├── go.mod
├── go.sum
├── cmd/
│   └── moos/
│       └── main.go              # Assembly only: wires core + shell + transports
├── core/                        # PURE — zero imports from shell/
│   ├── types.go                 # URN, Kind, Port, Stratum, MorphismType
│   ├── envelope.go              # Envelope, payloads, validation
│   ├── state.go                 # GraphState, Object, Wire, WireIndex
│   ├── evaluate.go              # evaluate(Envelope, GraphState) → (GraphState, []Effect)
│   ├── effects.go               # Effect type definitions
│   └── evaluate_test.go         # Pure tests — no DB, no network
├── shell/                       # EFFECTS — imports core/, never imported by core/
│   ├── interpreter.go           # Effect interpreter (DB, notify, metrics)
│   ├── loader.go                # Scoped GraphState loader (SQL → core.GraphState)
│   ├── persistence.go           # DB adapter (pgx/v5)
│   ├── persistence_test.go      # Integration tests (testcontainers)
│   └── transaction.go           # Multi-effect transaction wrapper
├── transport/                   # EFFECTS — imports core/ for types only
│   ├── http.go                  # Chi router, REST endpoints
│   ├── websocket.go             # gorilla/websocket gateway
│   ├── mcp.go                   # MCP/SSE bridge
│   └── middleware.go            # Auth, logging, metrics middleware
├── provider/                    # EFFECTS — LLM adapters
│   ├── dispatch.go              # Provider multiplexer
│   ├── anthropic.go             # Anthropic adapter
│   ├── openai.go                # OpenAI adapter
│   └── types.go                 # Message, CompletionResult, Chunk
├── session/                     # EFFECTS — session lifecycle
│   ├── manager.go               # Session state machine
│   └── store.go                 # Session persistence adapter
├── tool/                        # EFFECTS — tool registry and dispatch
│   ├── registry.go              # Tool definitions
│   ├── runner.go                # Execution dispatcher
│   └── policy.go                # Execution policy
├── migrate/                     # EFFECTS — schema migrations
│   ├── runner.go
│   └── migrations/
│       ├── 0001_strata_core.sql          # Stratum 0 + 1 bootstrap
│       ├── 0002_operational_graph.sql     # Stratum 2 tables
│       └── 0003_embeddings.sql           # pgvector
└── seed/                        # Stratum 0 seed data
    └── bootstrap.go             # Creates the ~10 Stratum 0 objects
```

### Dependency Rule (ENFORCED)

```
core/ ← shell/ ← transport/
core/ ← shell/ ← provider/
core/ ← shell/ ← session/
core/ ← shell/ ← tool/

core/ imports NOTHING from shell/, transport/, provider/, session/, tool/
```

This is the Go equivalent of the hexagonal architecture / ports-and-adapters pattern, but derived from the categorical principle: the pure core is the evaluation functor $F_{\text{eval}}$, and everything else is infrastructure morphisms.

---

## §7 — Migration Strategy from FFS1

The greenfield repo does NOT import FFS1 code. It uses FFS1 as reference
only — see `normalization_and_migration.md` Part 2 for the
keep/reinterpret/discard matrix.

### What migrates conceptually (Keep)

| FFS1 Concept | Greenfield Location | Notes |
| --- | --- | --- |
| Morphism executor Apply/Add/Link/Mutate/Unlink | `core/evaluate.go` | Rewritten as pure function, not struct method with DB |
| MorphismLogRecord append | `shell/interpreter.go` LogAppend effect | Effect, not inline DB call |
| WireRecord 4-tuple model | `core/state.go` Wire type | Same structure, typed ports |
| Container Record fields | `core/state.go` Object type | Renamed, stratum-aware |
| Version CAS | `core/evaluate.go` MUTATE validation | Pure check against GraphState |
| TreeTraversal recursive CTE | `shell/loader.go` scoped load | SQL stays in shell, core sees loaded state |

### What does NOT migrate

- `container.Store` as a god-object (split into core types + shell persistence)
- Direct SQL in evaluation path (all SQL moves to shell)
- Session manager interleaved with morphism execution (clean boundary)
- Provider-specific code in kernel path (provider/ package)
- `main.go` as monolith (split into cmd/ assembly)

---

## §8 — Open Specifications (Blocking Design Decisions)

These must be resolved before implementation begins. Each is a concrete
question, not a philosophical one.

### 8.1 — Envelope Batching

**Question:** Should the kernel accept batch envelopes (multiple
morphisms in one request)?

**Current answer:** No. Single-morphism transactions (foundations §3:
atomicity). Composition is application-level semicolon, not kernel
transaction.

**Tension:** The session manager needs to apply LLM-proposed morphism
sequences atomically (all-or-nothing for a single agent turn). Without
batching, a partial sequence can corrupt the graph.

**Proposed resolution:** Introduce a `Program` type — an ordered list of
envelopes evaluated sequentially against accumulating state. The pure
core evaluates the full program or returns the first failure. The effect
shell commits all effects or none (single DB transaction).

```go
type Program struct {
    Envelopes []Envelope
    ActorURN  URN
    ScopeURN  URN
}

func EvaluateProgram(prog Program, state GraphState, now time.Time) (EvalResult, error) {
    // Fold: each envelope evaluated against the state produced by the previous
    // If any fails, return error and zero effects (nothing committed)
}
```

### 8.2 — Port Schema Validation

**Question:** Should LINK validate that source_port and target_port are
compatible (schema-checked)?

**Current answer:** Not yet — ports are untyped strings.

**Proposed resolution:** Stratum 1 `_S1_PORT_VOCAB` objects define
schemas for port names. LINK validation checks port compatibility when
both participating objects reference the same vocabulary. Untyped ports
(no vocabulary reference) are allowed during bootstrap/mock phases.

### 8.3 — Payload Merge Strategy for MUTATE

**Question:** Is MUTATE a full replacement or a JSON merge patch?

**Current FFS1:** Full replacement of `kernel_json`.

**Proposed resolution:** Support both via a `merge_strategy` field on
MutatePayload: `"replace"` (default) or `"merge_patch"` (RFC 7396).
The pure core applies the strategy deterministically.

### 8.4 — Clock Authority

**Question:** Who provides the timestamp — client or kernel?

**Proposed resolution:** Both. Envelope carries `issued_at` (client
timestamp). Kernel records `committed_at` (server timestamp injected
into pure core as parameter). Morphism log stores both. `committed_at`
is the ordering authority.

### 8.5 — URN Format

**Question:** What is the canonical URN format?

**Current FFS1:** `urn:moos:{kind}:{uuid}` — e.g., `urn:moos:session:abc123`.

**Proposed resolution:** Keep the format but enforce it in the pure
core:
```
urn:moos:{stratum}:{kind}:{uuid}
```
Example: `urn:moos:s2:workspace:550e8400-e29b-41d4-a716-446655440000`

This makes stratum membership visible in the URN itself — useful for
debugging and log reading. Stratum 0 URNs are hardcoded constants, not
generated.

---

## §9 — Error Taxonomy

*Derived from: go-error-handling (sentinel errors, structured types, wrapping policy).*

The pure core returns `error` as its last result. Callers must be able
to programmatically distinguish failure modes. Following Go convention,
errors are values — never panics.

### Sentinel Errors (Static, Matchable)

```go
package core

import "errors"

// Envelope syntax errors — malformed input, never retryable.
var (
    ErrEnvelopeEmpty       = errors.New("envelope has no payload")
    ErrEnvelopeAmbiguous   = errors.New("envelope has multiple payloads")
    ErrMorphismTypeUnknown = errors.New("unknown morphism type")
)

// Structural constraint violations — valid syntax, invalid against state.
var (
    ErrURNNotFound      = errors.New("object URN not found in graph state")
    ErrURNAlreadyExists = errors.New("object URN already exists in graph state")
    ErrVersionConflict  = errors.New("MUTATE version does not match current state")
    ErrWireDuplicate    = errors.New("LINK 4-tuple already exists in wire index")
    ErrWireNotFound     = errors.New("UNLINK 4-tuple not found in wire index")
)

// Permission violations — valid structure, insufficient actor authority.
var (
    ErrPermissionDenied = errors.New("actor lacks required wire to scope")
    ErrStratumProtected = errors.New("stratum 0 objects cannot be modified by non-evaluator actors")
)
```

### Structured Errors (Dynamic, Matchable)

When callers need both the failure kind AND contextual data:

```go
// VersionConflictError carries the current version for CAS retry.
type VersionConflictError struct {
    URN            URN
    ExpectedVersion int64
    ActualVersion   int64
}

func (e *VersionConflictError) Error() string {
    return fmt.Sprintf("version conflict on %s: expected %d, got %d",
        e.URN, e.ExpectedVersion, e.ActualVersion)
}

func (e *VersionConflictError) Is(target error) bool {
    return target == ErrVersionConflict
}

// PermissionError carries the actor and missing wire for diagnostics.
type PermissionError struct {
    ActorURN URN
    ScopeURN URN
    Required string // e.g., "can_hydrate"
}

func (e *PermissionError) Error() string {
    return fmt.Sprintf("actor %s lacks %s wire to scope %s",
        e.ActorURN, e.Required, e.ScopeURN)
}

func (e *PermissionError) Is(target error) bool {
    return target == ErrPermissionDenied
}
```

### Error Wrapping Policy

| Boundary | Verb | Rationale |
| --- | --- | --- |
| Pure core → caller | `%w` | Preserve error chain — callers use `errors.Is` |
| Shell → transport | `%w` | Transport maps to HTTP status codes via `errors.Is` |
| Transport → HTTP response | `%v` | Strip internal details at system boundary |
| Shell → metrics | `%v` | Error strings in Prometheus labels must be stable |

### Error Strings

Following Go convention: lowercase, no trailing punctuation.

```go
// Good
fmt.Errorf("evaluating ADD for %s: %w", env.Add.URN, err)

// Bad
fmt.Errorf("Failed to evaluate ADD for %s.", env.Add.URN)
```

### Error Flow in the Pure Core

`Evaluate` returns `error` only for **envelope syntax failures** (malformed
input that cannot be evaluated at all). Structural violations (URN not
found, version conflict, permission denied) are also errors — they abort
evaluation — but they carry structured context.

The pure core NEVER returns a partial `EvalResult` on error. If error is
non-nil, `EvalResult` is the zero value and must not be used.

---

## §10 — Concurrency Model

*Derived from: go-concurrency (goroutine lifetimes, sync primitives),
go-defensive (copy at boundaries, defer for cleanup).*

### Evaluation is Single-Threaded Per Scope

A morphism evaluation for scope $\mathcal{C}_W$ holds no locks during
the pure core phase. The concurrency model is **optimistic**:

1. **Load**: Shell loads `GraphState` via scoped SQL query (row-level
   shared lock, released immediately after load).
2. **Evaluate**: Pure core computes `(EvalResult, error)` on the loaded
   snapshot. No locks held. No database access.
3. **Commit**: Shell interprets effects inside a DB transaction.
   `ContainerWrite` uses optimistic CAS: `UPDATE ... WHERE version = $expected`.
   If CAS fails (concurrent writer committed first), the transaction
   rolls back and returns `ErrVersionConflict` to the caller.
4. **Retry**: Caller (session manager or transport) may reload and
   re-evaluate. The kernel does not auto-retry — retry policy is the
   caller's concern.

### Why Not Pessimistic Locking

Pessimistic locks (SELECT FOR UPDATE) would serialize all mutations to a
scope. Since evaluation is pure and typically fast (< 1ms), optimistic
locking with CAS retry is both simpler and more concurrent.

### Goroutine Lifetimes

Every goroutine in the kernel has an explicit shutdown mechanism:

| Goroutine | Owner | Shutdown Signal | Wait Mechanism |
| --- | --- | --- | --- |
| HTTP server | `cmd/moos/main.go` | `context.Context` cancellation | `server.Shutdown(ctx)` |
| WebSocket conn handler | `transport/websocket.go` | Client disconnect or context cancel | Handler function returns |
| Embedding recompute worker | `shell/interpreter.go` | Close `embedQ` channel | `sync.WaitGroup` |
| Notification broadcaster | `shell/interpreter.go` | `context.Context` cancellation | `sync.WaitGroup` |
| MCP SSE stream | `transport/mcp.go` | Client disconnect or context cancel | Handler function returns |

**No goroutine is fire-and-forget.** Every `go` statement is paired with
a shutdown path. Use `go.uber.org/goleak` in test teardown to verify.

### Channel Conventions

```go
// Embedding queue: buffered channel, closed on shutdown.
// Producer: effect interpreter. Consumer: embedding worker.
embedQ chan<- string // URN queue

// Notification fan-out: the broadcaster owns the channel.
// Subscribers receive via their own channel, registered at connect time.
type Broadcaster struct {
    mu     sync.RWMutex
    subs   map[string]chan<- Event
    ctx    context.Context
    cancel context.CancelFunc
}
```

### Mutex Discipline

- Zero-value mutexes only (`sync.Mutex{}`, never `new(sync.Mutex)`).
- `defer mu.Unlock()` immediately after `mu.Lock()`.
- Mutexes protect data, not code — document what they guard.
- Never hold a mutex across an `Evaluate` call (pure core is lock-free).

---

## §11 — Interface Contracts & Compile-Time Verification

*Derived from: go-interfaces (implicit satisfaction, generality, hide
implementation), go-defensive (compile-time interface checks).*

### Core Interfaces

The shell depends on abstract interfaces, not concrete types. This
enables testing the shell with in-memory fakes and swapping
infrastructure without touching the pure core.

```go
// persistence.Store — the shell's only contact with the database.
// Implementations: PGStore (production), MemStore (tests).
type Store interface {
    LoadGraphState(ctx context.Context, scopeURN core.URN) (core.GraphState, error)
    CommitEffects(ctx context.Context, effects []core.Effect) error
    AppendLog(ctx context.Context, entry core.LogEntry) error
}

// notify.Broadcaster — the shell's notification surface.
type Broadcaster interface {
    Publish(ctx context.Context, channel string, event Event) error
    Subscribe(ctx context.Context, channel string) (<-chan Event, func(), error)
}

// provider.LLM — the session manager's LLM contact point.
type LLM interface {
    Complete(ctx context.Context, req CompletionRequest) (<-chan Chunk, error)
}
```

### Compile-Time Verification

Every concrete type that implements an interface MUST have an assertion
at file scope (go-defensive: verify interface compliance):

```go
// shell/persistence.go
var _ persistence.Store = (*PGStore)(nil)

// shell/persistence_mem.go (test double)
var _ persistence.Store = (*MemStore)(nil)

// provider/anthropic.go
var _ provider.LLM = (*AnthropicAdapter)(nil)

// provider/openai.go
var _ provider.LLM = (*OpenAIAdapter)(nil)
```

If the concrete type drifts from the interface, compilation fails
immediately — not at test time, not at runtime.

### Interface Naming

Following Go convention (one-method → `-er` suffix):

| Interface | Method | Notes |
| --- | --- | --- |
| `Store` | multiple | Aggregate, not single-method — noun name |
| `Broadcaster` | `Publish` + `Subscribe` | Agent noun for the capability |
| `LLM` | `Complete` | Initialism, all caps |
| `Evaluator` | `Evaluate` | If the pure core is ever behind an interface |
| `Runner` | `Run` | Tool execution dispatch |

### Receiver Names

Per go-naming, receivers are short (1-2 letter) abbreviations, consistent
across all methods of a type:

| Type | Receiver | NOT |
| --- | --- | --- |
| `PGStore` | `s` | `store`, `this`, `pgStore` |
| `Interpreter` | `i` | `interp`, `self` |
| `Broadcaster` | `b` | `broadcaster` |
| `AnthropicAdapter` | `a` | `adapter`, `anthropic` |
| `GraphState` | `gs` | `state`, `graphState` |
| `Envelope` | `e` | `env`, `envelope` |
| `Object` | `o` | `obj`, `object` |

### Hide Implementation, Expose Interface

Constructors for shell components return interfaces, not concrete types
(go-interfaces: generality):

```go
// Good: Returns interface
func NewStore(pool *pgxpool.Pool) persistence.Store {
    return &PGStore{pool: pool}
}

// Bad: Returns concrete type
func NewStore(pool *pgxpool.Pool) *PGStore {
    return &PGStore{pool: pool}
}
```

**Exception**: The pure core types (`GraphState`, `Envelope`, `Object`,
`Wire`) are concrete structs, not interfaces. They are data — not
behavior behind an abstraction.

---

## §12 — Testing Architecture

*Derived from: go-testing (table-driven tests, cmp.Diff, no assertion
libraries, useful failure messages), go-style-core (simplicity).*

### No Assertion Libraries

The kernel uses only the standard library `testing` package plus
`github.com/google/go-cmp/cmp` for struct diffs. No testify, no
gomega, no assertion helpers.

Rationale (go-testing): assertion libraries fragment the developer
experience and produce unhelpful failure messages. `cmp.Diff` with
direction keys `(-want +got)` is universally readable.

### Pure Core Tests: Table-Driven Morphism Evaluation

```go
func TestEvaluate_ADD(t *testing.T) {
    base := newTestGraphState() // factory helper

    tests := []struct {
        name    string
        env     Envelope
        state   GraphState
        want    GraphState
        wantErr error
    }{
        {
            name:  "creates object with version 1",
            env:   addEnvelope("urn:moos:s2:doc:001", "document"),
            state: base,
            want:  withObject(base, "urn:moos:s2:doc:001", Object{Version: 1}),
        },
        {
            name:    "rejects duplicate URN",
            env:     addEnvelope("urn:moos:s2:doc:existing", "document"),
            state:   withObject(base, "urn:moos:s2:doc:existing", Object{Version: 1}),
            wantErr: ErrURNAlreadyExists,
        },
        {
            name:    "rejects stratum 0 from non-evaluator",
            env:     addEnvelopeWithStratum("urn:moos:s0:test:001", "_S0_TEST", 0),
            state:   base,
            wantErr: ErrStratumProtected,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Evaluate(tt.env, tt.state, testTime)
            if !errors.Is(err, tt.wantErr) {
                t.Fatalf("Evaluate(%s) error = %v, wantErr %v",
                    tt.name, err, tt.wantErr)
            }
            if err != nil {
                return
            }
            if diff := cmp.Diff(tt.want, got.NextState); diff != "" {
                t.Errorf("Evaluate(%s) state mismatch (-want +got):\n%s",
                    tt.name, diff)
            }
        })
    }
}
```

### Failure Message Convention

Every test failure includes: **function name**, **inputs**, **got**,
**want**. Format: `Func(inputs) = got, want expected`.

```go
// Good
t.Errorf("Evaluate(%q, %q) = %v, want %v", env.Type, env.Add.URN, got, want)

// Bad — missing inputs
t.Errorf("got %v, want %v", got, want)
```

### GraphState Comparison

`cmp.Diff` against full `GraphState` structs, with `cmpopts.IgnoreFields`
for non-deterministic fields (e.g., generated URNs when testing with
kernel-generated IDs):

```go
if diff := cmp.Diff(want, got.NextState,
    cmpopts.IgnoreFields(Object{}, "URN"),  // kernel-generated
); diff != "" {
    t.Errorf("state mismatch (-want +got):\n%s", diff)
}
```

### Shell Integration Tests: testcontainers

Shell tests spin up a real Postgres via testcontainers-go. No mocked SQL.

```go
func TestPGStore_CommitEffects(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test in short mode")
    }
    ctx := context.Background()
    pool := setupTestDB(t, ctx)  // testcontainers helper
    store := NewPGStore(pool)

    effects := []core.Effect{
        core.ContainerWrite{...},
        core.LogAppend{...},
    }
    if err := store.CommitEffects(ctx, effects); err != nil {
        t.Fatalf("CommitEffects() error = %v", err)
    }
    // Verify via direct SQL query...
}
```

### Goroutine Leak Detection

Every package that spawns goroutines includes a `TestMain` with goleak:

```go
func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

### Test Organization

| Package | Test Type | What it verifies |
| --- | --- | --- |
| `core/` | Unit (table-driven) | All 4 morphisms × all validation rules, pure |
| `core/` | Unit (property) | `Evaluate` is deterministic: same input → same output |
| `shell/` | Integration (testcontainers) | DB round-trips, CAS behavior, transaction atomicity |
| `transport/` | Integration (httptest) | HTTP → core → effects → response |
| `session/` | Integration | Message → LLM → morphism program → committed state |
| `cmd/moos/` | Smoke (docker) | Binary starts, health endpoint responds |

### Coverage Target

- `core/` — **100%** line coverage (it's pure and finite — no excuse)
- `shell/` — **90%+** (integration tests may miss edge cases in error recovery)
- `transport/` — **80%+** (middleware, routing, error mapping)
- Overall — **90%+** (measured by `go test -coverprofile`)

### Stratum Enum: Deliberate Zero-Value

The go-defensive skill prescribes starting enums at `iota + 1` so the
zero value signals "uninitialized." The `Stratum` type is a **deliberate
exception**: Stratum 0 means "bootstrap substrate" and IS a valid value.
The zero value is meaningful, not accidental.

```go
type Stratum uint8

const (
    StratumBootstrap   Stratum = 0 // S0 — deliberate zero
    StratumAuthoring   Stratum = 1 // S1
    StratumOperational Stratum = 2 // S2
    // S3 (projection) is never stored — no constant needed
)
```

`MorphismType` uses string constants (not iota) because they appear in
JSON envelopes and must be human-readable in logs:

```go
type MorphismType string

const (
    MorphismADD    MorphismType = "ADD"
    MorphismLINK   MorphismType = "LINK"
    MorphismMUTATE MorphismType = "MUTATE"
    MorphismUNLINK MorphismType = "UNLINK"
)
```

The zero value `MorphismType("")` is explicitly invalid and caught by
envelope validation (`ErrMorphismTypeUnknown`).

---

## §13 — Rewriting Semantics and Causal Invariance

*Derived from: Wolfram Physics Project (hypergraph rewriting, multiway
systems, causal invariance), `papers/wolfram_hdc_digest.md`.*

### Morphisms as Local Rewriting Rules

The `Evaluate` function implements a **hypergraph rewriting step**. Each
call to `Evaluate(env, state, t)` is a single rule application:

1. **Match**: The envelope specifies the rewriting pattern — which objects
   and wires are involved (URN targets, port types).
2. **Validate**: The pure core checks that the pattern matches actual
   graph state (object exists, stratum allows mutation, version matches).
3. **Replace**: The `EvalResult` describes the local graph change — new
   objects, new wires, modified payloads, removed wires.
4. **Record**: The effect list includes a `LogAppend` that records the
   rewriting step.

This is Wolfram's `{{x,y},{x,z}} → {{x,z},{x,w},{y,w},{z,w}}` applied
to the mo:os domain: the envelope IS the rule, the GraphState IS the
hypergraph, and `Evaluate` IS the rewriting engine.

### Causal Invariance Property

For two morphisms $m_1$ and $m_2$ that target **disjoint** subgraphs:

$$\text{Evaluate}(m_1, \text{Evaluate}(m_2, s, t), t') = \text{Evaluate}(m_2, \text{Evaluate}(m_1, s, t), t')$$

This is the **causal invariance** condition — the order of independent
rewriting steps does not affect the final state. The optimistic locking
model (§10) enforces this: concurrent commits succeed only when their
target subgraphs are disjoint (version vectors don't conflict).

**Testing causal invariance**: This is a property-based test. For any
two morphisms whose target URNs are disjoint, applying them in either
order must produce identical `GraphState`:

```go
func TestCausalInvariance(t *testing.T) {
    base := seedState()
    m1 := mutateEnvelope("urn:a", payload1)
    m2 := mutateEnvelope("urn:b", payload2)

    // Order 1: m1 then m2
    r1, err := Evaluate(m1, base, t0)
    require(t, err)
    r12, err := Evaluate(m2, r1.NextState, t1)
    require(t, err)

    // Order 2: m2 then m1
    r2, err := Evaluate(m2, base, t0)
    require(t, err)
    r21, err := Evaluate(m1, r2.NextState, t1)
    require(t, err)

    if diff := cmp.Diff(r12.NextState, r21.NextState); diff != "" {
        t.Errorf("causal invariance violated (-m1;m2 +m2;m1):\n%s", diff)
    }
}
```

### The Morphism Log as Causal Graph

Each entry in the morphism log records: **who** (actor), **what**
(morphism type + targets), **when** (timestamp), **from** (prior version).
The "from" field creates a partial order — a **causal graph** of
morphism events. Two entries are causally related if one's "from"
references the other's resulting version; they are causally independent
if neither references the other.

This causal graph is the mo:os analog of Wolfram's causal graph of
updating events. The replay guarantee ($\Sigma$ is a catamorphism,
§1 of foundations) means the causal graph determines the final state
regardless of the temporal ordering of independent events.

### Reachable State Space

The set of all graph states reachable from the current state via any
finite sequence of the four morphisms is the mo:os **state space**. In
Wolfram's terminology, this is a finite projection of the **ruliad** —
the entangled limit of all possible computations from all possible rules.

The four morphisms are computation-universal for graph transformations:
any target graph (on the same vertex set + any extensions) is reachable.
This universality means the state space branches exponentially — but the
append-only log collapses it to one realized history, with the multiway
branches recorded as rejected proposals or unexplored agent alternatives.

---

## §14 — Cross-Provider Category Mapping

*Derived from: foundations §9 (benchmarks as functors), Go adapter
pattern (`internal/model/`), go-interfaces skill, category-master skill.*

### Provider Categories as Graph Subcategories

Each LLM provider is represented in the graph as a **container** in S2
with child model containers, linked via typed ports:

```sql
-- Provider container
INSERT INTO containers (urn, kind, stratum) VALUES
  ('urn:moos:provider:anthropic', 'provider', 2);

-- Model containers  
INSERT INTO containers (urn, kind, stratum) VALUES
  ('urn:moos:model:claude-3-7-sonnet', 'model', 2),
  ('urn:moos:model:claude-3-5-haiku', 'model', 2);

-- Ownership wires (provider OWNS models)
INSERT INTO wires (source_urn, source_port, target_urn, target_port) VALUES
  ('urn:moos:provider:anthropic', 'owns', 'urn:moos:model:claude-3-7-sonnet', 'owned_by'),
  ('urn:moos:provider:anthropic', 'owns', 'urn:moos:model:claude-3-5-haiku', 'owned_by');

-- Capability wires (model CAN_EXECUTE operations)
INSERT INTO wires (source_urn, source_port, target_urn, target_port, wire_config) VALUES
  ('urn:moos:model:claude-3-7-sonnet', 'can_execute', 'urn:moos:op:complete', 'executed_by',
   '{"context_window": 200000, "tool_use": true, "streaming": true}'::jsonb);
```

The provider category $\mathcal{P}_p$ is the OWNS subcategory (§6) rooted
at the provider container. Its objects are model containers; its morphisms
are `can_execute` wires to capability containers.

### The Adapter Interface as Forgetful Functor

The Go `Adapter` interface (§11) defines the forgetful functor that
strips provider-specific structure:

```go
// U: P_p → C_adapter — forgets API keys, headers, SSE parsing
type Adapter interface {
    Name() string
    Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error)
    Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error)
}
```

Each concrete adapter (Anthropic, Gemini, OpenAI) satisfies this
interface — the compile-time check `var _ Adapter = (*AnthropicAdapter)(nil)`
asserts well-definedness of the forgetful functor at compile time.

**What the functor forgets:**

| Provider-Specific (forgotten) | Standard (preserved) |
| --- | --- |
| API key management, auth headers | `CompletionRequest` input |
| SSE framing, event parsing | `CompletionResult` output |
| Model name strings, pricing tiers | `[]morphism.Envelope` extraction |
| Rate limits, retry policies | `[]ToolCall` parsing |

### The Dispatcher as Colimit

The `Dispatcher` computes the **colimit** (coproduct + universal map) of
the provider categories:

```go
// ∐ P_p → C_kernel  — colimit over provider categories
func NewDispatcher(primary string, adapters ...Adapter) *Dispatcher
```

The fallback chain (`primary → secondary₁ → secondary₂ → error`)
implements the colimit's universal property: given any cocone from the
provider coproduct to the kernel, the Dispatcher mediates through the
colimit. In practice: the first successful `Complete` call IS the
colimit morphism. The kernel receives `CompletionResult` — an object
in $\mathcal{C}_{\text{kernel}}$ — regardless of which provider produced it.

### Benchmark Functor Implementation Pattern

Per foundations §9, benchmark functors are parameterized by task type.
The implementation pattern in Go:

```go
// BenchmarkFunc maps a provider's CompletionResult to a standard score.
type BenchmarkFunc func(task Task, result CompletionResult) BenchmarkScore

// BenchmarkScore lives in C_standard — provider-agnostic.
type BenchmarkScore struct {
    TaskID         string
    Accuracy       float64  // valid morphism extraction rate
    Compositionality float64 // B(g∘f) vs B(g)∘B(f) deviation
    Latency        time.Duration
    TokenCost      TokenCost
    ErrorClass     string   // LogicGraph taxonomy classification
}

// TokenCost captures billing-relevant token counts.
type TokenCost struct {
    InputTokens  int
    OutputTokens int
}
```

**Functoriality check** — the benchmark runner must verify composition:

```go
func verifyFunctoriality(b BenchmarkFunc, task Task, steps []CompletionResult, composed CompletionResult) error {
    // Score each step independently
    stepScores := make([]BenchmarkScore, len(steps))
    for i, step := range steps {
        stepScores[i] = b(task, step)
    }

    // Score the composed result
    composedScore := b(task, composed)

    // Verify B(g∘f) ≈ compose(B(g), B(f))
    expectedAccuracy := composeAccuracies(stepScores)
    if math.Abs(composedScore.Accuracy - expectedAccuracy) > epsilon {
        return fmt.Errorf("functoriality violation: composed=%.3f, expected=%.3f",
            composedScore.Accuracy, expectedAccuracy)
    }
    return nil
}
```

### Cross-Provider Comparison in the Graph

Benchmark results are stored AS graph objects — benchmark score containers
linked to both the model and the task via typed wires:

```text
Provider: Anthropic          Provider: Gemini
  │ owns                       │ owns
  ▼                            ▼
Model: claude-3-7 ──────── Model: gemini-2.0
  │ scored_on                  │ scored_on
  ▼                            ▼
Score(t₁, 0.92)           Score(t₁, 0.87)
  │ evaluates_task             │ evaluates_task
  ▼                            ▼
Task: t₁ (reasoning)       Task: t₁ (reasoning)   ← SAME object
```

**Comparison = graph query.** To find the best provider for task $t_1$:
traverse `evaluates_task` wires TO $t_1$, then `scored_on` wires TO model
containers, rank by score. This is a standard §4 superposition query —
the benchmark results ARE the graph, not a separate table.

### Natural Transformations Detect Capability Correlations

When benchmark functors $B_t$ and $B_{t'}$ (for different task types)
have a natural transformation $\eta: B_t \Rightarrow B_{t'}$, it means
improving on task $t$ predictably improves on task $t'$.

**Detection:** Run all providers through both benchmarks. If the score
rankings are preserved across providers (with consistent scaling), a
natural transformation exists. If rankings shuffle, the tasks measure
independent capabilities.

**Operational impact:** When $\eta$ exists, the system can SKIP
expensive benchmark $t'$ for a new provider and predict its score from
benchmark $t$ alone — saving evaluation cost while maintaining
categorical guarantees.
