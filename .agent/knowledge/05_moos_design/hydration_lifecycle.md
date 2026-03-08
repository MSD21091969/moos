# mo:os — Hydration Lifecycle

> Formalizes how syntax becomes semantics through the strata.
> Status: **Active design** — candidate material for promotion into `01_foundations` §14 and `02_architecture`.
> Depends on: `kernel_specification.md`, `strata_and_authoring.md`.
>
> **Related**: `kernel_specification.md` §9 (error taxonomy), §10 (concurrency model),
> §11 (interface contracts), §12 (testing architecture), §13 (rewriting semantics), §14 (cross-provider mapping).
> `strata_and_authoring.md` Part 3 (categorical formalization), Part 4 (Go realization), Part 6 (hypergraph computation).
> `papers/wolfram_hdc_digest.md` (§11 source analysis).
> **Cross-provider**: `foundations.md` §9 (benchmark functors), `architecture.md` §12 (benchmark architecture).
> **Category Registry**: `foundations.md` §21 — $\mathcal{A}, \mathcal{V}, \mathcal{P}, \mathcal{L}_i$ are L1 (named only); promotion needed.

---

## §1 — What Hydration Is

Hydration is the process by which **syntax** (structured declarations,
code references, schema fragments) becomes **semantics** (evaluated,
committed, operational graph state). It is the operational reification
of the syntax/semantics bridge (foundations §14).

Hydration is NOT a single step. It is a **pipeline** with distinct
stages, each with its own validation gate and failure mode.

$$\text{Author} \to \text{Validate} \to \text{Materialize} \to \text{Evaluate} \to \text{Project}$$

Each arrow is a morphism in a higher category — it transforms the
representation of the thing, not the thing's content.

---

## §2 — The Five Hydration Stages

### Stage 1: Author

**Input:** Human or FP program intent.
**Output:** Structured syntax artifacts (typed records, JSON IR, morphism envelope sequences).
**Stratum:** Produces Stratum 1 syntax objects.

Authoring may happen through:
- FP authoring program (typed ADTs compiled to JSON IR)
- Manual JSON/YAML declaration
- LLM proposal (the LLM outputs morphism envelopes, which are syntax)
- Import from external system (MCP tool manifest, OpenAPI spec)

**Validation gate:** Syntactic well-formedness only. Does the artifact
parse? Are required fields present? Is the JSON valid?

**Failure mode:** Parse error → reject immediately, no graph mutation.

### Stage 2: Validate

**Input:** Stratum 1 syntax artifacts.
**Output:** Validated syntax artifacts (same structure, annotated with validation results).
**Stratum:** Still Stratum 1 — validation does not promote.

Validation checks:
1. **Schema compliance**: Does the artifact conform to its declared `_S1_SCHEMA`?
2. **Port vocabulary compliance**: Are referenced ports declared in a `_S1_PORT_VOCAB`?
3. **Category membership**: Does the referenced kind exist as a `_S1_CATEGORY`?
4. **Stratum 0 invariant compliance**: Does the artifact respect the invariant morphism algebra? (No fifth morphism type, no direct `state_payload` write, etc.)
5. **Referential integrity**: Do referenced URNs exist in the target stratum?

**Validation gate:** All checks pass → artifact may proceed to materialization. Any failure → artifact rejected with diagnostic report.

**Failure mode:** Validation error → stored as `_S1_INVALID` with diagnostic payload. Can be corrected and re-validated.

### Stage 3: Materialize

**Input:** Validated Stratum 1 syntax.
**Output:** Morphism Program (ordered sequence of ADD/LINK/MUTATE/UNLINK envelopes).
**Stratum:** Transition point — Stratum 1 syntax is translated into Stratum 2 mutation envelopes.

Materialization is a **compiler step**: it translates authoring
declarations into the kernel's invariant algebra.

Examples:
- A `_S1_CATEGORY` declaration → `ADD(kind="purpose", stratum=2)` + `LINK(category_decl, new_object, "materializes_from", "materialized_by")`
- A tool importing → `ADD(kind="tool")` + `LINK(workspace, tool, "owns", "owned_by")` + `MUTATE(tool, {code_ref: "..."})`
- A port vocabulary → distributed as `MUTATE` to all participating objects' `interface_spec`

**Validation gate:** The generated Program must pass EvaluateProgram in
the pure core (kernel_specification §8.1). If any envelope in the
sequence fails, the entire materialization is rejected.

**Failure mode:** Materialization error → Stratum 1 source is correct but
cannot be realized in the current graph state (e.g., missing parent,
permission denied). Stored as `_S1_BLOCKED` with dependency report.

### Stage 4: Evaluate

**Input:** Committed Stratum 2 graph state (morphisms applied, log appended).
**Output:** Semantic effects — the graph IS the evaluated state.
**Stratum:** Stratum 2 — this is where operational meaning lives.

Evaluation is what the kernel does. The morphism program from Stage 3
has been committed, the morphism log is updated, and the graph reflects
the new state. At this point:

- Tool code references can be resolved and executed
- Agent actor subgraphs can traverse the new structure
- Sessions can interact with the new objects
- Embedding functor can recompute vectors for mutated objects
- Benchmark functor can evaluate the new structure

**Validation gate:** Post-commit invariant checks. The committed state
must satisfy all Stratum 0 rules. If it doesn't, the morphism log
entry is flagged (but NOT deleted — the log is append-only).

**Failure mode:** Invariant violation post-commit → flagged in log,
alert emitted. The system does not crash — it records the violation and
continues. Manual resolution required.

### Stage 5: Project

**Input:** Evaluated Stratum 2 graph state.
**Output:** Stratum 3 projections (UI renders, API responses, embedding vectors, compressed DAGs).
**Stratum:** Stratum 3 — never stored in `containers`, always computed.

Projection is what the functors do:
- $F_{\text{ui}}$ → React component tree
- $F_{\text{embed}}$ → vectors in `embeddings` table
- $F_{\text{struct}}$ → compressed DAG in memory
- Transport surfaces → JSON/SSE/WebSocket serialization

**Validation gate:** None — projections are derived and can always be
recomputed. If a projection is wrong, the fix is upstream (in the
evaluated state or the functor implementation).

**Failure mode:** Rendering error, stale cache → recompute from Stratum 2.

---

## §3 — Hydration as Categorical Construction

The five stages form a **chain of functors** between categories of
representations:

$$\mathcal{A} \xrightarrow{V} \mathcal{V} \xrightarrow{M} \mathcal{P} \xrightarrow{E} \mathcal{C} \xrightarrow{P} \mathcal{L}$$

| Functor | Name | Source | Target |
| --- | --- | --- | --- |
| $V$ | Validate | $\mathcal{A}$ (authored artifacts) | $\mathcal{V}$ (validated artifacts) |
| $M$ | Materialize | $\mathcal{V}$ (validated artifacts) | $\mathcal{P}$ (morphism programs) |
| $E$ | Evaluate | $\mathcal{P}$ (morphism programs) | $\mathcal{C}$ (operational graph) |
| $P$ | Project | $\mathcal{C}$ (operational graph) | $\mathcal{L}$ (lens surfaces) |

**Why functors?** Each stage preserves compositional structure:
- Validating (A composed with B) = validating A then validating B
- Materializing (A composed with B) = materializing A then materializing B
- Evaluating (program₁ ; program₂) = evaluating program₁ then evaluating program₂
- Projecting (subgraph A ∪ B) = projecting A ∪ projecting B (for independent subgraphs)

**The full pipeline** $P \circ E \circ M \circ V$ is the **complete
hydration functor** from authored intent to visible projection. This
is the full syntax/semantics bridge plus projection.

---

## §4 — Mock Category Hydration Lifecycle

Mock categories (normalization §1B) follow the same pipeline but with
explicit lifecycle state tracking.

### State Machine

```
                    ┌──────────────┐
                    │   AUTHORED   │ ← FP program or manual declaration
                    └──────┬───────┘
                           │ Validate
                    ┌──────▼───────┐
               ┌────│  VALIDATED   │────┐
               │    └──────┬───────┘    │
          (fail)           │ Materialize (fail)
               │    ┌──────▼───────┐    │
               │    │ MATERIALIZED │    │
               │    └──────┬───────┘    │
               │           │ Evaluate   │
               │    ┌──────▼───────┐    │
               │    │  EVALUATED   │────┘
               │    └──────┬───────┘
               │           │ Lifecycle decision
               ▼     ┌─────┼─────┬──────────┐
          ┌────────┐  │     │     │          │
          │INVALID │  ▼     ▼     ▼          ▼
          └────────┘ DELETE PROMOTE SPLIT  RECLASSIFY
                       │     │      │         │
                       ▼     ▼      ▼         ▼
                    (gone) (S2)  (2×S1)    (S1')
```

### Lifecycle Operations

| Operation | Effect | Morphisms |
| --- | --- | --- |
| **PROMOTE** | Mock category becomes permanent Stratum 2 object | MUTATE(mock, {lifecycle: "promoted"}) → remove `_MOCK` prefix from kind |
| **DELETE** | Mock category removed from graph | UNLINK all wires → object becomes orphan (invisible to traversal) |
| **SPLIT** | Mock category decomposes into finer categories | ADD(sub₁) + ADD(sub₂) + LINK(mock, sub₁) + LINK(mock, sub₂) + MUTATE(mock, {lifecycle: "split_into"}) |
| **RECLASSIFY** | Mock category changes its categorical classification | MUTATE(mock, {kind: new_kind, lifecycle: "reclassified"}) |

### Mandatory Fields on Mock Objects

```json
{
  "lifecycle": "mock",
  "mock_purpose": "Test topology for agent workspace decomposition",
  "mock_created_at": "2026-03-07T00:00:00Z",
  "mock_review_by": "2026-03-14T00:00:00Z",
  "mock_metrics": {
    "discovery_cost": null,
    "retrieval_cost": null,
    "hydration_cost": null
  }
}
```

Every mock category must declare its purpose and review deadline. Mocks
without review dates are rejected at validation (Stage 2).

---

## §5 — Tool Hydration as Special Case

Tools are the most important hydration case because they bridge code
(external syntax) into graph semantics (evaluated capability).

### Tool Hydration Flow

```
1. Author:      ADD(kind="tool", payload={code_ref: "git://repo/path", language: "go"})
2. Validate:    Check code_ref is resolvable, language is supported
3. Materialize: LINK(workspace, tool, "owns", "owned_by")
                LINK(tool, capability_category, "provides", "provided_by")
4. Evaluate:    On invocation → resolve code_ref → load code → execute in sandbox
5. Project:     Tool appears in MCP tools/list, UI tool palette, agent capability graph
```

**Key principle from foundations §1:** Code is syntax until hydrated and
evaluated in topological context. The SAME tool evaluated in workspace A
(wires {W₁, W₂, W₃}) and workspace B (wires {W₁, W₄}) produces
different evaluations because the topological context differs.

### Hydration Context Record

Every tool evaluation MUST record its hydration context:

```json
{
  "tool_urn": "urn:moos:s2:tool:abc123",
  "evaluation_context": {
    "workspace_urn": "urn:moos:s2:workspace:def456",
    "active_wires": ["W1", "W2", "W3"],
    "actor_urn": "urn:moos:s2:agent:ghi789",
    "timestamp": "2026-03-07T12:00:00Z"
  },
  "result": { ... },
  "cost": {
    "hydration_ms": 45,
    "execution_ms": 200,
    "total_ms": 245
  }
}
```

Without this record, benchmark results are context-free and
uninterpretable (foundations §1, §9).

---

## §6 — The Authoring Pipeline in Practice

### From FP Declaration to Graph

The recommended authoring flow for the greenfield repo:

```
Step 1: Write Go types for the category you want to declare
        → e.g., type WorkspaceCategoryDecl struct { ... }

Step 2: Compile to JSON IR
        → workspaceCategoryDecl.ToJSON() → {"kind": "_S1_CATEGORY", "name": "workspace", ...}

Step 3: Wrap in morphism envelopes
        → []Envelope{ {Type: ADD, Add: {Kind: "_S1_CATEGORY", ...}} }

Step 4: Submit to kernel
        → POST /api/v1/morphisms with envelope body

Step 5: Kernel evaluates (pure core)
        → Validates, applies to GraphState, emits effects

Step 6: Effect shell commits
        → Morphism log append, container cache update

Step 7: Promotion trigger (manual or automated)
        → Materialize S1 declaration into S2 operational objects
```

### The Self-Describing Property

Once the greenfield kernel is bootstrapped, the authoring pipeline
itself is described in the graph:

- Stratum 0 declares that morphisms are the only way to change state
- Stratum 1 declares what categories and port vocabularies exist
- Stratum 2 contains the actual operational instances
- The pipeline for creating new Stratum 1 declarations is itself a
  Stratum 1 declaration (self-reference is legal — the graph allows cycles)

This self-describing property is the endgame of the hydration lifecycle:
the system that creates the system is IN the system.

---

## §7 — Extended Cost Model

Beyond the D/R ratio (foundations §7), the hydration lifecycle exposes
seven cost dimensions that the kernel should track at each stage.

| Dimension | Stage | Definition | Metric |
| --- | --- | --- | --- |
| **Discovery** | Any | Cost of finding candidate edges/objects | $O(\|E_{\text{scope}}\| \times c_{\text{index}})$ |
| **Retrieval** | Any | Cost of fetching known objects | $O(k + 1)$ where $k$ = batch size |
| **Validation** | 2 | Cost of checking syntax compliance | Schema complexity × object count |
| **Materialization** | 3 | Cost of compiling S1 → envelope sequence | Declaration complexity × dependency resolution |
| **Hydration** | 4 (tools) | Cost of loading + binding code | Code size + dependency count + sandbox init |
| **Execution** | 4 | Cost of running evaluated code/morphisms | Morphism count × per-morphism latency |
| **Transport** | 5 | Cost of serialization + network delivery | Payload size × connection count |

### Composite Metric: Total Hydration Cost (THC)

$$\text{THC} = \sum_{i=1}^{5} w_i \cdot C_i$$

where $C_i$ is the cost at stage $i$ and $w_i$ is the weight
(configurable per deployment). This gives a single optimization target
for the full hydration pipeline.

### Per-Subcategory THC

Each subcategory (foundations §8) has its own THC profile:

| Subcategory | Dominant Cost | Optimization |
| --- | --- | --- |
| Session objects | Execution (frequent MUTATE) | Batch writes, in-memory state |
| Tool resources | Hydration (code loading) | Warm cache, preload |
| Agent actors | Discovery (capability graph scan) | Index capability ports |
| Document objects | Retrieval (payload fetch) | Payload compression |

Tracking THC per subcategory enables targeted optimization instead of
global guessing.

---

## §8 — Go Interface Contracts for Hydration Stages

*Derived from: go-interfaces (implicit satisfaction, generality),
go-defensive (compile-time verification), go-error-handling (sentinel errors).*

Each functor in the §3 chain ($V$, $M$, $E$, $P$) becomes a Go interface.
This enables isolated testing of each stage and swapping implementations
(e.g., dry-run materializer for test, real materializer for production).

### Stage Interfaces

```go
package hydration

import "context"

// Validator checks authored artifacts against kernel contracts.
// Functor V: A → V in §3.
type Validator interface {
    Validate(ctx context.Context, artifact AuthoredArtifact) (ValidatedArtifact, error)
}

// Materializer compiles validated artifacts into morphism Programs.
// Functor M: V → P in §3.
type Materializer interface {
    Materialize(ctx context.Context, va ValidatedArtifact) (core.Program, error)
}

// Evaluator applies morphism Programs to graph state (pure core + effect shell).
// Functor E: P → C in §3. This wraps the kernel's Evaluate + Interpret cycle.
type Evaluator interface {
    Execute(ctx context.Context, prog core.Program) (core.EvalResult, error)
}

// Projector renders evaluated graph state into lens surfaces.
// Functor P: C → L in §3.
type Projector interface {
    Project(ctx context.Context, state core.GraphState, target ProjectionTarget) (Projection, error)
}

// ProjectionTarget specifies which functor/surface to project into.
type ProjectionTarget string

const (
    TargetUI        ProjectionTarget = "ui_lens"
    TargetEmbedding ProjectionTarget = "embedding"
    TargetMCP       ProjectionTarget = "mcp"
    TargetStructure ProjectionTarget = "structure"
)
```

### Compile-Time Verification

```go
// Production implementations
var _ Validator     = (*SchemaValidator)(nil)
var _ Materializer  = (*StandardMaterializer)(nil)
var _ Evaluator     = (*KernelEvaluator)(nil)
var _ Projector     = (*UILensProjector)(nil)
var _ Projector     = (*EmbeddingProjector)(nil)

// Test doubles
var _ Validator     = (*StubValidator)(nil)
var _ Materializer  = (*DryRunMaterializer)(nil)
var _ Evaluator     = (*MemoryEvaluator)(nil)
var _ Projector     = (*NoOpProjector)(nil)
```

### The Full Pipeline Combinator

The composition $P \circ E \circ M \circ V$ from §3 is realized as a
pipeline function that chains the four interfaces:

```go
// Hydrate runs the full pipeline: validate → materialize → evaluate → project.
// This is the concrete realization of the hydration functor composition.
func Hydrate(
    ctx context.Context,
    artifact AuthoredArtifact,
    v Validator,
    m Materializer,
    e Evaluator,
    p Projector,
    target ProjectionTarget,
) (Projection, error) {
    va, err := v.Validate(ctx, artifact)
    if err != nil {
        return Projection{}, fmt.Errorf("validation: %w", err)
    }
    prog, err := m.Materialize(ctx, va)
    if err != nil {
        return Projection{}, fmt.Errorf("materialization: %w", err)
    }
    result, err := e.Execute(ctx, prog)
    if err != nil {
        return Projection{}, fmt.Errorf("evaluation: %w", err)
    }
    proj, err := p.Project(ctx, result.NextState, target)
    if err != nil {
        return Projection{}, fmt.Errorf("projection: %w", err)
    }
    return proj, nil
}
```

Error wrapping uses `%w` at every stage so callers can use `errors.Is`
to determine WHERE in the pipeline a failure occurred.

---

## §9 — Error Types per Hydration Stage

*Derived from: go-error-handling (sentinel/structured errors, wrapping policy).*

Each stage has its own sentinel errors. These extend the kernel's error
taxonomy (kernel_specification §9) into the hydration domain.

### Sentinel Errors

```go
package hydration

// Stage 1: Authoring errors (before validation)
var (
    ErrArtifactMalformed  = errors.New("authored artifact is syntactically invalid")
    ErrArtifactEmpty      = errors.New("authored artifact has no content")
)

// Stage 2: Validation errors
var (
    ErrSchemaViolation    = errors.New("artifact violates declared schema")
    ErrPortUndeclared     = errors.New("referenced port not in any vocabulary")
    ErrKindUnregistered   = errors.New("referenced kind has no S1 declaration")
    ErrInvariantBreach    = errors.New("artifact violates S0 invariant")
    ErrRefIntegrity       = errors.New("referenced URN does not exist in target stratum")
)

// Stage 3: Materialization errors
var (
    ErrDependencyMissing  = errors.New("materialization blocked by missing dependency")
    ErrPermissionDenied   = errors.New("actor lacks permission to materialize")
    ErrProgramEmpty       = errors.New("materialization produced zero envelopes")
)

// Stage 5: Projection errors
var (
    ErrProjectionTarget   = errors.New("unknown projection target")
    ErrProjectionStale    = errors.New("projection source state is stale")
)
```

### Structured Error for Validation Diagnostics

```go
// ValidationReport accumulates all violations (not just the first).
type ValidationReport struct {
    Violations []Violation
}

type Violation struct {
    Rule    string // e.g., "schema_compliance", "port_vocabulary"
    Path    string // JSON pointer to the offending field
    Message string
}

func (r *ValidationReport) Error() string {
    return fmt.Sprintf("%d validation violations", len(r.Violations))
}

func (r *ValidationReport) Is(target error) bool {
    return target == ErrSchemaViolation
}
```

---

## §11 — Multi-Path Evaluation and Distributed Representation

*Derived from: Wolfram multiway systems, HDC/VSA encoding, founder's
manuscript, `papers/wolfram_hdc_digest.md`.*

### Multi-Path Hydration

The hydration pipeline (§1–§5) describes a single linear path:
Author → Validate → Materialize → Evaluate → Project. But in practice,
multiple agents may hydrate different subgraphs concurrently, producing
a **multiway hydration graph** — all possible orderings of hydration
steps explored simultaneously.

```text
              ┌─ Agent A hydrates Template T₁ ──→ Materialized M₁
AuthoredSet ──┤
              └─ Agent B hydrates Template T₂ ──→ Materialized M₂
                                                       │
                                   ┌───────────────────┴──────────────┐
                                   ▼                                  ▼
                           M₁ ∪ M₂ (merged)              M₂ ∪ M₁ (same result)
```

If T₁ and T₂ are independent (no shared wire targets), the merge
produces the same state regardless of order — causal invariance holds
for the hydration pipeline, not just for individual morphisms.

The cost model (§8) captures this: the Transport dimension $T$ measures
the cost of coordinating concurrent hydration paths. Independent paths
have $T = 0$ coordination cost; paths that share targets require
conflict resolution.

### HDC Encoding in the Embedding Stage

The Embedding functor (architecture §2 FUN03) maps graph substructures to
vector space. HDC provides the compositional algebra for this mapping:

**Stage-level encoding**: Each hydration stage produces graph structure
that can be encoded as hypervectors:

| Stage | HDC Encoding | Purpose |
| --- | --- | --- |
| Validate | $\phi_V = \bigoplus \phi(\text{violation})$ | Similarity-search for related validation failures |
| Materialize | $\phi_M = \bigoplus_w \phi(w)$ for new wires | Detect structurally similar materializations |
| Evaluate | $\phi_E = \bigoplus_i \pi^i(\phi(m_i))$ for morphisms | Compare execution histories |
| Project | $\phi_P = \mathbf{LENS} \otimes \phi_E$ | Lens-specific view encoding |

**Practical benefit**: When hydrating a new template, the system can
find previously hydrated templates with similar structure by computing
$\text{cos}(\phi(\text{new}), \phi(\text{existing}))$. This enables:
- Template recommendation (what templates look like this one?)
- Error prediction (templates with similar structure had these failures)
- Cost estimation (similar templates took this long to hydrate)

### Hydration as Dimension Emergence

Wolfram's model shows that iterating rewriting rules on a seed produces
emergent spatial structure. The hydration pipeline is analogous:

$$\text{Seed} \xrightarrow{V} \text{Validated skeleton} \xrightarrow{M} \text{Wired graph} \xrightarrow{E} \text{Evaluated graph} \xrightarrow{P_i} \text{View}$$

Each stage INCREASES the effective dimension of the subgraph:
- The seed (authored template) has low connectivity → low $d_{\text{eff}}$
- After materialization, wires connect to existing objects → $d_{\text{eff}}$ rises
- After evaluation, morphism effects ripple through connected objects → $d_{\text{eff}}$ approaches steady state
- Projection collapses back to a lower-dimensional view (a specific port-type slice)

The "port diameter" concept (strata_and_authoring §6) thus has a natural
lifecycle interpretation: templates start low-dimensional and gain
effective dimension through hydration.

The `ValidationReport` accumulates ALL violations rather than
failing on the first one — this gives the author a complete
diagnostic on a single pass (following go-testing's "keep going"
principle applied to validation).

---

## §10 — Testing the Hydration Pipeline

*Derived from: go-testing (table-driven, cmp.Diff, useful failure messages),
go-style-core (simplicity).*

### Stage-Isolated Tests

Each stage is tested independently using its interface + test double:

```go
func TestSchemaValidator_CategoryDeclaration(t *testing.T) {
    v := &SchemaValidator{Schemas: loadTestSchemas(t)}

    tests := []struct {
        name    string
        input   AuthoredArtifact
        wantErr error
    }{
        {
            name:  "valid category declaration passes",
            input: validCategoryArtifact("workspace"),
        },
        {
            name:    "missing name field fails",
            input:   categoryArtifactWithout("name"),
            wantErr: ErrSchemaViolation,
        },
        {
            name:    "unknown port reference fails",
            input:   categoryWithUndeclaredPort("nonexistent_port"),
            wantErr: ErrPortUndeclared,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := v.Validate(context.Background(), tt.input)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("Validate(%s) error = %v, wantErr %v",
                    tt.name, err, tt.wantErr)
            }
        })
    }
}
```

### Full Pipeline Integration Test

The `Hydrate` combinator is tested end-to-end with a `MemoryEvaluator`
(in-memory GraphState, no DB) and `NoOpProjector`:

```go
func TestHydrate_EndToEnd(t *testing.T) {
    v := &SchemaValidator{...}
    m := &StandardMaterializer{}
    e := &MemoryEvaluator{State: newTestGraphState()}
    p := &NoOpProjector{}

    artifact := validCategoryArtifact("document")
    proj, err := Hydrate(context.Background(), artifact, v, m, e, p, TargetUI)
    if err != nil {
        t.Fatalf("Hydrate() error = %v", err)
    }

    // Verify the evaluator's state was mutated
    if _, ok := e.State.Objects["urn:moos:s1:category:document"]; !ok {
        t.Error("Hydrate() did not create S1 category object in graph state")
    }
}
```

### Mock Category Lifecycle Tests

The §4 state machine is tested via table-driven tests that walk a mock
category through its lifecycle:

```go
func TestMockLifecycle(t *testing.T) {
    tests := []struct {
        name       string
        operation  string // "promote", "delete", "split", "reclassify"
        initial    core.Object
        wantKind   core.Kind
        wantExists bool
    }{
        {
            name:       "promote removes mock prefix",
            operation:  "promote",
            initial:    mockObject("_MOCK_workspace"),
            wantKind:   "workspace",
            wantExists: true,
        },
        {
            name:       "delete makes object unreachable",
            operation:  "delete",
            initial:    mockObject("_MOCK_experiment"),
            wantExists: false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            state := stateWith(tt.initial)
            result := applyLifecycleOp(tt.operation, tt.initial.URN, state)
            obj, exists := result.Objects[tt.initial.URN]
            if exists != tt.wantExists {
                t.Fatalf("after %s: object exists = %v, want %v",
                    tt.operation, exists, tt.wantExists)
            }
            if tt.wantExists && obj.Kind != tt.wantKind {
                t.Errorf("after %s: kind = %v, want %v",
                    tt.operation, obj.Kind, tt.wantKind)
            }
        })
    }
}
```

### THC Metric Verification

The §7 cost model is tested by asserting that every tool evaluation
records all 7 cost dimensions:

```go
func TestToolHydration_RecordsCostDimensions(t *testing.T) {
    record := hydrateTestTool(t, "urn:moos:s2:tool:test")

    dimensions := []string{
        "discovery", "retrieval", "validation",
        "materialization", "hydration", "execution", "transport",
    }
    for _, dim := range dimensions {
        if _, ok := record.Cost[dim]; !ok {
            t.Errorf("tool hydration record missing cost dimension %q", dim)
        }
    }
}
```
