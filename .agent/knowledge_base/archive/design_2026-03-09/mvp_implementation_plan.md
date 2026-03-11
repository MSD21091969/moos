# MVP Implementation Plan — All Mocks

**Date:** 2026-03-09  
**Status:** Actionable — refers to 20260309-categorical-instruction.md for justification  
**Stack:** Go 1.23, TypeScript 5+, PostgreSQL (optional), Vite, Chrome Extension MV3  
**Principle:** Every mock satisfies the same categorical type as the real thing

---

## Step 0 — Concrete Category: Go + TypeScript

**Go** for the kernel and anything that touches the carrier (GraphState):

- Objects: `URN`, `Kind`, `Port`, `Stratum`, `Node`, `Wire`, `GraphState`, `Envelope`, `EvalResult`
- Morphisms: functions between these types
- Native constructs: products (structs), coproducts (interface + type switch), hom-sets (func signatures)
- Faithful functor: Go's type system — `string` → set of UTF-8 sequences, `map[URN]Node` → set of partial functions URN → Node

**TypeScript** for anything that touches a functor target (UI, visualization):

- Objects: TS types/interfaces mirroring the Go types via JSON serialization
- Native constructs: sum types (discriminated unions), products (interfaces), exponentials (first-class functions)
- Faithful functor: TS's structural type system

**Boundary:** JSON over HTTP is the natural transformation between the two concrete categories. The serialization is a functor $\text{JSON}: \mathbf{Go} \to \mathbf{TS}$ — structure-preserving, information-preserving for the types we care about.

---

## Step 1 — Topos: Go Runtime + V8 (Chrome)

**Go runtime:**

- Limits: struct construction, map/slice allocation
- Exponentials: `func` values, closures (limited but present)
- $\Omega$: `bool` + `error` — predicates on state are `func(GraphState) bool`; registry validation is the subobject classifier

**V8 (Chrome extension):**

- Limits: object construction
- Exponentials: first-class functions, closures
- $\Omega$: `boolean` + type guards — richer dynamic classification than Go

---

## Step 2 — Presheaf: Directory Structure

```
platform/
├── kernel/                          Carrier + catamorphism + effect shell
│   ├── cmd/kernel/main.go           Boot: seed, serve
│   ├── internal/
│   │   ├── core/                    PURE — no IO, no imports outside stdlib
│   │   │   ├── types.go             Objects in the carrier
│   │   │   ├── evaluate.go          Algebra map
│   │   │   ├── semantics.go         Operad (SemanticRegistry)
│   │   │   ├── program.go           Free monoid composition
│   │   │   ├── envelope.go          Envelope constructors
│   │   │   ├── errors.go            Sentinel errors
│   │   │   └── traversal.go         ← NEW: pure ReachableNodes, InducedSubgraph
│   │   ├── shell/                   Effect shell — IO boundary
│   │   │   ├── runtime.go           Monad: read → evaluate → write
│   │   │   ├── store.go             Store interface (carrier persistence)
│   │   │   ├── log_store.go         JSONL algebra
│   │   │   ├── postgres_store.go    Postgres algebra
│   │   │   └── registry_loader.go   Operad loader
│   │   ├── httpapi/                 String diagram: HTTP endpoint box
│   │   │   ├── server.go            Route registrations
│   │   │   └── explorer.go          UI_Lens functor (embedded)
│   │   └── hydration/               Batch materialization
│   │       └── materializer.go
│   └── go.mod
│
├── collider/                        ← NEW: Chrome Extension (functor target)
│   ├── manifest.json                MV3 declaration
│   ├── sidepanel.html               Entry point
│   ├── background.ts                Service worker
│   ├── vite.config.ts               Build monoidal category definition
│   ├── tsconfig.json                Enriched category (type system config)
│   ├── package.json                 Yoneda embedding (imports/exports)
│   └── src/
│       ├── App.tsx                  Root functor composition
│       ├── api/kernel.ts            String diagram client (HTTP → TS types)
│       ├── store/graphStore.ts      Local carrier mirror (Zustand)
│       ├── store/identity.ts        Actor URN state
│       ├── nodes/GraphNode.tsx      Kind → React component (functor)
│       ├── edges/GraphEdge.tsx      Wire → React edge (functor)
│       ├── panels/DetailPanel.tsx   Subobject inspector
│       ├── panels/FilterBar.tsx     Subobject classifier UI
│       ├── panels/EditPayload.tsx   MUTATE envelope builder
│       ├── dialogs/AddNode.tsx      ADD envelope builder
│       └── handlers/onConnect.ts    LINK envelope builder
│
└── presets/                         Deployment topology metadata
```

**Restriction maps:**

- `core/` → sees nothing outside itself. This IS the purity boundary.
- `shell/` → sees `core/`. Cannot see `httpapi/`.
- `httpapi/` → sees `shell/`. Cannot see `core/` directly (only via shell).
- `collider/src/` → sees only its own modules + HTTP API (via network, not import).

---

## Step 3 — Yoneda Embedding: Go Modules + npm

**Go:**

- `moos/platform/kernel` imports exactly one external module: `pgx/v5`
- `internal/core` imports zero external modules — it IS the initial algebra, pure
- `internal/shell` imports `core` + `pgx` (for postgres_store only)
- `internal/httpapi` imports `shell`

**npm (collider):**

- `react`, `react-dom` — functor target category (React component category)
- `@xyflow/react` — graph visualization functor
- `zustand` — local carrier mirror
- `@dagrejs/dagre` — layout algorithm (pure function: graph → positions)
- `vite` — monoidal category (build)
- `typescript` — enriched category (type checker)
- `@types/chrome` — Chrome API type declarations

**Forbidden:** No ORM, no GraphQL client, no state machine library, no CSS framework. If the operad doesn't declare it, it doesn't exist.

---

## Step 4 — Monoidal Category: `go build` + Vite

**Go:**

- $I$ = `.go` source files
- $\otimes$ = `go build ./cmd/kernel` → single binary
- One morphism: source → binary. No intermediate steps.
- Coherence: `go build` is deterministic — same source → same binary (module proxy ensures reproducibility)

**TypeScript (Collider):**

- $I$ = `.tsx` / `.ts` source files
- $\otimes$ = `vite build` → bundled JS + HTML
- Morphisms: source → type-checked → bundled → extension package
- Coherence: lockfile (`package-lock.json`) pins transitive deps

---

## Step 5 — String Diagram: HTTP + JSON

```
┌──────────┐         JSON/HTTP          ┌──────────┐
│  Kernel   │◄─────── strings ─────────►│ Collider │
│  (Go)     │                            │  (TS)    │
│           │  GET /state ──────────►    │          │
│           │  GET /state/scope/:a ──►   │          │
│           │  GET /semantics/registry►  │          │
│           │  ◄── POST /morphisms       │          │
│           │  ◄── POST /programs        │          │
└──────────┘                            └──────────┘
```

- **Boxes:** Kernel process, Collider extension
- **Strings:** HTTP request/response pairs carrying JSON-encoded envelopes
- **$\otimes$:** Multiple endpoints on same connection (multiplexing via path routing)
- **$\circ$:** Request → Response sequencing (HTTP semantics)
- **Braiding:** Stateless — requests from different tabs don't interfere (symmetric monoidal)

---

## Step 6 — Operad: Ontology Fixes (Phase 0)

Current ontology has 13 Kinds (OBJ01–OBJ13). MVP adds:

| ID    | Kind                      | Ports (out)                         | Ports (in) | Stratum | Notes                                    |
| ----- | ------------------------- | ----------------------------------- | ---------- | ------- | ---------------------------------------- |
| OBJ14 | `Kernel`                  | `implements`, `exposes`, `persists` | —          | S2      | Seed node type                           |
| OBJ15 | `SystemCapability`        | —                                   | `feature`  | S2      | Replaces `Feature` for pure capabilities |
| —     | `ProtocolAdapter` (OBJ11) | —                                   | `binding`  | S2      | Already exists; http-api reseeded here   |
| —     | `InfraService` (OBJ12)    | —                                   | `store`    | S2      | Already exists; log store seeded here    |

New morphism types:

| ID    | Name       | Source port     | Target port             | NT decomposition |
| ----- | ---------- | --------------- | ----------------------- | ---------------- |
| MOR17 | `exposes`  | Kernel.exposes  | ProtocolAdapter.binding | LINK             |
| MOR18 | `persists` | Kernel.persists | InfraService.store      | LINK             |

**Actor fix:** `urn:moos:kernel:self` gets an ADD as first seed morphism. Kind = `User` (OBJ01) or new `SystemActor` — decision deferred, but the node MUST exist.

---

## Step 7 — Hom-sets: What wires are legal

Already defined in `ontology.json` via `source_connections` / `target_connections` / PortTarget lists. MVP adds:

| Hom(A, B)                     | Port pair              | Meaning                      |
| ----------------------------- | ---------------------- | ---------------------------- |
| Hom(Kernel, SystemCapability) | `implements → feature` | Kernel declares a capability |
| Hom(Kernel, ProtocolAdapter)  | `exposes → binding`    | Kernel exposes a transport   |
| Hom(Kernel, InfraService)     | `persists → store`     | Kernel uses a store          |
| Hom(User, any)                | `owns → child`         | Ownership scope chain        |

All other hom-sets: unchanged from current ontology.

---

## Step 8 — Initial Algebra + Carrier: Already Implemented

- **Carrier:** `GraphState` = `{Nodes: map[URN]Node, Wires: map[string]Wire}` — this is $G: \mathcal{O}^{\text{op}} \to \mathbf{Set}$
- **Initial algebra:** `[]PersistedEnvelope` — the morphism log (free monoid)
- **Algebra map:** `EvaluateWithRegistry(state, envelope, time, registry) → (EvalResult, error)` — already implemented, already respects operad, already deterministic, already total on valid inputs

**No changes.** The catamorphism core is done.

---

## Step 9 — Functors: MVP Defines Two

### F_UI: Graph → React Components (UI_Lens, FUN02)

$$F_{\text{UI}}: \mathcal{C} \to \mathbf{React}$$

- $F_{\text{UI}}(\text{Node}) = \text{<GraphNode>}$ — Kind-driven component with stratum coloring
- $F_{\text{UI}}(\text{Wire}) = \text{<GraphEdge>}$ — port-labeled XYFlow edge
- Structure-preserving: wires between nodes → edges between components
- Read-only: the React tree never writes back to GraphState

**MVP mock:** Fetch `/state`, map nodes → XYFlow nodes, map wires → XYFlow edges. All 13+ Kinds render as the same `<GraphNode>` with Kind badge and stratum color. No special per-Kind components yet.

### F_Explorer: Graph → HTML (existing, FUN02 variant)

Already implemented in `explorer.go`. Embedded HTML served at `GET /explorer`. No changes.

---

## Step 10 — Algebras: MVP Defines Three

### α_UI: User clicks → Envelopes (Collider write path)

$$\alpha_{\text{UI}}: \text{State} \to [\text{Envelope}]$$

- ADD: `<AddNode>` dialog → Kind selector + URN input + Stratum → POST `/morphisms`
- LINK: XYFlow `onConnect` → source/target + port names → POST `/morphisms`
- MUTATE: double-click node → edit JSON payload → POST `/morphisms`
- UNLINK: right-click edge → confirm → POST `/morphisms`

**MVP mock:** All four work but with minimal validation. The operad (registry) validates server-side. Client trusts the server's error response.

### α_seed: Boot morphisms → Envelopes (seedKernel)

$$\alpha_{\text{seed}}: \emptyset \to [\text{Envelope}]$$

Already implemented. MVP fixes:

1. First envelope: `ADD urn:moos:kernel:self` (actor node)
2. Change `http-api` from Feature to ProtocolAdapter
3. Add `persists → store` wire to InfraService node

### α_agent: State → Envelopes (agent function)

$$\alpha_{\text{agent}}: \text{State} \to [\text{Envelope}]$$

**MVP mock:** $\alpha_{\text{agent}}(\text{any}) = []$ — the trivial algebra. Does nothing. Satisfies the type. Placeholder for rules or LLM dispatch later. Not implemented as code — its absence IS the mock (no writer = empty envelope list).

---

## Step 11 — Catamorphism: Already Implemented

$$\text{cata} = \text{foldl}(\text{EvaluateWithRegistry}, \emptyset, \text{log}[0..t])$$

This is `Runtime.Apply` / `Runtime.ApplyProgram` + store replay on boot. No changes.

---

## Step 12 — Subobject Classifier: Tests + Queries

### Go tests (existing + new)

Existing tests validate the algebra map. MVP adds:

| Test                             | $\chi$ (predicate)                                       | What it classifies        |
| -------------------------------- | -------------------------------------------------------- | ------------------------- |
| `TestSeedActorNode`              | Node(`urn:moos:kernel:self`) exists                      | Actor is in the graph     |
| `TestProtocolAdapterReseed`      | Node(`urn:moos:adapter:http`).Kind == ProtocolAdapter    | Transport correctly typed |
| `TestScopeTraversal`             | ReachableNodes(state, urn) == expected set               | OWNS slice is correct     |
| `TestRegistryRejectsUnknownKind` | EvaluateWithRegistry returns error for unregistered Kind | Operad enforcement        |

### HTTP queries (existing)

- `GET /state/nodes?kind=Kernel` → $\chi_{\text{Kernel}}$: classify all Kernel-kinded nodes
- `GET /state/nodes?kind=ProtocolAdapter&stratum=S2` → $\chi_{\text{transport}}$: classify active transports
- `GET /state/traversal/outgoing/{urn}` → outgoing star of a node

### New query: scope

- `GET /state/scope/:actor` → $\chi_{\text{scope}}$: classify the full subcategory reachable via OWNS from actor

---

## Implementation Order

### Wave 0 Corrections (blocks everything)

| #   | What                                                      | File(s)                  | CT step |
| --- | --------------------------------------------------------- | ------------------------ | ------- |
| 1   | Add OBJ14 Kernel, OBJ15 SystemCapability to ontology.json | `superset/ontology.json` | 6       |
| 2   | Add MOR17 exposes/binding, MOR18 persists/store           | `superset/ontology.json` | 7       |
| 3   | ADD `urn:moos:kernel:self` as first seed morphism         | `cmd/kernel/main.go`     | 10      |
| 4   | Reseed http-api as ProtocolAdapter + exposes wire         | `cmd/kernel/main.go`     | 10      |
| 5   | Seed InfraService node + persists wire                    | `cmd/kernel/main.go`     | 10      |
| 6   | `go test ./...` — all pass                                | —                        | 12      |

### Backend: Scope Traversal

| #   | What                                                       | File(s)                           | CT step |
| --- | ---------------------------------------------------------- | --------------------------------- | ------- |
| 7   | `ReachableNodes(state, urn, portFilter) → set[URN]` — pure | `internal/core/traversal.go`      | 8       |
| 8   | `InducedSubgraph(state, nodeSet) → GraphState` — pure      | `internal/core/traversal.go`      | 8       |
| 9   | `ScopedSubgraph(urn)` — locked wrapper                     | `internal/shell/runtime.go`       | 11      |
| 10  | `GET /state/scope/:actor` handler                          | `internal/httpapi/server.go`      | 5       |
| 11  | Tests for traversal + scope                                | `internal/core/traversal_test.go` | 12      |

### Frontend: Collider Extension Shell

| #   | What                                    | File(s)                            | CT step        |
| --- | --------------------------------------- | ---------------------------------- | -------------- |
| 12  | `npm init`, `package.json` with deps    | `platform/collider/package.json`   | 3              |
| 13  | Vite config for Chrome Extension build  | `platform/collider/vite.config.ts` | 4              |
| 14  | `tsconfig.json`                         | `platform/collider/tsconfig.json`  | 0              |
| 15  | `manifest.json` (MV3 + sidepanel)       | `platform/collider/manifest.json`  | 5              |
| 16  | `sidepanel.html` + `background.ts`      | `platform/collider/`               | 5              |
| 17  | `src/api/kernel.ts` — typed HTTP client | `platform/collider/src/api/`       | 5              |
| 18  | `src/store/graphStore.ts` — Zustand     | `platform/collider/src/store/`     | carrier mirror |

### Frontend: Read Functor (F_UI)

| #   | What                                                   | File(s)                         | CT step |
| --- | ------------------------------------------------------ | ------------------------------- | ------- |
| 19  | `src/nodes/GraphNode.tsx` — Kind badge + stratum color | `platform/collider/src/nodes/`  | 9       |
| 20  | `src/edges/GraphEdge.tsx` — port labels                | `platform/collider/src/edges/`  | 9       |
| 21  | `src/App.tsx` — XYFlow canvas + dagre layout           | `platform/collider/src/`        | 9       |
| 22  | `src/panels/DetailPanel.tsx` — node inspector          | `platform/collider/src/panels/` | 12      |
| 23  | `src/panels/FilterBar.tsx` — Kind/Stratum dropdowns    | `platform/collider/src/panels/` | 12      |

### Frontend: Write Algebras (α_UI)

| #   | What                                         | File(s)                           | CT step |
| --- | -------------------------------------------- | --------------------------------- | ------- |
| 24  | `src/dialogs/AddNode.tsx` — ADD form         | `platform/collider/src/dialogs/`  | 10      |
| 25  | `src/handlers/onConnect.ts` — LINK on drag   | `platform/collider/src/handlers/` | 10      |
| 26  | `src/panels/EditPayload.tsx` — MUTATE inline | `platform/collider/src/panels/`   | 10      |
| 27  | UNLINK via edge context menu                 | `src/edges/GraphEdge.tsx`         | 10      |

### Verification (end-to-end)

| #   | What                                              | CT step |
| --- | ------------------------------------------------- | ------- |
| 28  | `go test ./...` — all green                       | 12      |
| 29  | Kernel boots → `GET /state` shows corrected seed  | 12      |
| 30  | Load extension → sidepanel → XYFlow renders graph | 9       |
| 31  | ADD, LINK, MUTATE, UNLINK from UI → persist       | 10      |
| 32  | Scope query returns OWNS slice                    | 12      |

---

## What's Mocked

| Component                       | Mock                                        | Real (future)                                 |
| ------------------------------- | ------------------------------------------- | --------------------------------------------- |
| Agent ($\alpha_{\text{agent}}$) | Absent — trivial algebra $[] $              | Rules engine or LLM dispatch                  |
| Auth                            | Actor URN self-declared in `chrome.storage` | OAuth / identity provider                     |
| Scope enforcement               | Returns full graph if no OWNS wires         | Real BFS on OWNS chains                       |
| Per-Kind node rendering         | Same `<GraphNode>` for all Kinds            | Custom components per Kind                    |
| Layout                          | Dagre auto-layout                           | User-persisted positions                      |
| HDC embedding (FUN03)           | Not present                                 | $F_{\text{HDC}}: \mathcal{C} \to \mathcal{H}$ |
| Multiway system                 | Serial `RWMutex`                            | Scope-partitioned concurrent apply            |

Every mock satisfies its categorical type. Replacing a mock with the real thing changes the function body, not the signature.
