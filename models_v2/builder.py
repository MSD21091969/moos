"""Collider Graph Builder - main API for constructing graphs.

Wraps pydantic-graph/beta GraphBuilder while maintaining models_v2 topology.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

from models_v2.graph import Graph
from models_v2.node import Node
from models_v2.edge import Edge
from models_v2.port import Port
from models_v2.step_node import StepNode, EmptyNode
from models_v2.decision_node import DecisionNode, DecisionBranch
from models_v2.subgraph_node import SubgraphNode
from models_v2.edge_condition import EdgeCondition, AnyCondition
from models_v2.collider_graph import ColliderGraph

# Try to import pydantic-graph beta (optional dependency)
try:
    from pydantic_graph.beta import GraphBuilder, StepContext
    PYDANTIC_GRAPH_AVAILABLE = True
except ImportError:
    PYDANTIC_GRAPH_AVAILABLE = False
    GraphBuilder = None
    StepContext = None


# ============================================================================
# STATE MODEL
# ============================================================================

@dataclass
class ColliderState:
    """
    Shared state across all nodes in a Collider graph.
    
    Each graph execution gets a fresh instance.
    Subgraphs get ISOLATED state (not shared with parent).
    """
    graph_id: UUID = field(default_factory=uuid4)
    scope_depth: int = 0
    execution_trace: list[str] = field(default_factory=list)
    accumulated_data: dict = field(default_factory=dict)
    
    def trace(self, node_name: str) -> None:
        """Record node execution in trace."""
        self.execution_trace.append(node_name)
    
    def set(self, key: str, value: Any) -> None:
        """Store data in accumulated state."""
        self.accumulated_data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve data from accumulated state."""
        return self.accumulated_data.get(key, default)


# ============================================================================
# HANDLER REGISTRY
# ============================================================================

class HandlerRegistry:
    """
    Registry of step handler functions.
    
    Enables serialization by name + runtime binding.
    """
    
    _handlers: dict[str, Callable] = {}
    
    @classmethod
    def register(cls, name: str) -> Callable[[Callable], Callable]:
        """Decorator to register a handler by name."""
        def decorator(fn: Callable) -> Callable:
            cls._handlers[name] = fn
            return fn
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Callable | None:
        """Get handler by name."""
        return cls._handlers.get(name)
    
    @classmethod
    def all_names(cls) -> list[str]:
        """List all registered handler names."""
        return list(cls._handlers.keys())


# ============================================================================
# BUILDER
# ============================================================================

class ColliderGraphBuilder:
    """
    Builder for constructing Collider graphs.
    
    Wraps pydantic-graph/beta GraphBuilder (if available) while
    maintaining models_v2 topology in parallel.
    
    Features:
    - Add nodes with/without definitions
    - Connect via edges (with optional conditions)
    - Create subgraphs (nested builders)
    - Derive boundary from edge analysis
    
    Example:
        g = ColliderGraphBuilder(name="MyGraph")
        
        @g.step
        async def process(ctx):
            return ctx.inputs * 2
        
        g.connect(g.start, process)
        g.connect(process, g.end)
        
        graph = g.build()
        result = await graph.run(inputs=10)
    """
    
    def __init__(
        self,
        name: str,
        scope_depth: int = 0,
        owner_id: UUID | None = None,
        state_type: type = ColliderState,
        input_type: type = Any,
        output_type: type = Any
    ):
        self.name = name
        self._scope_depth = scope_depth
        self._state_type = state_type
        self._input_type = input_type
        self._output_type = output_type
        
        # Topology layer
        self._graph = Graph(
            name=name,
            owner_id=owner_id or uuid4()
        )
        
        # Node registries
        self._step_nodes: dict[UUID, StepNode] = {}
        self._decision_nodes: dict[UUID, DecisionNode] = {}
        self._subgraph_nodes: dict[UUID, SubgraphNode] = {}
        self._empty_nodes: dict[UUID, EmptyNode] = {}
        
        # Handler registry for this builder
        self._handlers: dict[str, Callable] = {}
        
        # pydantic-graph layer (optional)
        self._pyd_builder = None
        if PYDANTIC_GRAPH_AVAILABLE:
            self._pyd_builder = GraphBuilder(
                state_type=state_type,
                input_type=input_type,
                output_type=output_type
            )
        
        # Start/End virtual nodes
        self._start_node_id: UUID | None = None
        self._end_node_id: UUID | None = None
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def start(self) -> UUID:
        """Start node ID (virtual entry point)."""
        if self._start_node_id is None:
            # Create virtual start node
            node = self._graph.add_node(
                name="__start__",
                scope_depth=self._scope_depth
            )
            self._start_node_id = node.id
            self._empty_nodes[node.id] = EmptyNode(node=node, label="START")
        return self._start_node_id
    
    @property
    def end(self) -> UUID:
        """End node ID (virtual exit point)."""
        if self._end_node_id is None:
            node = self._graph.add_node(
                name="__end__",
                scope_depth=self._scope_depth
            )
            self._end_node_id = node.id
            self._empty_nodes[node.id] = EmptyNode(node=node, label="END")
        return self._end_node_id
    
    @property
    def scope_depth(self) -> int:
        """Current scope depth (R-value)."""
        return self._scope_depth
    
    # ========================================================================
    # NODE CREATION
    # ========================================================================
    
    def add_empty_node(
        self,
        name: str,
        label: str = "",
        visual_x: float = 0.0,
        visual_y: float = 0.0
    ) -> EmptyNode:
        """
        Create empty bubble node (no logic).
        
        Used for visual organization or placeholders.
        """
        node = self._graph.add_node(
            name=name,
            scope_depth=self._scope_depth,
            visual_x=visual_x,
            visual_y=visual_y
        )
        empty = EmptyNode(node=node, label=label)
        self._empty_nodes[node.id] = empty
        return empty
    
    def step(self, fn: Callable) -> StepNode:
        """
        Decorator to create step node from async function.
        
        Example:
            @g.step
            async def my_handler(ctx):
                return ctx.inputs * 2
        """
        handler_name = fn.__name__
        self._handlers[handler_name] = fn
        
        # Create topology node
        node = self._graph.add_node(
            name=handler_name,
            scope_depth=self._scope_depth
        )
        
        # Create step node
        step_node = StepNode(
            node=node,
            handler_name=handler_name
        )
        step_node.bind_handler(fn)
        
        self._step_nodes[node.id] = step_node
        
        # Register with pydantic-graph if available
        if self._pyd_builder:
            self._pyd_builder.step(fn)
        
        return step_node
    
    def add_step_node(
        self,
        name: str,
        handler: Callable,
        definition_id: UUID | None = None,
        visual_x: float = 0.0,
        visual_y: float = 0.0
    ) -> StepNode:
        """
        Create step node with explicit handler.
        
        Alternative to decorator syntax.
        """
        handler_name = handler.__name__
        self._handlers[handler_name] = handler
        
        node = self._graph.add_node(
            name=name,
            definition_id=definition_id,
            scope_depth=self._scope_depth,
            visual_x=visual_x,
            visual_y=visual_y
        )
        
        step_node = StepNode(
            node=node,
            handler_name=handler_name,
            definition_id=definition_id
        )
        step_node.bind_handler(handler)
        
        self._step_nodes[node.id] = step_node
        
        if self._pyd_builder:
            self._pyd_builder.step(handler)
        
        return step_node
    
    def add_decision_node(
        self,
        name: str,
        branches: list[tuple[str, AnyCondition, UUID]] | None = None,
        visual_x: float = 0.0,
        visual_y: float = 0.0
    ) -> DecisionNode:
        """
        Create decision node for conditional branching.
        
        Args:
            name: Node name
            branches: List of (label, condition, target_node_id) tuples
        """
        node = self._graph.add_node(
            name=name,
            scope_depth=self._scope_depth,
            visual_x=visual_x,
            visual_y=visual_y
        )
        
        decision = DecisionNode(node=node)
        
        if branches:
            for label, condition, target_id in branches:
                decision.add_branch(label, condition, target_id)
        
        self._decision_nodes[node.id] = decision
        return decision
    
    def add_subgraph(
        self,
        name: str,
        inner_builder: "ColliderGraphBuilder",
        visual_x: float = 0.0,
        visual_y: float = 0.0
    ) -> SubgraphNode:
        """
        Embed nested graph as single node.
        
        The inner graph's scope_depth is incremented.
        Its boundary becomes this node's I/O interface.
        """
        # Increment inner scope
        inner_builder._scope_depth = self._scope_depth + 1
        
        # Build inner graph
        inner_graph = inner_builder.build()
        
        # Derive boundary definition
        boundary = inner_graph.derive_definition(f"{name}_boundary")
        
        # Create outer node
        node = self._graph.add_node(
            name=name,
            definition_id=boundary.id,
            scope_depth=self._scope_depth,
            visual_x=visual_x,
            visual_y=visual_y
        )
        
        subgraph = SubgraphNode(
            node=node,
            inner_graph_id=inner_graph.topology.id,
            boundary_definition_id=boundary.id
        )
        subgraph.bind_graph(inner_graph.topology)
        subgraph.bind_boundary(boundary)
        
        self._subgraph_nodes[node.id] = subgraph
        return subgraph
    
    # ========================================================================
    # EDGE CREATION
    # ========================================================================
    
    def connect(
        self,
        source: UUID | StepNode | DecisionNode | SubgraphNode | EmptyNode,
        target: UUID | StepNode | DecisionNode | SubgraphNode | EmptyNode,
        condition: AnyCondition | None = None,
        wire_map: dict[str, str] | None = None
    ) -> Edge:
        """
        Connect two nodes with an edge.
        
        Args:
            source: Source node or ID
            target: Target node or ID
            condition: Optional condition for edge activation
            wire_map: Port mapping {source_port_name: target_port_name}
        """
        source_id = source if isinstance(source, UUID) else source.id
        target_id = target if isinstance(target, UUID) else target.id
        
        # Build wire specs from wire_map
        wire_specs = []
        if wire_map:
            for src_port, tgt_port in wire_map.items():
                wire_specs.append({
                    "source_port_id": str(uuid4()),  # Would resolve from definition
                    "target_port_id": str(uuid4()),
                    "source_port_name": src_port,
                    "target_port_name": tgt_port
                })
        
        edge = self._graph.add_edge(
            source_node_id=source_id,
            target_node_id=target_id,
            wire_specs=wire_specs
        )
        
        # Store condition (will be used at runtime)
        if condition:
            # Add condition tracking (edge model would need extension)
            pass
        
        # Add to pydantic-graph if available
        if self._pyd_builder:
            source_step = self._handlers.get(self._get_handler_name(source_id))
            target_step = self._handlers.get(self._get_handler_name(target_id))
            
            if source_step and target_step:
                # Would add edge via pyd_builder
                pass
        
        return edge
    
    def _get_handler_name(self, node_id: UUID) -> str | None:
        """Get handler name for a node."""
        if node_id in self._step_nodes:
            return self._step_nodes[node_id].handler_name
        return None
    
    # ========================================================================
    # BUILD
    # ========================================================================
    
    def build(self) -> ColliderGraph:
        """
        Build the final executable graph.
        
        Returns ColliderGraph with topology + execution.
        """
        graph = ColliderGraph(
            topology=self._graph,
            step_nodes=self._step_nodes,
            decision_nodes=self._decision_nodes,
            subgraph_nodes=self._subgraph_nodes,
            empty_nodes=self._empty_nodes
        )
        
        # Bind pydantic-graph executor if available
        if self._pyd_builder:
            # Build pydantic-graph
            # (Full implementation would add all edges to pyd_builder first)
            try:
                pyd_graph = self._pyd_builder.build()
                graph.bind_executor(pyd_graph)
            except Exception:
                # Graph might be incomplete for pyd-graph
                pass
        
        return graph
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def derive_definition(self, name: str) -> "CompositeDefinition":
        """Derive CompositeDefinition from current topology."""
        from models_v2.definition import CompositeDefinition
        return self._graph.derive_composite_definition(name)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram of current topology."""
        graph = self.build()
        return graph.render(title=self.name)


# ============================================================================
# CONVENIENCE EXPORTS
# ============================================================================

def create_builder(
    name: str,
    scope_depth: int = 0
) -> ColliderGraphBuilder:
    """Factory function to create a builder."""
    return ColliderGraphBuilder(name=name, scope_depth=scope_depth)
