# Scope Isolation & Port Promotion Theory - Conversation Archive

**Date**: 2026-01-15  
**Topic**: Mathematical investigation of scope crossing, port promotion as categorical lifting, and implications for Collider base models architecture  
**Conversation ID**: 47b0eafd-e380-41a2-bff4-ea44c702ac56

---

## Context

Part of 7-topic mathematical research series investigating theoretical foundations for the Collider architecture. This conversation (Topic 7) focused on scope isolation mechanics and how data crosses encapsulation boundaries in a type-safe, mathematically rigorous manner.

**Related Conversations**:

- Topic 1: Category Theory & Functorial Semantics
- Topic 2: Geometric Deep Learning & Graph Embeddings
- Topic 3: Process Vectors & Path Integration
- Topic 4: Boundary Derivation & Operad Theory
- Topic 5: Neural-Symbolic AI & VSA
- Topic 6: Tensor Operations & Graph Matrices

---

## Key Insights

### 1. Port Promotion as Categorical Lifting

**Mathematical Framework**: Traced Monoidal Categories

A port promotion is a functor `F: Inner_scope@R+1 → Outer_scope@R` that:

- Preserves composition: `F(g∘f) = F(g)∘F(f)`
- Preserves monoidal structure: `F(A⊗B) = F(A)⊗F(B)`
- Enforces type preservation across scope boundaries

**String Diagram Representation**:

```
┌─────────┐         ┌─────────┐
│  Inner  │         │  Outer  │
│  ┌───┐  │  F(p)   │    p'   │
│  │ p │──┼────────>├─────────┤
│  └───┘  │         │         │
└─────────┘         └─────────┘
```

### 2. The 4-Step Handshake

Formal boundary crossing protocol:

1. **Declaration** - Define port signature (type + direction + scope)
2. **Binding** - Map internal wire to port
3. **Promotion** - Lift to parent scope (categorical functor F)
4. **Connection** - Wire across boundary with type safety

### 3. Type Theory for Scope Crossing

**Dependent type system**:

```
Port : (direction: In|Out) → (scope: ℕ) → Type → Type
promote : Port dir R τ → Port dir (R-1) τ  // Decrements scope depth
connect : Port Out R τ → Port In R τ → Wire R τ  // Same-scope only
```

**Visibility Calculus**:

- Wire at depth R only connects ports at depth R
- Promotion decrements R (moves toward root UserObject at R=0)
- Prevents cross-scope violations (R=3 cannot reach R=1 directly)

### 4. Analogies to Existing Systems

| System            | Scope Mechanism                  | Port Concept                    | Type Safety                |
| ----------------- | -------------------------------- | ------------------------------- | -------------------------- |
| **VHDL PORT MAP** | Component/architecture hierarchy | Signal routing between entities | Compile-time type checking |
| **React Props**   | Component tree depth             | Props passed parent→child       | TypeScript interfaces      |
| **Microservices** | Service boundaries               | API endpoints                   | OpenAPI schemas            |

All prevent "spaghetti wiring" through structured, type-safe interfaces.

### 5. Collider Architecture Translation

**Core Duality**:

- **Containers** = Special recursive group elements with depth R
- **Graph** = Dataflow topology (edges), unaware of dependencies/recursion

**Two Construction Modes**:

1. **Bottom-Up (Free Algebra)**:

   - Start with empty Containers (no Definition)
   - Add atomic Definitions
   - Wire Links gradually
   - Close graph boundaries when ready

2. **Top-Down (Cofree Coalgebra)**:
   - Start with abstract task at root
   - Decompose/refine recursively
   - Allocate boundaries at each level

**Galois Connection**: `α: Concrete ⇄ Abstract :γ` (adjoint pair)

### 6. The Semantic Bridge Problem

**Challenge**: Map abstract task descriptions → concrete Container structure

**Infinity Depth Issue**:

- At any R, you can ask "how?" and decompose deeper
- Structural problem, not topological (semantics, not graph shape)

**Proposed Solution**: Metric Learning

```python
E_semantic: TaskDescription → ℝ^d  # Abstract intent
E_symbolic: ContainerGraph → ℝ^d   # Concrete structure
sim(task, graph) = cos(E_semantic(task), E_symbolic(graph))
```

Train on validated (task, implementation) pairs from past executions.

### 7. Graph Morphing Operations

**Injection** - Insert graph inside node:

```python
morph_inject(target: Container@R, subgraph: Graph) → Container@R:
    Replace Definition with subgraph
    Promote subgraph boundaries to match target's I/O
    Increment all subgraph nodes to R+1
```

**Splitting** - Decompose node:

```python
morph_split(node: Container@R, strategy) → List[Container@R]:
    Partition by: I/O groups, Definition type, semantic cluster
    Redistribute Definitions
    Re-route Links to maintain dataflow
```

**Fusion** - Merge nodes (inverse):

```python
morph_fuse(nodes: List[Container@R]) → Container@R:
    Union all Definitions
    Merge boundary I/O
    Collapse internal Links
```

These are **natural transformations** between graph functors.

### 8. Preset Structures (Graph Grammars)

**Graph Rewriting Rules**: `Pattern P → Structure Q`

Example - MapReduce Template:

```
Pattern: Single Container with [list] → [aggregate]
Rewrite:
    Container_parent@R
      ├─ Map@R+1 (parallel copies)
      └─ Reduce@R+1 (aggregation)
```

**PIKE-RAG Integration**:

- Query knowledge graph for structural patterns
- Retrieve templates matching "API Gateway", "ETL Pipeline", etc.
- Instantiate with parameters

---

## Implementation Considerations

### Pydantic Base Models (Proposed)

```python
from pydantic import BaseModel
from typing import Literal, Type
from uuid import UUID

class Port(BaseModel):
    """Type-safe port with scope enforcement"""
    id: UUID
    direction: Literal["in", "out"]
    scope_depth: int  # R value (0=root, R+1=nested)
    port_type: Type
    name: str

    def promote(self) -> "Port":
        """Categorical lifting to parent scope"""
        if self.scope_depth == 0:
            raise ValueError("Cannot promote root port")
        return Port(
            id=self.id,
            direction=self.direction,
            scope_depth=self.scope_depth - 1,
            port_type=self.port_type,
            name=f"promoted_{self.name}"
        )

class Wire(BaseModel):
    """Scope-enforced connection"""
    source_port: Port
    target_port: Port

    @field_validator("target_port")
    def validate_scope_match(cls, v, info):
        source = info.data.get("source_port")
        if source and source.scope_depth != v.scope_depth:
            raise ValueError(
                f"Scope violation: {source.scope_depth} → {v.scope_depth}"
            )
        return v

class Container(BaseModel):
    """Recursive container with scope depth"""
    id: UUID
    scope_depth: int  # R
    definition: Optional[Definition] = None
    ports: List[Port] = []
    links: List[Wire] = []

    def add_nested_container(self, child: "Container"):
        """Add child at R+1"""
        child.scope_depth = self.scope_depth + 1
        # ... wire promoted ports
```

### Questions for Multi-Topic Synthesis

1. **Category Theory** (Topic 1): Should `scope_depth` be part of Container's type, or metadata?
2. **GDL** (Topic 2): Max reliable embedding depth for hierarchical Containers?
3. **Process Vectors** (Topic 3): Does semantic delta work across scope transitions?
4. **Boundary Derivation** (Topic 4): Performance of recursive boundary algorithm at deep R?
5. **VSA** (Topic 5): Can vector encoding replace explicit `scope_depth` field?
6. **Tensors** (Topic 6): Block-diagonal adjacency matrices per scope level?

---

## Unresolved Design Decisions

### LinkedContainerDefinition Mechanism

**Question**: How to retrieve Definitions for graph execution?

**Option A**: Graph logic retrieves directly

- Pros: Fast, topology-aware
- Cons: Tight coupling, harder to validate nested state

**Option B**: Nested Container traversal

- Pros: Encapsulation, natural recursion
- Cons: Slower, potential for state/topology mismatch

**Option C**: Hybrid

- Graph knows topology (Links)
- Containers own state (Definition instances)
- Dependencies tracked in both layers

**Recommendation**: Option C - separation of concerns

### Scope Depth Representation

**Option A**: Explicit field `scope_depth: int`

- Pros: Fast lookups, clear semantics
- Cons: Manual maintenance, potential desync

**Option B**: Implicit (derived from parent chain)

- Pros: Always correct, no duplication
- Cons: O(R) traversal cost

**Option C**: Cached with lazy recomputation

- Pros: Fast + correct
- Cons: Invalidation logic complexity

**Recommendation**: Option C with Pydantic computed fields

### Preset Structures vs AI Guidance

**Structural Approach** (Graph Grammars):

- Predictable, type-safe
- Fast instantiation
- Limited to known patterns

**AI Approach** (PIKE-RAG + LLM):

- Flexible, adaptive
- Discovers novel patterns
- Requires validation, slower

**Hybrid Strategy**:

1. Check preset library first (graph grammars)
2. If no match, query PIKE-RAG for similar entity structures
3. Use LLM to adapt template to specific context
4. Validate with Pydantic before instantiation

---

## Next Actions

### Immediate (This Conversation)

- [x] Document port promotion mathematics
- [x] Create synthesis prompts for Topics 1-6
- [x] Archive conversation per docs/conversations/README.md

### Cross-Topic Coordination

1. Post synthesis prompts to 6 other conversations
2. Collect Pydantic model proposals from each topic
3. Resolve conflicts/overlaps in unified design session
4. Create `architecture.md` section: "Base Models v2.0"

### Implementation Phase

1. **Foundation** (`shared/models/base.py`):

   - Port, Wire, Container classes
   - Scope validation logic
   - Promotion/demotion methods

2. **Graph Logic** (`parts/graph/builder.py`):

   - pydantic-graph (beta) integration
   - Scope-aware graph construction
   - Morphing operations (inject, split, fuse)

3. **Preset Library** (`parts/graph/templates/`):

   - Graph grammar rules
   - Common patterns (MapReduce, Pipeline, Gateway)
   - Template instantiation engine

4. **Testing** (`tests/graph/`):
   - Scope violation detection
   - Functorial preservation checks
   - Morphing operation correctness

---

## References

### Mathematical Foundations

1. **Joyal, Street, Verity (1996)** - "Traced Monoidal Categories"

   - Trace operator for closing feedback loops
   - Symmetric monoidal structure

2. **Spivak (2013)** - "The Operad of Wiring Diagrams"

   - Wiring as operadic composition
   - Port mapping formalization

3. **Baez & Stay (2011)** - "Physics, Topology, Logic and Computation: A Rosetta Stone"
   - String diagrams for monoidal categories
   - Functorial semantics

### System Analogies

1. **VHDL IEEE 1076 Standard** - Hardware description language port semantics
2. **React Component Model** - Props typing and component boundaries
3. **OpenAPI 3.0 Specification** - Microservice interface contracts

### Related Collider Research

- [Category Theory Applied to Collider](file:///d:/agent-factory/docs/math/category_theory_collider.md)
- [Boundary Derivation Research](file:///d:/agent-factory/docs/math/boundary_derivation_research.md)
- [Phase 2: Graph Integration](file:///d:/agent-factory/docs/planning/phases/phase_2_graph_integration.md)

---

## Artifacts Created

- [`synthesis_prompts.md`](file:///C:/Users/hp/.gemini/antigravity/brain/47b0eafd-e380-41a2-bff4-ea44c702ac56/synthesis_prompts.md) - Cross-topic coordination prompts with design questions

---

**End of Conversation Archive**
