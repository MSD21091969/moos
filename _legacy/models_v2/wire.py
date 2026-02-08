"""Wire model - port-to-port connection with validation.

Wires connect output ports to input ports at the same scope depth.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
from typing_extensions import Self

from .port import Port


from .categorical_base import Morphism

class Wire(Morphism):
    """
    Port-to-port connection with scope and type validation.
    
    Wires enforce:
    1. Source must be OUTPUT port
    2. Target must be INPUT port
    3. Same scope depth
    4. Compatible type schemas
    """
    id: UUID = Field(default_factory=uuid4)
    source_port_id: UUID
    target_port_id: UUID
    
    # Port objects for validation (excluded from serialization)
    source_port: Optional[Port] = Field(default=None, exclude=True)
    target_port: Optional[Port] = Field(default=None, exclude=True)

    @property
    def source(self) -> UUID:
        """Source object in category (Source Port ID)"""
        return self.source_port_id

    @property
    def target(self) -> UUID:
        """Target object in category (Target Port ID)"""
        return self.target_port_id

    def compose(self, other: Morphism) -> Optional[Morphism]:
        """
        Compose wires: self ∘ other
        other.target (port) == self.source (port)
        """
        if not isinstance(other, Wire):
            return None
        if self.source != other.target:
            return None
            
        # Composite wire? Or just logical composition?
        # A wire composed with a wire is a path.
        # For now, return a new virtual Wire connecting start to end.
        return Wire(
            source_port_id=other.source_port_id,
            target_port_id=self.target_port_id,
            source_port=other.source_port,
            target_port=self.target_port
        )

    @classmethod
    def identity(cls, obj_id: UUID) -> Morphism:
        """Identity wire (Port connected to itself?)"""
        return cls(source_port_id=obj_id, target_port_id=obj_id)

        """Enforce wiring rules when port objects are provided."""
        if self.source_port is None or self.target_port is None:
            return self  # Skip validation if ports not provided
        
        # Rule 1: Direction - output to input
        if self.source_port.direction != "output":
            raise ValueError("Source port must be OUTPUT")
        if self.target_port.direction != "input":
            raise ValueError("Target port must be INPUT")
        
        # Rule 2: Scope depth must match
        if self.source_port.scope_depth != self.target_port.scope_depth:
            raise ValueError(
                f"Scope mismatch: R={self.source_port.scope_depth} "
                f"→ R={self.target_port.scope_depth}. Use port promotion."
            )
        
        # Rule 3: Type compatibility
        if self.source_port.type_schema != self.target_port.type_schema:
            raise ValueError(
                f"Type mismatch: {self.source_port.type_schema} "
                f"→ {self.target_port.type_schema}"
            )
        
        return self

    @property
    def scope_depth(self) -> Optional[int]:
        """Scope depth of this wire (from ports)."""
        if self.source_port:
            return self.source_port.scope_depth
        return None
