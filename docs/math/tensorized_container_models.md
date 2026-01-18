# TensorizedContainer Base Models - Architecture Proposal

## Overview

Synthesizes **Topic 6 (Tensor Operations)** with **Topic 7 (Scope Isolation)** to create matrix-based graph operations that respect scope boundaries and enable efficient boundary detection, composition, and morphing.

**Key Insight**: Scope isolation creates **block-diagonal adjacency matrices** where each R-depth level has its own matrix A_R, and cross-scope connections only occur via port promotion.

---

## 1. Scope-Stratified Adjacency Matrices

### Core Concept

```
Wire@R only connects Ports@R
→ Adjacency matrix A is block-diagonal by scope level
→ A = block_diag(A_0, A_1, ..., A_n)
```

Each scope level R has isolated topology unless explicitly promoted.

### Pydantic Models

```python
from pydantic import BaseModel, Field, computed_field
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import numpy as np
from scipy.sparse import csr_matrix, block_diag
from enum import Enum

class ScopeLevel(BaseModel):
    """Single scope level R with its adjacency matrix"""
    depth: int  # R value (0=root, increasing inward)
    container_ids: List[UUID]  # Nodes at this level
    adjacency: Optional[np.ndarray] = None  # A_R matrix

    # Sparse representation for large graphs
    _sparse_adjacency: Optional[csr_matrix] = None

    @computed_field
    @property
    def n_nodes(self) -> int:
        return len(self.container_ids)

    def to_sparse(self) -> csr_matrix:
        """Convert dense adjacency to sparse CSR format"""
        if self._sparse_adjacency is None and self.adjacency is not None:
            self._sparse_adjacency = csr_matrix(self.adjacency)
        return self._sparse_adjacency

    def detect_boundaries(self) -> Tuple[List[int], List[int]]:
        """
        Boundary detection via matrix operations
        Returns: (input_boundary_indices, output_boundary_indices)
        """
        A = self.to_sparse()

        # In-degree: sum over rows (incoming edges)
        in_degree = np.array(A.sum(axis=0)).flatten()

        # Out-degree: sum over columns (outgoing edges)
        out_degree = np.array(A.sum(axis=1)).flatten()

        # Zero in-degree = input boundary (no predecessors)
        input_boundaries = np.where(in_degree == 0)[0].tolist()

        # Zero out-degree = output boundary (no successors)
        output_boundaries = np.where(out_degree == 0)[0].tolist()

        return input_boundaries, output_boundaries


class PortPromotion(BaseModel):
    """
    Categorical lifting from R+1 → R
    Matrix: A_promotion[parent_idx, child_boundary_idx]
    """
    source_scope: int  # R+1 (inner)
    target_scope: int  # R (outer)
    source_port_idx: int  # Local index in child Container
    target_port_idx: int  # Local index in parent Container
    port_type: str  # Type preservation

    def validate_promotion(self) -> bool:
        """Functor property: F(R+1) → F(R), R>0"""
        return self.target_scope == self.source_scope - 1 and self.target_scope >= 0


class StratifiedAdjacency(BaseModel):
    """
    Multi-level adjacency structure with scope isolation
    A_global = block_diag(A_0, A_1, ..., A_n) + A_promotion
    """
    scope_levels: Dict[int, ScopeLevel] = Field(default_factory=dict)
    promotions: List[PortPromotion] = Field(default_factory=list)

    def get_level(self, depth: int) -> Optional[ScopeLevel]:
        """Get scope level by R-depth"""
        return self.scope_levels.get(depth)

    def build_global_adjacency(self) -> csr_matrix:
        """
        Construct block-diagonal adjacency with cross-scope promotions
        """
        # Stack all scope-level matrices
        level_matrices = [
            self.scope_levels[r].to_sparse()
            for r in sorted(self.scope_levels.keys())
        ]

        # Block-diagonal base structure
        A_base = block_diag(level_matrices, format='csr')

        # Add promotion edges (cross-block connections)
        # TODO: Map local indices to global indices
        A_promotion = self._build_promotion_matrix(A_base.shape[0])

        return A_base + A_promotion

    def _build_promotion_matrix(self, n: int) -> csr_matrix:
        """Build sparse matrix for port promotions"""
        rows, cols, data = [], [], []

        # Global index mapping: scope -> offset
        offset = 0
        scope_offsets = {}
        for r in sorted(self.scope_levels.keys()):
            scope_offsets[r] = offset
            offset += self.scope_levels[r].n_nodes

        for promo in self.promotions:
            # Map local to global indices
            source_global = scope_offsets[promo.source_scope] + promo.source_port_idx
            target_global = scope_offsets[promo.target_scope] + promo.target_port_idx

            rows.append(source_global)
            cols.append(target_global)
            data.append(1)  # Unweighted edge

        return csr_matrix((data, (rows, cols)), shape=(n, n))

    def compute_reachability(self, max_hops: int = 10) -> np.ndarray:
        """
        Matrix exponentiation for k-hop reachability
        R = I + A + A^2 + ... + A^k
        """
        from scipy.linalg import expm

        A = self.build_global_adjacency().toarray()

        # Use matrix exponential for infinite path sums
        # exp(A) = I + A + A^2/2! + A^3/3! + ...
        # For binary reachability, use boolean power sum

        R = np.eye(len(A))  # Identity
        A_power = A.copy()

        for k in range(1, max_hops + 1):
            R = R + A_power
            A_power = A_power @ A

        return (R > 0).astype(int)  # Boolean reachability
```

---

## 2. Graph Morphing as Matrix Operations

### Morphing Operations

| Operation  | Matrix Interpretation                     | Scope Impact        |
| ---------- | ----------------------------------------- | ------------------- |
| **Inject** | Block matrix insertion at A_R+1           | Add new scope level |
| **Split**  | Matrix decomposition + redistribute edges | Same R, partition A |
| **Fusion** | Matrix contraction (merge rows/cols)      | Same R, reduce A    |

### Pydantic Models

```python
from typing import Protocol

class GraphMorphism(Protocol):
    """Protocol for all graph morphing operations"""
    def apply(self, graph: StratifiedAdjacency) -> StratifiedAdjacency:
        ...

class MorphInject(BaseModel):
    """
    Injection: Insert subgraph inside target container
    Matrix: Expand A_R, add new A_R+1 block
    """
    target_container_id: UUID
    target_scope: int  # R
    subgraph: StratifiedAdjacency  # Graph to inject

    def apply(self, graph: StratifiedAdjacency) -> StratifiedAdjacency:
        """
        1. Find target container in A_R
        2. Remove target row/col from A_R (now defined by subgraph)
        3. Increment all subgraph nodes to R+1
        4. Create promotions for subgraph boundaries → target's original connections
        """
        target_level = graph.get_level(self.target_scope)
        if not target_level:
            raise ValueError(f"Scope {self.target_scope} not found")

        # Find target index
        try:
            target_idx = target_level.container_ids.index(self.target_container_id)
        except ValueError:
            raise ValueError(f"Container {self.target_container_id} not in scope {self.target_scope}")

        # Remove target from A_R (it's now a composite)
        new_A_R = np.delete(target_level.adjacency, target_idx, axis=0)
        new_A_R = np.delete(new_A_R, target_idx, axis=1)
        new_container_ids = [
            cid for i, cid in enumerate(target_level.container_ids) if i != target_idx
        ]

        # Add subgraph at R+1
        new_scope = self.target_scope + 1
        subgraph_level = ScopeLevel(
            depth=new_scope,
            container_ids=self.subgraph.scope_levels[0].container_ids,  # Assume subgraph at R=0
            adjacency=self.subgraph.scope_levels[0].adjacency
        )

        # Create new graph
        new_graph = StratifiedAdjacency(
            scope_levels={
                **graph.scope_levels,
                self.target_scope: ScopeLevel(
                    depth=self.target_scope,
                    container_ids=new_container_ids,
                    adjacency=new_A_R
                ),
                new_scope: subgraph_level
            },
            promotions=graph.promotions + self._create_boundary_promotions(subgraph_level, target_idx)
        )

        return new_graph

    def _create_boundary_promotions(self, subgraph: ScopeLevel, parent_idx: int) -> List[PortPromotion]:
        """Map subgraph boundaries to parent container's I/O"""
        input_boundaries, output_boundaries = subgraph.detect_boundaries()

        promotions = []
        # TODO: Map to actual port types from schemas
        for inp_idx in input_boundaries:
            promotions.append(PortPromotion(
                source_scope=subgraph.depth,
                target_scope=subgraph.depth - 1,
                source_port_idx=inp_idx,
                target_port_idx=parent_idx,  # Simplified
                port_type="promoted_input"
            ))

        return promotions


class MorphSplit(BaseModel):
    """
    Splitting: Decompose container into multiple nodes
    Matrix: Partition A_R, redistribute edges
    """
    target_container_id: UUID
    target_scope: int
    partition_strategy: str  # "semantic" | "io_groups" | "random"
    n_partitions: int = 2

    def apply(self, graph: StratifiedAdjacency) -> StratifiedAdjacency:
        """
        1. Find target in A_R
        2. Duplicate row/col into n_partitions
        3. Redistribute edges based on strategy
        """
        # Implementation: matrix row/column duplication + edge redistribution
        raise NotImplementedError("Split morphism")


class MorphFuse(BaseModel):
    """
    Fusion: Merge multiple containers into one
    Matrix: Contract rows/cols, union edges
    """
    target_container_ids: List[UUID]
    target_scope: int
    fusion_strategy: str  # "union" | "intersection"

    def apply(self, graph: StratifiedAdjacency) -> StratifiedAdjacency:
        """
        1. Find targets in A_R
        2. Merge rows: A_fused[i,:] = OR(A[i1,:], A[i2,:], ...)
        3. Merge cols: A_fused[:,j] = OR(A[:,j1], A[:,j2], ...)
        4. Remove old rows/cols
        """
        # Tensor contraction: sum over fused indices
        raise NotImplementedError("Fuse morphism")
```

---

## 3. Boundary Detection via Matrix Ops

### Einstein Summation for Path Integration

```python
class PathIntegrator(BaseModel):
    """
    Compute cumulative transformations across graph paths
    Using Einstein summation notation
    """
    adjacency: StratifiedAdjacency

    def integrate_paths(self, source_idx: int, target_idx: int, max_depth: int = 5) -> List[List[int]]:
        """
        Find all paths from source to target using matrix powers
        A^k gives k-hop connections
        """
        A = self.adjacency.build_global_adjacency().toarray()

        paths = []
        A_power = A.copy()

        for k in range(1, max_depth + 1):
            # Check if k-hop path exists
            if A_power[source_idx, target_idx] > 0:
                # Use BFS/DFS to enumerate actual paths (matrix only tells existence)
                paths.extend(self._enumerate_paths(A, source_idx, target_idx, k))

            # Next power: A^(k+1) = A^k @ A
            A_power = A_power @ A

        return paths

    def _enumerate_paths(self, A: np.ndarray, src: int, tgt: int, length: int) -> List[List[int]]:
        """DFS to find all paths of exact length"""
        # Backtracking algorithm
        paths = []

        def dfs(current: int, path: List[int], remaining: int):
            if remaining == 0:
                if current == tgt:
                    paths.append(path.copy())
                return

            # Explore neighbors
            neighbors = np.where(A[current, :] > 0)[0]
            for neighbor in neighbors:
                if neighbor not in path:  # Avoid cycles
                    path.append(neighbor)
                    dfs(neighbor, path, remaining - 1)
                    path.pop()

        dfs(src, [src], length)
        return paths

    def einsum_composition(self, matrices: List[np.ndarray]) -> np.ndarray:
        """
        Compose multiple transformations using Einstein summation
        Example: A @ B @ C = einsum('ij,jk,kl->il', A, B, C)
        """
        if len(matrices) == 1:
            return matrices[0]

        result = matrices[0]
        for mat in matrices[1:]:
            result = np.einsum('ij,jk->ik', result, mat)

        return result
```

### Composite Boundary Detection

```python
class CompositeBoundaryDetector(BaseModel):
    """
    Detect emerged I/O for composite containers
    Algorithm: unsatisfied inputs/outputs at scope boundary
    """
    stratified_graph: StratifiedAdjacency

    def detect_composite_boundary(self, container_id: UUID, container_scope: int) -> Tuple[List[int], List[int]]:
        """
        For a composite Container@R containing subgraph@R+1:

        1. Get A_R+1 (internal topology)
        2. Find nodes with edges crossing to R (promotions)
        3. Inputs = promoted nodes with external predecessors
        4. Outputs = promoted nodes with external successors
        """
        inner_level = self.stratified_graph.get_level(container_scope + 1)
        if not inner_level:
            raise ValueError(f"No internal scope for composite at R={container_scope}")

        # Find promoted ports
        promoted_ports = [
            p for p in self.stratified_graph.promotions
            if p.source_scope == container_scope + 1 and p.target_scope == container_scope
        ]

        # Boundary = nodes with promotions
        input_boundary = []
        output_boundary = []

        for promo in promoted_ports:
            # Check direction based on edge in parent scope
            # (Simplified: would need type/direction metadata)
            source_idx = promo.source_port_idx

            # Check if this is input or output boundary
            # Input: promoted port receives from outside
            # Output: promoted port sends to outside

            # Use local adjacency to determine
            A_inner = inner_level.to_sparse()

            # If node has no internal predecessors → input boundary
            in_deg = A_inner[:, source_idx].sum()
            if in_deg == 0:
                input_boundary.append(source_idx)

            # If node has no internal successors → output boundary
            out_deg = A_inner[source_idx, :].sum()
            if out_deg == 0:
                output_boundary.append(source_idx)

        return input_boundary, output_boundary
```

---

## 4. TensorizedContainer Integration Model

### Main Container Class

```python
class TensorizedContainer(BaseModel):
    """
    Container with matrix-based graph operations
    Integrates scope isolation + tensor operations
    """
    id: UUID
    scope_depth: int  # R value
    name: str

    # Graph representation
    local_graph: Optional[StratifiedAdjacency] = None  # If composite

    # Port definitions (type-safe boundaries)
    input_ports: List[Port] = Field(default_factory=list)
    output_ports: List[Port] = Field(default_factory=list)

    # Sparse matrix indexing
    _matrix_index: Optional[int] = None  # Index in scope-level adjacency

    @computed_field
    @property
    def is_composite(self) -> bool:
        """Has internal graph structure"""
        return self.local_graph is not None

    def inject_subgraph(self, subgraph: StratifiedAdjacency) -> "TensorizedContainer":
        """
        Morphism: Atomic → Composite
        Matrix operation: Add A_R+1 block, create promotions
        """
        morph = MorphInject(
            target_container_id=self.id,
            target_scope=self.scope_depth,
            subgraph=subgraph
        )

        # Apply morphism (creates new graph structure)
        new_graph = morph.apply(self.local_graph or StratifiedAdjacency())

        # Update container
        return TensorizedContainer(
            id=self.id,
            scope_depth=self.scope_depth,
            name=self.name,
            local_graph=new_graph,
            input_ports=self.input_ports,
            output_ports=self.output_ports
        )

    def compute_boundaries(self) -> Tuple[List[int], List[int]]:
        """
        Boundary detection via matrix operations
        """
        if not self.is_composite:
            # Atomic: boundaries = all ports
            return (
                list(range(len(self.input_ports))),
                list(range(len(self.output_ports)))
            )

        detector = CompositeBoundaryDetector(stratified_graph=self.local_graph)
        return detector.detect_composite_boundary(self.id, self.scope_depth)

    def to_adjacency_matrix(self) -> Optional[csr_matrix]:
        """Export as sparse adjacency matrix"""
        if not self.is_composite:
            return None

        return self.local_graph.build_global_adjacency()


class Port(BaseModel):
    """Type-safe port with scope enforcement (from Topic 7)"""
    id: UUID
    direction: Literal["in", "out"]
    scope_depth: int
    port_type: str  # JSON Schema type
    name: str

    def promote(self) -> "Port":
        """Categorical lifting F: R+1 → R"""
        if self.scope_depth == 0:
            raise ValueError("Cannot promote root-level port")

        return Port(
            id=self.id,
            direction=self.direction,
            scope_depth=self.scope_depth - 1,
            port_type=self.port_type,
            name=f"promoted_{self.name}"
        )
```

---

## 5. GPU Tensor Operations Support

### Considerations

```python
class GPUAcceleratedGraph(BaseModel):
    """
    PyTorch Geometric integration for GPU-accelerated operations
    """
    stratified_graph: StratifiedAdjacency
    device: str = "cpu"  # "cuda" for GPU

    def to_pytorch_geometric(self):
        """
        Convert to PyG Data format
        """
        try:
            import torch
            from torch_geometric.data import Data
        except ImportError:
            raise ImportError("PyTorch Geometric required for GPU operations")

        A = self.stratified_graph.build_global_adjacency()

        # Convert to edge index format (COO)
        edge_index = torch.tensor(
            np.array(A.nonzero()),
            dtype=torch.long,
            device=self.device
        )

        # Node features (scope depth as feature)
        node_features = []
        for scope_level in self.stratified_graph.scope_levels.values():
            node_features.extend([scope_level.depth] * scope_level.n_nodes)

        x = torch.tensor(node_features, dtype=torch.float, device=self.device).unsqueeze(1)

        return Data(x=x, edge_index=edge_index)

    def batch_boundary_detection(self, container_ids: List[UUID]):
        """
        Parallel boundary detection for multiple containers using GPU
        """
        # Use PyG message passing for parallel computation
        # Each node computes its in/out degree in parallel
        raise NotImplementedError("GPU batch boundary detection")
```

---

## 6. pydantic-graph Execution Pipeline

### Matrix Multiplication as Computation

```python
class MatrixExecutionPipeline(BaseModel):
    """
    Execution as matrix multiplication chain
    Result = D_n @ D_(n-1) @ ... @ D_1 @ Input
    where D_i are Definition transformations
    """
    graph: StratifiedAdjacency
    definitions: Dict[UUID, "Definition"]  # Container ID -> Definition

    def execute_as_matrix_chain(self, input_data: np.ndarray) -> np.ndarray:
        """
        Topological sort → execution order → matrix chain
        """
        # Get execution order from topological sort
        A = self.graph.build_global_adjacency()
        execution_order = self._topological_sort(A)

        # Build transformation matrices for each Definition
        transformation_matrices = []
        for node_idx in execution_order:
            # Get Definition for this node
            container_id = self._get_container_id(node_idx)
            definition = self.definitions.get(container_id)

            if definition:
                # Convert Definition logic to matrix (if possible)
                D = self._definition_to_matrix(definition)
                transformation_matrices.append(D)

        # Compose: Result = D_n @ ... @ D_1 @ Input
        result = input_data
        for D in transformation_matrices:
            result = D @ result

        return result

    def _topological_sort(self, A: csr_matrix) -> List[int]:
        """Kahn's algorithm for topological sort"""
        import networkx as nx

        # Convert to NetworkX
        G = nx.from_scipy_sparse_array(A, create_using=nx.DiGraph)
        return list(nx.topological_sort(G))

    def _definition_to_matrix(self, definition) -> np.ndarray:
        """
        Convert Definition logic to linear transformation
        (Only works for linear Definitions)
        """
        # Placeholder: most Definitions are non-linear
        raise NotImplementedError("Non-linear Definitions cannot be pure matrices")
```

---

## Summary

### Key Models

1. **ScopeLevel** - Single R-depth adjacency matrix
2. **StratifiedAdjacency** - Multi-level block-diagonal structure
3. **PortPromotion** - Cross-scope functor F: R+1 → R
4. **MorphInject/Split/Fuse** - Graph transformations as matrix operations
5. **TensorizedContainer** - Integration with existing Container model
6. **CompositeBoundaryDetector** - Matrix-based unsatisfied I/O detection

### Properties Preserved

- ✅ Scope isolation: Block-diagonal A_R
- ✅ Type safety: Port promotion validation
- ✅ Functorial composition: Matrix multiplication chains
- ✅ Sparse efficiency: scipy.sparse.csr_matrix
- ✅ GPU acceleration: PyTorch Geometric compatibility

### Next Steps

1. Integrate with existing `models.py` (Link, UserContainer)
2. Implement morphism operations fully
3. Add unit tests for boundary detection accuracy
4. Benchmark sparse vs dense for typical graph sizes
5. Prototype GPU execution pipeline with PyG
