# Tensor Operations & Graph Matrices for Collider

## Current Collider Architecture

### Graph Structure

Collider uses **NetworkX DiGraph** for topology ([graph.py](file:///d:/my-tiny-data-collider/shared/topology/graph.py)):

- `Container` nodes (vertices)
- `Link` edges (predecessor → successor)
- DAG enforcement via cycle detection
- Topological sorting for execution order

### Data Models ([models.py](file:///d:/my-tiny-data-collider/shared/domain/models.py))

```python
class Link(BaseModel):
    owner_id: UUID              # Successor/Consumer
    predecessor_id: UUID        # Dependency
    definition_id: Optional[UUID]
    input_mapping: Dict[str, str]

class UserContainer(BaseModel):
    id: UUID
    parent_id: Optional[UUID]   # Recursive nesting (R-depth)
    definition_id: Optional[UUID]
```

---

## Matrix Representations for Graphs

### 1. Adjacency Matrix (A)

**Definition**: Square matrix where `A[i,j] = 1` if edge from node i → j

**For Collider**:

```python
# n containers × n containers
# A[pred_idx, succ_idx] = 1
# Symmetric for undirected, asymmetric for DAG
```

**Operations**:

- **A²**: 2-hop paths (composition chains)
- **A^k**: k-hop reachability
- **Matrix exponentiation** (`scipy.linalg.expm`): `exp(A·t)` for diffusion/propagation

### 2. Incidence Matrix (B)

**Definition**: `V×E` matrix where `B[v,e] = ±1` if vertex v incident to edge e

**For Collider**:

```python
# containers × links
# B[container_idx, link_idx] = -1 (source/predecessor)
#                             = +1 (target/successor)
```

**Use**: Edge-node relationships, explicitly models `Link` objects

### 3. Tensor Contraction

**Definition**: Generalized Einstein summation over shared indices

**Example**:

```python
# Path integration via einsum
import numpy as np
# A[i,j] × B[j,k] → C[i,k]
C = np.einsum('ij,jk->ik', A, B)
```

**For Collider**: Compose multi-layer Container graphs by contracting intermediate nodes

### 4. Graph Product (Tensor Product of Graphs)

**Kronecker/Tensor Product**: Adjacency of G₁⊗G₂ = **A₁ ⊗ A₂** (Kronecker product)

**Use**: Compose two Container subgraphs into combined structure

---

## Matrix Operations for Boundary Detection

### Input/Output Boundary Detection

| Operation              | Collider Mapping                                              |
| ---------------------- | ------------------------------------------------------------- |
| **Zero in-degree**     | `np.sum(A, axis=0) == 0` → Input boundaries (no predecessors) |
| **Zero out-degree**    | `np.sum(A, axis=1) == 0` → Output boundaries (no successors)  |
| **Incidence boundary** | Rows in B with single non-zero → External links               |

### Subgraph Composition I/O

For nested Container at R-depth, **emerged I/O** = boundary of internal graph:

```python
# Internal adjacency A_internal
# External connections E_external
# Boundary nodes = E_external ∩ V_internal
```

**Matrix formulation**:

1. Build adjacency `A` for all Links in Container
2. Identify nodes with edges crossing Container boundary (parent_id ≠ container.id)
3. Aggregate input/output schemas from boundary Definitions

---

## Python Libraries

### Current Stack

- **NetworkX** ([graph.py:1](file:///d:/my-tiny-data-collider/shared/topology/graph.py#L1)): Graph algorithms, DAG validation

### Tensor-Enabled Extensions

| Library                      | Use Case                           | Integration                  |
| ---------------------------- | ---------------------------------- | ---------------------------- |
| **NumPy/SciPy**              | Matrix ops, `scipy.sparse.csgraph` | Fast adjacency operations    |
| **PyTorch Geometric**        | GNN layers, batched graphs         | If adding ML to graph        |
| **Deep Graph Library (DGL)** | Scalable GNN, message passing      | Multi-GPU graph ops          |
| **opt_einsum**               | Optimized Einstein summation       | Efficient tensor contraction |

### Recommendation for Collider

**Add scipy.sparse for adjacency matrices**:

```python
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path, connected_components

# Build from Links
A = csr_matrix((data, (preds, succs)), shape=(n, n))
# Reachability
dist = shortest_path(A)
```

---

## Key Question: Matrix Ops ↔ Boundary Detection

### Boundary Detection as Matrix Operation

```python
import numpy as np
from scipy.sparse import csr_matrix

def detect_boundaries(links, containers):
    """
    Returns (input_nodes, output_nodes) using adjacency matrix
    """
    n = len(containers)
    container_ids = {c.id: i for i, c in enumerate(containers)}

    # Build adjacency
    rows, cols = [], []
    for link in links:
        pred_idx = container_ids[link.predecessor_id]
        succ_idx = container_ids[link.owner_id]
        rows.append(pred_idx)
        cols.append(succ_idx)

    A = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))

    # Boundary detection
    in_degree = np.array(A.sum(axis=0)).flatten()
    out_degree = np.array(A.sum(axis=1)).flatten()

    input_nodes = np.where(in_degree == 0)[0]   # No incoming
    output_nodes = np.where(out_degree == 0)[0]  # No outgoing

    return input_nodes, output_nodes
```

### Composition via Tensor Contraction

For **nested Containers** (Composite Definitions):

1. Each internal Container has I/O schema
2. Internal Links wire them together
3. **Contracted I/O** = external-facing inputs/outputs only

**Matrix approach**:

```python
# Internal schema adjacency S (schema-level graph)
# Edge contraction → reduced graph with boundary nodes
# output_schema = union of all output boundary nodes
```

---

## Next Steps for Collider Integration

### 1. **Add Matrix View to GraphTopology**

Extend [graph.py](file:///d:/my-tiny-data-collider/shared/topology/graph.py) with:

```python
def to_adjacency_matrix(self) -> np.ndarray:
def find_boundaries(self) -> Tuple[List[UUID], List[UUID]]:
def compute_reachability(self) -> np.ndarray:  # A^k
```

### 2. **Use for Composite Definition I/O**

When Runtime builds Composite Definitions:

- Build adjacency from internal Links
- Detect boundary nodes (matrix operations)
- Extract their schemas → composite I/O

### 3. **Path Integration for Dependencies**

Use matrix exponentiation for transitive dependencies:

```python
# Full dependency closure
import scipy.linalg
A_closure = scipy.linalg.expm(A)  # All path weights
```

### 4. **Optional: GNN for Smart Wiring**

If implementing AI-assisted graph building:

- Use PyTorch Geometric
- Train on Container connection patterns
- Predict optimal Link placements

---

## References

- **Adjacency matrices**: [Wikipedia](https://en.wikipedia.org/wiki/Adjacency_matrix)
- **Einstein summation**: [NumPy einsum](https://numpy.org/doc/stable/reference/generated/numpy.einsum.html)
- **Matrix exponentiation**: [SciPy linalg.expm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html)
- **GNN frameworks**: PyTorch Geometric, DGL
- **Tensor networks**: Graph representation via tensor contraction
