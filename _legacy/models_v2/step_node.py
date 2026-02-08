"""Step node - executable node with attached code.

Bridges models_v2.Node with pydantic-graph step functions.
"""
from __future__ import annotations
from typing import Any, Callable, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from .node import Node

if TYPE_CHECKING:
    from .definition import AtomicDefinition


class StepNode(BaseModel):
    """
    Node with executable step function.
    
    Combines:
    - models_v2.Node (topology, visual position)
    - pydantic-graph step reference (execution)
    - Optional AtomicDefinition (I/O contract)
    
    Example:
        @builder.step
        async def my_handler(ctx):
            return ctx.inputs * 2
            
        step = StepNode(
            node=Node(name="doubler", ...),
            handler_name="my_handler",
            definition=some_atomic_def
        )
    """
    
    # Topology reference
    node: Node
    
    # Handler identification (for serialization)
    handler_name: str = Field(..., description="Name of registered step function")
    
    # Runtime reference (not serialized)
    step_fn: Any = Field(default=None, exclude=True, description="pydantic-graph step reference")
    
    # Optional definition for I/O contract
    definition_id: Optional[UUID] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    # ========================================================================
    # CONVENIENCE PROPERTIES  
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        """Node ID."""
        return self.node.id
    
    @property
    def name(self) -> str:
        """Node name."""
        return self.node.name
    
    @property
    def scope_depth(self) -> int:
        """Node scope depth (R-value)."""
        return self.node.scope_depth
    
    @property
    def visual_position(self) -> tuple[float, float]:
        """Visual coordinates for rendering."""
        return (self.node.visual_x, self.node.visual_y)
    
    # ========================================================================
    # EXECUTION BINDING
    # ========================================================================
    
    def bind_handler(self, handler: Callable) -> None:
        """
        Bind runtime handler function.
        
        Called by ColliderGraphBuilder when building the executable graph.
        """
        self.step_fn = handler
    
    def is_bound(self) -> bool:
        """Check if handler is bound for execution."""
        return self.step_fn is not None
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_topology_dict(self) -> dict:
        """Export for Three.js visualization."""
        return {
            "id": str(self.node.id),
            "name": self.node.name,
            "type": "step",
            "scope_depth": self.node.scope_depth,
            "visual_x": self.node.visual_x,
            "visual_y": self.node.visual_y,
            "handler": self.handler_name,
            "definition_id": str(self.definition_id) if self.definition_id else None
        }


class EmptyNode(BaseModel):
    """
    Empty bubble node - no logic, just topology.
    
    Used for:
    - Visual organization
    - Placeholder for future logic
    - Grouping without execution
    """
    
    node: Node
    label: str = ""  # Optional display label
    
    @property
    def id(self) -> UUID:
        return self.node.id
    
    @property
    def name(self) -> str:
        return self.node.name
    
    @property
    def scope_depth(self) -> int:
        return self.node.scope_depth
    
    def to_topology_dict(self) -> dict:
        """Export for Three.js visualization."""
        return {
            "id": str(self.node.id),
            "name": self.node.name,
            "type": "empty",
            "scope_depth": self.node.scope_depth,
            "visual_x": self.node.visual_x,
            "visual_y": self.node.visual_y,
            "label": self.label
        }
