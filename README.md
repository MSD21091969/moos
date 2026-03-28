# mo:os — Categorical Graph Kernel

> Everything reduces to state. Purpose is to influence it.  
> State is topological. Structures are projections.  
> The kernel is a catamorphism over a typed hypergraph.  
> **Wave 0 is live.**

---

## The Claim

Every meaningful computation — model inference, tool execution, retrieval,
governance, benchmarking — is reducible to four invariant morphisms applied
over a typed graph. If that holds, then providers, storage, deployment
targets, user interfaces, even the industry landscape itself become
**objects in the graph** rather than fixed dependencies.

The kernel at `platform/kernel` is the running proof. It accepts morphisms
over HTTP, persists them as an append-only log, replays full state from that
log on every boot, loads semantic constraints from `ontology.json`, and
self-seeds its own node and feature set into the graph at startup.

A read-only projection explorer is live at `http://localhost:8000/explorer`.

## Release

Wave 0 MVP is published as **v0.1.0**:

- Release page: https://github.com/MSD21091969/moos/releases/tag/v0.1.0
- Assets: `moos-linux-amd64`, `moos-darwin-amd64`, `moos-darwin-arm64`, `moos-windows-amd64.exe`

---

## Why a Hypergraph

A graph captures binary relations. A hypergraph captures higher-order structure:
edges connect arbitrary sets of vertices through typed ports. This is the natural
substrate when relationships are not pairwise but structural — when a model is
bound to a provider via an adapter, scored against a benchmark suite, scheduled
onto a compute resource, and wired to a user through a protocol, all at once.

The stored graph is the union of its port-typed subgraphs:

$$G_{\text{stored}} = \bigcup_{p \in \text{Ports}} G_p$$

Each wire carries a four-tuple key — `(source_urn, source_port, target_urn,
target_port)` — so multiple typed edges coexist between the same node pair.
This is König incidence encoding: binary wires that carry hypergraph semantics.

Wolfram's hypergraph rewriting program gives the computational model. The stored
graph _is_ program state. Morphism applications are rewriting rules. Independent
morphisms commute — `LINK(A→B) ; LINK(C→D) = LINK(C→D) ; LINK(A→B)` — because
they touch disjoint hyperedge structure. Causal invariance is the consistency
guarantee: the order in which independent rewrites are applied does not change
the resulting causal graph.

---

## The Categorical Framework

Category theory supplies the formal language. Every component is an **object**
(a typed container with a URN) or a **morphism** (a state-changing connection
composed from four invariant primitives). Functors project graph state into
other domains. Natural transformations ensure those projections are coherent.

The graph itself is a presheaf $G: \mathcal{O}^{\text{op}} \to \mathbf{Set}$
over the ontology schema. Morphisms between graph states are natural
transformations. Functors to codomain categories (React, metric spaces,
vector spaces, DAGs) are geometric morphisms of the topos. Queries classify
subpresheaves via characteristic morphisms — every query is a subobject
classifier.

This is not applied category theory for decoration. The kernel's `Evaluate()`
function **is** the catamorphism:

```
state(t) = fold(log[0..t])
```

It takes state plus an envelope and returns new state. The entire system is a
fold over an algebraic data type. Everything else — HTTP, files, registries —
is plumbing in an effect shell around this pure function.

---

## Axioms

Five non-negotiable constraints. Not open to per-feature overrides.

| ID  | Axiom                                 | What it rules out                                         |
| --- | ------------------------------------- | --------------------------------------------------------- |
| AX1 | Primary substrate is a typed graph    | No flat key-value stores, no blob storage as truth        |
| AX2 | Meaning is not projection             | UI, embeddings, and prompts are lenses, not ground truth  |
| AX3 | Structural truth is replayable        | No mutable state that cannot be derived from the log      |
| AX4 | Evaluation does not redefine ontology | Runtime views never update the canonical type system      |
| AX5 | Governance is structural              | Access control is a graph morphism, not a middleware flag |

---

## Four Invariant Morphisms

The only operations that can change graph state. All sixteen morphism types
in the ontology decompose from these four natural transformations. Queries,
projections, and embeddings are read-only — they never appear in the log.

| NT         | Signature          | What it does                               |
| ---------- | ------------------ | ------------------------------------------ |
| **ADD**    | $\emptyset \to C$  | Create a typed container with a URN        |
| **LINK**   | $C \times C \to W$ | Wire two containers through named ports    |
| **MUTATE** | $C \to C$          | Update a container's payload (version-CAS) |
| **UNLINK** | $W \to \emptyset$  | Remove a wire by its 4-tuple key           |

Every envelope in the log carries exactly one of these four, plus an actor URN
(who issued it) and an optional scope URN (which sub-graph it targets).

---

## Five Strata

Each container has a stratum marking its position in the realization pipeline.
Strata are ordered; promotion is upward only.

| Stratum | Name         | Meaning                                              |
| ------- | ------------ | ---------------------------------------------------- |
| S0      | Authored     | Declared syntax; not yet validated                   |
| S1      | Validated    | Schema-checked; admissible for realization           |
| S2      | Materialized | Implemented, operational, graph-ready                |
| S3      | Evaluated    | Contingent state after execution, replay, or scoring |
| S4      | Projected    | View surface — UI, embedding, metric, file tree      |

S0–S1 are computationally reducible: deterministic, verifiable. S2 and above are
partially irreducible — LLM outputs, user actions, emergent topology that cannot
be predicted from initial conditions alone.

**The kernel self-seeds at S2.** It exists in its own graph as a Materialized
container, alongside its six feature nodes, before accepting any external request.

---

## Protocols and Pipeline Costs

Knowledge discovery, information retrieval, tool execution, and benchmark
evaluation are not the same operation. They are different **protocols** — typed
subgraph traversals with different cost profiles:

- **Knowledge discovery** is edge-heavy: finding what exists, mapping
  relationships, resolving transitive ownership. Cost scales with the number
  of edges explored. Creating edges _is_ the discovery itself.
- **Information retrieval** is node-heavy: locating a known container by URN
  or kind, reading its payload. Cost scales with the number of nodes indexed.
- **Tool execution** is morphism-heavy: composing a program of envelopes,
  submitting it atomically, folding state. Cost is in the fold.
- **Benchmark evaluation** is functor-heavy: mapping provider subcategories
  into a metric space, comparing scores, classifying equivalence classes.

The graph records all of these as typed wires between typed containers.
The audit trail is not a side effect — it is the morphism log itself.
Every actor, every scope, every timestamp is structural. This makes the
cost of each protocol measurable, optimizable, and attributable.

---

## Projections, Not Ground Truth

A functor is a structure-preserving map from the graph category into a target
category. **Functor outputs are never ground truth** — they are projections
over evaluated state. Treating any functor output as ontology is an explicit
violation of AX2 and AX4.

| ID    | Functor    | Signature                    | Codomain     | Status  |
| ----- | ---------- | ---------------------------- | ------------ | ------- |
| FUN01 | FileSystem | $F_{fs}$: Manifest → C       | Manifest     | Active  |
| FUN02 | UI_Lens    | $F_{ui}$: C → React          | React        | Active  |
| FUN03 | Embedding  | $F_{embed}$: payload → ℝ^n   | ℝ^1536       | Active  |
| FUN04 | Structure  | $F_{struct}$: subgraph → DAG | DAG          | Planned |
| FUN05 | Benchmark  | $F_{bench}$: Provider → Met  | Metric space | Active  |

FUN05 is the classifying functor: it maps provider subcategories into a metric
space. Its pre-image yields equivalence classes — providers that score
identically on a benchmark suite are equivalent under that functor. The product
functor $\prod_i F_i$ across all benchmarks defines the provider's full
evaluation identity.

The explorer at `/explorer` is the Wave 0 UI_Lens functor. It reads and
renders. It does not write morphisms.

---

## The Industry as a Subcategory

Providers, frameworks, languages, protocols, compute platforms — the complete
technology landscape is modeled as objects and morphisms in subcategories of the
graph. Not as external configuration, but as first-class graph citizens:

- **Providers** (OBJ17) own model containers (OBJ06) via OWNS edges
- **Benchmark suites** (OBJ18) group tasks (OBJ19); models are scored (OBJ20)
  via SCORED_ON, EVALUATES_TASK, BENCHMARKED_BY morphisms
- **Protocol adapters** (OBJ11) route traffic between surfaces and tools
- **Compute resources** (OBJ10) are scheduled via CAN_SCHEDULE morphisms

The ontology defines 22 formal categories organized into five groups: core
graph categories, stratum chain, hydration pipeline, functor codomains, and
cross-provider categories including the per-provider subcategory $\mathcal{P}_p$
and the metric space Met.

When a new provider launches, a new model ships, or a benchmark is published,
the update is a sequence of ADD and LINK morphisms — not a code change.
The industry is mapped and updated inside the living graph.

---

## Data Sovereignty and Knowledge Currency

The append-only morphism log is a complete, auditable record of every state
change, every actor, every scope. This is not logging as an afterthought — it
is the structural foundation (AX3). State is always reconstructible from the
log alone.

This creates a **knowledge currency index**: the log tells you not just what
the current state is, but who built it, when, through which operations, at what
cost. Data I/O per user, per group, per scope is attributable. The value of a
subgraph is measurable by the morphisms that produced it.

Sovereignty follows from structure. The graph is self-contained. Containers
own their data through typed OWNS edges with transitive propagation. Users
are actors in the graph, not external identities bolted on. Independence from
any single provider, any single store, any single deployment target is a
consequence of the axioms — not a feature added later.

Small data, used well, with full provenance. Grass roots: actual use of the
system produces the graph that the system reasons over. When patterns
consolidate, they become kernel code — programs composed from the same four
morphisms, validated against the same registry.

---

## The Kernel Architecture

Seven packages separated by a strict purity boundary.

### Pure Core — no IO, no side effects

| Package  | Purpose                                                      |
| -------- | ------------------------------------------------------------ |
| `cat`    | Categorical types: URN, Node, Wire, Envelope, Program, State |
| `fold`   | Catamorphism: `Evaluate()`, `Replay()`, morphism application |
| `operad` | Semantic registry: type validation, constraint checking      |

`fold.Evaluate()` is the kernel. It takes a state, an envelope, and a registry,
and returns a new state. No imports from `os`, `net`, or any persistence
package. It is the categorical specification written in Go.

### Effect Shell — IO boundary

| Package     | Purpose                                                         |
| ----------- | --------------------------------------------------------------- |
| `shell`     | Runtime: RWMutex-guarded state, Apply, SeedIfAbsent, Store      |
| `transport` | HTTP server: 16 routes, JSON API, UI_Lens explorer              |
| `hydration` | Batch materialization: structured documents → morphism programs |
| `config`    | Configuration loader: JSON preset files                         |

All shared state is guarded by `sync.RWMutex`. Read paths use `RLock`; write
paths use `Lock`. The Store interface abstracts persistence — JSONL file store
or in-memory store, with Postgres planned.

### Boot Sequence

```
1. Parse --config flag
2. Load config from JSON preset
3. Load semantic registry from ontology.json (optional; warns if missing)
4. Open store (file or memory)
5. Create runtime — replay full morphism log → reconstruct state
6. Apply seed — idempotent (SeedIfAbsent absorbs ErrNodeExists)
7. Start HTTP server
8. Graceful shutdown on SIGINT/SIGTERM
```

---

## HTTP API

Transport layer only. HTTP is not semantics; it is a port on the IO boundary.

| Method | Path                          | What it does                        |
| ------ | ----------------------------- | ----------------------------------- |
| GET    | `/healthz`                    | Status, node/wire/log counts        |
| GET    | `/state`                      | Full graph state snapshot           |
| GET    | `/state/nodes`                | All nodes                           |
| GET    | `/state/nodes/{urn}`          | Single node by URN                  |
| GET    | `/state/wires`                | All wires                           |
| GET    | `/state/wires/outgoing/{urn}` | Coslice: outgoing wires from a node |
| GET    | `/state/wires/incoming/{urn}` | Slice: incoming wires to a node     |
| GET    | `/state/scope/{urn}`          | Scoped subgraph (OWNS closure)      |
| POST   | `/morphisms`                  | Apply a single envelope             |
| POST   | `/programs`                   | Apply a program (atomic)            |
| GET    | `/log`                        | Full append-only morphism log       |
| GET    | `/log/stream`                 | SSE stream — live morphisms         |
| GET    | `/semantics/registry`         | Loaded ontology registry            |
| POST   | `/hydration/materialize`      | Batch materialization from payload  |
| GET    | `/functor/ui`                 | UI projection (S4 Explorer lens)    |
| GET    | `/functor/benchmark/{suite}`  | Benchmark functor projection        |
| GET    | `/explorer`                   | Embedded HTML Explorer UI           |

---

## Self-Seeding

The kernel does not sit above the graph. It is **in** the graph. On first boot,
`seedKernel()` issues an ADD morphism for the kernel container via
`SeedIfAbsent`, signed by actor `urn:moos:kernel:self`. On subsequent boots,
the log is replayed first, the node exists in state, and the seed is a no-op.

The kernel's own existence is visible in the live graph without any external
script.

---

## Running Locally (Windows)

Prerequisites: Go 1.22+, PowerShell 7+

```powershell
# from the repository root
.\platform\windows\installers\bootstrap.ps1
```

The bootstrap resolves `platform/presets/windows-local-dev.json`, sets
environment variables (resolving paths to absolute), and starts the kernel.
Default port: `8000`. Open `http://localhost:8000/explorer`.

To load the demo graph:

```powershell
.\platform\windows\installers\seed-explorer-demo.ps1
```

### Environment Variables

| Variable                    | Default                     | Purpose                  |
| --------------------------- | --------------------------- | ------------------------ |
| `MOOS_HTTP_PORT`            | `8000`                      | HTTP listen port         |
| `MOOS_KERNEL_STORE`         | `file`                      | `file` or `memory`       |
| `MOOS_KERNEL_LOG_PATH`      | `./data/morphism-log.jsonl` | Morphism log path        |
| `MOOS_KERNEL_REGISTRY_PATH` | auto-detected               | Semantic registry source |

---

## VS Code (Standalone)

This repository now includes a local VS Code configuration in `.vscode/` with:

- Extension recommendations for Go, PowerShell, YAML, Markdown, and REST testing
- Launch profiles for `kb-starter`, `ffs0` KB hydration, and `--mcp-stdio`
- Tasks for build, full test, run, kernel health, MCP health, and MCP SSE smoke checks

Quick sequence in VS Code:

1. `Kernel: run (kb-starter + hydrate)`
2. `Kernel: check health`
3. `MCP: check health`
4. `MCP: SSE endpoint smoke`

If you are working alongside the private workspace clone, use `Kernel: run (ffs0 KB + hydrate)`.

---

## Ontology Registry

The structured ontology (see `examples/kb-starter/superset/ontology.json` for
the schema) is the formal type system — loaded by the kernel at boot via `--kb`
to construct the semantic registry that constrains all morphism evaluation.

| Element                 | Count | IDs                                          |
| ----------------------- | ----- | -------------------------------------------- |
| Axioms                  | 5     | AX1–AX5                                      |
| Objects (Kinds)         | 21    | OBJ01–OBJ21                                  |
| Morphism types          | 16    | MOR01–MOR16 (decompose into 4 invariant NTs) |
| Functors                | 5     | FUN01–FUN05                                  |
| Natural Transformations | 4     | ADD, LINK, MUTATE, UNLINK                    |
| Categories              | 22    | CAT01–CAT22 (5 groups)                       |

### Object Kinds

| ID    | Kind              | Stratum | Role                                        |
| ----- | ----------------- | ------- | ------------------------------------------- |
| OBJ01 | User              | S2, S3  | Authenticated actor                         |
| OBJ02 | ColliderAdmin     | S2, S3  | Category administrator                      |
| OBJ03 | SuperAdmin        | S2, S3  | Root administrator (transitive OWNS)        |
| OBJ04 | AppTemplate       | S1, S2  | Reusable subgraph pattern                   |
| OBJ05 | NodeContainer     | S2, S3  | General-purpose container                   |
| OBJ06 | AgnosticModel     | S2, S3  | Provider-agnostic LLM/ML model              |
| OBJ07 | SystemTool        | S2, S3  | Tool container (MCP surface)                |
| OBJ08 | UI_Lens           | S4      | UI rendering surface (functor output)       |
| OBJ09 | RuntimeSurface    | S2, S3  | Execution endpoint (HTTP/WS/MCP)            |
| OBJ10 | ComputeResource   | S2, S3  | GPU, container, thread pool, VM             |
| OBJ11 | ProtocolAdapter   | S2, S3  | Routable communication container            |
| OBJ12 | InfraService      | S2, S3  | Postgres, disk volume, network segment      |
| OBJ13 | MemoryStore       | S2–S4   | Vector store, context window, history       |
| OBJ14 | PlatformConfig    | S2, S3  | Distribution configuration                  |
| OBJ15 | WorkstationConfig | S2, S3  | Workstation environment descriptor          |
| OBJ16 | Preference        | S2, S3  | Runtime key-value preference (scoped)       |
| OBJ17 | Provider          | S2, S3  | LLM/AI provider (owns model containers)     |
| OBJ18 | BenchmarkSuite    | S2      | Named benchmark collection                  |
| OBJ19 | BenchmarkTask     | S2      | Individual benchmark task definition        |
| OBJ20 | BenchmarkScore    | S3      | Model's score on a task (evaluated result)  |
| OBJ21 | AgentSpec         | S2, S3  | Agent specification (model, tools, persona) |

### Category Groups

| Group              | Categories                        | Purpose                                        |
| ------------------ | --------------------------------- | ---------------------------------------------- |
| Core               | C, Coslice, Slice, Scoped, Kernel | Universal graph, fan-out/in, subcategories     |
| Stratum chain      | C₀, C₁, C₂, C₃, C₄                | Per-stratum full subcategories                 |
| Hydration pipeline | A, V, P, E, L                     | Pipeline stage categories                      |
| Functor codomains  | Manifest, React, ℝ^1536, DAG      | Target categories for FUN01–FUN04              |
| Cross-provider     | Provider_p, Met, Adapter          | Per-provider, metric space, protocol transport |

---

## Repository Layout

```text
moos/
├── platform/
│   ├── kernel/                   Go kernel module (moos/platform/kernel)
│   │   ├── cmd/moos/main.go     Entrypoint: config → registry → store → runtime → seed → HTTP
│   │   ├── internal/cat/         Pure types: URN, Node, Wire, Envelope, State
│   │   ├── internal/fold/        Pure catamorphism: Evaluate, Replay
│   │   ├── internal/operad/      Semantic registry: type validation
│   │   ├── internal/shell/       Effect shell: Runtime, Store, SeedIfAbsent
│   │   ├── internal/transport/   HTTP server: 16 routes, JSON API
│   │   ├── internal/hydration/   Batch materialization pipeline
│   │   ├── internal/mcp/         MCP bridge: SSE on :8080, 5 tools
│   │   ├── internal/functor/     Projection functors: UI_Lens, Benchmark
│   │   ├── internal/config/      JSON configuration loader
│   │   ├── data/                 morphism-log.jsonl (generated at runtime, gitignored)
│   │   └── examples/
│   │       ├── kb-starter/       Minimal KB scaffold for new users
│   │       ├── demo.sh           Demo walkthrough (bash)
│   │       └── demo.ps1          Demo walkthrough (PowerShell)
│   ├── presets/                  Declarative environment launch recipes
│   └── windows/installers/       bootstrap.ps1, seed-explorer-demo.ps1
├── LICENSE                       MIT
└── README.md                     This file
```

**External (not in repo):**

The kernel expects a knowledge base directory passed via `--kb <path>`. See
`examples/kb-starter/` for the minimal scaffold, or create your own with:

```text
my-kb/
├── superset/
│   └── ontology.json             Type system (21 kinds, 16 morphisms)
├── instances/
│   ├── providers.json            LLM providers and models
│   ├── tools.json                System tools
│   ├── surfaces.json             Runtime surfaces and adapters
│   └── ...                       Additional instance files
└── design/                      Architecture specs and decisions
```

---

## Glossary

**Actor** — URN identifying who issued a morphism. Recorded structurally in
every envelope. Governance over actor claims is AX5.

**Catamorphism** — Fold over an algebraic structure. The kernel is a
catamorphism: `state(t) = fold(log[0..t])`.

**Container** — Any node in the graph. Has a URN, Kind, Stratum, Payload,
Metadata, and version counter.

**Envelope** — A single morphism record: `{type, actor, scope?, payload}`.
The atomic unit of the morphism log.

**Functor** — Structure-preserving map from the graph category to a target
category. Outputs are projections, never ground truth.

**Hypergraph** — Graph where wires carry typed ports and connect via a 4-tuple
key. Binary edges with hyperedge semantics through König encoding.

**Kind** — Categorical type of a container. Declared in the semantic registry.
Controls allowed strata and ports.

**Morphism** — State-changing operation. One of ADD, LINK, MUTATE, UNLINK.
Connections are morphisms; functors are not.

**Program** — Ordered sequence of envelopes submitted atomically. All succeed
or none are committed.

**Projection** — Read-only derived view (S4). Does not appear in the log.
Cannot affect graph truth (AX2, AX4).

**Replay** — Reconstructing graph state by folding all persisted envelopes
from the log. Runs on every kernel boot.

**Semantic Registry** — Constraint system derived from `ontology.json`. Valid
kinds, strata, ports, permitted wires. Loaded once at boot; not mutable at
runtime.

**Stratum** — Realization layer: S0 Authored → S1 Validated → S2 Materialized
→ S3 Evaluated → S4 Projected. Promotion only.

**Wire** — Directed typed connection: `(source_urn, source_port, target_urn,
target_port)`. Created by LINK, removed by UNLINK.

---

## Normalization Rules

These prevent categorical drift in documentation and code.

1. **Category before implementation.** Every component is either a container or
   a morphism. Nothing is named without a parent category.
2. **Purpose before packaging.** Semantic identity is defined by purpose, not
   by library or product name.
3. **Topology before inventory.** State is a reachable graph condition, not a
   stored bag of properties.
4. **Semantics before transport.** HTTP, WebSocket, MCP, and CLI are transport
   ports on the IO boundary, not semantic layers.
5. **Projection is not ontology.** UI, embeddings, and dashboards are lenses.
6. **Provider is downstream.** LLM providers are containers in the graph, wired
   in via LINK, not hard dependencies.
7. **Metadata is secondary.** Graph structure carries primary semantics; payload
   and metadata carry contingent data.
