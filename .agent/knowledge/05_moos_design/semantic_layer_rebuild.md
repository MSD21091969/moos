# mo:os Semantic-Layer Rebuild

> **Status**: This document's phase structure has been **superseded** by
> `06_planning/greenfield_implementation_waves.md` for implementation sequencing.
> It remains valuable as the **rationale and verification checklist** for WHY
> each phase exists. Read this for the reasoning; read `greenfield_implementation_waves.md`
> for the concrete wave-by-wave build plan.
>
> **Concrete specs**: The kernel design decisions referenced here are now
> formalized in `kernel_specification.md` (§2–§12) and `hydration_lifecycle.md` (§1–§10).
> Strata decisions are in `strata_and_authoring.md` (Parts 1–5).

Related artifacts:
- [`normalization_and_migration.md`](./normalization_and_migration.md) — category normalization rules + FFS1 keep/reinterpret/discard matrix. Use this before naming modules, APIs, categories, or repo surfaces.
- [`strata_and_authoring.md`](./strata_and_authoring.md) — bootstrap strata decision and FP authoring JSON output policy.

Create a new open-source `moos` repository from the FFS1 boundary only
as a greenfield rewrite, not a lift-and-shift extraction. Ground the
rebuild in FFS0’s active `.agent/knowledge`, with the ontology centered
on purpose, categories, morphisms, hypergraph topology, and kernel
evaluation. The key architectural move is to separate five layers
cleanly: foundations, architecture/infrastructure, schema/topology/
metrics, syntax-semantics bridge, and higher-level skill/tool/provider
integration. Use `mo:os` as the brand and `moos` as the repo/folder slug.

## Steps

### Phase 1 — Finalize foundations before any repo scaffold

Lock the categorical vocabulary and anti-translation rules.

- Every implementation-specific thing (API, ID, workstation, provider,
   package, runtime, spec, tool, skill, transport, document) must first
   be generalized to the category it belongs to before it is modeled
   concretely.
- Purpose is the root semantic anchor, replacing the old root-container
   framing.
- User graphs are reachable, permissioned subgraphs of the same collider
   hypergraph, not separate app trees.
- Kernel categories, user categories, mock categories, and migrated
   categories must be named as distinct strata or lifecycle states, not
   blurred together.

This phase should also produce a terminology sheet mapping legacy FFS1
words to `mo:os` words. *Blocks all later steps.*

### Phase 1A — Define the category stratification rules precisely

Use category-theory rigor to prevent level-confusion.

- Object/morphism level: concrete graph entities and transitions.
- Category/functor level: structured mappings between scopes or
   representations.
- Natural-transformation/coherence level: invariants that must commute
   across scopes.
- Transport surfaces are morphisms, not functors.
- Benchmark/projection/lens/embedding surfaces may be functors only if
   they preserve structure explicitly.

This step is important because the current knowledge already warns
against calling every movement a functor. *Depends on Phase 1.*

### Phase 1B — Define mock categories as formal scaffolds

Specify lifecycle rules.

- Mock category created to test topology, execution, governance, or
   schema hypotheses.
- Mock category validated against canonical invariants and metric
   expectations.
- Mock category is either deleted, promoted, split, or reclassified.

This prevents prototype categories from silently hardening into
ontology. *Parallel with Phase 1A once Phase 1 is locked.*

### Phase 2 — Recast architecture as a pure evaluation core

Use the FP discipline directly.

- Kernel core should be modeled as a pure morphism evaluator/reducer
   wherever possible.
- Storage, transport, tool hydration, provider calls, and OS/process
   interaction should be explicit effect adapters around that core.
- Errors should be modeled as explicit outcomes in the semantic layer,
   not hidden control flow.
- Composition should dominate orchestration; avoid burying semantics in
   stateful services or app-centric modules.

This phase turns the current Go kernel from “the app backend” into the
evaluator of the graph language. *Depends on Phase 1A.*

### Phase 2A — Rebuild infrastructure in categorical terms

Specify infrastructure as graph-relevant movement rather than
host-centric plumbing.

- HTTP, WebSocket, MCP/SSE, CLI, file IO, and future transports are
   connection morphisms in the same category.
- Groups govern which subgraphs, ports, or packaged category-sets are
   reachable.
- Open-source distribution should happen through category/group
   exposure, not app templates.
- Infra components should be named by the role they play in graph
   movement, hydration, validation, or projection.

*Depends on Phase 2; parallel with Phase 2B where useful.*

### Phase 2B — Define the reference matrix from current FFS1

For each active FFS1 surface, classify it as:

- keep conceptually
- reinterpret categorically
- discard as legacy implementation baggage

Focus especially on the current Go kernel pipeline, the persistence
model, and FFS3 graph/lens ideas. *Depends on Phase 2.*

### Phase 3 — Design data, schema, topology, and metrics as one layer

Do not split schema from topology.

- Define what is syntactic structure versus semantic outcome.
- Model typed ports/signatures as subcategory vocabulary, not loose
   metadata tags.
- Define topological state as the reachable/evaluable subgraph context,
   not merely stored node state.
- Encode how groups, ownership scopes, and behavioral signatures
   intersect.
- Make edge richness and traversal complexity first-class factors in
   performance design.

*Depends on Phase 1A and Phase 2.*

### Phase 3A — Lock the metric model around traversal and evaluation cost

Use the D/R framing and extend it.

- discovery cost
- retrieval cost
- hydration cost
- execution cost
- validation cost
- transport/serialization cost
- topological branching/edge-density cost

Benchmarks must record topological context; a tool or semantic path
evaluated in different subgraphs is not the same evaluation. *Depends on
Phase 3.*

### Phase 4 — Formalize the syntax/semantics bridge

Reuse the strongest existing knowledge directly.

- Syntax category = schema, code references, port signatures, graph
   wiring, decomposition vocabulary.
- Semantics category = evaluated morphism results, committed state
   transitions, tool outputs, validated LLM proposals.
- Evaluation functor = kernel reducer from syntax to semantics.
- Decomposition/composition must be guaranteed through invariant
   morphisms, not delegated to natural-language task breakdown.
- Code is syntax until hydrated and evaluated in topological context.

This is the deepest bridge layer and should remain distinct from
skill/tool packaging concerns. *Depends on Phase 3.*

### Phase 4A — Separate semantic bridge from higher-level integration

Build an explicit boundary.

- The semantic bridge explains how graph syntax becomes verified meaning.
- Skill/tool/provider/API integration explains how external industry
   capabilities are represented, linked, hydrated, benchmarked, and
   governed inside that graph.
- These are different abstraction levels of the same system and must not
   be collapsed into one document or one runtime concept.

*Depends on Phase 4.*

### Phase 5 — Model tools, skills, providers, and external capabilities

Recommended framing.

- Tools are code-bearing or code-referencing graph resources whose
   semantics appear only on evaluation.
- Skills are higher-order knowledge or capability classifications that
   constrain routing, discovery, composition, or benchmarking.
- Providers/runtimes/models are benchmarkable categories or objects, not
   the center of the ontology.
- Packaging should preserve graph meaning and group distribution, not
   merely bundle files.

This keeps “current industry paradigm” features inside the collider
recursive graph without letting them define the kernel semantics.
*Depends on Phase 4A.*

### Phase 6 — Turn the architecture into a backlog for the new repo

Sequence the first implementation waves.

- repo and governance bootstrap
- terminology and category sheet
- purpose-root and subgraph model
- pure kernel core plus effect adapters
- schema/topology layer
- evaluation functor and morphism log contract
- tool/skill/provider integration layer
- projection/lens surfaces only after semantics are stable

Each wave should state what it proves, what mock categories it relies
on, and what old assumptions it deletes. *Depends on Phase 5.*

## Relevant files

- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agent\knowledge\01_foundations\foundations.md`
   — canonical source for categorical inventory, coslice/slice
   structure, subcategories, D/R ratio, and the syntax/semantics bridge.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agent\knowledge\02_architecture\architecture.md`
   — current architecture reference for transport-as-morphism and kernel
   execution surfaces.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agent\knowledge\MANIFESTO.md` — sovereignty and harness-agnostic framing for public identity.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agent\knowledge\_archive\brainstorms\kernel_system_3_exploration.txt`
   — raw user intent normalized into the new ontology.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\workspaces\FFS1_ColliderDataSystems\CLAUDE.md` — FFS1 scope boundary and active-stack context.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\cmd\kernel\main.go`
   — reference for the current reducer pipeline only.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\internal\container\store.go`
   — persistence ancestry to reinterpret into graph/topology terms.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\internal\morphism\executor.go`
   — execution ancestry to reinterpret into pure-core/effect-boundary
   terms.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\apps\ffs4\src\stores\graphStore.ts`
   — optional lens/projection reference, only after semantic layers are
   stable.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agents\skills\category-master\SKILL.md` — rigor source for keeping objects, functors, and coherence levels distinct.
- `c:\Users\HP\cloned-repos\ffs0-factory-super\.agents\skills\functional-programming\SKILL.md`
   — discipline source for purity, composition, explicit effects, and
   error-as-value planning.

## Verification

1. Confirm the new repo remains FFS1-scoped and greenfield, with FFS0 used only as knowledge authority and reference material.
2. Produce a terminology sheet where every implementation noun is generalized to a category before any concrete API/module naming is accepted.
3. Verify that transports are modeled as morphisms and that only true structure-preserving mappings are called functors.
4. Verify that the kernel architecture is split into a pure evaluation core and explicit effect adapters.
5. Verify that topological context is mandatory in benchmark and evaluation records, especially for tool hydration and provider comparison.
6. Verify that the syntax/semantics bridge document is distinct from the skill/tool/provider integration document.
7. Verify that each mock category has an explicit lifecycle outcome: delete, promote, split, or reclassify.
8. Keep / reinterpret / discard matrix for the main FFS1 references → see `normalization_and_migration.md` Part 2.

## Decisions

- Brand/product name remains `mo:os`; repository and filesystem slug remain `moos`.
- The rebuild is a new repo, not an extraction from the existing superrepo.
- FFS1 is the implementation ancestry boundary; FFS0 `.agent\knowledge` is the conceptual authority.
- Every implementation object or morphism must be generalized to its category before it is accepted into the design.
- Purpose is the root semantic anchor.
- Topological state, not flat object inventory, is the primary notion of state.
- The syntax/semantics bridge is a deeper layer than tool/skill/provider integration and must be planned separately.
- Mock categories are required scaffolds and must have lifecycle rules.
- Functional-programming discipline should shape the kernel boundary: pure core, explicit effects, composition-first orchestration.

## Further considerations

1. Category normalization sheet → completed, see `normalization_and_migration.md` Part 1.
2. Bootstrap strata decision → completed, see `strata_and_authoring.md` Part 1.
3. Recommended next split in the docs: one document for semantic bridge, one for tool/skill/provider integration, one for schema/topology/metrics.
