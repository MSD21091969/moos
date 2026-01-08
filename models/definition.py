"""Recursive Definition model for the Factory.

A Definition can contain child definitions, enabling composite structures.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class IOSchema(BaseModel):
    """Input/Output schema for a definition."""
    model_config = ConfigDict(frozen=True)
    
    name: str
    type_hint: str = "Any"
    description: str = ""
    required: bool = True
    default: Any = None


class DefinitionSpec(BaseModel):
    """Specification for how to run a definition."""
    model_config = ConfigDict(frozen=True)
    
    runtime: str = "fatruntime"  # Which runtime to use
    environment: str = "default"  # Environment type
    timeout_seconds: int = 30
    retries: int = 0


class Definition(BaseModel):
    """
    Recursive Definition model.
    
    Definitions can contain child definitions, creating a hierarchy.
    When a container's dependencies change, composite definitions emerge.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    name: str
    version: int = 1
    description: str = ""
    
    # Ownership
    owner_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # I/O Contract
    inputs: list[IOSchema] = Field(default_factory=list)
    outputs: list[IOSchema] = Field(default_factory=list)
    
    # Execution
    spec: DefinitionSpec = Field(default_factory=DefinitionSpec)
    code: str = ""  # Python code or reference
    
    # Recursion: Child definitions
    children: list["Definition"] = Field(default_factory=list)
    parent_id: UUID | None = None
    
    # State
    is_atomic: bool = True  # False if has children (composite)
    is_validated: bool = False
    validation_score: float = 0.0
    
    def add_child(self, child: "Definition") -> None:
        """Add a child definition, making this composite."""
        child.parent_id = self.id
        self.children.append(child)
        self.is_atomic = False
        self.updated_at = datetime.utcnow()
    
    def get_all_descendants(self) -> list["Definition"]:
        """Get all descendants recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def compute_composite_io(self) -> tuple[list[IOSchema], list[IOSchema]]:
        """
        Compute the composite I/O from all children.
        
        Inputs: Union of all children's unconnected inputs
        Outputs: Union of all children's exposed outputs
        """
        if self.is_atomic:
            return self.inputs, self.outputs
        
        # Aggregate from children
        all_inputs = []
        all_outputs = []
        for child in self.children:
            c_in, c_out = child.compute_composite_io()
            all_inputs.extend(c_in)
            all_outputs.extend(c_out)
        
        return all_inputs, all_outputs
    
    def to_collider_object(self) -> dict:
        """Export as Collider-compatible object."""
        return {
            "type": "Definition",
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "is_atomic": self.is_atomic,
            "children_count": len(self.children),
            "inputs": [i.model_dump() for i in self.inputs],
            "outputs": [o.model_dump() for o in self.outputs],
        }


# Enable forward refs
Definition.model_rebuild()
