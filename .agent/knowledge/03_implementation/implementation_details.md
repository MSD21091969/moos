# Implementation Details

## Runtime Morphism Switching

Wires are not static. The `wire_config` JSONB on each wire can contain temporal
and environmental rules that change edge behavior at runtime:

```json
{
  "active_from": "2026-06-01T00:00:00Z",
  "active_until": "2026-12-31T23:59:59Z",
  "env": ["staging"],
  "transitive": true
}
```

When the kernel traverses a wire, it checks `wire_config` against the current
execution context (timestamp, environment). If the wire is not active, traversal
skips it. This means:

- **Temporal edges**: wires that only exist during a time window (feature flags,
  timed access grants, scheduled maintenance windows)
- **Environment-scoped edges**: wires that only exist in specific environments
  (dev-only tools, production-only data sources)
- **Combined**: "this CAN_HYDRATE wire is active in staging from June to December"

No code change required. No redeployment. The graph reconfigures itself based on
time and environment. This is possible because everything is keys, indexes,
pointers, URNs — switching user categories at runtime is just changing which
wires are active.

## Permission Composition via Declared Transitivity

Two transitivity modes:

### OWNS — Transitive by Nature

If Alice OWNS workspace W, and W OWNS tool T, then Alice transitively owns T.
OWNS wires are always transitive. The kernel follows OWNS chains without checking
per-edge transitivity flags.

```
Alice ──OWNS──→ Workspace ──OWNS──→ Tool
∴ Alice transitively owns Tool
```

### CAN_HYDRATE — Transitive by Declaration

CAN_HYDRATE is NOT automatically transitive. Each workspace declares what it
passes through:

```
FFS0 ──CAN_HYDRATE(transitive: true)──→ Rule_A
FFS1 ──CAN_HYDRATE(transitive: false)──→ Rule_B
```

FFS0's children inherit Rule_A (transitive). FFS1's children do NOT inherit
Rule_B (non-transitive). The manifest is the transitivity controller — it
declares which knowledge, rules, and configs propagate down the workspace tree.

## User Graph Sync

A user's graph is portable. The set of wires originating from a user URN defines
everything that user can access. Sync between environments works by:

1. Export: serialize all wires where `source_urn = user_urn`
2. Transfer: move wire set to target environment
3. Import: create wires in target database (containers must already exist)

This is git-like: the user's wire set can diverge between environments and be
merged. Conflicts happen when the same wire (same 4-tuple) has different
`wire_config` values in source and target. Resolution: last-write-wins or
explicit merge rules in the sync protocol.

## Linear vs Non-Linear Growth in Practice

### Adding a Container (Linear)

```sql
INSERT INTO containers (urn, type_id, state_payload) VALUES (...);
INSERT INTO morphism_log (morphism_type, ...) VALUES ('ADD', ...);
```

One row in containers. One row in morphism_log. O(1) per container. Total storage
grows linearly with container count.

### Adding a Wire (Non-Linear Potential)

Each new container introduces n potential new wires (one to every existing
container). In practice, only k wires are created (k ≪ n). But the DECISION of
which k wires to create requires evaluating rules against all n candidates.

This is where the system's intelligence lives: the rules that filter n² potential
edges down to k actual edges. Better rules = fewer wires = cleaner graph = faster
traversal = more precise answers.

## Morphism Pipeline Implementation (Go)

```go
func (k *Kernel) Execute(ctx context.Context, req MorphismRequest) (MorphismResult, error) {
    // 1. Route: resolve target container
    container, err := k.store.GetContainer(ctx, req.TargetURN)

    // 2. Dispatch: select handler by morphism type
    handler := k.handlers[req.MorphismType] // ADD, LINK, MUTATE, or UNLINK

    // 3. Validate: check actor has wire to target
    hasAccess, err := k.store.HasWire(ctx, req.ActorURN, req.TargetURN)

    // 4. Transform: execute in transaction
    result, err := handler.Execute(ctx, k.store, req)

    // 5. Commit: log the morphism
    k.store.LogMorphism(ctx, req.MorphismType, req.ActorURN, req.TargetURN,
        result.PreviousState, result.NewState)

    return result, nil
}
```

Each handler (AddHandler, LinkHandler, MutateHandler, UnlinkHandler) is a single
Go struct with one method. No inheritance. No polymorphism beyond the Handler
interface. The kernel is thin.

## Phase 5: System 3 / LogicGraph Execution via gRPC

To counter the inherent flaws of LLM autoregressive reasoning (which prioritizes semantic fluency over logical entailment, leading to insufficient premise deductions and result-oriented hallucinations), mo:os implements true System 3 reasoning.

### 1. `CAN_FORK` and VRAM Graph Instantiation

The kernel forks the existing in-memory graph directly into CUDA-addressable memory. Because containers are highly optimized (~1KB per container), a ~10K container workspace requires roughly 10MB of active state in VRAM. This leaves massive headroom for parallel branch evaluation, model weights, and tensor buffers.

### 2. Transporting Explicit Reasoning Graphs

Rather than relying on the LLM to process logic purely in natural language or semantic token space, the complex multi-step reasoning is formulated as an explicit, discrete reasoning graph (LogicGraph). This DAG incorporates:

- **Knowledge nodes**
- **Logical relationships**
- **Calculation operations**
- **Requirement conditions**

Once formulated, this graph is transported via **gRPC** to an external deterministic execution or solver engine (e.g., Python execution environments, Prover9, or Lean 4).

### 3. Process-Verified GRPO Pipeline

By outsourcing the logical verification to formal solvers over gRPC, mo:os eliminates the need for LLM-based objective scoring or human-annotated reinforcement learning (RLHF).

- The solver engine returns an absolute, objective boolean (`true`/`false`) or a precisely verified code exception.
- This programmatic feedback acts as the process reward for a **Group Relative Policy Optimization (GRPO)** algorithm.
- Using absolute solver rewards combined with KL divergence penalties (to prevent deviation from supervised baselines), the policy network is conditioned accurately on structured DAG sequences without prompt hacking.

### 4. Branch Collapse

Parallel logical branches are scored. Weak branches demonstrating semantic comprehension errors or logical execution flaws (such as rule misapplication) are pruned. The verified, deterministically sound "winning" branch collapses its topological delta back to the main Resting State.
