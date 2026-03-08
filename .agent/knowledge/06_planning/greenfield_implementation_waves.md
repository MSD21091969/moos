# mo:os — Greenfield Implementation Waves

> Translates `05_moos_design/` specifications into a sequenced implementation
> backlog. Each wave states what it builds, what it proves, what mock
> categories it relies on, and what old assumptions it deletes.
>
> Depends on: `kernel_specification.md`, `hydration_lifecycle.md`,
> `normalization_and_migration.md`, `strata_and_authoring.md`.
> **Cross-provider**: `foundations.md` §9 (benchmark functors), `kernel_specification.md` §14 (provider category mapping),
> `architecture.md` §12 (benchmark architecture). Realized in Wave 6.
> **Category Registry**: `foundations.md` §21 — each wave must promote L1→L2 or L2→L3 for categories it realizes.
> **Value Layer**: `datasets/` — benchmarks.json, providers.json, preferences.json, workstation.json.
> **Machine-Readable Ontology**: `superset/ontology_v3.json` (+ `.csv`) — full §21 registry in structured form.
>
> The ACT 2026 paper workstream runs in parallel — see `act2026_and_launch.md`.

---

## Principles

1. **Each wave is independently testable.** No wave depends on "the rest
   being done" — each produces a running binary and passing tests.
2. **Each wave kills old assumptions.** Explicitly list what FFS1
   habits are deleted by this wave.
3. **Mock categories are tracked.** Every wave that introduces
   provisional concepts must schedule their lifecycle review.
4. **Knowledge promotes.** When a wave validates a concept from
   `05_moos_design`, that concept is promoted into `01_foundations`
   or `02_architecture`.

---

## Wave 0 — Repository Bootstrap & Pure Core

**Goal:** Establish the greenfield `moos` repo with the pure
core/effect boundary as a proven, tested foundation.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| Go module scaffold | `go.mod`, `cmd/moos/main.go` | Repo compiles, runs, responds on health endpoint |
| Core types | `core/types.go` | URN, Kind, Port, Stratum, MorphismType as concrete Go types |
| Envelope + validation | `core/envelope.go` | All validation rules from kernel_specification §5 pass |
| GraphState | `core/state.go` | In-memory graph representation with WireIndex |
| Effects | `core/effects.go` | Effect type definitions (LogAppend, ContainerWrite, etc.) |
| Pure evaluator | `core/evaluate.go` | `Evaluate(Envelope, GraphState, Time) → (EvalResult, error)` |
| **100% pure core tests** | `core/evaluate_test.go` | All 4 morphisms tested: ADD, LINK, MUTATE, UNLINK — zero DB |
| Stratum protection tests | `core/evaluate_test.go` | S0 objects cannot be mutated by non-evaluator actors |
| Version CAS tests | `core/evaluate_test.go` | MUTATE with wrong version → explicit error, correct version returned |

### Tests (target: 30+)

- ADD: creates object in GraphState, version=1
- ADD: duplicate URN → error
- ADD: stratum 0 → rejected unless actor is evaluator
- LINK: creates wire in WireIndex, 4-tuple unique
- LINK: duplicate 4-tuple → error
- LINK: nonexistent source/target URN → error
- MUTATE: correct version → updates payload, increments version
- MUTATE: wrong version → ErrVersionConflict with current version
- MUTATE: stratum 0 target → rejected
- UNLINK: removes wire from WireIndex
- UNLINK: nonexistent wire → error
- Permission: actor without CAN_HYDRATE wire → rejected
- Envelope: missing payload → error
- Envelope: multiple payloads → error
- Stratum: all 4 morphisms respect stratum boundaries

### Assumptions Killed

- `container.Store` as god-object → replaced by `core/` types + `shell/` adapter
- DB in evaluation path → pure core has zero DB references
- `main.go` monolith → clean separation from day one

### Mock Categories

None. Wave 0 is pure mathematics — no provisional concepts.

---

## Wave 1 — Effect Shell & Persistence

**Goal:** Wire the pure core to PostgreSQL via the effect shell. The
kernel can now accept HTTP requests, evaluate morphisms, and persist
results.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| Effect interpreter | `shell/interpreter.go` | All effect types dispatched to real infrastructure |
| DB adapter | `shell/persistence.go` | pgx/v5 CRUD + morphism_log append |
| Scoped GraphState loader | `shell/loader.go` | OWNS-recursive CTE loads subcategory into core.GraphState |
| Transaction wrapper | `shell/transaction.go` | Multi-effect atomic commit (all-or-nothing) |
| Migration: strata core | `migrate/migrations/0001_strata_core.sql` | Tables with `stratum` column, S0 seed data |
| Migration: operational | `migrate/migrations/0002_operational_graph.sql` | Full containers/wires/morphism_log schema |
| HTTP transport | `transport/http.go` | Chi router with morph/container/health endpoints |
| Assembly entrypoint | `cmd/moos/main.go` | Wires core + shell + transport into running binary |
| **Integration tests** | `shell/persistence_test.go` | Full round-trip: HTTP → pure core → effects → DB → query back |

### Schema

```sql
CREATE TABLE containers (
    urn         TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    stratum     SMALLINT NOT NULL DEFAULT 2,
    parent_urn  TEXT REFERENCES containers(urn),
    interface_json  JSONB DEFAULT '{}'::jsonb,
    payload_json    JSONB DEFAULT '{}'::jsonb,
    permissions_json JSONB DEFAULT '{}'::jsonb,
    version     BIGINT NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE wires (
    source_urn  TEXT NOT NULL REFERENCES containers(urn),
    source_port TEXT NOT NULL,
    target_urn  TEXT NOT NULL REFERENCES containers(urn),
    target_port TEXT NOT NULL,
    stratum     SMALLINT NOT NULL DEFAULT 2,
    config_json JSONB DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source_urn, source_port, target_urn, target_port)
);

CREATE TABLE morphism_log (
    id          BIGSERIAL PRIMARY KEY,
    type        TEXT NOT NULL CHECK (type IN ('ADD','LINK','MUTATE','UNLINK')),
    actor_urn   TEXT NOT NULL,
    scope_urn   TEXT NOT NULL,
    stratum     SMALLINT NOT NULL DEFAULT 2,
    payload_json JSONB NOT NULL,
    issued_at   TIMESTAMPTZ NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Assumptions Killed

- Direct SQL in evaluation path → SQL lives only in `shell/`
- `container.Record.ParentURN` as dominant model → one wire type among many
- No stratum awareness in schema → `stratum` column on every table

### Mock Categories

- `SESSION`, `MESSAGE` kinds used in integration tests → lifecycle review at Wave 3

---

## Wave 2 — Morphism Programs & Session Pipeline

**Goal:** The kernel can evaluate ordered sequences of morphisms
atomically. Session manager submits LLM-proposed morphism programs.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| Program type | `core/program.go` | `EvaluateProgram(Program, GraphState, Time) → (EvalResult, error)` |
| Program tests | `core/program_test.go` | Multi-morphism sequences: all-or-nothing semantics |
| LLM adapter (Anthropic) | `provider/anthropic.go` | Streaming SSE, morphism extraction from response |
| LLM adapter (OpenAI) | `provider/openai.go` | Streaming, fallback chain |
| Provider dispatch | `provider/dispatch.go` | Primary/fallback model selection |
| Morphism parser | `provider/parser.go` | Extract `[]Envelope` from LLM text output |
| Session manager | `session/manager.go` | Create session → send message → LLM responds → morphisms applied |
| WebSocket gateway | `transport/websocket.go` | Persistent session connections, event broadcasting |
| Session program flow | integration test | User message → LLM → morphism program → pure core → effects → DB |

### Key Design Decision

The `Program` type resolves the batching question from kernel_specification §8.1:

```go
type Program struct {
    Envelopes []Envelope
    ActorURN  URN
    ScopeURN  URN
}
```

The pure core folds envelopes sequentially. If envelope $n$ fails,
envelopes $1..n-1$ are rolled back (no effects emitted). This gives
the session manager atomicity for LLM turns without violating
single-morphism purity.

### Assumptions Killed

- Session manager interleaved with morphism execution → clean boundary
- LLM output treated as trusted → kernel validates every proposed morphism
- Ad-hoc morphism batching → formal Program type with all-or-nothing

### Mock Categories

- `AGENT` kind → used for session actor identity, lifecycle review at Wave 4
- Provider adapter stubs → promote or replace at Wave 4

---

## Wave 3 — MCP Server & Tool Registry

**Goal:** External LLM clients (Claude Desktop, Cursor) can connect to
the kernel via MCP and invoke tools that are graph objects.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| MCP transport | `transport/mcp.go` | JSON-RPC 2.0 + SSE stream endpoints |
| Tool registry | `tool/registry.go` | Built-in tools: echo, list_children, read_payload, search |
| Tool as graph object | integration test | Tools are S2 containers with `can_execute` wires |
| Tool discovery via traversal | integration test | `tools/list` returns tools reachable from session scope |
| MCP initialize/ping/tools/list/tools/call | integration test | Full MCP protocol flow |

### Assumptions Killed

- Separate tool registry → tools are graph objects, discovered by wire traversal
- `resources/list` and `resources/read` stubs → proper implementation or explicit omission

### Mock Categories

- Built-in tool definitions (echo, list_children) → lifecycle review: keep as S0 bootstrap tools, or promote as S1 declarations?

---

## Wave 4 — Stratum 1 Authoring Pipeline

**Goal:** The system can author and materialize category declarations.
The self-describing property begins: the graph can define new kinds of
objects in itself.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| S1 category declaration format | `core/strata.go` | `_S1_CATEGORY` struct + validation |
| S1 port vocabulary format | `core/strata.go` | `_S1_PORT_VOCAB` struct + validation |
| S1 schema format | `core/strata.go` | `_S1_SCHEMA` struct + JSON Schema validation |
| Materialization compiler | `shell/materialize.go` | S1 declaration → morphism Program → S2 objects |
| Mock lifecycle enforcement | `core/evaluate.go` | Mock objects require purpose + review_by fields |
| Mock lifecycle audit | `shell/audit.go` | Query: list all mocks past review deadline |
| Promotion flow | integration test | S1 category → materialized into S2 → S1 marked "promoted" |

### Assumptions Killed

- Kind strings as unmanaged vocabulary → kinds trace to S1 declarations
- No ontology governance → mock categories have enforced lifecycle
- "Container" as universal noun → purpose-first vocabulary via S1 categories

### Mock Categories Resolved

All mocks from Waves 1-3 reviewed:
- `SESSION` → promote (fundamental operational kind)
- `MESSAGE` → promote (fundamental operational kind)
- `AGENT` → promote or reclassify (depends on agent architecture decision)
- Built-in tools → promote as S0 bootstrap tools

---

## Wave 5 — Embedding Functor & Semantic Search

**Goal:** The embedding functor is operational. The kernel can
auto-embed container payloads and serve vector similarity queries.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| Embedding functor pipeline | `functor/embedding.go` | MUTATE → EmbeddingRecompute effect → vector stored |
| pgvector schema | `migrate/migrations/0003_embeddings.sql` | HNSW index on `embedding` column |
| Embedding provider adapter | `provider/embedding.go` | Configurable: OpenAI ada-002, local model, etc. |
| Semantic search endpoint | `transport/http.go` | `GET /api/v1/search?q=...` → vector + graph hybrid results |
| Separation principle test | integration test | Embeddings stored in `embeddings` table, NOT in `payload_json` |
| Recompute-on-MUTATE test | integration test | MUTATE triggers embedding update for affected URN |

### Assumptions Killed

- Keyword search only → vector similarity + graph structure hybrid
- Embeddings as one-time import → continuous recomputation on mutation
- Embedding table as orphan → wired into morphism effect pipeline

---

## Wave 6 — Projections, Federation, Cost Metrics & Cross-Provider Benchmarks

**Goal:** The remaining architecture commitments are realized:
Prometheus cost metrics, cross-provider benchmark functors, federation
protocol sketch, and formal projection pipeline.

See `foundations.md` §9, `kernel_specification.md` §14, `architecture.md` §12.

### Deliverables

| Deliverable | Package | What it proves |
| --- | --- | --- |
| 7-dimension cost metrics | `shell/metrics.go` | Prometheus histograms for all 7 THC dimensions |
| Per-subcategory labeling | `shell/metrics.go` | Metrics labeled by subcategory type |
| Hydration context recording | `tool/context.go` | Every tool evaluation records topological context |
| Provider category containers | `migrate/`, `shell/` | Provider + Model containers, `owns`/`can_execute` wires in graph |
| Benchmark functor pipeline | `functor/benchmark.go` | `BenchmarkFunc` type; scores stored as graph containers with `scored_on`/`evaluates_task` wires |
| Cross-provider comparison query | integration test | Given a task, query all provider scores via graph traversal |
| Natural transformation detection | `functor/benchmark.go` | Verify functoriality; detect when task-t scores predict task-t′ scores |
| Dispatcher feedback loop | `model/dispatcher.go` | `wire_config.benchmark_override` drives task-dependent provider ordering |
| Federation wire type | `core/types.go` | `CAN_FEDERATE` as wire port with endpoint config |
| Federation sync protocol spec | `05_moos_design/federation.md` | Design doc, not implementation |
| Projection pipeline formalization | integration test | S2 mutation → effect → functor recompute → S3 output |

### Assumptions Killed

- Ad-hoc Prometheus metrics → systematically derived from cost model
- Benchmarks without topological context → hydration context mandatory
- Benchmarks in separate analytics tables → scores are first-class graph containers
- Provider selection as static fallback → task-dependent selection via benchmark feedback
- Federation as future aspiration → concrete wire type + protocol design

---

## Wave Dependency Graph

```
Wave 0  (Pure Core)
  │
  ▼
Wave 1  (Shell + Persistence)
  │
  ├───────────┐
  ▼           ▼
Wave 2      Wave 3
(Sessions)  (MCP + Tools)
  │           │
  └─────┬─────┘
        ▼
      Wave 4  (S1 Authoring)
        │
        ▼
      Wave 5  (Embeddings)
        │
        ▼
      Wave 6  (Metrics + Federation)
```

Waves 2 and 3 can run in parallel after Wave 1.

---

## Verification Checklist (Per Wave)

Before a wave is considered complete:

- [ ] All listed tests pass
- [ ] `go vet ./...` clean
- [ ] No `core/` package imports from `shell/` or `transport/`
- [ ] Any new mock categories have `mock_purpose` and `mock_review_by`
- [ ] Knowledge from `05_moos_design` validated by this wave is promoted to `01` or `02`
- [ ] Category Registry (`foundations.md` §21) updated: realized categories promoted L1→L2 or L2→L3
- [ ] Assumptions listed as "killed" are verifiably absent from new code
- [ ] Docker single-stage build produces working image
- [ ] README updated with current Wave status

---

## Relationship to ACT 2026

The paper workstream (see `act2026_and_launch.md`) runs in parallel:

| Wave | Paper Section Unblocked |
| --- | --- |
| Wave 0 | §3 Container Category — can cite pure core evaluation |
| Wave 1 | §7 Implementation — can cite schema + Go types |
| Wave 2 | §4 Functorial Composition vs Task Decomposition — can cite Program type |
| Wave 3 | §7 Implementation — can cite MCP interop |
| Wave 4 | §5 Recursive Semantic Bridge — can cite self-describing graph |
| Wave 5 | §6 System 3 — can cite embedding + search pipeline |

The paper abstract (March 23) can be written after Wave 0 design is
locked, even before implementation begins. The full paper (March 30)
benefits from Wave 0 tests passing as evidence.
