"""Collider Graph - combined topology + execution.

The final executable graph produced by ColliderGraphBuilder.
"""
from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from uuid import UUID
from pydantic import BaseModel, Field

from models_v2.graph import Graph
from models_v2.step_node import StepNode, EmptyNode
from models_v2.decision_node import DecisionNode
from models_v2.subgraph_node import SubgraphNode

if TYPE_CHECKING:
    from models_v2.definition import CompositeDefinition


# Union of all node types
AnyNode = StepNode | DecisionNode | SubgraphNode | EmptyNode


class ColliderGraph(BaseModel):
    """
    Complete Collider graph with topology + execution.
    
    Produced by ColliderGraphBuilder.build().
    
    Contains:
    - topology: models_v2.Graph (nodes, edges, scope)
    - executor: pydantic-graph Graph (runtime execution)
    - typed_nodes: Registry of StepNode/DecisionNode/SubgraphNode
    
    Example:
        graph = builder.build()
        result = await graph.run(inputs={"query": "hello"})
        mermaid = graph.render()
    """
    
    # Topology layer (serializable)
    topology: Graph
    
    # Typed node registry
    step_nodes: dict[UUID, StepNode] = Field(default_factory=dict)
    decision_nodes: dict[UUID, DecisionNode] = Field(default_factory=dict)
    subgraph_nodes: dict[UUID, SubgraphNode] = Field(default_factory=dict)
    empty_nodes: dict[UUID, EmptyNode] = Field(default_factory=dict)
    
    # Execution layer (not serialized)
    _executor: Any = None  # pydantic-graph Graph
    
    class Config:
        arbitrary_types_allowed = True
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    async def run(
        self,
        inputs: Any = None,
        state: Any = None,
        deps: Any = None
    ) -> Any:
        """
        Execute the graph.
        
        Args:
            inputs: Initial input data
            state: Shared mutable state
            deps: Injected dependencies
            
        Returns:
            Final output from end node
        """
        if self._executor is None:
            raise RuntimeError("Graph not bound to executor. Use bind_executor() first.")
        
        return await self._executor.run(state=state, inputs=inputs, deps=deps)
    
    async def run_iter(
        self,
        inputs: Any = None,
        state: Any = None,
        deps: Any = None
    ):
        """
        Execute graph step-by-step (generator).
        
        Yields execution events for debugging/tracing.
        """
        if self._executor is None:
            raise RuntimeError("Graph not bound to executor.")
        
        async with self._executor.iter(state=state, inputs=inputs, deps=deps) as graph_run:
            async for event in graph_run:
                yield event
            # Yield final output (async generators can't return values)
            if graph_run.output is not None:
                yield {"type": "output", "value": graph_run.output}
    
    def bind_executor(self, executor: Any) -> None:
        """Bind pydantic-graph executor at runtime."""
        self._executor = executor
    
    # ========================================================================
    # VISUALIZATION
    # ========================================================================
    
    def render(self, title: str = "Collider Graph", direction: str = "LR") -> str:
        """
        Generate Mermaid diagram.
        
        Uses pydantic-graph's render if available, otherwise manual generation.
        """
        if self._executor and hasattr(self._executor, 'render'):
            return self._executor.render(title=title, direction=direction)
        
        # Manual Mermaid generation from topology
        return self._render_from_topology(title, direction)
    
    def _render_from_topology(self, title: str, direction: str) -> str:
        """Generate Mermaid from topology when executor not available."""
        lines = [
            "---",
            f"title: {title}",
            "---",
            "stateDiagram-v2",
            f"direction {direction}",
            ""
        ]
        
        # Add nodes
        for node in self.topology.nodes:
            node_type = self._get_node_type(node.id)
            if node_type == "step":
                lines.append(f"    {node.name}")
            elif node_type == "decision":
                lines.append(f"    {node.name}: <<decision>>")
            elif node_type == "subgraph":
                lines.append(f"    state {node.name} {{")
                # Add inner nodes
                subgraph = self.subgraph_nodes.get(node.id)
                if subgraph:
                    for inner in subgraph.get_inner_nodes():
                        lines.append(f"        {inner.name}")
                lines.append("    }")
            else:
                lines.append(f"    {node.name}: <<empty>>")
        
        lines.append("")
        
        # Add edges
        for edge in self.topology.edges:
            source = self.topology.get_node(edge.source_node_id)
            target = self.topology.get_node(edge.target_node_id)
            if source and target:
                lines.append(f"    {source.name} --> {target.name}")
        
        return "\n".join(lines)
    
    def _get_node_type(self, node_id: UUID) -> str:
        """Determine node type from registries."""
        if node_id in self.step_nodes:
            return "step"
        elif node_id in self.decision_nodes:
            return "decision"
        elif node_id in self.subgraph_nodes:
            return "subgraph"
        elif node_id in self.empty_nodes:
            return "empty"
        return "unknown"
    
    # ========================================================================
    # DEFINITION DERIVATION
    # ========================================================================
    
    def derive_definition(
        self,
        name: str,
        definition_registry: dict[UUID, Any] | None = None
    ) -> "CompositeDefinition":
        """
        Derive CompositeDefinition from graph topology.
        
        The emerged I/O boundary becomes the Definition interface.
        """
        return self.topology.derive_composite_definition(name, definition_registry)
    
    # ========================================================================
    # NODE ACCESS
    # ========================================================================
    
    def get_node(self, node_id: UUID) -> AnyNode | None:
        """Get typed node by ID."""
        if node_id in self.step_nodes:
            return self.step_nodes[node_id]
        elif node_id in self.decision_nodes:
            return self.decision_nodes[node_id]
        elif node_id in self.subgraph_nodes:
            return self.subgraph_nodes[node_id]
        elif node_id in self.empty_nodes:
            return self.empty_nodes[node_id]
        return None
    
    def get_all_nodes(self) -> list[AnyNode]:
        """Get all typed nodes."""
        nodes: list[AnyNode] = []
        nodes.extend(self.step_nodes.values())
        nodes.extend(self.decision_nodes.values())
        nodes.extend(self.subgraph_nodes.values())
        nodes.extend(self.empty_nodes.values())
        return nodes
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def to_threejs_data(self) -> dict:
        """
        Export full graph data for Three.js visualization.
        
        Returns structure matching your 3D rendering.
        """
        nodes_data = []
        
        for node in self.get_all_nodes():
            nodes_data.append(node.to_topology_dict())
        
        edges_data = []
        for edge in self.topology.edges:
            edges_data.append({
                "id": str(edge.id),
                "source_id": str(edge.source_node_id),
                "target_id": str(edge.target_node_id),
                "has_condition": bool(edge.condition_id) if hasattr(edge, 'condition_id') else False
            })
        
        return {
            "graph_id": str(self.topology.id),
            "graph_name": self.topology.name,
            "nodes": nodes_data,
            "edges": edges_data,
            "scope_depths": list(self.topology.scope_depths)
        }
