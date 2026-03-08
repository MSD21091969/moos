# mo:os — System Architecture

> Consolidated from `_legacy/02_architecture/` — see `_legacy/` for historical versions.
> Version: 3.0 | Date: 2026-07-03 | Locked Agreements: 9
>
> **Wolfram/HDC integration**: §11 (Embedding functor HDC algebra).
> **Cross-provider mapping**: §12 (benchmark architecture, provider dispatch, task-dependent selection).
> **Category Registry**: `foundations.md` §21 (formalization levels — functor codomains Manifest, React, DAG are L1).
> Sources: `papers/wolfram_hdc_digest.md`.

---

## §1 — Kernel Architecture

The Go kernel implements a single pipeline that reduces every external
event to a morphism:

```text
Connection → Route → Dispatch → Transform → Commit
```

| Stage          | Responsibility                          | Code                                                     |
| -------------- | --------------------------------------- | -------------------------------------------------------- |
| **Connection** | Accept transport (HTTP, WS, MCP/SSE)    | Chi router, gorilla/websocket, SSE handler               |
| **Route**      | Parse request → determine morphism type | URL + method → one of {ADD, LINK, MUTATE, UNLINK}        |
| **Dispatch**   | Validate against graph state            | Check URN existence, wire uniqueness, permission wires   |
| **Transform**  | Apply morphism to state                 | JSONB operations on `containers.state_payload`           |
| **Commit**     | Append to morphism_log, update caches   | `INSERT INTO morphism_log` → update `containers`/`wires` |

This pipeline is the semantic heart of the system. Purpose is the top
program; authoring formats, JSON envelopes, route handlers, and code
references are syntax until they enter this reducer. The kernel executes
category-bearing programs and commits their semantics to the morphism
log. Transport surfaces, CRUD wrappers, and projection layers are all
downstream wrappers around that semantic core.

**Connection transport surfaces** (morphisms in $\mathcal{C}$, NOT functors — see foundations.md §2 Categorical Inventory):

| Transport           | Port  | Surface    | Protocol |
| ------------------- | ----- | ---------- | -------- |
| Data compatibility  | 8000  | HTTP REST  | JSON     |
| Agent compatibility | 8004  | HTTP REST  | JSON     |
| MCP endpoint        | 8080  | SSE stream | MCP/SSE  |
| NanoClaw bridge     | 18789 | WebSocket  | JSON-RPC |

These are four wires from the kernel to external consumers — a coslice
category (foundations.md §5). Adding a fifth transport (e.g., gRPC)
means adding a fifth wire, not a new functor. The transport carries the
program; the kernel provides the semantics.

### Go Type Safety

```go
type Morphism struct {
    Type       MorphismType  // ADD | LINK | MUTATE | UNLINK
    TargetURN  uuid.UUID
    SourceURN  *uuid.UUID    // nil for ADD
    Payload    json.RawMessage
    Author     uuid.UUID
    Timestamp  time.Time
}

type MorphismType int
const (
    MorphismADD    MorphismType = iota
    MorphismLINK
    MorphismMUTATE
    MorphismUNLINK
)
```

**Pipeline is Σ.** The kernel pipeline IS the reducer
$\Sigma: \text{Log} \to \text{State}$ — the colimit of the morphism
chain applied one message at a time (see foundations.md §1). Each
request enters as syntax (HTTP/WS payload) and exits as committed
semantics (morphism in the log).

### Stack

| Layer     | Technology           | Role                                          |
| --------- | -------------------- | --------------------------------------------- |
| Language  | Go 1.23+             | All backend logic                             |
| Router    | Chi                  | HTTP routing                                  |
| WebSocket | gorilla/websocket    | Persistent connections                        |
| Database  | pgx/v5 (Postgres 16) | All storage — containers, wires, morphism_log |
| Vectors   | pgvector             | Embeddings in `container_embeddings`          |
| Metrics   | Prometheus           | `/metrics` endpoint                           |
| Container | Docker (multi-stage) | Single `moos-kernel:dev` image                |

---

## §2 — Four Morphisms Implementation

### Go Signatures

```go
// ADD: ∅ → C (create container)
func (k *Kernel) Add(ctx context.Context, typeID string, payload json.RawMessage) (uuid.UUID, error)

// LINK: C × C → W (create wire)
func (k *Kernel) Link(ctx context.Context, src, dst uuid.UUID, srcPort, dstPort string, config json.RawMessage) error

// MUTATE: C → C (update state)
func (k *Kernel) Mutate(ctx context.Context, urn uuid.UUID, patch json.RawMessage) error

// UNLINK: W → ∅ (remove wire)
func (k *Kernel) Unlink(ctx context.Context, src, dst uuid.UUID, srcPort, dstPort string) error
```

### Composition Rules

Morphisms compose via sequential execution (`;` operator in foundations.md §3):

```go
// Create a workspace, add a file, link them
wsURN, _ := k.Add(ctx, "workspace", wsPayload)
fileURN, _ := k.Add(ctx, "file", filePayload)
_ = k.Link(ctx, wsURN, fileURN, "owns", "owned_by", nil)
_ = k.Mutate(ctx, fileURN, contentPatch)
```

**Atomicity guarantee:** Each morphism is a single SQL transaction.
Composition is application-level — the kernel doesn't provide
multi-morphism transactions (by design: this forces explicit sequencing
and prevents hidden dependencies).

### Morphism Log Entry

```go
type MorphismLogEntry struct {
    ID         int64           `db:"id"`
    Type       MorphismType    `db:"morphism_type"`
    TargetURN  uuid.UUID       `db:"target_urn"`
    SourceURN  *uuid.UUID      `db:"source_urn"`
    NewState   json.RawMessage `db:"new_state"`
    PrevState  json.RawMessage `db:"prev_state"`
    Author     uuid.UUID       `db:"author"`
    CreatedAt  time.Time       `db:"created_at"`
}
```

**Ground truth:** This table is the morphism history of $\mathcal{C}$. The reducer $\Sigma$ (foundations.md §1, §15) folds it to produce current state.

### Superset Mapping

The four morphisms map onto the superset ontology (`superset/superset_ontology_v2.json`). Key correspondences:

| Superset Concept       | Morphism | Wire Port                       |
| ---------------------- | -------- | ------------------------------- |
| Create entity          | ADD      | —                               |
| Establish relationship | LINK     | Determined by relationship type |
| Update property        | MUTATE   | —                               |
| Remove relationship    | UNLINK   | Matches original LINK ports     |

Connection morphisms (transport surfaces) re-expose these four
operations over network protocols. The kernel pipeline is
protocol-agnostic — the same morphism struct is processed regardless of
whether it arrived via HTTP, WebSocket, or MCP/SSE.

---

## §3 — Functorial Surfaces

Five functors map $\mathcal{C}$ to external domains. Each is a structure-preserving map that projects the graph into a target category.

### Functor Table

| #   | Functor    | Signature                                                            | Status  | Implementation                               |
| --- | ---------- | -------------------------------------------------------------------- | ------- | -------------------------------------------- |
| 1   | FileSystem | $F_{\text{fs}}: \text{Manifest} \to \mathcal{C}$                     | Active  | Reads `manifest.yaml` → emits LINK morphisms |
| 2   | UI_Lens    | $F_{\text{ui}}: \mathcal{C} \to \text{React}$                        | Active  | Graph query → XYFlow component tree          |
| 3   | Embedding  | $F_{\text{embed}}: \text{state\_payload} \to \mathbb{R}^{1536}$      | Active  | pgvector in `container_embeddings`           |
| 4   | Structure  | $F_{\text{struct}}: \text{subgraph} \to \text{DAG}$                  | Planned | GPU topological analysis                     |
| 5   | Benchmark  | $B: \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}$ | Planned | Provider evaluation mapping                  |

### Connection Morphisms and Coslice Structure

Transport surfaces (HTTP, WebSocket, MCP/SSE) are **morphisms in $\mathcal{C}$**, not functors. They implement the arrows of the category over network protocols.

**Why connections are NOT functors:**

- A functor maps one category to another, preserving structure.
  Transport surfaces don't map between categories — they are
  infrastructure that carries morphisms within $\mathcal{C}$.
- Adding a new transport (e.g., gRPC on :50051) creates a new wire, not a new functor.
- The four morphisms (ADD/LINK/MUTATE/UNLINK) pass through all transports identically — the transport is invisible to the categorical structure.

**Connection properties** (per wire in `wire_config`):

| Property     | Values                          | Purpose                 |
| ------------ | ------------------------------- | ----------------------- |
| Transport    | HTTP, WebSocket, MCP/SSE        | Protocol implementation |
| Direction    | Unidirectional, Bidirectional   | Communication pattern   |
| Statefulness | Stateful (WS), Stateless (HTTP) | Connection lifecycle    |
| Encoding     | JSON, Protobuf, SSE events      | Serialization format    |

**Coslice structure for transport fan-out:**

The kernel fans out to multiple transport endpoints. In categorical
terms, this is the coslice category $\text{Kernel}/\mathcal{C}$ (see
foundations.md §5):

```text
Kernel → :8000 (HTTP data)
       → :8004 (HTTP agent)
       → :8080 (MCP/SSE)
       → :18789 (WebSocket NanoClaw)
```

Each transport endpoint is an object in the coslice. The forgetful
functor $U: \text{Kernel}/\mathcal{C} \to \mathcal{C}$ recovers the
target containers from the fan-out structure.

**Protocol-agnostic principle:** The kernel processes the same
`Morphism` struct regardless of transport origin. Protocol-specific
concerns (auth headers, SSE framing, WS handshake) are handled at the
Connection stage of the pipeline (§1) and stripped before reaching
Route.

### FileSystem Functor ($F_{\text{fs}}$)

```text
manifest.yaml → parse → LINK morphisms → graph
```

**Functoriality check:**

- Identity: empty manifest → no wires → identity on graph
- Composition: manifest A merged with manifest B = processing A then B
- Structure preservation: manifest relationships map to LINK operations


### UI_Lens Functor ($F_{\text{ui}}$)

```text
graph query → container/wire data → React component tree → XYFlow render
```

**Functoriality check:**

- Identity: empty subgraph → empty render → identity on UI state
- Composition: render(A ∪ B) = render(A) ∪ render(B) for independent subgraphs
- Natural transformation: the four morphisms commute with rendering — ADD in graph → ADD in UI, LINK in graph → LINK in UI


**Implementation:** FFS4 sidepanel uses Zustand stores (`graphStore`, `sessionStore`) that subscribe to graph change events and re-render the XYFlow component tree.

### Embedding Functor ($F_{\text{embed}}$)

```text
state_payload → embedding model → ℝ^1536 → pgvector storage
```

**Separation principle** (foundations.md §13): Embeddings are functor output, stored in `container_embeddings`, NOT in `state_payload`. Regenerated on every MUTATE.

**Functoriality check:**

- Identity: empty payload → zero vector → identity in embedding space
- Composition: embedding(A + B) ≈ embedding(A) + embedding(B) (approximate, inherent to neural models)


### Structure Functor ($F_{\text{struct}}$) — Planned

See foundations.md §10 for full description. GPU-accelerated topological compression of subgraphs into DAGs for LLM context windows.

### Benchmark Functor ($B$) — Planned

See foundations.md §9 for full description, including the functoriality = process-verified evaluation insight.

### Functor Composition

Functors compose:

$$F_{\text{struct}} \circ F_{\text{embed}}: \text{state\_payload} \to \text{compressed DAG}$$

This chains embedding + structure analysis: first embed content into vector space, then analyze the resulting structure.

**Composition order matters:**

- $F_{\text{struct}} \circ F_{\text{embed}}$: semantic structure (meaning-based clustering)
- $F_{\text{embed}} \circ F_{\text{struct}}$: structural semantics (topology-aware embedding) — different result


### Anti-Pattern: Functor-as-Metadata

**Never store functor output in `state_payload`.** Functor output belongs in its own domain:

| Functor             | Output Storage            | NOT In          |
| ------------------- | ------------------------- | --------------- |
| $F_{\text{embed}}$  | `container_embeddings`    | `state_payload` |
| $F_{\text{ui}}$     | React virtual DOM         | `state_payload` |
| $F_{\text{struct}}$ | GPU memory / computed DAG | `state_payload` |
| $B$                 | Evaluation result store   | `state_payload` |

Violating this creates circular dependencies: the graph contains its own projections, which change when the graph changes, requiring re-projection, ad infinitum.

---

## §4 — Runtime Morphism Switching

**Locked Agreement #5.** Wire behavior changes without schema migration.

### wire_config JSONB

Each wire carries a `wire_config` column with runtime parameters:

```json
{
  "transport": "websocket",
  "encoding": "json",
  "temporal": {
    "active_after": "2024-01-01T00:00:00Z",
    "active_before": "2024-12-31T23:59:59Z"
  },
  "env": {
    "required_env": "production"
  },
  "conditions": {
    "min_trust_score": 0.8,
    "required_capabilities": ["execute_code"]
  }
}
```

### Runtime Resolution

```sql
SELECT *
FROM wires
WHERE source_urn = :actor
  AND target_urn = :resource
  AND source_port = :port_type
  AND (wire_config->'temporal'->>'active_after')::timestamptz <= NOW()
  AND (wire_config->'temporal'->>'active_before')::timestamptz >= NOW()
  AND wire_config->'env'->>'required_env' = :current_env
```

**No schema migration required.** Changing a wire's behavior = `MUTATE` on the wire's config. The four morphisms handle their own evolution.

**Temporal rules:** Wires can activate/deactivate based on time ranges.
This enables scheduled access grants, trial periods, maintenance
windows, and compliance-driven access revocation.

**Environmental rules:** Wires can be environment-specific. Same graph structure in dev, staging, prod — different active wires.

---

## §5 — Permission & Access Architecture

**Locked Agreement #3.** Wire existence = permission (foundations.md §11).

### Permission Check

```sql
-- Can actor hydrate resource?
SELECT 1 FROM wires
WHERE source_urn = :actor
  AND target_urn = :resource
  AND source_port = 'can_hydrate'
  AND (wire_config IS NULL OR
       (wire_config->'temporal'->>'active_before')::timestamptz >= NOW())
```

No ACL table. No role table. No permission matrix. Wire existence IS the permission. Wire absence IS denial.

### OWNS Transitivity (Recursive CTE)

**This CTE computes the objects of subcategory $\mathcal{C}_W$ — see foundations.md §6.**

```sql
WITH RECURSIVE ownership AS (
    -- Base: direct children of workspace W
    SELECT target_urn AS urn, 1 AS depth
    FROM wires
    WHERE source_urn = :workspace_urn
      AND source_port = 'owns'

    UNION ALL

    -- Recurse: children of children
    SELECT w.target_urn, o.depth + 1
    FROM wires w
    JOIN ownership o ON w.source_urn = o.urn
    WHERE w.source_port = 'owns'
      AND o.depth < :max_depth  -- safety limit
)
SELECT urn, depth FROM ownership;
```

**Result:** All containers transitively owned by workspace W, with
depth. This is $\text{Ob}(\mathcal{C}_W) \setminus \{W\}$ (the
workspace itself is added as depth 0).

### Scoped Permission Check

Combining OWNS + CAN_HYDRATE:

```sql
-- Can actor hydrate anything in workspace?
SELECT DISTINCT o.urn
FROM ownership o
JOIN wires w ON w.target_urn = o.urn
WHERE w.source_urn = :actor
  AND w.source_port = 'can_hydrate'
```

This intersects the subcategory $\mathcal{C}_W$ with the actor's hydration edges — the "accessible slice" of a workspace.

---

## §6 — MCP & Tooling Architecture

### MCP as Transport Morphism

MCP (Model Context Protocol) is a connection morphism — a wire from the kernel to LLM tool-use infrastructure:

```text
Kernel → :8080 (MCP/SSE transport)
       ↓
   LLM tool-use clients (Claude, etc.)
```

**Categorical identity:** MCP is an object in the kernel's coslice
category (foundations.md §5). It is one of several transport endpoints,
not a special functor. The same four morphisms (ADD/LINK/MUTATE/
UNLINK) are exposed over MCP identically to how they are exposed over
HTTP.

```text
MCP/SSE on :8080 → parse SSE events → Morphism struct → kernel pipeline
```

**MCP-specific concerns** (handled at Connection stage, stripped before Route):

- SSE framing and event stream management
- Tool manifest declaration (exposing graph operations as MCP tools)
- Session management (SSE connection lifecycle)


### Tool Lifecycle

| Phase     | Action                                        | Morphisms Used        |
| --------- | --------------------------------------------- | --------------------- |
| Register  | ADD tool container + LINK to capability graph | ADD, LINK             |
| Configure | MUTATE tool's `state_payload` with config     | MUTATE                |
| Bind      | LINK tool to agent/workspace                  | LINK                  |
| Execute   | Traverse wire → hydrate tool → run            | (read-only traversal) |
| Unbind    | UNLINK tool from agent/workspace              | UNLINK                |

**Key insight:** Tool registration IS graph manipulation. There is no
separate tool registry — tools are containers with specific port types
(`can_execute`, `provides_capability`). Tool discovery = graph
traversal through capability wires.

### Protocol Comparison

| Property          | HTTP REST (:8000) | WebSocket (:18789)   | MCP/SSE (:8080)      |
| ----------------- | ----------------- | -------------------- | -------------------- |
| Direction         | Request/response  | Bidirectional        | Server→client stream |
| Statefulness      | Stateless         | Stateful             | Semi-stateful (SSE)  |
| Use case          | CRUD operations   | Real-time agent chat | LLM tool use         |
| Morphism delivery | Synchronous       | Async push           | Event stream         |

All three are coslice objects from the kernel (see §1 transport table). The protocol is infrastructure; the morphisms are identical.

---

## §7 — User Graph Sync

**Locked Agreement #6.** User graphs are portable.

### Model: Git-Like Diverge/Merge

User graph sync follows a diverge/merge model analogous to git:

| Phase        | Description                                       | Implementation                                                |
| ------------ | ------------------------------------------------- | ------------------------------------------------------------- |
| **Snapshot** | Export user's current wires as morphism log slice | `SELECT * FROM morphism_log WHERE author = :user ORDER BY id` |
| **Diverge**  | User works offline or in different instance       | Local morphism log accumulates                                |
| **Merge**    | Reconcile diverged logs                           | Conflict resolution on overlapping morphisms                  |

### Conflict Resolution

| Conflict Type                               | Resolution Strategy                                          |
| ------------------------------------------- | ------------------------------------------------------------ |
| Same wire modified                          | Last-write-wins OR manual merge (configurable per wire type) |
| Wire deleted on one side, modified on other | Delete wins (conservative)                                   |
| New wires on both sides                     | Both accepted (no conflict — wires are independent)          |
| Contradictory MUTATE payloads               | Three-way merge on JSONB keys                                |

### Federation: CAN_FEDERATE Wires

Cross-instance sharing uses a specific wire type:

```sql
-- Declare that workspace W can federate to external instance
INSERT INTO wires (source_urn, source_port, target_urn, target_port, wire_config)
VALUES (:workspace_urn, 'can_federate', :external_instance_urn, 'federation_target',
        '{"transport": "https", "endpoint": "https://remote.instance/api/sync"}'::jsonb);
```

**Categorical identity:** CAN_FEDERATE is a wire type (morphism with
port `can_federate`) — a declared transitivity edge (foundations.md
§12). The `wire_config` carries transport details (endpoint URL, auth
token reference). Federation sync traverses these wires to discover
remote instances, then executes the diverge/merge protocol over the
configured transport.

**Security:** Federation wires are subject to the same permission
architecture (§5). Only users with appropriate CAN_HYDRATE edges to the
workspace can initiate federation. The wire's `wire_config` can include
temporal restrictions and environment gates (§4).

### Portable Edges

The key insight: **wires are the portable unit**, not containers. A container's URN is globally unique (UUID). A wire references two URNs + ports. This means:

1. Export = serialize wires as morphism log entries
2. Import = replay morphism log entries in target instance
3. Containers are created on-demand if URNs don't exist in target (ADD morphisms precede LINK morphisms in the log)

This is $\Sigma$ (the reducer) applied across instances: the morphism log is the source of truth, and any instance can reconstruct state by replaying it.

---

## §8 — Pure Core / Effect Boundary Architecture

**New fundamental concept.** The greenfield kernel separates into a
**pure evaluation core** with zero side effects and an **effect shell**
that interprets the core's output against real infrastructure.

### The Pure Core

The pure core is a single function signature:

```
evaluate : (Envelope, GraphState, Time) → (GraphState', [Effect]) | Error
```

It takes a morphism envelope, the current (scoped) graph state, and the
current time. It produces the next graph state plus a list of effects.
Error is returned only for malformed envelopes (syntax failures).

**The pure core never:**
- Touches the database (GraphState is loaded beforehand)
- Makes network calls
- Reads the filesystem
- Accesses the system clock (time is injected)
- Writes logs (log append is an Effect in the output list)

**The pure core always:**
- Validates envelope syntax
- Checks version consistency (CAS for MUTATE)
- Checks permission reachability (wire existence in GraphState)
- Checks structural invariants (unique 4-tuple for LINK, URN existence)
- Computes state transition deterministically
- Emits effects for the shell to interpret

### The Effect Shell

The effect shell interprets the `[Effect]` list:

| Effect Type | Interpretation |
| --- | --- |
| `LogAppend(entry)` | INSERT INTO morphism_log |
| `ContainerWrite(urn, state)` | UPSERT containers (cache) |
| `WireWrite(wire)` | INSERT INTO wires (cache) |
| `WireDelete(wire)` | DELETE FROM wires (cache) |
| `EmbeddingRecompute(urn)` | Queue for embedding functor |
| `Notify(channel, event)` | Push to subscribers (WS/SSE) |
| `MetricIncrement(name)` | Prometheus counter |

### Categorical Meaning

The pure core IS the evaluation functor $F_{\text{eval}}: \mathcal{S} \to \mathcal{M}$ (foundations §14). Its purity guarantees that:

1. **Replay is deterministic:** Given the same morphism log and the same starting state, the pure core produces the same result. This is $\Sigma$ (foundations §1) made operational.
2. **Composition is guaranteed:** `evaluate(env₂, evaluate(env₁, state).NextState) = evaluate(env₁ ; env₂, state)` — sequential evaluation equals batch evaluation.
3. **Testing is infrastructure-free:** Pass in a GraphState literal, get back a GraphState literal. No database, no mocks.

### Go Module Boundary (Enforced by Import Rules)

```
core/    → imports nothing from shell/, transport/, provider/, session/
shell/   → imports core/
transport/ → imports core/ (types only)
provider/  → imports core/ (types only)
session/   → imports core/ (types only), shell/
```

The core/ package is the mathematical heart. Everything else is
infrastructure morphism — wiring that carries the semantics to external
surfaces.

**Reference:** Full module layout and migration strategy in
`05_moos_design/kernel_specification.md`.

---

## §9 — Stratum Materialization Pipeline

The four strata (foundations §17) require a concrete realization path in
the architecture. This section specifies how declarations move through
the system.

### Stratum 0 → Database Seed

Stratum 0 objects are created once, by a seed script, during initial
database migration. They are never created by user morphisms.

```sql
-- Migration: 0001_strata_core.sql
INSERT INTO containers (urn, kind, stratum, kernel_json, version)
VALUES
  ('urn:moos:s0:algebra:invariant', '_S0_ALGEBRA', 0,
   '{"morphisms": ["ADD","LINK","MUTATE","UNLINK"], "invariant": true}'::jsonb, 1),
  ('urn:moos:s0:contract:log_truth', '_S0_LOG_CONTRACT', 0,
   '{"truth_source": "morphism_log", "caches": ["containers","wires"]}'::jsonb, 1),
  ('urn:moos:s0:primitive:identity', '_S0_IDENTITY', 0,
   '{"format": "urn:moos:{stratum}:{kind}:{uuid}"}'::jsonb, 1),
  ('urn:moos:s0:primitive:version', '_S0_VERSION', 0,
   '{"protocol": "CAS", "field": "version"}'::jsonb, 1),
  ('urn:moos:s0:evaluator:kernel', '_S0_EVALUATOR', 0,
   '{"pipeline": ["validate","check_permission","check_structure","compute_transition","emit_effects"]}'::jsonb, 1);
```

**Protection rule:** The pure core rejects any envelope targeting a
Stratum 0 URN unless the actor is the `_S0_EVALUATOR` itself (bootstrap
operations only).

### Stratum 1 → Authoring Ingestion

Stratum 1 objects enter via the morphism API like any other, but with
`stratum: 1` in the envelope. The kernel validates them against S0
rules and stores them as authoring syntax.

**Ingestion contract:**
1. Envelope with `stratum: 1` and `kind: _S1_*`
2. Pure core validates against S0 invariants
3. Stored in `containers` with `stratum = 1`
4. NOT yet operational — S1 objects are metadata about the system, not the system itself

### Stratum 1 → Stratum 2 Promotion (Materialization)

When an S1 declaration is ready to become operational, a
**materialization program** is generated:

1. Read S1 declaration payload (category name, port vocabularies, schema)
2. Generate morphism program: `[ADD(s2_object), LINK(workspace, s2_object, "owns"), ...]`
3. Submit program to kernel (evaluated by pure core as normal)
4. S2 objects appear in operational graph
5. S1 declaration is MUTATED to record promotion: `{lifecycle: "promoted", promoted_to: [s2_urns]}`

This is a compiler step — S1 syntax is compiled into S2 operational
morphisms.

### Stratum 2 → Stratum 3 Projection

S2 state is projected to S3 by the five functors (§3). This is
always on-demand or event-driven:

- **On-demand:** API request → query S2 → functor transforms → response
- **Event-driven:** Morphism committed to S2 → notification effect → functor recomputes projection

**Reference:** Full hydration lifecycle in
`05_moos_design/hydration_lifecycle.md`.

---

## §10 — Extended Cost Model

The D/R ratio (foundations §7) is one metric. The full hydration
pipeline exposes seven cost dimensions, each measurable per
subcategory.

### Seven Cost Dimensions

| # | Dimension | Definition | Measured At |
| --- | --- | --- | --- |
| 1 | **Discovery** | Scanning candidate edges in scope | Graph traversal (CTE depth) |
| 2 | **Retrieval** | Fetching known objects by URN | Direct lookup latency |
| 3 | **Validation** | Checking syntax compliance against schemas | Hydration Stage 2 |
| 4 | **Materialization** | Compiling S1 declarations into envelope programs | Hydration Stage 3 |
| 5 | **Hydration** | Loading + binding code for tool evaluation | Tool invocation path |
| 6 | **Execution** | Running morphism programs / evaluated code | Kernel pipeline latency |
| 7 | **Transport** | Serialization + network delivery to surfaces | Transport morphism overhead |

### Total Hydration Cost (THC)

$$\text{THC}(\mathcal{C}_\sigma) = \sum_{i=1}^{7} w_i \cdot C_i(\mathcal{C}_\sigma)$$

where $C_i(\mathcal{C}_\sigma)$ is cost dimension $i$ for subcategory
$\mathcal{C}_\sigma$ and $w_i$ are configurable weights.

### Per-Subcategory Optimization Profiles

| Subcategory Type | Dominant Cost | Optimization Strategy |
| --- | --- | --- |
| Session objects | Execution (frequent MUTATE) | Batch writes, in-memory state accumulation |
| Tool resources | Hydration (code loading) | Warm capability cache, preload on LINK |
| Agent actors | Discovery (capability scan) | Index `can_execute` port, precompute coslice |
| Document objects | Retrieval (payload fetch) | Payload compression, partial load |
| Provider objects | Validation (benchmark compliance) | Cache validation results, incremental recheck |

### Prometheus Integration

Each dimension maps to a Prometheus histogram:

```
moos_cost_discovery_seconds{subcategory="session"}
moos_cost_retrieval_seconds{subcategory="tool"}
moos_cost_hydration_seconds{subcategory="tool"}
moos_cost_execution_seconds{subcategory="agent"}
moos_cost_transport_seconds{transport="http"}
```

THC is computed as a derived metric in Grafana or alerting rules, not
stored in Prometheus directly.

---

## §11 — Embedding Functor: HDC Algebra

*References: papers/wolfram_hdc_digest.md, Kanerva (2009), founders §4.*

The Embedding functor (FUN03) maps graph substructures to a vector space
for similarity retrieval. HDC / Vector Symbolic Architectures provide the
**compositional algebra** that makes this functor structure-preserving.

### Monoidal Structure of $\mathcal{H}$

$\mathcal{H}$ is a **symmetric monoidal category** $(\mathcal{H}, \otimes, \mathbf{1})$
where $\mathbf{1}$ is the identity hypervector. Bundle $\oplus$ gives
$\mathcal{H}$ **biproduct** structure (simultaneously product and
coproduct), making it a **semiadditive category**. This is why
similarity search works — bundled vectors can be approximately
decomposed.

The mo:os architecture uses **BSC** (Binary Spatter Codes:
$\{-1,+1\}^d$ with XOR bind) — one of several monoidal structures on
the same carrier set. Others (MAP, HRR, FHRR) define different
$\otimes$ but preserve the same categorical properties.

GPU residence is an **implementation detail of the codomain**, not a
categorical property. The functor $F_{\text{embed}}$ maps from
$\mathcal{C}$ (Postgres) to $\mathcal{H}$ (wherever its objects
live). The objects happen to live in GPU RAM because the operations
are embarrassingly parallel.

### Operations

| HDC Op | Symbol | Categorical Role | Graph Meaning |
| --- | --- | --- | --- |
| Bind | $\otimes$ | Monoidal product in $\mathcal{H}$ | Associate role + entity in a wire |
| Bundle | $\oplus$ | Coproduct (biproduct) | Superpose all wires at a node |
| Permute | $\pi^k$ | Endofunctor on $\mathcal{H}$ | Encode position $k$ in morphism history |
| Similarity | $\cos(x,y)$ | Hom-set computation | Retrieve nearest neighbors |

### Wire Encoding

A wire `(src, src_port, tgt, tgt_port)` encodes as:

$$\phi(w) = \mathbf{S} \otimes \phi(\text{src}) \oplus \mathbf{SP} \otimes \phi(\text{src\_port}) \oplus \mathbf{T} \otimes \phi(\text{tgt}) \oplus \mathbf{TP} \otimes \phi(\text{tgt\_port})$$

Role vectors $\mathbf{S}, \mathbf{SP}, \mathbf{T}, \mathbf{TP}$ are
fixed random base vectors. Entity vectors $\phi(\text{urn})$ are either
random base vectors (for atomic URNs) or composed (for container
hierarchies via recursive bundling).

### Node Context Encoding

$$\phi_{\text{ctx}}(v) = \bigoplus_{w \in \text{wires}(v)} \phi(w)$$

This produces the **hypergraph hypervector** — one $d$-dimensional vector
encoding the full relational context of a node across ALL port types
simultaneously. This is the vectorized form of §4's superposition.

### Structure Preservation (Functoriality)

The Embedding functor must satisfy: if two subgraphs compose
(wire-connect), their embeddings compose (bundle):

$$\phi(\text{subgraph}_1 \cup \text{subgraph}_2) \approx \phi(\text{subgraph}_1) \oplus \phi(\text{subgraph}_2)$$

HDC bundling is associative and commutative, so this holds. The
approximation ($\approx$) is inherent to high-dimensional distributed
representations — similarity degrades gracefully as more terms are
bundled ($\sim d / \log d$ capacity), not catastrophically.

### GPU Parallelism

All three HDC operations (bind = element-wise XOR or multiplication,
bundle = element-wise addition, permute = circular shift) are
embarrassingly parallel and map directly to GPU SIMD instructions. This
is the founding vision: *"then gpu"* — once the graph is encoded as
hypervectors, similarity search and pattern matching execute as bulk
vector operations, not sequential graph traversals.

### Robustness

HDC representations tolerate at least 10x more noise than neural network
embeddings. This justifies using approximate nearest-neighbor search in
pgvector (IVFFlat, HNSW indexes) without catastrophic degradation — the
algebraic structure ensures approximately correct retrievals are still
semantically meaningful.

### Implementation Status (2026-03-07)

**Schema ready, runtime absent.** The `embeddings` table
(`vector(1536)`, HNSW with `vector_cosine_ops`, m=16, ef_construction=64)
is deployed via `0001_phase0_core.sql`. The LLM embedding path works
through provider adapters (Gemini/Anthropic/OpenAI). However, **no Go
code implements compositional HDC operations** (binding, bundling,
permutation). The wire→hypervector encoding formula and node context
aggregation exist only as formal theory. Wave 5 targets this gap.

This is validated by HyperGraphRAG Proposition 2: the `wires` table IS
a bipartite hypergraph encoding (incidence graph), and the 4-tuple
UNIQUE constraint preserves the information that binary decomposition
would destroy (Proposition 1).

---

## §12 — Cross-Provider Benchmark Architecture

*References: foundations §9 (benchmarks as functors, cross-provider
category mapping), kernel_specification §14 (implementation pattern).*

### Provider Dispatch Layer

The `model.Dispatcher` provides the architectural surface for
cross-provider evaluation. Its structure:

```text
                    ┌──────────────────┐
CompletionRequest ──│   Dispatcher     │──→ CompletionResult
                    │  (colimit)       │
                    ├──────────────────┤
                    │  primary: "anthropic"
                    │  adapters:        │
                    │    ├ anthropic ──→│ AnthropicAdapter.Complete()
                    │    ├ gemini ────→│ GeminiAdapter.Complete()
                    │    └ openai ────→│ OpenAIAdapter.Complete()
                    └──────────────────┘
```

The Dispatcher tries adapters in priority order (primary first, then
secondary alphabetically). The first success returns. This is a
**colimit** over the provider coproduct — the kernel receives
`CompletionResult` regardless of source.

### Benchmark Evaluation Pipeline

The benchmark pipeline threads through the same kernel evaluation path
as production traffic. The only difference: the benchmark **records**
intermediate states instead of discarding them.

```text
Task Definition
  │
  ├──→ Provider A: Complete(task) ──→ B(result_A) ──→ Score_A
  ├──→ Provider B: Complete(task) ──→ B(result_B) ──→ Score_B
  └──→ Provider C: Complete(task) ──→ B(result_C) ──→ Score_C
                                                        │
                                               ┌────────┘
                                               ▼
                                    Store as graph objects:
                                    Score containers linked to
                                    Model + Task via wires
```

### Provider Objects in the Graph

Providers and models are S2 containers with typed wires:

| Wire Type | From | To | Semantics |
| --- | --- | --- | --- |
| `owns` | Provider | Model | Provider contains model |
| `can_execute` | Model | Operation | Model supports this capability |
| `scored_on` | Model | BenchmarkScore | Model achieved this score |
| `evaluates_task` | BenchmarkScore | Task | Score applies to this task |
| `benchmarked_by` | BenchmarkScore | BenchmarkSuite | Score belongs to this suite |

This makes benchmark results **first-class graph objects** — queryable
via the same superposition model (§4 foundations) as all other data.
"Find the best model for reasoning tasks" is a graph traversal, not a
separate analytics query.

### Benchmark Dimensions

Each benchmark functor evaluates a set of dimensions that map to
operational metrics:

| Dimension | What It Measures | Prometheus Metric |
| --- | --- | --- |
| Morphism accuracy | % valid envelopes in output | `moos_benchmark_morphism_accuracy` |
| Compositionality | step-wise vs pipeline consistency | `moos_benchmark_compositionality_deviation` |
| Latency | time to first morphism | `moos_cost_execution_seconds{provider=...}` |
| Token cost | input/output tokens per morphism | `moos_benchmark_tokens_per_morphism` |
| Error classification | LogicGraph taxonomy distribution | `moos_benchmark_error_class{class=...}` |
| Tool fidelity | correct tool invocations | `moos_benchmark_tool_accuracy` |

### Cross-Provider Selection via Wire Config

The benchmark results inform runtime provider selection through
`wire_config` on `can_execute` wires (§4 runtime switching):

```jsonc
// wire_config on the model → operation wire
{
  "benchmark_override": {
    "reasoning": "anthropic",   // Best on reasoning tasks
    "code_gen": "openai",       // Best on code generation
    "bulk_extract": "gemini"    // Best price/performance for extraction
  },
  "fallback_order": ["anthropic", "gemini", "openai"]
}
```

This means the Dispatcher's provider order becomes **task-dependent** —
the benchmark functor's results feed back into the runtime dispatch
configuration, closing the loop between evaluation and execution.
