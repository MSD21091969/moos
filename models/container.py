"""Recursive Container model for the Factory.

A Container holds a Definition and a subgraph of child Containers.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from models.definition import Definition


class Position(BaseModel):
    """Position in the UX canvas."""
    x: float = 0.0
    y: float = 0.0


class ContainerState(BaseModel):
    """Runtime state of a container."""
    status: str = "idle"  # idle, running, success, failed
    last_run: datetime | None = None
    error: str | None = None


class Container(BaseModel):
    """
    Recursive Container model.
    
    Containers hold definitions and form subgraphs.
    When a container is defined, its dependents get redefined.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    
    # Ownership
    owner_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Definition binding
    definition: Definition | None = None
    definition_id: UUID | None = None
    
    # Recursion: Subgraph
    subgraph: list["Container"] = Field(default_factory=list)
    parent_id: UUID | None = None
    
    # Graph position (for predecessor/successor)
    predecessors: list[UUID] = Field(default_factory=list)
    successors: list[UUID] = Field(default_factory=list)
    
    # UX
    position: Position = Field(default_factory=Position)
    state: ContainerState = Field(default_factory=ContainerState)
    
    # Depth (R=1 is root)
    depth: int = 1
    
    def add_to_subgraph(self, child: "Container") -> None:
        """Add a container to the subgraph."""
        child.parent_id = self.id
        child.depth = self.depth + 1
        self.subgraph.append(child)
        self.updated_at = datetime.utcnow()
    
    def get_all_descendants(self) -> list["Container"]:
        """Get all containers in subgraph recursively."""
        descendants = []
        for child in self.subgraph:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def compute_composite_definition(self) -> Definition | None:
        """
        Compute composite definition from subgraph.
        
        When dependencies change, this recomputes.
        """
        if not self.subgraph:
            return self.definition
        
        # Collect all definitions from subgraph
        child_defs = []
        for child in self.subgraph:
            if child.definition:
                child_defs.append(child.definition)
            # Recurse
            child_composite = child.compute_composite_definition()
            if child_composite:
                child_defs.append(child_composite)
        
        if not child_defs:
            return self.definition
        
        # Create composite
        composite = Definition(
            name=f"{self.name}_composite",
            description=f"Composite definition for {self.name}",
            is_atomic=False,
            children=child_defs,
        )
        
        return composite
    
    def propagate_redefinition(self, containers: dict[UUID, "Container"]) -> None:
        """
        When this container is redefined, propagate to successors.
        
        Successor-predecessor logic: downstream dependents get redefined.
        """
        for succ_id in self.successors:
            if succ_id in containers:
                succ = containers[succ_id]
                # Trigger recomputation
                succ.compute_composite_definition()
                # Recurse
                succ.propagate_redefinition(containers)
    
    def to_collider_object(self) -> dict:
        """Export as Collider-compatible object."""
        return {
            "type": "Container",
            "id": str(self.id),
            "name": self.name,
            "depth": self.depth,
            "definition_id": str(self.definition_id) if self.definition_id else None,
            "subgraph_count": len(self.subgraph),
            "predecessors": [str(p) for p in self.predecessors],
            "successors": [str(s) for s in self.successors],
        }


# Enable forward refs
Container.model_rebuild()
