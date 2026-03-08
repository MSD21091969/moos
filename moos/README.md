# mo:os — Categorical Graph Kernel

An evaluation engine that reduces morphisms over a typed graph.
Everything is a category. Everything else is a projection.

Current values: Go 1.23 kernel, PostgreSQL persistence, pgvector embeddings.

Active forward-work path: `D:\FFS0_Factory\moos\platform`.

> [!IMPORTANT]
> This README primarily documents a legacy MOOS runtime snapshot preserved for reference.
> For forward work in this repository, only `moos/platform/` is active. The rest of the
> `moos/` tree should be treated as archival implementation context unless explicitly reactivated.

---

## What mo:os Is

mo:os is a **semantic evaluation engine**. It does not run "apps." It maintains a
typed graph of objects organized into categories, connected by wires, and
mutated exclusively through four invariant morphisms: `ADD`, `LINK`, `MUTATE`,
`UNLINK`. All state lives in the graph. All history lives in the morphism log.
All views (UI, agent chat, API, CLI) are lenses projected over the graph.

The kernel's job:

```
Syntax (envelope) → Validation → Evaluation → Graph Mutation → Log
```

That's it. No framework, no ORM abstractions, no app lifecycle.

---

## Categories

mo:os organizes all objects into **categories** — typed semantic domains that must
be named before any concrete object is accepted. Categories are hydrated at
installation time and extended at runtime through morphisms.

### Essential Categories (always present)

| ID | Category | What it holds | Level |
|----|----------|---------------|-------|
| CAT01 | `identity` | Authenticated users, groups, governance actors | L0/L2 |
| CAT02 | `platform` | OS, architecture, CPU, GPU, RAM — detected at install | L0/L1 |
| CAT03 | `compute` | Kernel runtime, LLM providers, CUDA capabilities | L0/L1 |
| CAT04 | `preference` | User/system/workspace/session defaults | L0/L1 |
| CAT05 | `transport` | HTTP, WebSocket, MCP/SSE surfaces and ports | L0 |
| CAT06 | `governance` | Invariant morphism algebra, normalization rules, log truth | L2 |

### Common Categories (hydrated on demand)

| ID | Category | What it holds | Level |
|----|----------|---------------|-------|
| CAT07 | `workspace` | User's reachable subgraph (owned full subcategory) | L1 |
| CAT08 | `agent` | Interaction lens — evaluated actor subgraph over compute + identity | L1 |
| CAT09 | `extension` | Chrome extension surface (optional transport) | L0/L1 |
| CAT10 | `benchmark` | Provider scoring dimensions, comparison suites | L1/L2 |

### Levels

- **L0** — Object/Morphism: concrete graph entities and transitions
- **L1** — Category/Functor: structure-preserving mappings, typed vocabularies
- **L2** — Coherence/Governance: invariants, permissions, lifecycle rules

---

## Identity & Groups

There are no "roles." There are **group objects** with **OWNS morphisms**.
Permissions are graph reachability — what you can reach via OWNS edges is what
you can do.

| Group | URN | Morphisms | Who |
|-------|-----|-----------|-----|
| `superadmin` | `urn:moos:group:superadmin` | Transitive OWNS over all categories | Kernel operators, repo write access |
| `collider_admin` | `urn:moos:group:collider_admin` | OWNS on assigned categories, CAN_HYDRATE on S1 | Category maintainers |
| `user` | `urn:moos:group:user` | CAN_HYDRATE own workspace, read shared | Authenticated actors |

The old `app_admin` and `app_user` roles are gone. "App" is a projection surface,
not ontology. Groups are graph objects. Membership is a wire.

---

## Installation as Hydration

Installing mo:os is not "configuring." It is the kernel detecting the platform
and hydrating categories with initial objects via morphisms. The install log IS
the morphism log. There is no special install mode.

The bootstrap functor:

```
F_bootstrap: P_platform → C_S1
```

Detects what's on the machine, creates objects in the essential categories,
wires them together. Every step is an ADD or LINK recorded in `morphism_log`.

### Baseline: HP Z440 Workstation (superadmin)

This is the reference installation. 14 morphisms produce the complete initial
state for one superadmin on a low-budget workstation.

```
── identity ──────────────────────────────────────────────────
ADD   urn:moos:user:geurt                kind=identity
ADD   urn:moos:group:superadmin          kind=group
LINK  urn:moos:user:geurt.member_of    → urn:moos:group:superadmin.members

── platform ──────────────────────────────────────────────────
ADD   urn:moos:platform:z440             kind=platform
        os=windows_11  arch=x86_64  cpu=xeon_e5_1650v3
        ram_gb=32  gpu=quadro_k2200  gpu_cc=5.0  cuda=11.8
LINK  urn:moos:user:geurt.runs_on      → urn:moos:platform:z440.user

── compute ───────────────────────────────────────────────────
ADD   urn:moos:provider:gemini           kind=provider
ADD   urn:moos:provider:anthropic        kind=provider
ADD   urn:moos:provider:openai           kind=provider
LINK  urn:moos:user:geurt.default      → urn:moos:provider:gemini.user

── preference ────────────────────────────────────────────────
MUTATE urn:moos:user:geurt
        prefs={theme:dark, layout:TB, streaming:true, auto_embed:true}

── workspace ─────────────────────────────────────────────────
ADD   urn:moos:workspace:geurt_root      kind=workspace
LINK  urn:moos:user:geurt.owns         → urn:moos:workspace:geurt_root.owner

── transport ─────────────────────────────────────────────────
ADD   urn:moos:surface:data_api          kind=transport  port=8000
ADD   urn:moos:surface:mcp_sse           kind=transport  port=8080
ADD   urn:moos:surface:nanoclaw_ws       kind=transport  port=18789
```

### Variant: MacBook Air M3 (new user)

Same categories, different objects:

```
ADD   urn:moos:platform:mba_m3           kind=platform
        os=macos_15  arch=arm64  cpu=apple_m3  ram_gb=16
        gpu=apple_m3_gpu  gpu_cc=none  cuda=none
LINK  urn:moos:user:alice.member_of    → urn:moos:group:user.members
```

No CUDA — the Embedding functor falls back to CPU. The graph structure is
identical. Only the objects differ.

---

## Invariants

These hold always, enforced by the kernel, not by convention.

| # | Invariant |
|---|----------|
| 1 | Four morphisms only: ADD, LINK, MUTATE, UNLINK |
| 2 | Morphism log is append-only source of truth |
| 3 | Optimistic concurrency — version CAS on mutation |
| 4 | Category before implementation — no object without parent category |
| 5 | Wire uniqueness — (from, from_port, to, to_port) |
| 6 | Every morphism has an actor URN |

How these are currently enforced (values in `infra` category):
CHECK constraint on log type, no UPDATE/DELETE grant on log table,
version column with CAS check, UNIQUE on wire tuple, NOT NULL on actor.

---

## Strata

The graph has four layers. Higher strata depend on lower ones via explicit
inclusion maps. Lower strata never reference higher ones.

| Stratum | Name | Contents |
|---------|------|----------|
| S0 | Bootstrap | Morphism algebra, kernel reducer, log truth, validation |
| S1 | Authoring | Category declarations, port vocabularies, governance presets |
| S2 | Operational | User categories, hydrated tools, provider resources, state |
| S3 | Projection | UI lenses, agent chat, dashboards — never stored as truth |

---

## Embedding Functor (Wave 5)

The Embedding functor maps graph substructures to a hyperdimensional vector
space H for similarity retrieval.

H is a **symmetric monoidal category** with biproduct structure:

| Operation | Symbol | Categorical role | Implementation |
|-----------|--------|------------------|----------------|
| Bind | ⊗ | Monoidal product | Element-wise XOR (BSC) |
| Bundle | ⊕ | Coproduct (biproduct) | Element-wise addition |
| Permute | π | Endofunctor | Circular shift |
| Similarity | cos(x,y) | Hom-set computation | Dot product |

Wire encoding:

```
φ(wire) = S ⊗ φ(src) ⊕ SP ⊗ φ(src_port) ⊕ T ⊗ φ(tgt) ⊕ TP ⊗ φ(tgt_port)
```

GPU residence is an implementation detail of the codomain, not a categorical
property. The persistence substrate currently uses pgvector with an HNSW index.
Go runtime HDC operations are the Wave 5 target.

---

## Transport Surfaces

Transport surfaces are **morphisms in C**, not functors. They carry the four
invariant operations over network protocols. Adding a new transport creates a
new wire, not a new functor.

Current values (objects in `transport` category):

| Surface | Port | Protocol |
|---------|------|----------|
| Data API | 8000 | HTTP |
| Tool Server | 8001 | HTTP |
| MCP/SSE | 8080 | JSON-RPC + SSE |
| NanoClaw | 18789 | WebSocket |
| Chrome Extension | — | Connects to MCP |

---

## Normalization Rules

These prevent the codebase from re-importing non-categorical terminology.

1. **Category before implementation.** No concrete noun without a parent category.
2. **Purpose before packaging.** The semantic anchor is purpose, not app/product.
3. **Topology before inventory.** State = reachable graph condition, not stored bags.
4. **Semantics before transport.** HTTP/WS/MCP/CLI are transport, not meaning.
5. **Projection is not ontology.** UI/agent/dashboard are lenses over the graph.
6. **Skill/tool/provider is downstream.** Above the syntax/semantics bridge.
7. **Metadata is secondary.** Graph structure carries primary semantics.

Anti-patterns to reject immediately:

- "the app does X" → which category, subgraph, or projection?
- "the agent decides" → which evaluated actor subgraph, constrained how?
- "the API is the architecture" → which semantic layer is being exposed?

---

## Persistence

The graph requires a substrate that can store objects, wires, and an
append-only morphism log. Current value: PostgreSQL with pgvector.

| Substrate role | Current table | What it holds |
|----------------|---------------|---------------|
| Object store | `containers` | URN-keyed objects with versioned JSONB payloads |
| Wire store | `wires` | Typed edges (4-tuple unique) |
| Truth log | `morphism_log` | Append-only record of every mutation |
| Embedding index | `embeddings` | Vector(1536) with HNSW cosine index |

---

## Running (current values)

```bash
# Full stack
docker compose -f docker-compose.dev.yml up -d

# Kernel only (persistence substrate must be running)
go run ./cmd/kernel

# Tests
go test ./... -v
```

Health: `http://localhost:8000/health`
Metrics: `http://localhost:8000/metrics`

---

## Platform Packaging & Presets

Platform-specific runtime assets now live under `platform/`.

- `platform/presets/` holds declarative launch presets for runtime environments.
- `platform/windows/installers/` is the home for Windows installer payloads such as `install.exe` plus their metadata.
- `platform/linux/installers/` and `platform/darwin/installers/` hold equivalent packaging assets for other operating systems.

The intent is to keep kernel semantics platform-agnostic while making runtime assumptions explicit and versioned.

---

## Repo Access

This repository is the source of truth. The kernel, migrations, datasets,
chrome extension, and documentation all live here. Write access requires
membership in `superadmin` or `collider_admin` groups — which means an
OWNS edge from your identity to one of those group objects in the graph.
