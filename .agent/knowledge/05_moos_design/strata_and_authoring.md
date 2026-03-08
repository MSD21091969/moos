# mo:os — Bootstrap Strata & Authoring Decisions

> Consolidates `bootstrap_strata_decision.md` + `authoring_json_output_decision.md`.
> Answers two sequential design questions: (1) where do kernel/bootstrap categories live relative to user categories? (2) should the FP authoring layer also output JSON?
>
> **Related**: `kernel_specification.md` §4 (schema realization), §12 (testing), §13 (rewriting semantics), §14 (cross-provider mapping),
> `hydration_lifecycle.md` (pipeline from S1→S2, §11 multi-path evaluation), `normalization_and_migration.md` (vocabulary discipline).
> `papers/wolfram_hdc_digest.md` (Part 6 source analysis).
> **Cross-provider**: `foundations.md` §9 (benchmark functors), `architecture.md` §12 (benchmark architecture).
> **Category Registry**: `foundations.md` §21 — $\mathcal{C}_0, \mathcal{C}_1, \mathcal{C}_2$ are L2 (partially modeled); inclusion functor proof needed.

---

## Part 1 — Bootstrap Strata Decision

### Decision

**Use a distinguished bootstrap stratum with explicit inclusion maps into user-visible graph space.**

Do **not** flatten kernel/bootstrap categories and user categories into one undifferentiated level from the start.

### Why this is the recommended direction

The current planning already distinguishes:

- invariant morphism algebra
- kernel evaluation / reducer logic
- transport and persistence adapters
- canonical ontology vocabulary
- user-visible categories and reachable subgraphs
- projection/lens surfaces

If all of these are placed immediately into one flat graph layer, two problems appear:

1. **Bootstrapping ambiguity** — the system cannot cleanly express which categories are required to make evaluation possible; authoring structures and runtime structures blur together too early.
2. **Semantic contamination** — projection surfaces, runtime adapters, and legacy implementation terms can leak upward and masquerade as first-class ontology.

A bootstrap stratum solves this by giving the system a protected authoring/evaluation foundation while still allowing explicit projection into user-visible graph structures.

### The role of structured data

Yes — **we will use structured data anyway** once an FP program exists to write categories, functors, schemas, and other graph-level constructs. That is not a contradiction.

The key distinction:

- **structured data is syntax**
- **kernel evaluation yields semantics**

The rule is not "avoid structured data." The rule is "do not mistake structured data for final meaning."

An FP authoring layer may legitimately emit typed structured forms such as category declarations, object inventories, morphism signatures, functor definitions, schema/port vocabularies, benchmark mappings, and bootstrap install/platform presets — as typed records, structured JSON, generated graph mutation envelopes, or compiled intermediate graph syntax. All of that is acceptable **as syntax**. What matters is that the syntax is validated, the kernel treats it as authoring/input structure, and graph semantics arise only when those structures are evaluated, linked, hydrated, benchmarked, or committed.

### Recommended strata

#### Stratum 0 — Bootstrap / evaluator substrate

Contains the minimum machinery required for the system to run at all:

- invariant morphism algebra (`ADD`, `LINK`, `MUTATE`, `UNLINK`)
- kernel reducer / evaluation loop
- log truth contract
- identity and versioning primitives
- transport/effect adapters required for execution
- validation rules for syntax envelopes

This stratum should be small, stable, and hard to contaminate with UI/app language.

#### Stratum 1 — Canonical authoring syntax

Contains structured syntax used to define the semantic world:

- category declarations
- object/morphism inventories
- functor declarations
- schema and typed port vocabularies
- governance/policy declarations
- bootstrap install/platform presets
- ontology authoring programs written in FP style

This stratum is still **syntax**, but it is syntax about the semantic world.

#### Stratum 2 — User-visible operational graph

Contains evaluated, reachable, permissioned graph structures:

- user categories
- group-governed category sets
- active subgraphs
- scheduled compute paths
- hydrated tools/capabilities
- provider/model resources as graph-bound objects
- memory and persistence routes

This is where user programming and runtime state transitions happen.

#### Stratum 3 — Projection / lens surfaces

Contains views and interfaces:

- UI lenses
- agent chat surfaces
- dashboards
- inspectors
- graph viewers
- API projections and operational panels

This stratum is downstream and must never define ontology by itself.

### Inclusion maps between strata

The crucial mechanism is not flattening, but **explicit inclusion**:

- Stratum 1 category syntax → included into Stratum 2 as evaluated category objects/subgraphs
- Stratum 0 evaluator contract → constrains all valid Stratum 2 transitions
- Stratum 2 graph state → projected into Stratum 3 via lens/functor surfaces

This lets the system say clearly where authoring lives, where semantics are executed, where user-visible state lives, and where projections are merely views.

### What this means for the superset

The current superset v2 can be read more cleanly through this strata model:

- axioms and invariant morphisms → mostly Stratum 0
- object/morphism/functor inventories → mostly Stratum 1 authoring syntax
- systems like `MainLoop`, `RestingStateDB`, `ActiveStateGraph` → span Stratum 0 and Stratum 2
- `UI_Lens` and related render surfaces → Stratum 3

Terms needing reinterpretation under this model:

- `RootContainer` → should become **root purpose** or a bootstrap-anchor concept, not a literal ontology root object for everything
- `NodeContainer` → likely remains an authoring-era or compatibility term, not the public semantic primitive
- `AppAdmin` → should be rethought in governance/group language
- `SystemTool` → should become a graph-bound evaluable capability resource within Stratum 2, authored from Stratum 1 syntax

### Implementation discipline

1. Author categories/functors/morphisms/schemas in Stratum 1 using typed structured data.
2. Validate them against Stratum 0 rules.
3. Materialize or include them into Stratum 2 as evaluated graph semantics.
4. Expose them through Stratum 3 only via explicit lenses/projections.

---

## Part 2 — Authoring JSON Output Decision

### Decision

**Yes — the FP authoring layer should also output JSON.**

But JSON should be treated as one of the **syntax / interchange / IR formats**, not as the unique or final source of semantic truth.

### Two-level authoring model

1. **Canonical authoring source** — typed FP declarations / ADTs / authoring program structures. This is the strongest place for authoring categories, functors, morphisms, schema vocabularies, and policy structures.

2. **Derived JSON output** — normalized JSON for interchange, inspection, debugging, persistence, transport, and graph-materialization input. This is an output format, not the ultimate meaning of the system.

### Why JSON output is useful

JSON is good at interchange between tools and runtimes, persistence of structured syntax artifacts, debugging and inspection, diff-friendly snapshots of authoring output, transport through HTTP/MCP/CLI workflows, bootstrap/install presets, emitting graph mutation envelopes, and storing normalized category/functor declarations before evaluation.

### Recommended JSON output families

The FP layer should ideally emit at least four JSON families:

1. **Ontology JSON** — category/object/morphism/functor declarations
2. **Mutation JSON** — invariant morphism envelopes and derived graph mutation programs
3. **Bootstrap JSON** — install presets, platform presets, bootstrap strata declarations
4. **Projection JSON** — exported views or lens-ready graph slices for tooling/debugging

### What JSON should NOT mean

JSON should **not** be treated as:

- semantics by itself
- proof that a category is valid just because a file exists
- the only authoring representation
- the ontology root instead of purpose/category/morphism structure
- a replacement for validation, compilation, or kernel evaluation

The old trap: "we have a JSON file, therefore we already have the system." Nope. Lovely file, still just syntax.

### Recommended pipeline

$$\text{FP Authoring} \to \text{JSON IR} \to \text{Kernel Validation} \to \text{Graph Semantics}$$

Steps:

1. Write categories/functors/schemas in typed FP authoring structures.
2. Validate them statically where possible.
3. Compile / normalize them into JSON IR.
4. Validate JSON IR against kernel-side contracts.
5. Materialize or evaluate into graph semantics.
6. Project to UI/tools/transport layers as needed.

### Relation to the current superset

The current `superset_ontology_v2.json` is a good example of why JSON output is valuable — easy to inspect, diff, and read across tools. But it also demonstrates the caution: a structured JSON ontology may still contain legacy naming, an embedded date may be misleading, and the file still requires normalization and semantic interpretation.

Lesson: **yes to JSON output, no to JSON worship.**

For `moos`, prefer this policy:

- **author in typed FP structures**
- **emit JSON too**
- **treat JSON as portable syntax / IR**

---

## Part 3 — Categorical Formalization of Strata

*Derived from: category-master skill (filtrations, inclusion functors,
subcategories), functional-programming skill (referential transparency).*

### Strata as a Categorical Filtration

The four strata form a **filtered subcategory chain** — a sequence of
full subcategories linked by inclusion functors:

$$\mathcal{C}_0 \hookrightarrow \mathcal{C}_1 \hookrightarrow \mathcal{C}_2$$

Where:
- $\mathcal{C}_0$ = bootstrap substrate (objects + wires where `stratum = 0`)
- $\mathcal{C}_1$ = authoring syntax ($\mathcal{C}_0$ ∪ objects where `stratum = 1`)
- $\mathcal{C}_2$ = operational graph ($\mathcal{C}_1$ ∪ objects where `stratum = 2`)

Each inclusion $\iota_k : \mathcal{C}_k \hookrightarrow \mathcal{C}_{k+1}$ is
a **faithful functor** — it preserves all morphisms and adds no new
ones between included objects. The inclusion is full: any morphism
between two $\mathcal{C}_k$ objects that exists in $\mathcal{C}_{k+1}$
already existed in $\mathcal{C}_k$.

**Stratum 3** is NOT part of this chain. It is a **separate target category**
$\mathcal{L}$ (lens surfaces) reached by projection functors:

$$F_{\text{proj}} : \mathcal{C}_2 \to \mathcal{L}$$

This is crucial: projections are *functorial images*, not subcategories.
A UI view is in $\mathcal{L}$, not in $\mathcal{C}_2$. It cannot create
morphisms in $\mathcal{C}_2$ — only the kernel can.

### Stratum Assignment is a Property, Not a Type

In the schema (kernel_specification §4), `stratum` is a column on both
`containers` and `wires`. It is a *property* of objects and morphisms,
not a separate type system. This means:

- A wire can connect objects across strata (e.g., S1 declaration
  `materializes_from` an S2 object it created).
- The filtration $\mathcal{C}_0 \subset \mathcal{C}_1 \subset \mathcal{C}_2$
  is defined by the stratum values, not by type-level partition.
- Cross-stratum wires are legal but semantically constrained: they flow
  **downward** during materialization (S1→S2), never **upward** from
  S2→S0 (S0 is write-protected by kernel policy, not by type system).

### Referential Opacity and Transparency

The FP skill defines **referential transparency**: an expression can be
replaced by its value without changing the program's meaning.

The strata encode a precise opacity/transparency gradient:

| Stratum | Referential Status | Meaning |
| --- | --- | --- |
| S0 | **Opaque** | Cannot be replaced — it IS the evaluation rules |
| S1 | **Transparent as syntax** | Can be inspected, diffed, validated, replaced — but has no runtime semantics yet |
| S2 | **Transparent as semantics** | Can be queried, traversed, mutated via morphisms — has committed meaning |
| S3 | **Derived (ephemeral)** | Can always be recomputed from S2 — referentially transparent by construction |

This gradient is why S1 objects can be freely duplicated, diffed, and
experimented with (they're just syntax), while S0 objects are sacred
(they define what evaluation means) and S2 objects require morphisms to
change (they carry committed semantics with version history).

### Promotion as Functor

The materialization step (S1→S2) is a functor
$M : \mathcal{C}_1 \to \mathcal{C}_2$ (hydration_lifecycle §3). It
preserves structure: composing two S1 declarations and then materializing
equals materializing each and composing the results.

$$M(d_1 \circ d_2) = M(d_1) \circ M(d_2)$$

This functoriality is what makes batch materialization safe — the order
of independent declarations doesn't matter.

### Demotion is NOT a Functor

There is no structure-preserving map from S2 back to S1. An operational
object that has accumulated morphism history, version state, and wire
connections cannot be losslessly projected back to a syntax declaration.
Demotion is an **extraction** operation (lossy), not a functor.

This asymmetry is deliberate: it's easy to compile syntax to semantics
(deterministic), hard to decompile semantics back to syntax (lossy).

---

## Part 4 — Go Realization of the Authoring Pipeline

*Derived from: go-interfaces (interface contracts), go-error-handling
(sentinel errors, structured types), go-functional-options (optional
configuration), go-defensive (compile-time verification).*

### Pipeline Interfaces

Each stage of the authoring pipeline (Part 2 recommended pipeline) is an
interface. This enables testing each stage in isolation and swapping
implementations.

```go
package authoring

// Compiler transforms FP-style typed declarations into JSON IR.
// Implementations: GoCompiler (compiles Go structs), FileCompiler (reads JSON files).
type Compiler interface {
    Compile(ctx context.Context, decl Declaration) (JSONIR, error)
}

// Validator checks JSON IR against kernel-side contracts.
// Implementations: SchemaValidator (JSON Schema), StubValidator (tests).
type Validator interface {
    Validate(ctx context.Context, ir JSONIR) (ValidatedIR, error)
}

// Materializer translates validated IR into morphism Programs.
// Implementations: StandardMaterializer, DryRunMaterializer (emits programs without submitting).
type Materializer interface {
    Materialize(ctx context.Context, vir ValidatedIR) (core.Program, error)
}
```

### Compile-Time Interface Verification

```go
var _ Compiler     = (*GoCompiler)(nil)
var _ Compiler     = (*FileCompiler)(nil)
var _ Validator    = (*SchemaValidator)(nil)
var _ Materializer = (*StandardMaterializer)(nil)
var _ Materializer = (*DryRunMaterializer)(nil)
```

### JSON IR Types

The four JSON output families from Part 2 become concrete Go types:

```go
// JSONIR is the intermediate representation between authoring and kernel.
type JSONIR struct {
    Family   IRFamily        `json:"family"`
    Version  string          `json:"version"`    // Schema version of this IR
    Payload  json.RawMessage `json:"payload"`
}

type IRFamily string

const (
    FamilyOntology   IRFamily = "ontology"    // Category/object/morphism/functor declarations
    FamilyMutation   IRFamily = "mutation"     // Morphism envelopes and derived programs
    FamilyBootstrap  IRFamily = "bootstrap"    // Install presets, platform presets, strata declarations
    FamilyProjection IRFamily = "projection"   // Exported views or lens-ready graph slices
)

// ValidatedIR wraps JSONIR with validation metadata.
type ValidatedIR struct {
    IR           JSONIR
    ValidatedAt  time.Time
    Diagnostics  []Diagnostic   // Warnings (non-fatal)
}
```

### Error Types per Pipeline Stage

```go
package authoring

// Compilation errors — FP declaration cannot produce valid IR.
var (
    ErrDeclarationMalformed = errors.New("declaration is syntactically malformed")
    ErrDeclarationIncomplete = errors.New("declaration is missing required fields")
)

// Validation errors — IR is well-formed but violates kernel contracts.
var (
    ErrSchemaViolation = errors.New("IR payload does not conform to declared schema")
    ErrPortUndeclared  = errors.New("referenced port not found in any port vocabulary")
    ErrKindUnknown     = errors.New("referenced kind has no S1 category declaration")
    ErrInvariantBreach = errors.New("IR violates stratum 0 invariant")
)

// Materialization errors — validated IR cannot be realized in current graph state.
var (
    ErrMaterializeDependency = errors.New("materialization blocked by missing dependency")
    ErrMaterializePermission = errors.New("actor lacks permission to materialize in target scope")
)

// Structured validation error with detail.
type SchemaViolationError struct {
    IRFamily    IRFamily
    SchemaPath  string   // JSON pointer to the violated schema node
    Message     string
}

func (e *SchemaViolationError) Error() string {
    return fmt.Sprintf("schema violation in %s at %s: %s",
        e.IRFamily, e.SchemaPath, e.Message)
}

func (e *SchemaViolationError) Is(target error) bool {
    return target == ErrSchemaViolation
}
```

### DryRunMaterializer for Testing

The `DryRunMaterializer` implements `Materializer` but returns the
`core.Program` without submitting it to the kernel. This enables testing
the full authoring pipeline (compile → validate → materialize) against
expected morphism sequences using `cmp.Diff`:

```go
func TestAuthoringPipeline_WorkspaceCategory(t *testing.T) {
    compiler := &GoCompiler{}
    validator := &SchemaValidator{...}
    materializer := &DryRunMaterializer{}

    decl := WorkspaceCategoryDecl{Name: "workspace", Ports: []string{"owns", "owned_by"}}

    ir, err := compiler.Compile(ctx, decl)
    if err != nil {
        t.Fatalf("Compile() error = %v", err)
    }

    vir, err := validator.Validate(ctx, ir)
    if err != nil {
        t.Fatalf("Validate() error = %v", err)
    }

    got, err := materializer.Materialize(ctx, vir)
    if err != nil {
        t.Fatalf("Materialize() error = %v", err)
    }

    want := core.Program{
        Envelopes: []core.Envelope{
            {Type: core.MorphismADD, Add: &core.AddPayload{Kind: "_S1_CATEGORY"}},
            // ...
        },
    }
    if diff := cmp.Diff(want, got); diff != "" {
        t.Errorf("Materialize() mismatch (-want +got):\n%s", diff)
    }
}
```

---

## Part 5 — Testing Strata Separation

*Derived from: go-testing (table-driven, cmp.Diff, no assertion libraries),
go-defensive (compile-time checks).*

### Strata Invariant Tests

The stratum model has concrete invariants that are testable in the pure
core without any database:

```go
func TestStrataProtection(t *testing.T) {
    tests := []struct {
        name    string
        env     core.Envelope
        state   core.GraphState
        wantErr error
    }{
        {
            name:    "S0 object rejects MUTATE from non-evaluator",
            env:     mutateEnvelope("urn:moos:s0:algebra:morph", "user-actor"),
            state:   stateWithS0Objects(),
            wantErr: core.ErrStratumProtected,
        },
        {
            name:    "S0 object rejects UNLINK from non-evaluator",
            env:     unlinkEnvelopeForS0Wire("user-actor"),
            state:   stateWithS0Objects(),
            wantErr: core.ErrStratumProtected,
        },
        {
            name:    "S0 evaluator actor CAN mutate S0",
            env:     mutateEnvelope("urn:moos:s0:algebra:morph", "urn:moos:s0:evaluator:kernel"),
            state:   stateWithS0Objects(),
            wantErr: nil,
        },
        {
            name:    "S2 object accepts MUTATE from authorized actor",
            env:     mutateEnvelope("urn:moos:s2:doc:001", "user-actor"),
            state:   stateWithPermission("user-actor", "scope"),
            wantErr: nil,
        },
        {
            name:    "S1 declaration can be created by authorized actor",
            env:     addEnvelopeWithStratum("_S1_CATEGORY", 1, "user-actor"),
            state:   stateWithPermission("user-actor", "scope"),
            wantErr: nil,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := core.Evaluate(tt.env, tt.state, testTime)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("Evaluate(%s) error = %v, wantErr %v",
                    tt.name, err, tt.wantErr)
            }
        })
    }
}
```

### Cross-Stratum Wire Tests

Verify that cross-stratum wires respect directionality constraints:

| Test Case | Expected |
| --- | --- |
| S1 → S2 wire (materialization) | Allowed |
| S2 → S2 wire (operational) | Allowed |
| S1 → S1 wire (authoring-internal) | Allowed |
| S2 → S0 wire (upward corruption) | Rejected |
| S0 → S0 wire (bootstrap-internal) | Allowed (evaluator actor only) |

### Import Boundary Test

The stratum model's compile-time equivalent is the Go import rule from
kernel_specification §6: `core/` imports nothing from `shell/`. This is
testable via a build constraint or CI lint — if `core/` ever imports
`shell/`, the pure core is contaminated.
- **never confuse emitted JSON with final semantics**

---

## Part 6 — Hypergraph Computation Model

*Derived from: Wolfram Physics Project (hypergraph rewriting), Kanerva's
Hyperdimensional Computing (VSA), founder's manuscript, category-master
skill. See `papers/wolfram_hdc_digest.md` for full source analysis.*

### Morphisms as Rewriting Rules

The four invariant morphisms (ADD, LINK, MUTATE, UNLINK) are **graph
rewriting rules** in the Wolfram sense. Each morphism application:

1. **Matches** a precondition pattern in the current graph state
2. **Replaces** the matched subgraph with a new local structure
3. **Appends** the transformation to the morphism log

This is exactly the computational primitive of the Wolfram Physics
Project: `pattern → replacement` applied to a hypergraph. The mo:os
graph evolves through iterated local rewriting, just as Wolfram's
hypergraph evolves through iterated rule application.

| Morphism | Rewriting Pattern | Effect |
| --- | --- | --- |
| ADD | $\emptyset \to \{v\}$ | Inserts a new vertex (container) |
| LINK | $\{u, v\} \to \{u, v, (u \xrightarrow{p} v)\}$ | Inserts a new hyperedge (wire) between existing vertices |
| MUTATE | $\{v, s\} \to \{v, s'\}$ | Replaces the state payload of an existing vertex |
| UNLINK | $\{u, v, (u \xrightarrow{p} v)\} \to \{u, v\}$ | Removes a hyperedge |

These four rules are **computation-universal for graph transformations**:
any target graph state can be reached from any source state via a finite
sequence of these four operations.

### Multiway Evaluation and Causal Invariance

When multiple agents propose morphisms concurrently, the kernel faces
the same branching that Wolfram's multiway system explores. Two agents
may propose different morphism sequences from the same graph snapshot:

```text
         ┌─ Agent A: LINK(x→y) ; MUTATE(y)
State₀ ──┤
         └─ Agent B: MUTATE(x) ; LINK(x→z)
```

The kernel resolves this via optimistic locking (§10 of kernel_specification):

- **Independent morphisms**: If A's and B's morphisms touch disjoint
  subgraphs, both commit. The final state is the same regardless of
  ordering — this is **causal invariance**.
- **Conflicting morphisms**: If both touch the same objects, one wins
  (version check), the other retries against the new state — this is
  **branch selection** in the multiway graph.

**Formal property:** For commutative (independent) morphisms $m_1, m_2$:

$$\Sigma(m_1 ; m_2) = \Sigma(m_2 ; m_1)$$

where $\Sigma$ is the catamorphism from morphism log to graph state.
This commutativity for independent operations is the mo:os analog of
Wolfram's causal invariance: the causal graph is the same regardless of
which branch was followed.

### Computational Reducibility Boundary

The strata model maps precisely to Wolfram's distinction between
computationally reducible and irreducible regions:

| Stratum | Wolfram Analog | Reducibility |
| --- | --- | --- |
| S0 (bootstrap) | The rewriting rules themselves | Fully reducible — deterministic, formally verifiable |
| S1 (authoring) | Initial conditions / rule configurations | Reducible as syntax — can be statically analyzed |
| S2 (operational) | The evolving hypergraph | Partly irreducible — LLM outputs, user actions, emergent topology |
| S3 (projection) | Observer's projection of the hypergraph | Derived — always recomputable from S2 |

S0 is the pocket of computational reducibility inside the irreducible
S2 system. The kernel's formal guarantees (pure core, deterministic
evaluation, replay consistency) exist *because* S0 is reducible. S2's
irreducibility is why we need the append-only log — we cannot predict
the graph's evolution, but we can replay it.

### Effective Dimension and Port Diameter

Wolfram measures the "dimension" of a hypergraph region by how fast the
neighborhood ball grows:

$$|\text{Ball}(v, r)| \sim r^d \quad \Rightarrow \quad d = \text{effective dimension at } v$$

In mo:os, this becomes the **port diameter** — the founder's
*"interface port diameter functor flow"*:

$$d_{\text{eff}}(v) = \frac{\log |\text{Ball}(v, r)|}{\log r}$$

where $\text{Ball}(v, r)$ is the set of containers reachable from $v$
within $r$ wire hops (across all port types in the superposition).

**Operational meaning:**
- High $d_{\text{eff}}$ → densely connected neighborhood → container acts
  as a hub (high fan-out, many dependents)
- Low $d_{\text{eff}}$ → sparse chain topology → container is in a linear
  pipeline (sequential data flow)
- The cost model's Discovery dimension (hydration_lifecycle §8) is
  directly proportional to $d_{\text{eff}}$

### HDC Encoding of Graph State

Hyperdimensional Computing provides the algebra for the Embedding functor's
internal operations. Each graph element is encoded as a hypervector
$\mathbf{v} \in \{-1, +1\}^d$ (with $d \approx 10{,}000$):

**Wire encoding** (binding creates relational structure):

$$\phi(w) = \mathbf{SRC} \otimes \phi(s) \oplus \mathbf{SRC\_P} \otimes \phi(p_s) \oplus \mathbf{TGT} \otimes \phi(t) \oplus \mathbf{TGT\_P} \otimes \phi(p_t)$$

where $\otimes$ = binding, $\oplus$ = bundling, and $\phi$ maps URNs to
base hypervectors.

**Node neighborhood encoding** (bundling creates superposition):

$$\phi_{\text{ctx}}(v) = \bigoplus_{w \in \text{wires}(v)} \phi(w)$$

This is the *"hypergraph hypervector"* from the manuscript — a single
distributed representation encoding a node's full relational context.
Two nodes with similar neighborhoods produce similar hypervectors,
enabling similarity-based retrieval without explicit graph traversal.

**Morphism history encoding** (permutation preserves sequence):

$$\phi_{\text{log}}(v) = \bigoplus_{i=0}^{n} \pi^i(\phi(m_i))$$

The full morphism history of a node encoded as one hypervector with
temporal ordering preserved by the permutation $\pi$.

### Three Operations ↔ Three Graph Primitives

| HDC | Graph Primitive | mo:os Implementation |
| --- | --- | --- |
| Bind $\otimes$ | Associate two entities through a typed port | LINK morphism |
| Bundle $\oplus$ | Superpose multiple relations at one node | `state_payload` + neighborhood |
| Permute $\pi$ | Order morphisms in the log | Log position index |

This correspondence is not metaphorical — it is the algebraic structure
that makes GPU-parallel graph operations possible. Once the graph is
encoded as hypervectors, similarity search, pattern matching, and
subgraph comparison reduce to vector operations (dot products, element-wise
XOR/addition) that map directly to GPU SIMD instructions.

The founder's vision: *"category theory and then hypervector and functional
programming to process the rigid logic of the numerous graphs in the
hypergraph instead of just 1 topological one then gpu."*
