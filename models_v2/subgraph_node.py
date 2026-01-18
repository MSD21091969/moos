"""Subgraph node - nested graph as single node.

Enables hierarchical composition with emerged I/O boundaries.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, computed_field

from models_v2.node import Node
from models_v2.port import Port

if TYPE_CHECKING:
    from models_v2.graph import Graph
    from models_v2.definition import CompositeDefinition


class SubgraphNode(BaseModel):
    """
    Node containing a nested graph.
    
    The subgraph's boundary becomes this node's I/O interface.
    Dependents emerge when edges cross into/out of the subgraph.
    
    Key properties:
    - inner_graph has scope_depth = parent.scope_depth + 1
    - boundary derived via tri-method validation
    - state is ISOLATED from parent (passed via edges)
    
    Example:
        # Create inner graph
        validation_builder = ColliderGraphBuilder(name="Validation")
        ...
        
        # Embed as subgraph
        subgraph = SubgraphNode(
            node=Node(name="validate", scope_depth=0, ...),
            inner_graph=validation_builder.build().topology,
            boundary=validation_builder.derive_definition("ValidationDef")
        )
    """
    
    # Outer topology (how this appears in parent graph)
    node: Node
    
    # Inner structure
    inner_graph_id: UUID = Field(..., description="ID of the nested Graph")
    
    # Derived boundary (I/O interface)
    boundary_definition_id: UUID = Field(..., description="ID of derived CompositeDefinition")
    
    # Cached references (not serialized, populated at runtime)
    _inner_graph: Any = None  # Graph
    _boundary: Any = None  # CompositeDefinition
    
    class Config:
        arbitrary_types_allowed = True
    
    # ========================================================================
    # CONVENIENCE PROPERTIES
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        return self.node.id
    
    @property
    def name(self) -> str:
        return self.node.name
    
    @property
    def scope_depth(self) -> int:
        """Outer scope depth (inner is +1)."""
        return self.node.scope_depth
    
    @property
    def inner_scope_depth(self) -> int:
        """Scope depth inside the subgraph."""
        return self.node.scope_depth + 1
    
    # ========================================================================
    # BOUNDARY ACCESS
    # ========================================================================
    
    def get_input_ports(self) -> list[Port]:
        """Get emerged input ports from boundary."""
        if self._boundary:
            return self._boundary.input_ports
        return []
    
    def get_output_ports(self) -> list[Port]:
        """Get emerged output ports from boundary."""
        if self._boundary:
            return self._boundary.output_ports
        return []
    
    def bind_graph(self, graph: "Graph") -> None:
        """Bind the inner graph reference at runtime."""
        self._inner_graph = graph
    
    def bind_boundary(self, boundary: "CompositeDefinition") -> None:
        """Bind the boundary definition at runtime."""
        self._boundary = boundary
    
    # ========================================================================
    # INNER GRAPH ACCESS
    # ========================================================================
    
    def get_inner_nodes(self) -> list:
        """Get nodes inside the subgraph."""
        if self._inner_graph:
            return self._inner_graph.nodes
        return []
    
    def get_inner_edges(self) -> list:
        """Get edges inside the subgraph."""
        if self._inner_graph:
            return self._inner_graph.edges
        return []
    
    def get_boundary_nodes(self) -> tuple[list, list]:
        """
        Get boundary nodes (entry/exit points).
        
        Returns:
            (input_nodes, output_nodes) - nodes at the subgraph boundary
        """
        if self._inner_graph:
            return self._inner_graph.boundary_nodes()
        return ([], [])
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_topology_dict(self) -> dict:
        """Export for Three.js visualization."""
        return {
            "id": str(self.node.id),
            "name": self.node.name,
            "type": "subgraph",
            "scope_depth": self.node.scope_depth,
            "visual_x": self.node.visual_x,
            "visual_y": self.node.visual_y,
            "inner_graph_id": str(self.inner_graph_id),
            "boundary_definition_id": str(self.boundary_definition_id),
            "input_ports": [
                {"name": p.name, "type": str(p.type_schema)}
                for p in self.get_input_ports()
            ],
            "output_ports": [
                {"name": p.name, "type": str(p.type_schema)}
                for p in self.get_output_ports()
            ],
            # Recursive: include inner nodes for visualization
            "inner_nodes": [
                {"id": str(n.id), "name": n.name, "scope_depth": n.scope_depth}
                for n in self.get_inner_nodes()
            ]
        }
