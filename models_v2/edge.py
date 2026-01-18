"""Edge model - morphism between nodes with port wiring.

Edges connect nodes in the graph. They are morphisms in the category
and carry port-to-port wire specifications.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from models_v2.categorical_base import Morphism


class WireSpec(BaseModel):
    """Port-to-port connection specification within an edge."""
    source_port_id: UUID
    target_port_id: UUID


class Edge(Morphism):
    """
    Graph edge - morphism between nodes.
    
    An Edge:
    - Connects source_node → target_node
    - Carries wire specifications (port mappings)
    - Validates scope depth consistency
    
    No legacy predecessors/successors - clean morphism semantics.
    """
    id: UUID = Field(default_factory=uuid4)
    
    # Morphism structure (source/target from Morphism base)
    source_node_id: UUID
    target_node_id: UUID
    
    # Port-level wiring
    wire_specs: list[WireSpec] = Field(default_factory=list)
    
    # Cached scope (set during validation with node context)
    _scope_depth: Optional[int] = None
    
    @model_validator(mode='before')
    @classmethod
    def set_morphism_fields(cls, data: dict) -> dict:
        """Map node IDs to morphism source/target."""
        if isinstance(data, dict):
            if 'source_node_id' in data and 'source' not in data:
                data['source'] = data['source_node_id']
            if 'target_node_id' in data and 'target' not in data:
                data['target'] = data['target_node_id']
        return data

    def compose(self, other: Edge) -> Optional[Edge]:
        """
        Compose edges: self ∘ other
        
        self: B → C, other: A → B
        result: A → C (if self.source == other.target)
        """
        if self.source != other.target:
            return None

        return Edge(
            source_node_id=other.source_node_id,
            target_node_id=self.target_node_id,
            wire_specs=[]  # Composite doesn't preserve individual wires
        )

    @classmethod
    def identity(cls, node_id: UUID) -> Edge:
        """Create identity edge: node → node"""
        return cls(
            source_node_id=node_id,
            target_node_id=node_id,
            wire_specs=[]
        )
