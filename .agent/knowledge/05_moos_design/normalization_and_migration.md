# mo:os — Category Normalization & FFS1 Migration

> Consolidates `category_normalization_sheet.md` + `ffs1_keep_reinterpret_discard_matrix.md`.
> Use this document before naming modules, APIs, categories, or repo surfaces, and as the semantic filter for migrating FFS1 concepts into the greenfield `moos` rebuild.
>
> **Related**: `strata_and_authoring.md` (strata decisions this sheet references),
> `kernel_specification.md` §6 (module layout these names flow into),
> `06_planning/greenfield_implementation_waves.md` (implementation target for migration decisions).

---

## Part 1 — Category Normalization Sheet

Purpose: prevent the greenfield `moos` rebuild from re-importing app/OOP/industry-buzz terminology as if it were ontology. Every concrete implementation noun must first normalize to a category, level, and graph role before it is accepted into design or code.

### Normalization rules

1. **Category before implementation.** Never accept a concrete noun (`API`, `tool`, `workstation`, `provider`, `skill`, `package`) as a primary design term until its parent category is named.
2. **Purpose before packaging.** The root semantic anchor is purpose, not app, product surface, or UI shell.
3. **Topology before inventory.** State means reachable/evaluable topological condition, not just a bag of stored objects.
4. **Semantics before transport.** HTTP, WebSocket, MCP/SSE, CLI, and file exchange are transport morphisms, not semantic roots.
5. **Projection is not ontology.** UI, agent chat, dashboards, sidepanels, and viewers are lenses/projections over the graph.
6. **Skill/tool/provider integration is downstream.** It sits above the syntax/semantics bridge and must not redefine kernel semantics.
7. **Metadata is secondary.** Prefer semantics from category naming, port signatures, reachable subgraph structure, and morphism constraints.
8. **Mock categories are legal, but temporary.** Every mock category must be marked for delete, promote, split, or reclassify.

### Level legend

- **L0 — Object/Morphism level**: concrete graph entities and graph transitions
- **L1 — Category/Functor level**: categories, subcategories, structure-preserving mappings, typed vocabularies
- **L2 — Coherence/Governance level**: invariants, permissions, lifecycle rules, benchmark comparability, naturality constraints

### Core normalization table

| Concrete noun / phrase | Normalize to | Level | Role in mo:os | Notes |
| --- | --- | --- | --- | --- |
| root container | **root purpose** / purpose-anchor category | L1 | top semantic anchor | Replace old container-centric framing entirely. |
| app | projection surface / packaged subgraph / lens target | L1 | optional presentation or distribution form | Never ontology root. |
| frontend | UI lens / projection functor target | L1 | rendered view of graph state | FFS4/5/6 are examples of projections. |
| sidepanel / dashboard / viewer | lens/projection surface | L1 | user-facing slice of graph | Treat as one of many possible views. |
| user graph | reachable, permissioned subgraph / state-transition trace | L1 | user-specific active slice of collider hypergraph | Not a separate app tree. |
| state | topological/evaluable graph condition | L1 | semantic condition of reachable structure | Not flat object inventory. |
| API | exposed morphism surface / interface vocabulary | L0/L1 | way graph semantics are accessed | Must be categorized by transport and semantic contract. |
| endpoint | transport-specific morphism path | L0 | concrete access path | Example: REST route, SSE stream, WS channel. |
| transport | connection morphism family | L0 | moves graph-structured requests/results | Not a functor unless structure-preserving mapping is proven. |
| protocol | transport grammar / channel vocabulary | L1 | shapes message form over a connection | Distinct from meaning itself. |
| MCP | transport surface for tool-use clients | L0/L1 | one connection morphism family | Downstream of semantic bridge. |
| WebSocket | transport morphism | L0 | push/pull channel | Infrastructure, not ontology. |
| HTTP | transport morphism | L0 | request/response channel | Infrastructure, not ontology. |
| CLI | transport/execution surface | L0 | local invocation surface | Same rule: morphism, not ontology root. |
| kernel | evaluation engine / reducer / semantic executor | L1 | maps syntax to semantics | Operationally the evaluation functor/reducer pipeline. |
| Go runtime | implementation setting / execution substrate object | L0 | current concrete runtime choice | Important, but not ontology center. |
| programming language | implementation-substrate category | L1 | medium for kernel/effect adapters | Go/F#/etc. are choices inside a broader category. |
| functional programming language | morphism-construction substrate | L1 | may be used to author evaluators or graph-building logic | Keep distinct from kernel semantics itself. |
| tool | evaluable capability resource / hydrated code-bearing object | L0/L1 | code becomes semantics only on evaluation | Treat as graph-bound resource, not magic registry entry. |
| skill | capability classification / routing-or-composition schema / higher-order template | L1 | organizes discovery, composition, or benchmarking | Distinct from tools; should not collapse into prompts. |
| prompt | syntax artifact / input object | L0 | one possible input into evaluation | Never the semantic control plane. |
| agent | lens role + optional evaluated semantic actor subgraph | L1 | one projection/interaction form over graph semantics | Not the root computational concept. |
| swarm / multi-agent system | composed subgraph of evaluable actors/resources | L1 | orchestration pattern inside graph | Must remain subordinate to kernel semantics and topology. |
| provider | benchmarkable external capability source | L1 | substitutable source of model/tool execution | Provider swap should not alter ontology. |
| model | evaluable provider-scoped object/category member | L0/L1 | candidate semantic coprocessor | Benchmark and governance object, not root. |
| LLM | fuzzy processing unit / proposal generator | L1 | proposes morphisms or semantic candidates | Kernel validates before commit. |
| runtime | execution substrate category | L1 | concrete environment for evaluation or hydration | Separate from purpose/category semantics. |
| dependency | external resource object / implementation-substrate relation | L0/L1 | linked support resource | Do not treat as hidden ambient force. |
| package / library | code resource object / reusable syntax asset | L0 | implementation artifact referenced by graph | Secondary to graph meaning. |
| spec | schema object / constraint vocabulary | L1 | types ports, payloads, or compatibility | Important in syntax layer. |
| schema | syntax-category structure | L1 | defines composable forms | Central to syntax side of bridge. |
| interface | declared compatibility boundary / port-signature vocabulary | L1 | controlled crossing point | Avoid vague use; tie to typed port signatures. |
| metadata | secondary descriptive payload | L0 | auxiliary annotation only | Should not carry the main semantics. |
| JSON payload | syntax-bearing state fragment | L0 | structured input/cache/result | Not identity, not ontology. |
| URN / ID | identity object/property | L0 | opaque identity anchor | Identity is not behavior. |
| auth user | identity object plus permission morphisms | L0/L2 | authorized actor in graph | Authentication gives reachability, not special ontology. |
| role | permission signature / governance classification | L2 | constrains reachable morphisms | Prefer explicit graph permissions over app roles. |
| permission | allowed morphism set / reachability constraint | L2 | governs transitions and access | Should attach to graph movement. |
| group | governance object / permission distribution subgraph | L1/L2 | package/expose category subsets | Preferred over app-admin framing. |
| admin | governance capability holder | L2 | may mint or authorize categories/morphisms | Prefer collider-admin / group-admin semantics. |
| workspace | owned/scoped full subcategory / reachable subgraph | L1 | structural and permission boundary | Not an app shell. |
| project | nested subcategory / packaged concern | L1 | organizational slice within larger graph | Use only if structure matters. |
| document / file | syntax-bearing object | L0 | content resource in graph | Can be hydrated, embedded, benchmarked, projected. |
| workstation / machine | compute-platform object | L0/L1 | infrastructure resource with capabilities | Example: user GPU box, local host, server. |
| OS / platform | platform capability category | L1 | install/hydration substrate | Windows/macOS/Linux are values or objects in this category. |
| install preset | bootstrap configuration subgraph | L1 | initial hydration path for a platform/user type | Good candidate for explicit mock/canonical distinction. |
| infrastructure | graph-moving and graph-hosting resource category | L1 | channels, stores, execution hosts, caches | Must be described in terms of graph movement. |
| database | persistence substrate / syntax store / log anchor | L0/L1 | stores identity, wires, morphism history, caches | Important substrate, not equivalent to semantics. |
| cache | derived syntax/result store | L0 | optimization artifact | Never source of truth. |
| benchmark | comparison functor / evaluation program | L1/L2 | compares provider/tool/category behavior | Must record topological context. |
| metric | traversal/evaluation measure | L2 | optimization and observability signal | Includes D/R, hydration cost, branching cost. |
| topology | structural reachability/composability relation | L1 | core state and evaluation context | One of the primary semantic carriers. |
| hypergraph | superset of possible category/object/morphism arrangements | L1 | full source-space of reachable structures | User graphs are slices/traces inside this. |
| category | typed semantic domain | L1 | parent structure for objects and morphisms | Must be named before concrete objects are accepted. |
| subcategory | scoped semantic domain / typed slice | L1 | ownership, behavior, or permission partition | Can arise from OWNS, signatures, or governance. |
| morphism | valid graph transition / relation / action | L0 | semantic movement in the graph | Primary action unit. |
| invariant morphism set | canonical algebra of allowed transitions | L2 | ADD/LINK/MUTATE/UNLINK-like kernel contract | Basis for decomposition/composition guarantees. |
| lens | projection or view mapping | L1 | renders or selects graph structure | Agent/UI should usually normalize here first. |
| feature | packaged semantic capability or exposed projection bundle | L1 | public-facing composition of lower layers | Must not replace category naming with buzzwords. |

### Anti-normalizations to reject

These phrases should be challenged immediately during planning:

- "the app does X" → ask: **which category, subgraph, or projection?**
- "the agent decides" → ask: **which evaluated actor subgraph, constrained by what purpose and permissions?**
- "the tool means X" → ask: **which code-bearing resource, hydrated in what topological context?**
- "the API is the architecture" → ask: **which semantic layer is merely being exposed through transport?**
- "the metadata says what it is" → ask: **what graph structure, port signature, or category name already carries that meaning?**
- "the provider is the capability" → ask: **what category of capability remains invariant under provider substitution?**

### Open design decisions this sheet exposes

1. **Kernel stratum question**: should boot/kernel categories live in the same graph stratum as user categories, or in a distinguished bootstrap stratum with explicit inclusion maps? → See `strata_and_authoring.md`.
2. **Skill definition question**: should skills normalize primarily to capability classifications, subgraph templates, or benchmark/routing vocabularies?
3. **Tool definition question**: should tools be treated as objects with hydration morphisms, or as named executable subgraphs whose identity is mostly relational?
4. **Platform question**: should machine/OS/platform/spec categories remain explicit in the public ontology, or stay mostly in bootstrap/install strata?

---

## Part 2 — FFS1 → mo:os Keep / Reinterpret / Discard Matrix

Purpose: classify active FFS1 implementation surfaces against the normalization rules above so the rebuild does **not** confuse current implementation details with future ontology. This is a migration lens, not a command to serialize every existing module into fixed graph objects.

Related references:
- [`semantic_layer_rebuild.md`](./semantic_layer_rebuild.md)
- [`../superset/superset_ontology_v2.json`](../superset/superset_ontology_v2.json)

### Superset v2 check: structure is strong, chronology needs caution

The v2 superset files are **useful and well-structured** as a typed inventory, but their dates need interpretation:

- embedded ontology `date` field in `superset_ontology_v2.json`: `2026-07-14`
- on-disk file timestamps: **2026-03-07** local time

The ontology is structurally valuable but the embedded date is **future-dated** and should not be treated as reliable chronology. Use it as a **typed design inventory**, not as proof of temporal sequence.

What the v2 superset contributes well:
- explicit **axioms** (`AX1`–`AX5`)
- explicit **object inventory** (`AuthUser`, `NodeContainer`, `SystemTool`, `RuntimeSurface`, `ProtocolAdapter`, `InfraService`, `MemoryStore`, etc.)
- explicit **morphism inventory** (`OWNS`, `CAN_HYDRATE`, `CAN_ROUTE`, `CAN_PERSIST`, etc.)
- explicit **functors** (`FileSystem`, `UI_Lens`, `Embedding`, `Structure`, `Benchmark`)

What still needs reinterpretation through Part 1 normalization:
- `RootContainer` → should use **root purpose** instead
- `AppAdmin` → recast into group/governance language
- `NodeContainer` → legacy anchor term, compatibility/storage vocabulary only
- `SystemTool` → evaluable capability resource, not privileged primitive
- `RuntimeSurface` / `ProtocolAdapter` → useful categories, but must not outrank the syntax/semantics bridge

### Decision legend

- **Keep** — preserve the concept almost directly
- **Reinterpret** — preserve the value, but rename/reframe/re-scope it categorically
- **Discard** — remove as ontology root or implementation habit

### Matrix

| Current FFS1 surface | Current role | Normalize to | Level | Decision | Why |
| --- | --- | --- | --- | --- | --- |
| `cmd/kernel/main.go` overall kernel bootstrap | starts transports, wires runtime services, hosts API/WebSocket/MCP surfaces | bootstrap evaluator assembly / effect-boundary composition | L1 | Reinterpret | Valuable as runtime assembly reference, but too host-centric to be ontology. |
| `main.go` reducer flow (route → dispatch → transform → commit) | current operational kernel path | evaluation functor / semantic reducer pipeline | L1 | Keep | This is close to the real semantic heart and should survive conceptually. |
| `main.go` HTTP server setup | REST ingress and health/metrics exposure | transport morphism surface | L0 | Reinterpret | Keep as infrastructure adapter, not semantic core. |
| `main.go` WebSocket gateway | persistent push/pull transport | transport morphism surface | L0 | Reinterpret | Same as HTTP: useful, but infra not ontology. |
| `main.go` MCP bridge / SSE broker | MCP tool-use exposure and session fanout | transport surface for capability hydration/discovery | L0/L1 | Reinterpret | Important interoperability surface, but downstream of semantic bridge. |
| `main.go` model dispatcher | routes calls to Anthropic/Gemini/OpenAI adapters | provider dispatch adapter / benchmarkable provider category access | L1 | Reinterpret | Preserve provider interchangeability, not provider-central architecture. |
| `main.go` session manager | manages chat/session lifecycles around model/tool execution | actor/session orchestration adapter | L1 | Reinterpret | Useful as orchestration ancestry, but current "session manager" framing is too app-centric. |
| `main.go` `authorizeAPIRequest` fallback behavior | auth gate with token-optional mode | permission/reachability check | L2 | Reinterpret | Permission stays; permissive fallback should not survive unchanged. |
| `/health`, `/metrics`, `/health/db` endpoints | ops visibility | observability projection surfaces | L1/L2 | Keep | Operationally necessary, but clearly projection/ops layer. |
| CRUD-style `/api/v1/containers*` routes | direct container/wire mutation/read API | graph mutation/read transport surface | L0/L1 | Reinterpret | Keep the capability, rename around graph semantics rather than container CRUD. |
| `/api/v1/morphisms` endpoint | explicit morphism ingestion | morphism ingress surface | L0/L1 | Keep | This is the closest transport surface to the intended semantic contract. |
| `container.Store` | DB-backed persistence API | persistence substrate / graph syntax store | L0/L1 | Reinterpret | Keep the substrate role, but not as the ontology center. |
| `container.Record` | container row model with `kind`, `interface_json`, `kernel_json`, `permissions_json`, `version` | graph object syntax record | L0 | Reinterpret | Useful record shape, but `container` name and JSON-field semantics need recasting. |
| `Record.ParentURN` | tree-style parent pointer | one structural relation / scoped subcategory hint | L1 | Reinterpret | Useful only as one relation among many; should not dominate the model. |
| `Record.Kind` | coarse type tag | category or category-member label | L1 | Reinterpret | Valuable if elevated into explicit category discipline. |
| `Record.InterfaceJSON` | interface/config payload | syntax boundary / port-signature or compatibility fragment | L1 | Reinterpret | Should become more precise than generic "interface json." |
| `Record.KernelJSON` | state/config payload used by kernel | syntax-bearing evaluation fragment | L0/L1 | Reinterpret | Useful, but should not be mistaken for semantics itself. |
| `Record.PermissionsJSON` | per-record permissions payload | governance/permission syntax | L2 | Reinterpret | Keep governance role, but likely move toward explicit graph permissions. |
| `Record.Version` | optimistic concurrency counter | temporal consistency / replay coordination value | L0/L2 | Keep | Needed for safe mutation and log coherence. |
| `WireRecord` | explicit edge row between two containers | morphism relation record / typed connection syntax | L0 | Keep | This is very close to the desired graph-native structure. |
| `MetadataJSON` on wires | extra edge annotations | secondary descriptive payload | L0 | Reinterpret | Allow, but demote; structure and typed ports should carry primary meaning. |
| `MorphismLogRecord` / `MorphismLogEntry` | append-only audit trail of changes | semantic event log / source of truth | L1/L2 | Keep | This is one of the strongest parts of the current implementation ancestry. |
| `AppendMorphismLog` after mutation | audit append after store operation | event-log commit path | L1/L2 | Keep conceptually | Keep the log-first truth idea; implementation should become atomic/transactional. |
| `TreeTraversal` | recursive parent-child traversal | one projection over scoped subcategory structure | L1 | Reinterpret | Useful as a projection, but not the canonical shape of the graph. |
| `ListChildren` | parent-based child listing | ownership/subcategory projection | L1 | Reinterpret | Same reason: keep as one slice, not the whole ontology. |
| `ListByKind` | query by kind tag | category-member retrieval projection | L1 | Reinterpret | Useful if category discipline is formalized. |
| `morphism.Executor` overall | applies ADD/LINK/MUTATE/UNLINK and logs results | invariant morphism evaluator | L1 | Keep | This is the clearest semantic ancestor in current FFS1. |
| `Executor.Apply` switching on 4 invariant operations | dispatch over core algebra | invariant morphism decomposition/composition gate | L1 | Keep | This is exactly the kind of contract the new kernel should preserve. |
| `Executor.Add/Link/Mutate/Unlink` | atomic graph operations | canonical invariant morphism set | L1/L2 | Keep | Strongest candidate for direct conceptual inheritance. |
| `Executor.append(...)` payload logging | records semantic steps | process-verification / audit mechanism | L2 | Keep | Strong fit with process-verified semantics. |
| `actorURN` in executor | records source actor identity | identity + permission-bearing actor reference | L0/L2 | Keep | Identity and attribution matter, but should be categorized explicitly. |
| `ErrInvalidEnvelope` | malformed morphism rejection | syntax validation failure | L1/L2 | Keep | Important to keep explicit syntax/semantics boundary. |
| `graphStore.ts` overall | Zustand store for XYFlow nodes/edges | UI lens state / projection cache | L1 | Reinterpret | Valuable projection reference, not kernel truth. |
| `GraphMorphism` union (`ADD_NODE_CONTAINER`, `LINK_NODES`, etc.) | frontend event vocabulary | projection-specific derived morphism vocabulary | L1 | Reinterpret | Useful for UI translation, but not canonical kernel algebra. |
| `ADD_NODE_CONTAINER` | UI-side create-node event | projection of ADD + UI node instantiation | L1 | Reinterpret | Should derive from canonical morphisms, not replace them. |
| `LINK_NODES` | UI-side edge creation event | projection of LINK | L1 | Reinterpret | Same as above. |
| `UPDATE_NODE_KERNEL` | UI-side node patch event | projection of MUTATE | L1 | Reinterpret | Same as above. |
| `DELETE_EDGE` | UI-side edge removal event | projection of UNLINK | L1 | Reinterpret | Same as above. |
| XYFlow node positions / `nodeCard` type | render-specific layout and component identity | lens-local projection data | L0/L1 | Keep only as projection | Needed for UI, but must stay outside ontology. |
| `skillCount` / `toolCount` in `NodeData` | frontend summary counters | projection metadata over capability categories | L1 | Reinterpret | Counters may remain UI summaries, but "skill/tool" wording should be normalized. |
| `hasContainer` in `NodeData` | legacy container framing leak | projection flag from legacy model | L0 | Discard | Strong signal of old ontology leaking into frontend. |
| `path`, `label`, `emoji`, `domain` in `NodeData` | UI-friendly render metadata | lens metadata / display annotations | L0 | Keep only as projection | Fine for UI ergonomics, not semantic ground truth. |
| frontend `reset`, `loading`, `error` store state | UI control flow | lens runtime state | L0 | Keep only as projection | Necessary for UX, irrelevant to ontology. |

### What should become canonical in the new repo

The matrix suggests these current ideas are strong candidates for direct conceptual inheritance:

1. **Invariant morphism core** — `ADD`, `LINK`, `MUTATE`, `UNLINK`
2. **Append-only morphism log as truth anchor**
3. **Kernel reducer pipeline**
4. **Wire record as first-class typed relation**
5. **Provider interchangeability as adapter discipline, not ontology**
6. **Frontend as projection/lens, not business logic center**

### What must be demoted

These currently useful things should survive only as lower-level strata:

- HTTP / WebSocket / MCP / CLI surfaces
- session management and auth middleware
- persistence structs and JSON fields
- UI node labels, counts, positions, and component types
- `kind` filtering and tree traversal as one projection among many

### What should be actively removed from the new ontology

- container-centric naming as the base ontology
- `RootContainer` / `NodeContainer` as canonical type names
- treating parent/child tree structure as the dominant graph model
- frontend-derived morphism names becoming canonical semantic operations
- provider/model/tool/session vocabulary acting as root language instead of normalized categories
- UI flags such as `hasContainer` pretending to express semantics

### Reduction target for the numbered knowledge folders

The numbered folders should converge on this shape:

1. **`01_foundations`** — one axiom, purpose as top semantic anchor, invariant morphism algebra, syntax/semantics bridge, topology/subcategory language, explicit demotion of `container` to compatibility/storage wording
2. **`02_architecture`** — kernel reducer pipeline as semantic executor, effect boundaries and transport wrappers, morphism log as truth anchor, permission/federation/runtime switching as graph behavior
3. **`05_moos_design`** — active rewrite decisions only: normalization, keep/reinterpret/discard lenses, bootstrap decisions, authoring decisions — candidate material waiting to be promoted into `01` or `02`
4. **`06_planning`** — rollout, launch, backlog, conference, and implementation planning — never direct ontology truth
