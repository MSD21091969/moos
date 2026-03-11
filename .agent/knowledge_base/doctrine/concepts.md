# Concept Definitions

Formal definitions for all architectural concepts in mo:os, with cross-references to KB files, kernel code, instance data, and skills.

---

## Three-Layer Tower

The mo:os architecture is a three-layer tower of categories connected by functors:

```
Industry (𝓘)  →  Superset (𝓞_Superset)  →  Kernel (𝓞_K)
   classify            Include_K ⊣ Restrict_K
```

### Industry (𝓘)

- **Definition**: Curated external technology landscape — providers, protocols, frameworks, tools, compute resources, capabilities. Updated independently from the real world.
- **KB location**: `industry/*.json` (7 files: providers, protocols, tools, frameworks, compute, features, schema)
- **Change driver**: Real-world tech evolution (new providers, models, protocols)
- **Not**: mo:os types (those are superset), not active instances (those are instances)

### Superset (𝓞_Superset)

- **Definition**: The mo:os type system — a colored operad with 21 objects, 16 morphisms, 4 invariant natural transformations, 22 categories, 10 subcategories, 5 functors. The superset is a **slice category** over the industry layer.
- **KB location**: `superset/ontology.json`
- **Kernel code**: `internal/operad/registry.go` → `Registry{Types map[TypeID]TypeSpec}`
- **Change driver**: Hypergraph evolution — new object kinds, morphisms, categories emerge as the categorical structure matures
- **Key property**: Title literally says "mo:os Superset Ontology v3"

### Kernel (𝓞_K)

- **Definition**: Compiled sub-operad — the 5 colors that the kernel directly struct-depends on. Everything else is evaluated uniformly by the 4 invariant natural transformations.
- **KB location**: `superset/ontology.json` (subset), `platform/kernel/internal/`
- **Kernel code**: `internal/operad/loader.go` → `DeriveFromOntology()`
- **5 colors**: `runtime_surface`, `protocol_adapter`, `system_tool`, `infra_service`, `agnostic_model`

---

## Classifying Functor

```
classify : 𝓘 → 𝓞_Superset
```

- **Definition**: Maps industry entities to superset type_ids. This is what makes the superset a slice category over the industry.
- **Manifestation**: The `type_id` field in instance entries. Every instance entry has a `type_id` that points to a superset object.
- **Example**: Industry entity "Anthropic" → `type_id: "provider"` (OBJ17). Industry entity "Claude 3.7 Sonnet" → `type_id: "agnostic_model"` (OBJ06).
- **Instance files**: Every `instances/*.json` entry has a `type_id` field
- **Industry files**: Every `industry/*.json` entry has an `ind:` prefixed ID

---

## OS/Program Partition

### OS

- **Definition**: The 12 HTTP routes that the kernel exposes. These are the **authoritative, compiled** API surface. They are the OS.
- **Kernel code**: `internal/transport/server.go` → 12 route registrations
- **Routes**: 9 read (GET) + 3 write (POST /state, POST /programs, POST /hydration/materialize)
- **KB location**: `instances/surfaces.json` → `urn:moos:surface:kernel-http`
- **Property**: The OS surface does NOT change when new types, tools, or providers are added

### Program

- **Definition**: A composed sequence of Envelopes (ADD/LINK/MUTATE/UNLINK) submitted to the kernel's 3 write endpoints. Everything that is not the OS is a Program.
- **Kernel code**: `internal/shell/runtime.go` → `ApplyProgram()`
- **KB location**: `doctrine/install.md` (Programs 1-11)
- **Property**: Skills, tools, providers, templates, agents — all enter as Programs
- **Key insight**: Programs cannot create new routes, new types, or new invariant NTs. They compose within the existing categorical structure.

---

## Authority Boundary (Adjunction)

```
Include_K ⊣ Restrict_K : 𝓞_Superset → 𝓞_K
```

- **Definition**: The adjunction between the full superset and the kernel sub-operad. `Include_K` embeds the 5 kernel colors into the superset. `Restrict_K` projects superset types down to the kernel level.
- **Kernel code**: `internal/operad/validate.go` → validation checks per TypeSpec
- **Effect**: Types in 𝓞_K get specialized Go struct handling. Types outside 𝓞_K are evaluated uniformly by the 4 NTs (ADD/LINK/MUTATE/UNLINK) with no kernel-structural dependence.
- **5 kernel colors**: runtime_surface (OBJ09), protocol_adapter (OBJ11), system_tool (OBJ07), infra_service (OBJ12), agnostic_model (OBJ06)

---

## Functorial Semantics

```
F_sem : 𝓞_K^op → Go
```

- **Definition**: The theory-to-model functor. Maps the abstract sub-operad to concrete Go implementations. Lawvere's functorial semantics applied to the kernel.
- **Reference**: `.agent/knowledge_base/reference/papers/` — "Functorial Semantics as a Unifying Perspective"
- **Kernel code**: Each 𝓞_K color maps to a Go struct/interface in `internal/`
- **Example**: `runtime_surface` → HTTP server registration, `protocol_adapter` → WebSocket/MCP session handling

---

## Meta Presheaf

```
Meta(c) = { description, ports, strata, payload_fields, user_tags, morphism_summaries }
```

- **Definition**: For each 𝓞_K color `c`, Meta(c) is the set of metadata computable from graph state. It's the "IDE hover" lens over the sub-operad.
- **Kernel code**: `GET /explorer` endpoint — renders graph state as navigable HTML
- **Instance data**: Every ontology object has `description`, `source_connections`, `target_connections`, `mutable`, `allowed_strata`
- **Property**: Computable (not stored), changes as graph state evolves

---

## Catamorphism — Primary Morphism

```
mo:os = cata : Free(𝓞_K) → GraphState
```

- **Definition**: The structure map (catamorphism) that folds the free algebra of the sub-operad into graph state. This IS mo:os — the primary morphism.
- **Kernel code**: `internal/fold/evaluate.go` → `EvaluateWithRegistry()` (fold), `internal/fold/evaluate.go` → replay from log
- **Related**: `shell.Runtime.Apply()` executes individual envelopes; `ApplyProgram()` composes sequences

---

## Hypergraph

- **Definition**: The stored graph is a superposition of port-typed subgraphs encoded via König's theorem. Each "wire" has port types (source_port, target_port) that partition the graph into typed subgraphs.
- **Doctrine**: `doctrine/hypergraph.md`
- **Kernel code**: `internal/cat/object.go` → `Wire{SourcePort, TargetPort}` fields
- **Property**: The full graph is the union (superposition) of all port-typed subgraphs

---

## Strata

```
S0 (Authored) → S1 (Validated) → S2 (Materialized) → S3 (Evaluated) → S4 (Projected)
```

- **Definition**: Layered realization pipeline. Each container exists at exactly one stratum. Strata form a total order.
- **Doctrine**: `doctrine/strata.md`
- **Kernel code**: `internal/cat/object.go` → `Stratum` type; `internal/operad/registry.go` → `TypeSpec.AllowedStrata`
- **Instance data**: Each ontology object has `allowed_strata` field specifying valid strata
- **Mapping**: S0=declarations, S1=validated, S2=materialized (graph-ready), S3=evaluated (runtime), S4=projected (views)

---

## Invariant Natural Transformations (4 NTs)

```
ADD : ∅ → Container    (create URN)
LINK : C × C → Wire    (create edge)
MUTATE : C → C         (update state)
UNLINK : Wire → ∅      (remove edge)
```

- **Definition**: The 4 atomic operations on graph state. Every morphism decomposes into a sequence of these NTs. They are **invariant** — they don't change when the superset evolves.
- **Kernel code**: `internal/shell/runtime.go` → `Apply()` switch on `Envelope.Action`
- **Property**: Programs compose NTs. The OS executes NTs. The catamorphism folds NTs.

---

## De Novo Install

- **Definition**: Fresh `git clone` → `go build` → boot with `--kb` → self-hydrating Programs. Every field in the running system is created by a Program.
- **Doctrine**: `doctrine/install.md` (Programs 1-11)
- **Tiers**: T0 (file reads), T1 (seed Programs via SeedIfAbsent), T2 (bootstrap Programs via API)
- **Property**: No manual database setup, no migrations, no seeds outside Programs
