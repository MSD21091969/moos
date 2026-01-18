# Collider Mathematical Foundations

**Breadth Map** → Key concepts with references

---

## 1. Core Mathematical Framework

### Category Theory (Functors)

**What**: Containers = Objects, Edges = Morphisms (arrows), Composition = f∘g
**Key Insight**: Process Vector is a functor (structure-preserving map)

**References**:

- Physics, Topology, Logic and Computation: A Rosetta Stone (Baez & Stay)
- Seven Sketches in Compositionality (Fong & Spivak)
- Operad Theory → Wiring Diagrams (Spivak, 2013)

**Application**:

- Container.links = morphism composition
- Composite Definition = h∘g∘f (functorial composition)

---

### Geometric Deep Learning (GDL)

**What**: Neural networks on non-Euclidean data (graphs)
**Key Insight**: Graph fingerprinting - embed structure into vector

**Reference**:

- Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, Gauges (Bronstein, Bruna, LeCun, 2021)

**Application**:

- Container "shape" → vector embedding
- Compare pipelines by manifold distance

---

### Neural-Symbolic AI

**What**: Merge fuzzy vectors with strict logic
**Key Insight**: Vector Symbolic Architectures (VSA) - encode graph structure as vectors

**Reference**:

- Neuro-Symbolic Artificial Intelligence: The State of the Art (Besold et al.)

**Application**:

- Pydantic (symbolic) collides with embeddings (neural)
- "Container A inside Container B" as vector binding

---

### Representation Learning

**What**: Translation vectors in latent space
**Key Insight**: Operations as direction vectors (King - Man + Woman = Queen)

**Reference**:

- Efficient Estimation of Word Representations in Vector Space (Mikolov - Word2Vec)

**Application**:

- Edge transformation = translation vector
- Semantic delta: ΔS = E(output) - E(input)

---

## 2. Process Vector Model

### Path Integration Formula

```
V_Container = Σ V(T_i)   where T_i = transformation at edge i
```

**Components**:

1. **Domain (D_domain)**: Semantic position (Finance vs Biology) → BERT/Nomic embedding
2. **Transformation (T_transformation)**: Change vector (Unstructured → Structured)
3. **Complexity (C)**: Scalar cost = 1+2+...+d (graph depth)

**Not**:

- NOT data state
- NOT number of edges as dimensions
- IS the net transformation (cumulative processing)

### "Ground" Reference

**Question**: How to compare Container with 5 edges vs 50 edges?
**Answer**: Latent space of embedding model (e.g., nomic-embed-text, jina-code)

**Metaphor**:

- Data = Location (Lat/Lon)
- Edge/Transformation = Vector (Direction + Distance)
- Container = Trajectory (Path walked)

---

## 3. Boundary Schema Derivation

### The Algorithm: "Unsatisfied Needs"

**Composite Input** = (All inputs required by internal nodes) - (Internal edges)
**Composite Output** = Outputs NOT consumed internally

**Functorial View**:
If f→g→h, then Composite H = h∘g∘f

- Domain(H) = Domain(f)
- Codomain(H) = Codomain(h)

### Scientific Sources

1. **Operad Theory**: Algebras over Operads (wiring diagrams)
2. **Data Flow Analysis**: Reaching Definitions (compiler theory)
3. **Component-Based SE**: Interface Synthesis (Composite Pattern)

---

## 4. Port Promotion (4-Step Handshake)

### The Mechanism

Data cannot teleport from Node_Inside_A to Node_Inside_B.

**Path**:

1. **Promotion (Up)**: Internal node output → Boundary of Container A
2. **Edge (Across)**: Link takes A.Output → B.Input
3. **Demotion (Down)**: Value enters Container B's Input Boundary
4. **Injection (In)**: Boundary → Specific Internal Node in B

**Why**: Prevents "spaghetti wiring" (tight coupling)

### Analogies

- **VHDL/Verilog**: PORT MAP (chip design)
- **React**: Props (input) + Callbacks (output)
- **Kubernetes**: Service Discovery (exposed ports)

---

## 5. Graph Topology Calculations

### Adjacency Representation

**Flat Graph** with scope_id:

| Edge ID | Scope (Parent) | Source       | Target        | Type       |
| ------- | -------------- | ------------ | ------------- | ---------- |
| E1      | Container_A    | Node_1       | Node_2        | Internal   |
| E2      | Container_A    | Node_2       | SELF (Output) | Promotion  |
| E3      | Main           | Container_A  | Container_B   | Dependency |
| E4      | Container_B    | SELF (Input) | Node_99       | Injection  |

**Query Logic**:

- Run Container A: `WHERE scope_id = Container_A`
- Run Main: `WHERE scope_id = Main`

### Matrix Operations

**Incidence Matrix**: Rows = Nodes, Cols = Edges
**Adjacency Matrix**: Rows = Cols = Nodes, [i,j] = edge exists

**For Boundary Detection**:

1. Build adjacency matrix for internal graph
2. Compute reachability (matrix exponentiation)
3. Find nodes with degree_in = 0 (inputs) or degree_out = 0 (outputs)
4. Filter by scope

---

## 6. Semantic Bridge

### Problem

How to wire Container A (produces "CSV") to Container B (expects "Table")?

### Solution: Semantic Distance

```python
distance = cosine_similarity(
    embed("CSV"),
    embed("Table")
)
if distance > threshold:
    # Auto-wire with type adapter
```

**Embedding Model**: Code embedding (jina-code, nomic-code)

- Understands: "sort list" (Python) ≈ "ORDER BY" (SQL)

### Tensor Representation

Container graph as tensor:

- Dimension 0: Nodes
- Dimension 1: Edges
- Dimension 2: Features (embeddings)

**Operations**:

- Tensor contraction → Graph composition
- Einstein summation → Path integration

---

## 7. Dynamic Schema (create_model)

### The Bridge

JSON schema (stored) → Python BaseModel (runtime)

```python
from pydantic import create_model

InputModel = create_model(
    'DynamicInput',
    field1=(str, ...),
    field2=(int, Field(gt=0))
)
```

**Why Critical**:

1. Bridge: JSON → Python Objects
2. Agent Tools: Generate input models on-the-fly
3. Hot Reload: Inject definitions without restart

---

## Deep Dive Topics (Prioritized)

### 1. Boundary Derivation Algorithm

**Why**: Foundation for Composite Definition
**Focus**:

- NetworkX graph traversal
- Unsatisfied needs calculation
- Pydantic schema merging

### 2. Process Vector Implementation

**Why**: Container comparison & search
**Focus**:

- Path integration (cumulative embeddings)
- Semantic delta calculation
- Vector space indexing (Qdrant)

### 3. Port Promotion Mechanics

**Why**: Cross-container data flow
**Focus**:

- Promotion/demotion maps
- Scope isolation
- Type adapters

---

## References Summary

| Domain          | Key Paper                   | Relevance                |
| --------------- | --------------------------- | ------------------------ |
| Category Theory | Baez & Stay (Rosetta Stone) | Functor semantics        |
| Graph Embedding | Bronstein et al. (GDL)      | Container fingerprinting |
| Vector Algebra  | Mikolov (Word2Vec)          | Transformation vectors   |
| Neural-Symbolic | Besold et al.               | VSA for graph encoding   |
| Wiring Diagrams | Spivak (Operads)            | Composite derivation     |

---

## Next: Deep Dive

**Conversation to start**: Boundary Schema Derivation
**Why**: Enables Container → Composite Definition
**Math focus**: Graph traversal + schema composition
