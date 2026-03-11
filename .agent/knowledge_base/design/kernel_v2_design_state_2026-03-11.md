# kernel_v2 Design State — 2026-03-11

## Context

kernel_v2 clean rebuild is committed and pushed. 54 tests green, 6 packages.
This document captures the design decisions and forward plan from the planning conversation.

---

## Approved Decisions

### Decision 1 — Config Source: Option C (`--kb <path>`)

Kernel discovers everything from KB root. One flag, everything derives.

- `superset/ontology.json` for type system
- `instances/distribution.json` for platform config
- Instance hydration via API, not at boot

### Decision 2 — Hydration Scope: On-demand

- **Tier 0 (pre-boot):** distribution.json (config) + ontology.json (types) — read as files, never enter graph
- **Tier 1 (on-demand):** identities, surfaces — hydrated via API by bootstrap script or install wizard
- **Tier 2 (on-demand):** providers, preferences, benchmarks — hydrated when user activates them

### Decision 3 — Ontology Expansion: Yes, add OBJ14-OBJ20

All instance files need valid type_ids in ontology.json to be admissible as typed graph nodes.

| New Object              | type_id              | broad_category | Purpose                      |
| ----------------------- | -------------------- | -------------- | ---------------------------- |
| OBJ14 PlatformConfig    | `platform_config`    | platform       | Platform distribution config |
| OBJ15 WorkstationConfig | `workstation_config` | platform       | Local workstation config     |
| OBJ16 Preference        | `preference`         | config         | Key-value preference entry   |
| OBJ17 Provider          | `provider`           | compute        | LLM/API provider container   |
| OBJ18 BenchmarkSuite    | `benchmark_suite`    | evaluation     | Benchmark suite container    |
| OBJ19 BenchmarkTask     | `benchmark_task`     | evaluation     | Individual benchmark task    |
| OBJ20 BenchmarkScore    | `benchmark_score`    | evaluation     | Scored result                |

Note: `distribution_config` in distribution.json becomes `platform_config` to align.
Benchmarks already have MOR14-16 (SCORED_ON, EVALUATES_TASK, BENCHMARKED_BY) declared.

### Decision 4 — Schema Validation: Trust

No schema validation at boot. CI/CD + versioning handles correctness.
Instance file updates = morphisms ("just another update node").

---

## Architecture Agreements

### Two Distinct Layers: Git vs Graph

- **Git layer:** code + schemas + template configs. Versioned. Admin-managed. Fresh on pull.
- **Graph layer:** runtime state + function definitions. Morphism log. Append-only.
- Git itself IS a node in the graph (for admins).

### Config = Install Wizard Interview

- Fresh install: wizard captures user choices → config written → kernel boots
- Returning user: same loop — config check / hydrate / schema check
- Updates = partial derivative of initial config = "just another morphism"

### Hypergraph Structure

The stored graph is a superposition of all port-typed subgraphs (König encoding).
Binary Wire type in Go = incidence encoding, not the mathematical structure.
A NodeContainer with 6 port connections IS a 6-arity typed hyperedge signature.
Queries collapse superposition into projected subgraphs.

### Projections = Applications

- Admin sees full hypergraph via Scoped(Admin)
- Groups see subcategory via Scoped(Group) — OWNS traversal
- Users see subgraph of their group(s) via Scoped(User)
- AppTemplate (OBJ04) instantiated as subgraph pattern = "application"
- Applications, skills, tools = same mechanism, different templates

### The Missing Agent

The kernel has no real-use morphisms/objects/applications yet. It's a pure substrate.
An "agent" = user's way to change graph state, together with UI lens.
Models/LLMs handle heavy lifting; the agent is the interface.
Currently, the AI code assistant (Copilot in IDE) takes the agent's place.
**This requires a running database** as the minimum viable bridge — the agent
needs persistent, queryable graph state, not just a JSONL file.

---

## Forward Implementation Layers

### Layer A — Ontology Completion ✓ DONE (2026-03-11 curation)

- OBJ14-21 added to ontology.json (21 objects total)
- `mutable` and `allowed_strata` fields added per-object
- Ontology self-describing for ALL instance data
- ontology.csv synced

### Layer B — KB-Aware Boot (`--kb <path>`)

- Config struct reads distribution.json from KB root
- Ontology loaded from `superset/ontology.json` relative to KB root
- Seed morphism configurable in distribution.json
- One flag, everything derives

### Layer C — Scoped Projection (owner-aware subgraph)

- `ScopedSubgraph(urn URN) GraphState` on Runtime — BFS on OWNS wires
- `GET /state/scope/:actor` endpoint
- CAT04 Scoped(W) — basis for groups, user graphs, "applications"

### Layer D — Instance Hydration Flow

- Bootstrap morphisms from instance files via `/hydration/materialize`
- Install wizard output: each instance file → MaterializeRequest
- On-demand, not at boot

### Layer E — Template Instantiation (AppTemplate)

- Define template as stored subgraph pattern (OBJ04)
- Instantiation = parameterized ADD+LINK sequence, owned by requesting actor
- This is how "applications" get created

### Layer F — Tool Registration + Runtime Addressing

- Tools (OBJ07) wired to RuntimeSurface (OBJ09) via CAN_ROUTE (MOR10)
- Agent discovers tools via Scoped(Agent) projection
- MCP tool list = lossy S4 projection

### Layer G — Agent Interface (the missing piece)

- Agent = actor identity node that issues morphisms to change graph state
- Requires running database (not JSONL) for persistent queryable state
- AI assistant (IDE Copilot) serves as interim agent via HTTP API
- Real agent = UI lens + model dispatch + morphism generation

---

## Current platform/kernel Package Map

```
platform/kernel/
├── go.mod                    (module moos/platform/kernel, go 1.23)
├── cmd/moos/main.go          (boot: --config → store → replay → seed → HTTP)
├── internal/
│   ├── cat/                   (pure types: URN, TypeID, Node, Wire, GraphState, Envelope, Program)
│   ├── fold/                  (Σ-catamorphism: Evaluate, EvaluateProgram, Replay)
│   ├── operad/                (colored operad: Registry{Types}, TypeOf, Validate, DeriveFromOntology)
│   ├── shell/                 (effect boundary: Runtime, LogStore, MemStore, SeedIfAbsent)
│   ├── hydration/             (materialization: MaterializeRequest → Program)
│   ├── transport/             (HTTP API: 12 routes, no functor dependency)
│   └── config/                (JSON config loader, Seed struct)
├── data/                      (empty — JSONL log created at runtime)
└── registry/                  (empty — ontology comes from KB via superset/)
```

Import discipline: cat→stdlib; fold→cat,operad; operad→cat; shell→cat,fold,operad;
hydration→cat,operad; transport→shell,cat,hydration

54 tests across 6 packages, all green.

---

## SOT File Status

| File                        | Domain                   | Status                                                |
| --------------------------- | ------------------------ | ----------------------------------------------------- |
| superset/ontology.json      | Type system (21 objects) | Done — OBJ14-21 added (2026-03-11 curation)           |
| superset/ontology.csv       | Flat export              | Synced with ontology.json                             |
| instances/distribution.json | Platform config          | Done — type_id fixed, paths point to platform/kernel  |
| instances/surfaces.json     | Runtime surfaces         | Done — updated (2026-03-11 curation)                  |
| instances/workstation.json  | Local dev config         | Done — real hardware specs, toolchain updated          |
| instances/identities.json   | Actors                   | Done — updated (2026-03-11 curation)                  |
| instances/benchmarks.json   | Evaluation               | Ready (has scoring_dimensions)                        |
| instances/preferences.json  | User/system prefs        | Ready (10 entries)                                    |
| instances/providers.json    | LLM providers            | Done — 5 providers, 2026 models, config_source links  |
| instances/agents.json       | Agent specification      | Done — model_binding synced to gemini-3.1-pro          |

---

## Architecture Insight: The Kernel/Graph Barrier (2026-03-11, session 2)

### Code vs Morphisms

The kernel IS Go code. Graph state IS morphisms over nodes. Eventually the
rootcontainer will hold "folded functions" — references to actual scripts or
executable logic — inside the graph. This means:

- In the **Go program**, composition = function calls, goroutines, channels, struct embedding.
- In the **graph**, composition = Programs ([]Envelope sequences) that ADD/LINK/MUTATE/UNLINK nodes.
- The **barrier** is where Go code produces Envelopes that enter the graph, and where graph
  state (node payload, wire topology) informs what Go code does next.

The kernel's Go code never directly appears in the graph. What enters the graph are
**descriptions** of functionality (OBJ07 SystemTool metadata, OBJ05 FunctionDef signatures),
not the implementations themselves. The implementations live in some runtime environment
(Go binary, Python process, WASM module, shell script) — the graph holds the **addressing
and wiring** to reach them.

### "Big Code in Kernel" = Fanning Out in the Program

If complex logic lives in Go (e.g. a 500-line handler that coordinates 10 steps), that
fans out **in the program** — Go's call graph grows, the kernel binary gets bigger,
the composition is invisible to the graph.

If the same logic is decomposed into 10 graph nodes (tools, functions) wired together
via morphisms with a template orchestrating them, that fans out **in the graph** — the
kernel stays thin, composition is visible/queryable/recomposable.

The subtle difference: **graph-fanned composition is runtime-programmable**. A user or
agent can rewire, extend, or replace components without recompiling. Program-fanned
composition requires a kernel rebuild.

Go's relevant capabilities at this boundary:

- **Interfaces**: `Store`, `Runtime` — the kernel already uses them for pluggability
- **Plugin system** (`plugin` package): dynamic .so loading (Linux only, fragile)
- **WASM** (via wazero): sandboxed execution of graph-referenced functions
- **exec.Command**: shell out to scripts the graph points to
- **net/rpc / gRPC**: remote dispatch to processes the graph wires address

### AI Code Assistant as Agent Bridge

When mo:os is a running process, the AI code assistant (Copilot in this IDE) can
access the running DB. This turns the IDE conversation INTO the conversation a user
would have with the production-ready version.

- The user's "agentspec" is also a config matter — a node in the usergraph that
  defines the agent's identity, permissions, tool access, model preferences.
- AgentSpec hydration = `ADD(agent_node) ; LINK(user, 'owns', agent) ; LINK(agent, 'can_route', tool_1) ...`
- Re-entering the config node in the usergraph = MUTATE on the agent's config payload.

### Runtime Programming

"Runtime programming" means: from the get go (or later, when syncing and re-entering
the config node in the usergraph), the user is **defining categories or hydrating them**.

- Defining categories = adding new TypeIDs to the operad (extending ontology at runtime)
- Hydrating categories = instantiating existing types as nodes in the graph (materialization)
- Both are morphisms — the ontology itself could be graph-resident, not just a JSON file
- This is the "mo:os ultimately is purpose" statement: the platform IS the runtime
  programming environment for categorical graph structures.

### De Novo UX — DECIDED: Option B (self-hydrating), then agent-guided

**Phase 1 — Self-hydrating kernel (Option B):**
Kernel boots with `--kb`, auto-discovers instance files, hydrates them as its first
act of runtime programming. No separate wizard needed — the kernel IS the wizard.
Minimal hardcoded seed (RootContainer + kernel node), then auto-populate from KB.

**Phase 2 — Agent-guided (Option C, unfolds naturally):**
Once running kernel connects to VS Code via HTTP, the AI code assistant (Copilot)
becomes the interim agent. VS Code IS the UX lens. Current AI assists perform
future agent's job: guide user through graph setup, tool activation, provider config.
The agent "takes over" progressively — no separate agent binary needed initially.

**Without agent:** basic kernel + solid DB = minimum viable platform.
**With VS Code connected:** IDE conversation = agent conversation. The agentspec
(OBJ21) is a config node in the usergraph. Re-entering it = MUTATE.

### The Kernel Subcategory — Go Code IS the Algebra (CORRECTED 2026-03-11 s3)

CORRECTION: The kernel does NOT "traverse the graph to discover what to do."
The kernel IS an algebra over a specific subcategory of the hypergraph's colored operad.
Go code lines literally ARE morphisms in this subcategory. The kernel is "blind" to
deeper layers — it speaks a specific subcategory language, not the whole hypergraph.

**Formally (colored operad algebra):**

Let 𝓞 be the colored operad defined by ontology.json:

- Colors = TypeIDs (user, node_container, system_tool, agent_spec, ...)
- Operations 𝓞(c₁,...,cₙ; d) = admissible morphisms from inputs c₁,...,cₙ → output d
- Generators = the 4 invariant NTs: ADD, LINK, MUTATE, UNLINK

The kernel is an ALGEBRA over a sub-operad 𝓞_K ⊆ 𝓞:

- For each color c in 𝓞_K, a Go type is the carrier:
  - `cat.Node` carries the objects
  - `cat.Wire` carries the morphisms between objects
  - `cat.Envelope` carries a single operation application
  - `cat.Program` carries composed operations
  - `cat.GraphState` carries the carrier algebra (Ob(C) × Hom(C))

- For each operation in 𝓞_K, a Go function is the structure map:
  - `fold.Evaluate` : GraphState × Envelope → GraphState (single operation)
  - `fold.EvaluateProgram` : GraphState × Program → GraphState (composed operations)
  - `operad.ValidateAdd/Link/Mutate` : TypeSpec × Payload → bool (admissibility)

- The kernel is BLIND to layers outside 𝓞_K. It does not interpret deeper graph
  structure. It only computes the algebra maps for its subcategory.

**What this means for "fanning out":**

A programmer writes Go code that composes operations in 𝓞_K. Example intent:
"Split all datastreams in agent-team gRPC data with graph type X,Y,Z and
fanout to agnostic model graph router."

This is a TERM in the operad algebra. In Go it would be a Program:

```
Program{
  Actor: "urn:moos:kernel:self",
  Envelopes: [
    ADD(datastream_splitter, type=system_tool, payload={protocol:"grpc", graph_types:["X","Y","Z"]}),
    LINK(agent_team_surface, 'can_route', datastream_splitter, 'transport'),
    LINK(datastream_splitter, 'can_route', model_router, 'transport'),
    // ... fan-out links for each model endpoint
  ],
}
```

The Go code that constructs this Program IS the subcategory morphism. It doesn't
"read the graph and dispatch" — it IS the algebra map that takes the specification
(what types, what ports, what wiring) and produces the composed operations.

**Scoped(Kernel) = the sub-operad fiber:**

| Scope          | Sub-operad                                         | What code sees                            |
| -------------- | -------------------------------------------------- | ----------------------------------------- |
| Scoped(User)   | Colors = user-owned types only                     | User's subgraph                           |
| Scoped(Admin)  | Colors = all managed types                         | Full managed set                          |
| Scoped(Kernel) | Colors = foundation types (NTs, protocols, routes) | State-changing rules + typed data streams |

The kernel sub-operad 𝓞_K contains:

- The 4 invariant NT generators (foundational state-changing rules)
- ProtocolAdapter operations (typed data streams: gRPC, WS, HTTP, WebRTC)
- CAN_ROUTE composition (wire-level routing between surfaces and tools)
- URN resolution (addressing scheme for typed endpoints)

Go code accesses objects/morphisms IN this projected subcategory directly:
`r.state.Nodes[urn]` = accessing an object in 𝓞_K's carrier
`fold.Evaluate(state, envelope)` = applying a morphism in 𝓞_K

**Design implication:** The kernel Go code should be structured to mirror the
sub-operad structure. Each Go package = a slice of the sub-operad:

- cat = the carrier types (objects and morphisms of the subcategory)
- fold = the algebra maps (structure-preserving evaluation)
- operad = the constraint checking (admissibility in 𝓞_K)
- shell = the effect boundary (where algebra meets persistence)
- transport = the port interface (where subcategory meets external world)

**The "purpose" of the kernel language:**
A programmer conveys purpose ON the machine by writing terms in 𝓞_K's algebra.
The sub-operad's algebra ENABLES this — it provides exactly the typed composition
rules needed for: splitting data streams, routing to models, wiring protocols.
What it does NOT provide (by design) is: user preferences, UI rendering,
benchmark scoring — those live in deeper layers of the full operad 𝓞.

### Functorial Semantics — Connecting Syntax to Semantics (2026-03-11, session 3)

**Reference:** Functorial Semantics as a Unifying Perspective (in .agent/knowledge_base/reference/papers)

**Core insight from discussion:**
The subcategory's language POINTS TO code but is only VISIBLE at the semantic
(category) level. The category names, port types, and morphism signatures are
the "semantics." The Go code (function bodies, struct fields) is the "syntax."
We need a FUNCTOR connecting the two:

$$F_{\text{sem}} : \mathcal{O}_K^{\text{op}} \to \mathbf{Go}$$

Where:

- $\mathcal{O}_K^{\text{op}}$ is the kernel sub-operad (semantic level: type names, ports, rules)
- $\mathbf{Go}$ is the category of Go types and functions (syntactic level: actual code)
- $F_{\text{sem}}$ maps each color to its Go carrier, each operation to its Go function

This functor IS Lawvere's functorial semantics applied to mo:os:

- The THEORY = $\mathcal{O}_K$ (what operations exist, abstractly)
- The MODEL = the Go implementation (how operations are computed, concretely)
- The functor = the bridge — it lets you reason at the semantic level
  (category names, composition rules) while the computation happens at the
  syntactic level (Go code)

**Key consequence — the "IDE hover" analogy:**
Category-level metadata (type names, port specs, morphism decompositions,
accumulated node payload summaries, user tags, relational edges) acts like
docstrings/type annotations in an IDE. You hover over a category name and
"see" what features are available — without reading the Go implementation.
The semantic layer IS the lens through which the kernel code is understood.

This is a PRESHEAF on $\mathcal{O}_K$: for each color $c$, the "metadata fiber"
$\text{Meta}(c)$ = { description, ports, strata, accumulated payload fields,
user tags, morphism log summaries }. This presheaf is the "documentation"
of the kernel subcategory, computable from graph state.

**agnostic_model belongs in 𝓞_K (DECIDED):**
Model routing is kernel-structural. The programmer gives purpose by directing
state changes through model endpoints — this is foundational to the kernel's
role as dispatch substrate. The sub-operad boundary expands:

$\mathcal{O}_K$ colors (confirmed):

- runtime_surface (kernel IS one)
- protocol_adapter (dispatch through)
- system_tool (resolve & invoke)
- infra_service (persist through)
- agnostic_model (route to — PURPOSE TARGET)

$\mathcal{O} \setminus \mathcal{O}_K$ colors (kernel evaluates uniformly):

- user, collider_admin, superadmin (identity)
- app_template, node_container (structural)
- ui_lens, memory_store (surface/memory)
- compute_resource (schedulable — may enter 𝓞_K later)
- preference, provider, benchmark\_\* (config/eval)
- agent_spec (identity-adjacent — may enter 𝓞_K later)

**Unfolding in kernel vs graph — authority boundary:**

| In 𝓞_K (kernel)               | In 𝓞\𝓞_K (graph)                 |
| ----------------------------- | -------------------------------- |
| Compiled, fast                | Dynamic, recursive               |
| Authoritative (main morphism) | Delegated (agent/user morphisms) |
| Programmer-defined            | Runtime-programmable             |
| Sub-operad algebra            | Full operad algebra              |

Speed: yes, kernel-expressed operations are faster (compiled Go, no graph
traversal overhead). They are also AUTHORITATIVE — the kernel's evaluation
IS the ground truth, not a derived projection.

The "main morphism" (mo:os catamorphism) gains power proportional to 𝓞_K's
expressiveness. Richer 𝓞_K = more purpose expressible in compiled code = more
authoritative fast-path operations. But also = bigger binary, less flexibility.

**The feedback loop:**
User gives purpose → kernel code changes (new terms in 𝓞_K) → graph state
evolves → accumulated metadata makes new features "visible" at semantic
level → next purpose is informed by what the lens shows → cycle repeats.

This is the self-referential fixed-point structure: the kernel computes the
graph, the graph describes the kernel, the metadata informs the programmer,
the programmer extends the kernel.

### mo:os as Primary Morphism

Categorically: mo:os IS the primary morphism. Specifically:

1. **mo:os = the catamorphism.** It IS the unique arrow from the initial F-algebra
   (the free monoid of envelopes = morphism log) to the carrier algebra (GraphState).
   `state(t) = fold(log[0..t])` — this IS what the kernel computes.

2. **mo:os = functor between categories.** From the category of specifications
   (ontology + config + instance files) to the category of running states
   (live graph + active wires + routed tools). The kernel program is the map.

3. **Self-referential:** The graph contains descriptions of the kernel itself
   (RuntimeSurface node, ProtocolAdapter nodes). The morphism that computes
   the graph IS ITSELF described by a node in the graph. This is the
   fixed-point structure — mo:os is the Y combinator of its own graph.

The expected data types that carry machine state = GraphState { Nodes, Wires }.
The expected morphism types that change machine state = Envelope { ADD, LINK, MUTATE, UNLINK }.
mo:os, the running kernel, IS the morphism that evaluates the former via the latter.

### OBJ21 AgentSpec — New Ontology Object (DECIDED)

AgentSpec joins the ontology as a first-class identity-adjacent object:

```
OBJ21 AgentSpec
- type_id: "agent_spec"
- broad_category: "identity"
- description: "Agent configuration container — defines an agent's identity,
  permissions, tool access, model preferences, and conversation context.
  Lives in the usergraph as a config node. MUTATE = reconfigure agent."
- source_connections: [CAN_HYDRATE, CAN_ROUTE, SYNC_ACTIVE_STATE]
- target_connections: [OWNS]
```

Hydration: `ADD(agent_node) ; LINK(user, 'owns', agent) ; LINK(agent, 'can_route', tool_1) ...`
Reconfiguration: `MUTATE(agent_node, { model, temperature, tools, context_window, ... })`

---

## Three-Layer Tower — Industry → Superset → Kernel (2026-03-11, session 4)

### The Tower

```
𝓞_K  (Kernel sub-operad)          ← Go code IS the algebra (5 colors)
  ↑ sub-operad inclusion (Include_K ⊣ Restrict_K)
𝓞_Superset  (Superset slice)       ← ontology.json = typed categories over industry
  ↑ classifying functor (classify : 𝓘 → 𝓞_Superset)
𝓘  (Industry base layer)           ← curated, updated real-world tech dataset
```

### Industry (𝓘) — the base

A curated dataset of everything that exists in real-world technology. NOT a mo:os
invention — the real world. Mo:os needs a structured, updatable view of it.
Lives in `.agent/knowledge_base/industry/`.

Changes because: the real world moves. New providers, protocols, tools appear.
Existing things get deprecated. Independent of mo:os evolution.

### Superset (𝓞_Superset) — the slice

The mo:os ontology that classifies industry into typed categories.
Lives in `.agent/knowledge_base/superset/ontology.json` (title: "mo:os Superset Ontology v3").
Old concept, now formally a SLICE CATEGORY over industry.

The superset doesn't create tech — it TYPES it:

- OBJ07 SystemTool classifies industry tools
- OBJ17 Provider classifies industry LLM providers
- OBJ11 ProtocolAdapter classifies industry protocols
- OBJ06 AgnosticModel classifies industry models

Changes because: hypergraph evolves, new categories grow, new TypeIDs/morphisms added.
Independent of industry changes (though may be triggered by them).

### Classifying Functor

$$\text{classify} : \mathcal{I} \to \mathcal{O}_{\text{Superset}}$$

Maps each industry entity to its superset type. Manifests as the `type_id` field
in instance entries. Example: industry entity "Anthropic Claude 3.7 Sonnet" →
type_id: "agnostic_model" (OBJ06).

The adjunction:

- classify ⊣ forget : 𝓘 → 𝓞_Superset
- classify sends raw industry data UP to typed superset objects
- forget sends typed superset objects BACK DOWN to raw industry entities

### OS/Program Partition

"ANYTHING YOUR OS AND ITS HTTP LINES BASICALLY OFFERS, REST IS PROGRAM"

**OS = 12 HTTP routes (compiled, authoritative):**

READ (9 projections — RLock):

- GET /healthz, /state, /state/nodes, /state/nodes/{URN}
- GET /state/wires, /state/wires/outgoing/{URN}, /state/wires/incoming/{URN}
- GET /log, /semantics/registry

WRITE (3 mutations — Lock):

- POST /morphisms (single envelope)
- POST /programs (composed batch)
- POST /hydration/materialize (template expansion)

**Program = everything else (composed, dynamic, runtime):**
Skills, tools, providers, templates, agents, workflows — all compose as Programs
of ADD/LINK/MUTATE/UNLINK envelopes, submitted via the 3 write endpoints.

The kernel stays thin (12 lines). Expressiveness = composition over lines.

### Information Loss at Each Level

```
𝓘 → 𝓞_Superset : loses provider-specific API quirks, internal detail
𝓞_Superset → 𝓞_K : loses non-kernel types (preferences, UI, benchmarks, identity)
```

Each projection is lossy. Counit of each adjunction is NOT iso.

---

## Next Executable Step

KB Curation plan approved (session 4): Phases 0-7.

1. Save state (this section) ✓
2. Rename registry/ → superset/ ✓ (done)
3. Ontology expansion OBJ14-21
4. Create industry/ layer
5. Fix instances + create tools.json, agents.json
6. De novo install mapping (doctrine/install.md)
7. Concept definitions (doctrine/concepts.md)
8. Concept-to-instance map

After KB curation: Layer B (--kb boot), Layer G.min (Postgres), Layer C (scoped projections).
