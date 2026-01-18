"""Graph tensor - GPU-ready tensor operations on graphs.

Converts flat node index → adjacency matrix for O(1) operations.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from uuid import UUID
import numpy as np
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from models_v2.graph import Graph


class GraphTensor(BaseModel):
    """
    Tensor representation of graph for GPU operations.
    
    Converts:
    - nodes list → node index mapping
    - edges list → adjacency matrix
    - scope_depth → block-diagonal mask
    
    Example:
        tensor = GraphTensor.from_graph(graph)
        reach = tensor.reachability()
        inputs, outputs = tensor.boundary_indices()
    """
    
    # Node ordering
    node_ids: list[UUID]
    node_names: list[str] = Field(default_factory=list)
    scope_depths: list[int] = Field(default_factory=list)
    
    # Matrices (stored as nested lists for Pydantic serialization)
    _adjacency: Optional[np.ndarray] = None
    _scope_mask: Optional[np.ndarray] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    # ========================================================================
    # CONSTRUCTION
    # ========================================================================
    
    @classmethod
    def from_graph(cls, graph: "Graph") -> "GraphTensor":
        """
        Convert models_v2.Graph to tensor form.
        
        Args:
            graph: Graph with nodes and edges
            
        Returns:
            GraphTensor with adjacency and scope matrices
        """
        n = len(graph.nodes)
        node_ids = [node.id for node in graph.nodes]
        node_names = [node.name for node in graph.nodes]
        scope_depths = [node.scope_depth for node in graph.nodes]
        id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        
        # Build adjacency matrix
        adj = np.zeros((n, n), dtype=np.float32)
        for edge in graph.edges:
            src_idx = id_to_idx.get(edge.source_node_id)
            tgt_idx = id_to_idx.get(edge.target_node_id)
            if src_idx is not None and tgt_idx is not None:
                adj[src_idx, tgt_idx] = 1.0
        
        # Build scope isolation mask (block-diagonal)
        scope_mask = np.zeros((n, n), dtype=np.float32)
        for i in range(n):
            for j in range(n):
                if scope_depths[i] == scope_depths[j]:
                    scope_mask[i, j] = 1.0
        
        tensor = cls(
            node_ids=node_ids,
            node_names=node_names,
            scope_depths=scope_depths
        )
        tensor._adjacency = adj
        tensor._scope_mask = scope_mask
        
        return tensor
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def num_nodes(self) -> int:
        return len(self.node_ids)
    
    @property
    def adjacency(self) -> np.ndarray:
        if self._adjacency is None:
            self._adjacency = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float32)
        return self._adjacency
    
    @property
    def scope_mask(self) -> np.ndarray:
        if self._scope_mask is None:
            self._scope_mask = np.ones((self.num_nodes, self.num_nodes), dtype=np.float32)
        return self._scope_mask
    
    def node_index(self, node_id: UUID) -> int | None:
        """Get matrix index for node ID."""
        try:
            return self.node_ids.index(node_id)
        except ValueError:
            return None
    
    # ========================================================================
    # GRAPH OPERATIONS
    # ========================================================================
    
    def reachability(self, max_steps: int | None = None) -> np.ndarray:
        """
        Compute transitive closure (which nodes can reach which).
        
        Uses matrix powers: R = I + A + A² + A³ + ...
        
        Args:
            max_steps: Maximum path length (default: num_nodes)
            
        Returns:
            N×N boolean matrix where [i,j]=1 means i can reach j
        """
        if max_steps is None:
            max_steps = self.num_nodes
        
        result = np.eye(self.num_nodes, dtype=np.float32)
        power = self.adjacency.copy()
        
        for _ in range(max_steps):
            result = np.clip(result + power, 0, 1)
            power = power @ self.adjacency
            if not power.any():  # No more paths
                break
        
        return result
    
    def boundary_indices(self) -> tuple[list[int], list[int]]:
        """
        Find boundary node indices via matrix analysis.
        
        Returns:
            (input_indices, output_indices)
            - Inputs: nodes with no incoming edges (column sum = 0)
            - Outputs: nodes with no outgoing edges (row sum = 0)
        """
        col_sums = self.adjacency.sum(axis=0)
        row_sums = self.adjacency.sum(axis=1)
        
        inputs = np.where(col_sums == 0)[0].tolist()
        outputs = np.where(row_sums == 0)[0].tolist()
        
        return inputs, outputs
    
    def predecessors(self, node_idx: int) -> list[int]:
        """Get indices of nodes that point to this node."""
        return np.where(self.adjacency[:, node_idx] > 0)[0].tolist()
    
    def successors(self, node_idx: int) -> list[int]:
        """Get indices of nodes this node points to."""
        return np.where(self.adjacency[node_idx, :] > 0)[0].tolist()
    
    def in_degree(self, node_idx: int) -> int:
        """Number of incoming edges."""
        return int(self.adjacency[:, node_idx].sum())
    
    def out_degree(self, node_idx: int) -> int:
        """Number of outgoing edges."""
        return int(self.adjacency[node_idx, :].sum())
    
    # ========================================================================
    # SCOPE OPERATIONS
    # ========================================================================
    
    def scope_adjacency(self, scope_depth: int) -> np.ndarray:
        """
        Get adjacency matrix for specific scope level.
        
        Returns submatrix containing only nodes at given depth.
        """
        mask = np.array([1.0 if d == scope_depth else 0.0 for d in self.scope_depths])
        scope_filter = np.outer(mask, mask)
        return self.adjacency * scope_filter
    
    def nodes_at_scope(self, scope_depth: int) -> list[int]:
        """Get indices of nodes at given scope depth."""
        return [i for i, d in enumerate(self.scope_depths) if d == scope_depth]
    
    # ========================================================================
    # GPU ACCELERATION
    # ========================================================================
    
    def to_gpu(self) -> dict:
        """
        Convert matrices to CuPy arrays for GPU acceleration.
        
        Requires: pip install cupy-cuda12x (or appropriate version)
        
        Returns:
            Dict with 'adjacency' and 'scope_mask' as CuPy arrays
        """
        try:
            import cupy as cp
            return {
                "adjacency": cp.array(self.adjacency),
                "scope_mask": cp.array(self.scope_mask),
                "node_ids": self.node_ids,
            }
        except ImportError:
            raise ImportError("CuPy not installed. Install with: pip install cupy-cuda12x")
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> dict:
        """Export for JSON serialization."""
        return {
            "node_ids": [str(nid) for nid in self.node_ids],
            "node_names": self.node_names,
            "scope_depths": self.scope_depths,
            "adjacency": self.adjacency.tolist(),
            "scope_mask": self.scope_mask.tolist(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GraphTensor":
        """Restore from JSON serialization."""
        tensor = cls(
            node_ids=[UUID(nid) for nid in data["node_ids"]],
            node_names=data["node_names"],
            scope_depths=data["scope_depths"],
        )
        tensor._adjacency = np.array(data["adjacency"], dtype=np.float32)
        tensor._scope_mask = np.array(data["scope_mask"], dtype=np.float32)
        return tensor
