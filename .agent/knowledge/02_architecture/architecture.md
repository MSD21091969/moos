# mo:os — System Architecture

> Consolidated from `_legacy/02_architecture/` — see `_legacy/` for historical versions.
> Version: 3.0 | Date: 2026-07-03 | Locked Agreements: 9

---

## §1 — Kernel Architecture

The Go kernel implements a single pipeline that reduces every external event to a morphism:

```
Connection → Route → Dispatch → Transform → Commit
```

| Stage | Responsibility | Code |
|-------|---------------|------|
| **Connection** | Accept transport (HTTP, WS, MCP/SSE) | Chi router, gorilla/websocket, SSE handler |
| **Route** | Parse request → determine morphism type | URL + method → one of {ADD, LINK, MUTATE, UNLINK} |
| **Dispatch** | Validate against graph state | Check URN existence, wire uniqueness, permission wires |
| **Transform** | Apply morphism to state | JSONB operations on `containers.state_payload` |
| **Commit** | Append to morphism_log, update caches | `INSERT INTO morphism_log` → update `containers`/`wires` |

**Connection transport surfaces** (morphisms in $\mathcal{C}$, NOT functors — see foundations.md §2 Categorical Inventory):

| Transport | Port | Surface | Protocol |
|-----------|------|---------|----------|
| Data compatibility | 8000 | HTTP REST | JSON |
| Agent compatibility | 8004 | HTTP REST | JSON |
| MCP endpoint | 8080 | SSE stream | MCP/SSE |
| NanoClaw bridge | 18789 | WebSocket | JSON-RPC |

These are four wires from the kernel to external consumers — a coslice category (foundations.md §5). Adding a fifth transport (e.g., gRPC) means adding a fifth wire, not a new functor.

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

**Pipeline is Σ.** The kernel pipeline IS the reducer $\Sigma: \text{Log} \to \text{State}$ — the colimit of the morphism chain applied one message at a time (see foundations.md §1). Each request enters as syntax (HTTP/WS payload) and exits as committed semantics (morphism in the log).

### Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Language | Go 1.23+ | All backend logic |
| Router | Chi | HTTP routing |
| WebSocket | gorilla/websocket | Persistent connections |
| Database | pgx/v5 (Postgres 16) | All storage — containers, wires, morphism_log |
| Vectors | pgvector | Embeddings in `container_embeddings` |
| Metrics | Prometheus | `/metrics` endpoint |
| Container | Docker (multi-stage) | Single `moos-kernel:dev` image |

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

**Atomicity guarantee:** Each morphism is a single SQL transaction. Composition is application-level — the kernel doesn't provide multi-morphism transactions (by design: this forces explicit sequencing and prevents hidden dependencies).

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

| Superset Concept | Morphism | Wire Port |
|-----------------|----------|-----------|
| Create entity | ADD | — |
| Establish relationship | LINK | Determined by relationship type |
| Update property | MUTATE | — |
| Remove relationship | UNLINK | Matches original LINK ports |

Connection morphisms (transport surfaces) re-expose these four operations over network protocols. The kernel pipeline is protocol-agnostic — the same morphism struct is processed regardless of whether it arrived via HTTP, WebSocket, or MCP/SSE.

---

## §3 — Functorial Surfaces

Five functors map $\mathcal{C}$ to external domains. Each is a structure-preserving map that projects the graph into a target category.

### Functor Table

| # | Functor | Signature | Status | Implementation |
|---|---------|-----------|--------|---------------|
| 1 | FileSystem | $F_{\text{fs}}: \text{Manifest} \to \mathcal{C}$ | Active | Reads `manifest.yaml` → emits LINK morphisms |
| 2 | UI_Lens | $F_{\text{ui}}: \mathcal{C} \to \text{React}$ | Active | Graph query → XYFlow component tree |
| 3 | Embedding | $F_{\text{embed}}: \text{state\_payload} \to \mathbb{R}^{1536}$ | Active | pgvector in `container_embeddings` |
| 4 | Structure | $F_{\text{struct}}: \text{subgraph} \to \text{DAG}$ | Planned | GPU topological analysis |
| 5 | Benchmark | $B: \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}$ | Planned | Provider evaluation mapping |

### Connection Morphisms and Coslice Structure

Transport surfaces (HTTP, WebSocket, MCP/SSE) are **morphisms in $\mathcal{C}$**, not functors. They implement the arrows of the category over network protocols.

**Why connections are NOT functors:**
- A functor maps one category to another, preserving structure. Transport surfaces don't map between categories — they are infrastructure that carries morphisms within $\mathcal{C}$.
- Adding a new transport (e.g., gRPC on :50051) creates a new wire, not a new functor.
- The four morphisms (ADD/LINK/MUTATE/UNLINK) pass through all transports identically — the transport is invisible to the categorical structure.

**Connection properties** (per wire in `wire_config`):

| Property | Values | Purpose |
|----------|--------|---------|
| Transport | HTTP, WebSocket, MCP/SSE | Protocol implementation |
| Direction | Unidirectional, Bidirectional | Communication pattern |
| Statefulness | Stateful (WS), Stateless (HTTP) | Connection lifecycle |
| Encoding | JSON, Protobuf, SSE events | Serialization format |

**Coslice structure for transport fan-out:**

The kernel fans out to multiple transport endpoints. In categorical terms, this is the coslice category $\text{Kernel}/\mathcal{C}$ (see foundations.md §5):

```
Kernel → :8000 (HTTP data)
       → :8004 (HTTP agent)
       → :8080 (MCP/SSE)
       → :18789 (WebSocket NanoClaw)
```

Each transport endpoint is an object in the coslice. The forgetful functor $U: \text{Kernel}/\mathcal{C} \to \mathcal{C}$ recovers the target containers from the fan-out structure.

**Protocol-agnostic principle:** The kernel processes the same `Morphism` struct regardless of transport origin. Protocol-specific concerns (auth headers, SSE framing, WS handshake) are handled at the Connection stage of the pipeline (§1) and stripped before reaching Route.

### FileSystem Functor ($F_{\text{fs}}$)

```
manifest.yaml → parse → LINK morphisms → graph
```

**Functoriality check:**
- Identity: empty manifest → no wires → identity on graph
- Composition: manifest A merged with manifest B = processing A then B
- Structure preservation: manifest relationships map to LINK operations

### UI_Lens Functor ($F_{\text{ui}}$)

```
graph query → container/wire data → React component tree → XYFlow render
```

**Functoriality check:**
- Identity: empty subgraph → empty render → identity on UI state
- Composition: render(A ∪ B) = render(A) ∪ render(B) for independent subgraphs
- Natural transformation: the four morphisms commute with rendering — ADD in graph → ADD in UI, LINK in graph → LINK in UI

**Implementation:** FFS4 sidepanel uses Zustand stores (`graphStore`, `sessionStore`) that subscribe to graph change events and re-render the XYFlow component tree.

### Embedding Functor ($F_{\text{embed}}$)

```
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

| Functor | Output Storage | NOT In |
|---------|---------------|--------|
| $F_{\text{embed}}$ | `container_embeddings` | `state_payload` |
| $F_{\text{ui}}$ | React virtual DOM | `state_payload` |
| $F_{\text{struct}}$ | GPU memory / computed DAG | `state_payload` |
| $B$ | Evaluation result store | `state_payload` |

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

**Temporal rules:** Wires can activate/deactivate based on time ranges. This enables: scheduled access grants, trial periods, maintenance windows, compliance-driven access revocation.

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

**Result:** All containers transitively owned by workspace W, with depth. This is $\text{Ob}(\mathcal{C}_W) \setminus \{W\}$ (the workspace itself is added as depth 0).

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

```
Kernel → :8080 (MCP/SSE transport)
       ↓
   LLM tool-use clients (Claude, etc.)
```

**Categorical identity:** MCP is an object in the kernel's coslice category (foundations.md §5). It is one of several transport endpoints, not a special functor. The same four morphisms (ADD/LINK/MUTATE/UNLINK) are exposed over MCP identically to how they are exposed over HTTP.

```
MCP/SSE on :8080 → parse SSE events → Morphism struct → kernel pipeline
```

**MCP-specific concerns** (handled at Connection stage, stripped before Route):
- SSE framing and event stream management
- Tool manifest declaration (exposing graph operations as MCP tools)
- Session management (SSE connection lifecycle)

### Tool Lifecycle

| Phase | Action | Morphisms Used |
|-------|--------|---------------|
| Register | ADD tool container + LINK to capability graph | ADD, LINK |
| Configure | MUTATE tool's `state_payload` with config | MUTATE |
| Bind | LINK tool to agent/workspace | LINK |
| Execute | Traverse wire → hydrate tool → run | (read-only traversal) |
| Unbind | UNLINK tool from agent/workspace | UNLINK |

**Key insight:** Tool registration IS graph manipulation. There is no separate tool registry — tools are containers with specific port types (`can_execute`, `provides_capability`). Tool discovery = graph traversal through capability wires.

### Protocol Comparison

| Property | HTTP REST (:8000) | WebSocket (:18789) | MCP/SSE (:8080) |
|----------|------------------|-------------------|-----------------|
| Direction | Request/response | Bidirectional | Server→client stream |
| Statefulness | Stateless | Stateful | Semi-stateful (SSE) |
| Use case | CRUD operations | Real-time agent chat | LLM tool use |
| Morphism delivery | Synchronous | Async push | Event stream |

All three are coslice objects from the kernel (see §1 transport table). The protocol is infrastructure; the morphisms are identical.

---

## §7 — User Graph Sync

**Locked Agreement #6.** User graphs are portable.

### Model: Git-Like Diverge/Merge

User graph sync follows a diverge/merge model analogous to git:

| Phase | Description | Implementation |
|-------|------------|---------------|
| **Snapshot** | Export user's current wires as morphism log slice | `SELECT * FROM morphism_log WHERE author = :user ORDER BY id` |
| **Diverge** | User works offline or in different instance | Local morphism log accumulates |
| **Merge** | Reconcile diverged logs | Conflict resolution on overlapping morphisms |

### Conflict Resolution

| Conflict Type | Resolution Strategy |
|--------------|-------------------|
| Same wire modified | Last-write-wins OR manual merge (configurable per wire type) |
| Wire deleted on one side, modified on other | Delete wins (conservative) |
| New wires on both sides | Both accepted (no conflict — wires are independent) |
| Contradictory MUTATE payloads | Three-way merge on JSONB keys |

### Federation: CAN_FEDERATE Wires

Cross-instance sharing uses a specific wire type:

```sql
-- Declare that workspace W can federate to external instance
INSERT INTO wires (source_urn, source_port, target_urn, target_port, wire_config)
VALUES (:workspace_urn, 'can_federate', :external_instance_urn, 'federation_target',
        '{"transport": "https", "endpoint": "https://remote.instance/api/sync"}'::jsonb);
```

**Categorical identity:** CAN_FEDERATE is a wire type (morphism with port `can_federate`) — a declared transitivity edge (foundations.md §12). The `wire_config` carries transport details (endpoint URL, auth token reference). Federation sync traverses these wires to discover remote instances, then executes the diverge/merge protocol over the configured transport.

**Security:** Federation wires are subject to the same permission architecture (§5). Only users with appropriate CAN_HYDRATE edges to the workspace can initiate federation. The wire's `wire_config` can include temporal restrictions and environment gates (§4).

### Portable Edges

The key insight: **wires are the portable unit**, not containers. A container's URN is globally unique (UUID). A wire references two URNs + ports. This means:

1. Export = serialize wires as morphism log entries
2. Import = replay morphism log entries in target instance
3. Containers are created on-demand if URNs don't exist in target (ADD morphisms precede LINK morphisms in the log)

This is $\Sigma$ (the reducer) applied across instances: the morphism log is the source of truth, and any instance can reconstruct state by replaying it.
