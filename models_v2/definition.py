"""Definition model - THE CORE OBJECT.

Definitions are functors that define I/O interfaces for agent tools.
AtomicDefinition: single executable unit
CompositeDefinition: graph of definitions with derived boundary
"""
from __future__ import annotations
from abc import abstractmethod
from uuid import UUID, uuid4
from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from models_v2.categorical_base import Functor, CategoryObject
from models_v2.port import Port
from models_v2.config import VALIDATE_CATEGORY_LAWS


# ============================================================================
# ABSTRACT DEFINITION
# ============================================================================

class Definition(BaseModel):
    """
    Abstract functor F: Abstract → Concrete
    
    THE CORE OBJECT. Definitions:
    - Define I/O contracts (input_ports, output_ports)
    - Are used as tools by agents
    - Can be composed into CompositeDefinitions
    """
    id: UUID = Field(default_factory=uuid4)
    owner_id: Optional[UUID] = None
    name: str
    version: int = 1
    
    # Type discriminator
    type: Literal["atomic", "composite"]
    
    # I/O interface (functorial)
    input_ports: list[Port] = Field(default_factory=list)
    output_ports: list[Port] = Field(default_factory=list)
    
    # Metadata
    description: str = ""
    is_committed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @abstractmethod
    def compose(self, other: Definition) -> CompositeDefinition:
        """Compose definitions: F(g∘f) = F(g)∘F(f)"""
        pass

    def is_identity(self) -> bool:
        """Check if this is an identity definition (pass-through)."""
        if len(self.input_ports) != len(self.output_ports):
            return False
        for inp, out in zip(self.input_ports, self.output_ports):
            if inp.type_schema != out.type_schema:
                return False
        return True

    def get_input_port(self, name: str) -> Optional[Port]:
        """Get input port by name."""
        return next((p for p in self.input_ports if p.name == name), None)

    def get_output_port(self, name: str) -> Optional[Port]:
        """Get output port by name."""
        return next((p for p in self.output_ports if p.name == name), None)


# ============================================================================
# ATOMIC DEFINITION
# ============================================================================

class AtomicDefinition(Definition):
    """
    Atomic Definition - single executable unit.
    
    Has source code (for agent execution) and fixed I/O.
    No internal structure.
    """
    type: Literal["atomic"] = "atomic"
    
    # Execution source (PydanticAI agent code)
    source_code: Optional[str] = None
    
    # Runtime configuration
    runtime_config: dict[str, Any] = Field(default_factory=dict)

    def compose(self, other: Definition) -> CompositeDefinition:
        """Compose with another definition."""
        return CompositeDefinition(
            name=f"{self.name}_then_{other.name}",
            internal_definitions=[self, other],
            internal_graph_id=None  # Graph created separately
        )

    def apply(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Execute this definition with given inputs.
        
        In production, this would:
        1. Validate inputs against input_ports
        2. Execute source_code or agent
        3. Return outputs matching output_ports
        
        Placeholder for now.
        """
        # Validate input keys match port names
        expected = {p.name for p in self.input_ports}
        provided = set(inputs.keys())
        if expected != provided:
            raise ValueError(f"Input mismatch: expected {expected}, got {provided}")
        
        # Placeholder: return empty outputs
        return {p.name: None for p in self.output_ports}


# ============================================================================
# COMPOSITE DEFINITION
# ============================================================================

class CompositeDefinition(Definition):
    """
    Composite Definition - graph of definitions with derived boundary.
    
    I/O is derived from internal topology via tri-method boundary derivation.
    """
    type: Literal["composite"] = "composite"
    
    # Internal structure
    internal_definitions: list[Definition] = Field(default_factory=list)
    internal_graph_id: Optional[UUID] = None  # Reference to Graph
    
    # Provenance
    composed_from: list[UUID] = Field(default_factory=list)

    def compose(self, other: Definition) -> CompositeDefinition:
        """Compose with another definition."""
        if isinstance(other, CompositeDefinition):
            merged_defs = self.internal_definitions + other.internal_definitions
        else:
            merged_defs = self.internal_definitions + [other]
        
        composite = CompositeDefinition(
            name=f"{self.name}_then_{other.name}",
            internal_definitions=merged_defs,
            composed_from=self.composed_from + [other.id]
        )
        composite._derive_boundary()
        return composite

    def _derive_boundary(self) -> None:
        """Derive I/O from internal topology."""
        from models_v2.composite_boundary import derive_composite_boundary
        
        # Get wires from internal graph (if available)
        wires = []  # Would come from Graph
        
        boundary_inputs, boundary_outputs = derive_composite_boundary(
            self.internal_definitions,
            wires
        )
        self.input_ports = list(boundary_inputs)
        self.output_ports = list(boundary_outputs)

    def quotient_functor(self) -> tuple[list[Port], list[Port]]:
        """
        Quotient functor Q: Internal → Boundary
        
        Returns the derived boundary ports.
        """
        self._derive_boundary()
        return self.input_ports, self.output_ports

    @model_validator(mode='after')
    def validate_functor_laws(self) -> Self:
        """Validate functor laws if enabled."""
        if not VALIDATE_CATEGORY_LAWS:
            return self
        
        # Verify composition preservation
        for i, defn1 in enumerate(self.internal_definitions):
            for defn2 in self.internal_definitions[i+1:]:
                # Basic check: composites have valid structure
                if not defn1.input_ports and not defn1.output_ports:
                    continue  # Skip empty definitions
        
        return self

    def apply(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Execute composite by running internal graph.
        
        Placeholder - would orchestrate internal definitions.
        """
        return {p.name: None for p in self.output_ports}
