"""Port model - typed I/O interface with scope depth.

Ports define the input/output contract for Definitions.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from typing import Literal, Any
from pydantic import BaseModel, Field


class PortDirection(str):
    INPUT = "input"
    OUTPUT = "output"


class Port(BaseModel):
    """
    Type-safe port with scope depth for boundary enforcement.
    
    Ports are the I/O interface of Definitions. They carry:
    - Direction (input/output)
    - Type schema (JSON schema for validation)
    - Scope depth (R-value for promotion rules)
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    direction: Literal["input", "output"]
    type_schema: dict[str, Any] = Field(default_factory=dict)
    scope_depth: int = Field(ge=0, default=0)
    is_optional: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Port):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def promote(self) -> Port:
        """
        Functorial lifting: Port@R+1 → Port@R
        
        Preserves type_schema (functor law).
        Raises if already at root scope (R=0).
        """
        if self.scope_depth == 0:
            raise ValueError("Cannot promote root-level port (R=0)")

        return Port(
            id=uuid4(),  # New identity at parent scope
            name=f"promoted_{self.name}",
            direction=self.direction,
            type_schema=self.type_schema,  # PRESERVED
            scope_depth=self.scope_depth - 1,
            is_optional=self.is_optional
        )

    def demote(self) -> Port:
        """Inverse: push port into child scope."""
        return Port(
            id=uuid4(),
            name=f"nested_{self.name}",
            direction=self.direction,
            type_schema=self.type_schema,
            scope_depth=self.scope_depth + 1,
            is_optional=self.is_optional
        )

    def is_compatible_with(self, other: Port) -> bool:
        """
        Check if two ports can be wired together.
        
        Requirements:
        - Same scope depth
        - Opposite directions
        - Compatible type schemas
        """
        if self.scope_depth != other.scope_depth:
            return False
        if self.direction == other.direction:
            return False
        # Type compatibility: same schema (simplified)
        return self.type_schema == other.type_schema
