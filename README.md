# mo:os — Categorical Graph Kernel

> **Wave 0 status:** A running Go kernel is live under `platform/kernel`.
> It accepts morphisms over HTTP, maintains an append-only log, replays state from
> that log on every boot, loads semantic constraints from `ontology.json`, and
> self-seeds its own node and six feature nodes into the graph at startup.
> An in-browser projection explorer is served at `http://localhost:8000/explorer`.

---

## What mo:os is

mo:os is a **semantic evaluation engine** built on a categorical hypergraph model.
The core claim: every meaningful computation in an AI system is reducible to four
invariant morphisms applied over a typed graph. If that claim holds, then model
providers, storage backends, deployment environments, and user interfaces are all
interchangeable — they become objects in the graph rather than fixed dependencies.

This repository contains the kernel that proves or disproves that claim at Wave 0.

---

## The Theoretical Foundation

mo:os sits at the intersection of three formal frameworks. Each supplies a
distinct layer of the model; none is used in isolation.

```text
Category Theory ←————————→ Hypergraph Rewriting
        ↑                          ↑
        |                          |
        +———————— mo:os ———————————+
                      ↑
                      |
         Hyperdimensional Computing (HDC)
```

**Category Theory** supplies the formal language: objects, morphisms, functors,
natural transformations. The kernel speaks this language natively. Every
component is either an object (a container with a URN) or a morphism (one of
four state-changing operations).

**Hypergraph Rewriting (Wolfram)** supplies the computational model: the stored
graph _is_ the program state; morphism applications are rewriting rules; causal
invariance is the consistency guarantee. Independent morphisms commute —
`LINK(A→B) ; LINK(C→D) = LINK(C→D) ; LINK(A→B)` — because they touch
disjoint parts of the hyperedge structure.

**Hyperdimensional Computing (HDC / VSA)** supplies the representation layer:
every graph structure encodes as a high-dimensional random vector. The three
HDC operations map directly to the kernel's morphisms — bind (⊗) to LINK,
bundle (⊕) to MUTATE, permute (π) to temporal ordering in the morphism log.
This layer is not yet implemented; it is the target for Wave 5.

---

## Axioms

Five non-negotiable statements constrain everything else. They are not open to
per-feature overrides.

| ID  | Axiom                                 | What it rules out                                         |
| --- | ------------------------------------- | --------------------------------------------------------- |
| AX1 | Primary substrate is a typed graph    | No flat key-value stores, no blob storage as truth        |
| AX2 | Meaning is not projection             | UI, embeddings, and prompts are lenses, not ground truth  |
| AX3 | Structural truth is replayable        | No mutable state that cannot be derived from the log      |
| AX4 | Evaluation does not redefine ontology | Runtime views never update the canonical type system      |
| AX5 | Governance is structural              | Access control is a graph morphism, not a middleware flag |

---

## Four Invariant Morphisms

The only operations that can change graph state. Every write in the system is
one of these four. Queries, projections, and embeddings are read-only and do
not appear in the log.

| Morphism   | Categorical identity  | What it does in the graph                    |
| ---------- | --------------------- | -------------------------------------------- |
| **ADD**    | Introduce an object   | Create a new typed container node with a URN |
| **LINK**   | Compose a morphism    | Wire two nodes through named, typed ports    |
| **MUTATE** | Apply an endomorphism | Update a node's payload under version-CAS    |
| **UNLINK** | Remove a morphism     | Delete a wire by its 4-tuple key             |

Every envelope in the log carries exactly one of these four types, plus an
actor URN (who issued it) and an optional scope URN (which sub-graph it touches).

---

## Five Strata

Each node in the graph has a stratum that marks which stage of the realization
pipeline it has reached. Strata are ordered; a node can be promoted upward
but never demoted.

| Stratum | Name         | Meaning in the graph                       | Go constant           |
| ------- | ------------ | ------------------------------------------ | --------------------- |
| S0      | Authored     | Declared syntax; not yet validated         | `StratumAuthored`     |
| S1      | Validated    | Schema-checked; admissible for realization | `StratumValidated`    |
| S2      | Materialized | Implemented and operational in the graph   | `StratumMaterialized` |
| S3      | Evaluated    | Contingent state after execution or replay | `StratumEvaluated`    |
| S4      | Projected    | View surface — UI, embedding, metric       | `StratumProjected`    |

S0–S1 are computationally reducible (deterministic, verifiable). S2 and above
may be partially irreducible — they can involve LLM outputs, user actions, or
emergent topology that cannot be predicted from initial conditions alone.

**The kernel self-seeds at S2.** `urn:moos:kernel:wave-0` and its six feature
nodes are all Materialized — they are implemented and running, not authored
concepts.

---

## Five Functors

A functor is a structure-preserving map from the graph into a different domain.
Functor outputs are **never ground truth**; they are projections over evaluated
state (S3/S4). Treating any functor output as ontology is an explicit anti-pattern.

| Functor      | Maps graph into                     | Status                 |
| ------------ | ----------------------------------- | ---------------------- |
| `FileSystem` | Directory tree                      | Planned                |
| `UI_Lens`    | Browser-rendered interface          | Live (Wave 0 explorer) |
| `Embedding`  | Vector space (similarity retrieval) | Wave 5                 |
| `Structure`  | Schema and structural views         | Planned                |
| `Benchmark`  | Evaluation metric surfaces          | Planned                |

The current explorer at `/explorer` is the Wave 0 `UI_Lens` functor. It reads
projected state (S4) from the graph and renders it. It does not write morphisms.

---

## The Kernel Architecture

The kernel is organized into two layers separated by a strict boundary.

### Pure Core (`internal/core`)

Pure functions with no IO dependencies:

- **`EvaluateWithRegistry`** `(state, envelope, time, registry) → (EvalResult, error)` —
  the catamorphism. Folds a single morphism over current graph state and returns
  a new state. This is the kernel. Everything else is plumbing.
- **`EvaluateProgramWithRegistry`** — folds a sequence of envelopes atomically.
  If any envelope fails, no state change is committed.
- **`GraphState`** — the in-memory hypergraph: `Nodes map[URN]Node` and
  `Wires map[string]Wire`. Always reconstructible from the log (AX3).
- **`SemanticRegistry`** — the constraint system loaded from `ontology.json`.
  Defines which Kinds are allowed at which strata, which ports exist, and which
  inter-kind wires are permitted.

The pure core has no knowledge of HTTP, files, databases, or time sources.
It receives them as arguments. It is the categorical specification in Go.

### Effect Shell (`internal/shell`)

Wraps the pure core with IO:

- **`Runtime`** — holds `GraphState`, `Store`, `SemanticRegistry`, and in-memory
  log. All public methods lock a `sync.RWMutex`.
- **`Apply`** — calls the pure core, appends to the store, updates state.
- **`ApplyProgram`** — same for multi-envelope programs.
- **`SeedIfAbsent`** — calls `Apply` and silently absorbs `ErrNodeExists` /
  `ErrWireExists`. Used at boot for idempotent self-seeding.
- **`Store`** interface — implemented by `LogStore` (JSONL) and `PostgresStore`.
- **`LoadRegistry`** — reads `ontology.json` and derives a `SemanticRegistry`.

### HTTP API (`internal/httpapi`)

Transport layer only. HTTP is not semantics; it is a port on the IO boundary.

| Method | Path                                | What it does                                   |
| ------ | ----------------------------------- | ---------------------------------------------- |
| GET    | `/health`                           | `{"status":"ok"}`                              |
| GET    | `/graph/nodes`                      | List nodes; filter by `?kind=` and `?stratum=` |
| GET    | `/graph/nodes/:urn`                 | Single node by URN                             |
| GET    | `/graph/wires`                      | All wires                                      |
| GET    | `/graph/wires/from/:urn`            | Outgoing wires from a node                     |
| GET    | `/graph/wires/to/:urn`              | Incoming wires to a node                       |
| POST   | `/morphisms`                        | Apply a single envelope                        |
| POST   | `/programs`                         | Apply a program (atomic)                       |
| POST   | `/hydration/materialize`            | Batch materialization from a payload document  |
| GET    | `/hydration/examples/explorer-demo` | Demo materialization payload                   |
| GET    | `/graph/log`                        | Full append-only morphism log                  |
| GET    | `/explorer`                         | UI_Lens functor — browser graph explorer       |

### Hydration Layer (`internal/hydration`)

Translates a structured batch payload (nodes + wires as a document) into a
`Program` — a sequence of `ADD` and `LINK` envelopes — and submits it
atomically. This is how external formats enter the system without bypassing
the morphism discipline.

---

## URN Naming Convention

Every object in the graph is identified by a URN — a typed string the kernel
treats as an opaque unique key. The segments are a naming convention, not parsed
grammar.

```text
urn : moos : <sub-namespace> : <local-name>
 │      │          │                │
 │      │          │         unique name within the sub-namespace
 │      │          kind of thing in the graph hierarchy
 │    system namespace
 RFC 2141 URN scheme prefix
```

Live URNs in the kernel on first boot:

| URN                                      | Kind    | Stratum | What it is                          |
| ---------------------------------------- | ------- | ------- | ----------------------------------- |
| `urn:moos:kernel:wave-0`                 | Kernel  | S2      | The running kernel itself           |
| `urn:moos:feature:pure-graph-core`       | Feature | S2      | Pure core catamorphism module       |
| `urn:moos:feature:append-only-log`       | Feature | S2      | JSONL morphism log                  |
| `urn:moos:feature:http-api`              | Feature | S2      | HTTP transport layer                |
| `urn:moos:feature:program-composition`   | Feature | S2      | Atomic multi-envelope programs      |
| `urn:moos:feature:semantic-registry`     | Feature | S2      | Ontology-derived constraint system  |
| `urn:moos:feature:hydration-materialize` | Feature | S2      | Batch materialization endpoint      |
| `urn:moos:kernel:self`                   | —       | —       | Reserved actor for kernel morphisms |

---

## Self-Seeding: The Kernel as a Container

The kernel does not sit above the graph. It is **in** the graph. On first boot,
before accepting any HTTP request, `seedKernel()` issues `ADD` morphisms for
`urn:moos:kernel:wave-0` and for each of its six features, then `LINK`s each
feature to the kernel via `implements → feature` ports. All morphisms are signed
with actor `urn:moos:kernel:self`.

On subsequent boots the `SeedIfAbsent` guard makes the entire sequence a no-op:
the log is replayed first, the nodes already exist in state, and every `ADD`
returns `ErrNodeExists`, which is silently absorbed.

The kernel's own existence and its Wave 0 feature set are visible in the live
graph at `/graph/nodes?kind=Feature` without any external script.

---

## Running Locally (Windows)

Prerequisites: Go 1.22+, PowerShell 7+.

```powershell
# from D:\FFS0_Factory\moos
.\platform\windows\installers\bootstrap.ps1
```

The bootstrap resolves `platform/presets/windows-local-dev.json`, sets
environment variables (resolving paths to absolute), and runs the kernel.
Default port: `8000`.

Open `http://localhost:8000/explorer` to see the live graph.

To load the demo graph from the browser: click **Apply Explorer Demo** in the
explorer UI. To load from a script:

```powershell
.\platform\windows\installers\seed-explorer-demo.ps1
```

### Key environment variables

| Variable                    | Default                                | Purpose                  |
| --------------------------- | -------------------------------------- | ------------------------ |
| `MOOS_HTTP_PORT`            | `8000`                                 | HTTP listen port         |
| `MOOS_KERNEL_STORE`         | `file`                                 | `file` or `postgres`     |
| `MOOS_KERNEL_LOG_PATH`      | `./data/morphism-log.jsonl`            | Morphism log path        |
| `MOOS_KERNEL_REGISTRY_PATH` | auto-detected from candidates          | Semantic registry source |
| `MOOS_DATABASE_URL`         | _(unset — not required for file mode)_ | Postgres connection      |

---

## Repository Layout

```text
moos/
├── .agent/
│   ├── configs/                  Runtime agent configuration
│   └── knowledge_base/           Canonical knowledge base
│       ├── superset/             ontology.json — machine-readable type registry
│       ├── doctrine/             Human-readable prose (strata, hydration, secrets)
│       ├── design/               Timestamped decision + plan documents
│       ├── instances/            Contingent runtime facts (JSON, schema-validated)
│       ├── industry/             Curated industry landscape (providers, frameworks)
│       ├── reference/            Paper digests and raw sources (read-only)
│       └── archive/              Retired KB material (provenance only)
├── platform/
│   ├── kernel/                   Active Go kernel module
│   │   ├── cmd/kernel/main.go    Entry point
│   │   ├── internal/core/        Pure catamorphism kernel (no IO)
│   │   ├── internal/shell/       Effect shell: store, runtime, registry loader
│   │   ├── internal/httpapi/     HTTP transport and UI_Lens explorer
│   │   ├── internal/hydration/   Batch materialization
│   │   ├── data/                 morphism-log.jsonl (file store)
│   │   └── examples/             Demo materialization payloads
│   ├── presets/                  Declarative environment launch recipes
│   ├── windows/installers/       bootstrap.ps1 and seed scripts
│   ├── linux/installers/
│   └── darwin/installers/
├── archive/                      Retired code (Wave 0 kernel)
├── secrets/                      Local credential staging (never committed)
├── CLAUDE.md                     AI agent workspace authority
├── moos.code-workspace           VS Code workspace entry
└── README.md                     This file
```

---

## Implementation Status

| Component                      | Status   | Wave | Notes                                              |
| ------------------------------ | -------- | ---- | -------------------------------------------------- |
| Pure graph core (catamorphism) | **Live** | 0    | Pure function, no IO, tested                       |
| Append-only morphism log       | **Live** | 0    | JSONL file store and Postgres store                |
| HTTP API                       | **Live** | 0    | All morphism and query endpoints                   |
| Program composition            | **Live** | 0    | Atomic multi-envelope programs                     |
| Semantic registry              | **Live** | 0    | Derived from `ontology.json` at boot               |
| Hydration / materialize        | **Live** | 0    | `/hydration/materialize` batch endpoint            |
| Kernel self-seeding            | **Live** | 0    | Kernel and features are objects in their own graph |
| UI_Lens explorer               | **Live** | 0    | Read-only browser projection at `/explorer`        |
| S0→S1 validation pipeline      | Planned  | 4    | Authored → Validated promotion                     |
| Multi-provider LLM dispatch    | Planned  | 3    | Provider as container; dispatch as morphism        |
| Embedding functor              | Planned  | 5    | HDC vector encoding of graph structures            |
| FileSystem functor             | Planned  | —    | Graph → directory projection                       |
| Benchmark functor              | Planned  | —    | Evaluation metric surfaces                         |

---

## Ontology Registry

The structured ontology at `.agent/knowledge_base/superset/ontology.json`
defines the formal type system as machine-readable JSON, loaded by the kernel
at boot to construct the `SemanticRegistry`.

| Element                      | Count | Registry IDs                                 |
| ---------------------------- | ----- | -------------------------------------------- |
| Axioms                       | 5     | AX1–AX5                                      |
| Objects (Kinds)              | 21    | OBJ01–OBJ21                                  |
| Morphisms (connection types) | 16    | MOR01–MOR16 (decompose into 4 invariant NTs) |
| Functors                     | 5     | FUN01–FUN05                                  |
| Natural Transformations      | 4     | ADD, LINK, MUTATE, UNLINK                    |
| Categories                   | 22    | CAT01–CAT22                                  |

Formalization levels: **L3** (fully modeled — objects, morphisms, composition,
identity all explicit), **L2** (partially modeled), **L1** (named only).
Gaps are annotated, not hidden.

---

## Glossary

**Actor** — A URN identifying who issued a morphism. Every envelope carries an
actor. The kernel records it; governance over actor claims is a future
structural concern (AX5).

**Catamorphism** — A fold over an algebraic structure. The kernel is a
catamorphism: `state(t) = fold(log[0..t])`. The current graph state is always
reconstructible by replaying the log from the beginning.

**Container** — The canonical term for any node in the graph. Every container
has a URN, a Kind, a Stratum, a Payload (mutable data map), and optional
Metadata.

**Envelope** — A single morphism record: `{type, actor, scope?, <payload>}`.
Exactly one payload field is populated. The envelope is the unit of the
morphism log.

**Functor** — A structure-preserving map from the graph category into a target
category. Outputs are projections, never ground truth. The explorer is a
UI_Lens functor.

**Hypergraph** — A graph where edges carry typed ports and connect via a
4-tuple key `(source_urn, source_port, target_urn, target_port)`. This gives
wires hyperedge semantics while remaining binary in implementation.

**Kind** — The categorical type of a container. Declared in the semantic
registry. Controls which strata the container may inhabit and which ports it
exposes. `Kind` is a field on `Node`; `Wire` has no Kind.

**Materialization** — Translating authored content into graph-ready `ADD` and
`LINK` programs. The S0→S2 transition via the hydration pipeline.

**Morphism** — A state-changing operation. Exactly one of ADD, LINK, MUTATE,
UNLINK. The word "connection" is an informal synonym for morphism; functors are
not morphisms.

**Natural Transformation** — The four invariant morphisms (ADD, LINK, MUTATE,
UNLINK) are realized as natural transformations between the identity functor
and the graph-state functor.

**Port** — A typed connection point on a container. Ports have a direction
(`in` or `out`) and may declare allowed target kinds. The wire key includes
both source and target ports.

**Program** — An ordered sequence of envelopes submitted atomically. Either all
succeed, or none are committed. Programs are the transaction unit of graph
mutation.

**Projection** — A read-only derived view of graph state. S4 outputs are
projections. They do not appear in the morphism log and cannot affect graph
truth (AX2, AX4).

**Replay** — Reconstructing graph state by folding all persisted envelopes in
order from the append-only log. Used on every kernel boot.

**Scope** — An optional URN on an envelope identifying the sub-graph the
morphism targets. Used to partition operations across named workspaces.

**Semantic Registry** — The runtime constraint system derived from
`ontology.json`. Defines valid kinds, their allowed strata, ports, and
permitted inter-kind wires. Loaded once at boot; not mutable at runtime.

**Stratum** — One of five ordered realization layers: S0 Authored, S1
Validated, S2 Materialized, S3 Evaluated, S4 Projected. Set at ADD time;
constrained by the kind's registry entry.

**URN** — Uniform Resource Name. The primary key of every container in the
graph. An opaque, globally-unique, persistent string. Uniqueness is enforced
by the kernel; the colon-delimited naming segments are a convention only.

**Wire** — A directed, typed connection between two containers. Identified by
the 4-tuple `(source_urn, source_port, target_urn, target_port)`. Created by
LINK and removed by UNLINK. Multiple wires may exist between the same node
pair through different port combinations.

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
