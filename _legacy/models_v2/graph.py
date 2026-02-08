"""Graph model - owns nodes and edges, provides topology methods.

The Graph is a first-class object that manages topology. It derives
composite definitions from its structure.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, computed_field

from .node import Node
from .edge import Edge
from .port import Port

if TYPE_CHECKING:
    from models_v2.definition import CompositeDefinition


class Graph(BaseModel):
    """
    First-class graph object - owns nodes and edges.
    
    The Graph:
    - Manages topology (nodes + edges)
    - Derives composite definitions from structure
    - Provides query methods for topology
    
    Flat structure: nodes have scope_depth as attribute.
    No subgraphs field - UI derives nesting from scope values.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    owner_id: UUID  # UserObject or Definition that owns this graph
    
    # Graph structure
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    
    # ========================================================================
    # NODE OPERATIONS
    # ========================================================================
    
    def add_node(
        self,
        name: str,
        definition_id: Optional[UUID] = None,
        scope_depth: int = 0,
        visual_x: float = 0.0,
        visual_y: float = 0.0
    ) -> Node:
        """Add a new node to the graph."""
        node = Node(
            name=name,
            definition_id=definition_id,
            graph_id=self.id,
            scope_depth=scope_depth,
            visual_x=visual_x,
            visual_y=visual_y
        )
        self.nodes.append(node)
        return node

    def get_node(self, node_id: UUID) -> Optional[Node]:
        """Get node by ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def nodes_at_scope(self, scope_depth: int) -> list[Node]:
        """Get all nodes at a specific scope depth."""
        return [n for n in self.nodes if n.scope_depth == scope_depth]

    # ========================================================================
    # EDGE OPERATIONS
    # ========================================================================

    def add_edge(
        self,
        source_node_id: UUID,
        target_node_id: UUID,
        wire_specs: list[dict] | None = None
    ) -> Edge:
        """
        Add edge between nodes.
        
        Validates that source and target nodes exist and have same scope.
        """
        source = self.get_node(source_node_id)
        target = self.get_node(target_node_id)
        
        if source is None or target is None:
            raise ValueError("Source or target node not found in graph")
        
        if source.scope_depth != target.scope_depth:
            raise ValueError(
                f"Scope mismatch: cannot connect R={source.scope_depth} "
                f"to R={target.scope_depth}. Use port promotion."
            )
        
        from models_v2.edge import WireSpec
        specs = [WireSpec(**ws) for ws in (wire_specs or [])]
        
        edge = Edge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            wire_specs=specs
        )
        self.edges.append(edge)
        return edge

    def get_edges_from(self, node_id: UUID) -> list[Edge]:
        """Get all edges originating from a node."""
        return [e for e in self.edges if e.source_node_id == node_id]

    def get_edges_to(self, node_id: UUID) -> list[Edge]:
        """Get all edges targeting a node."""
        return [e for e in self.edges if e.target_node_id == node_id]

    # ========================================================================
    # TOPOLOGY QUERIES
    # ========================================================================

    def predecessors(self, node_id: UUID) -> list[Node]:
        """Get nodes that have edges pointing to this node."""
        incoming_edges = self.get_edges_to(node_id)
        return [
            n for n in self.nodes 
            if n.id in [e.source_node_id for e in incoming_edges]
        ]

    def successors(self, node_id: UUID) -> list[Node]:
        """Get nodes that this node points to."""
        outgoing_edges = self.get_edges_from(node_id)
        return [
            n for n in self.nodes 
            if n.id in [e.target_node_id for e in outgoing_edges]
        ]

    def boundary_nodes(self) -> tuple[list[Node], list[Node]]:
        """
        Find boundary nodes (inputs and outputs).
        
        Input nodes: no incoming edges
        Output nodes: no outgoing edges
        """
        node_ids = {n.id for n in self.nodes}
        targets = {e.target_node_id for e in self.edges}
        sources = {e.source_node_id for e in self.edges}
        
        input_ids = node_ids - targets  # No incoming
        output_ids = node_ids - sources  # No outgoing
        
        inputs = [n for n in self.nodes if n.id in input_ids]
        outputs = [n for n in self.nodes if n.id in output_ids]
        
        return inputs, outputs

    @computed_field
    @property
    def scope_depths(self) -> set[int]:
        """All unique scope depths in this graph."""
        return {n.scope_depth for n in self.nodes}

    # ========================================================================
    # DEFINITION DERIVATION
    # ========================================================================

    def derive_composite_definition(
        self,
        name: str,
        definition_registry: dict[UUID, "Definition"] | None = None
    ) -> "CompositeDefinition":
        """
        Create CompositeDefinition from this graph's topology.
        
        Collects definitions from nodes, derives boundary I/O.
        """
        from models_v2.definition import CompositeDefinition
        from models_v2.composite_boundary import BoundaryDerivation
        
        # Collect internal definitions
        internal_defs = []
        if definition_registry:
            for node in self.nodes:
                if node.definition_id and node.definition_id in definition_registry:
                    internal_defs.append(definition_registry[node.definition_id])
        
        # Derive boundary
        derivation = BoundaryDerivation(
            internal_definitions=internal_defs,
            internal_wires=self._extract_wires()
        )
        boundary_inputs, boundary_outputs = derivation.derive_boundary()
        
        return CompositeDefinition(
            name=name,
            input_ports=list(boundary_inputs),
            output_ports=list(boundary_outputs),
            internal_definitions=internal_defs,
            internal_graph_id=self.id
        )

    def _extract_wires(self) -> list:
        """Convert edges to wire format for boundary derivation."""
        from models_v2.wire import Wire
        wires = []
        for edge in self.edges:
            for ws in edge.wire_specs:
                wires.append(Wire(
                    source_port_id=ws.source_port_id,
                    target_port_id=ws.target_port_id
                ))
        return wires

    # ========================================================================
    # TENSOR / EMBEDDING OPERATIONS
    # ========================================================================

    def to_tensor(self) -> "GraphTensor":
        """
        Convert to tensor representation for GPU operations.
        
        Returns:
            GraphTensor with adjacency matrix and scope masks
        """
        from models_v2.graph_tensor import GraphTensor
        return GraphTensor.from_graph(self)

    def embed_nodes(self, method: str = "structural") -> dict:
        """
        Generate embeddings for all nodes.
        
        Args:
            method: "structural", "content", or "hybrid"
            
        Returns:
            Dict mapping node_id -> NodeEmbedding
        """
        from models_v2.node_embedding import EmbeddingGenerator
        generator = EmbeddingGenerator(method=method)
        return generator.embed_graph(self)

