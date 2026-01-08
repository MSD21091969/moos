"""UserObject model - stores all user properties including CompositeDefinition.

UserObject is the property bag for a user, containing:
- R=1 containers (root level)
- Profile
- Container and Definition registries
- Emerged CompositeDefinition (from Factory analysis)
"""
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from models.definition import Definition
from models.container import Container


class UserProfile(BaseModel):
    """User profile information."""
    display_name: str = ""
    email: str = ""
    avatar_url: str = ""
    preferences: dict = Field(default_factory=dict)


class UserObject(BaseModel):
    """
    UserObject - the complete user property bag.
    
    Contains:
    - Core identity
    - R=1 containers (root level, depth=1)
    - Profile
    - Registries for containers and definitions
    - CompositeDefinition (emerged, ready to ignite or analyze)
    """
    model_config = ConfigDict(validate_assignment=True)
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    auth_id: str = ""  # External auth provider ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Profile
    profile: UserProfile = Field(default_factory=UserProfile)
    
    # R=1 Containers (root level, user's top-level containers)
    containers: list[Container] = Field(default_factory=list)
    
    # Registries
    container_registry: dict[UUID, Container] = Field(default_factory=dict)
    definition_registry: dict[UUID, Definition] = Field(default_factory=dict)
    
    # Emerged CompositeDefinition (from Factory analysis)
    # This is the nested model definition ready to be ignited
    composite_definition: Definition | None = None
    composite_version: int = 0
    composite_updated_at: datetime | None = None
    
    # Cache (optional)
    cache: dict = Field(default_factory=dict)
    
    def add_container(self, container: Container) -> None:
        """Add a root container (R=1)."""
        container.owner_id = self.id
        container.depth = 1
        self.containers.append(container)
        self.container_registry[container.id] = container
        
        # Register any definition
        if container.definition:
            self.definition_registry[container.definition.id] = container.definition
    
    def add_definition(self, definition: Definition) -> None:
        """Add a definition to the registry."""
        definition.owner_id = self.id
        self.definition_registry[definition.id] = definition
    
    def compute_composite(self) -> Definition:
        """
        Compute the user's composite definition from all containers.
        
        This emerges from the dependency graph of all user's containers.
        """
        all_defs = []
        
        for container in self.containers:
            composite = container.compute_composite_definition()
            if composite:
                all_defs.append(composite)
        
        # Create user-level composite
        self.composite_definition = Definition(
            name=f"user_{self.id}_composite",
            description=f"Composite definition for user",
            is_atomic=False,
            children=all_defs,
            owner_id=self.id,
        )
        self.composite_version += 1
        self.composite_updated_at = datetime.utcnow()
        
        return self.composite_definition
    
    def get_container_by_id(self, container_id: UUID) -> Container | None:
        """Get container from registry."""
        return self.container_registry.get(container_id)
    
    def get_definition_by_id(self, definition_id: UUID) -> Definition | None:
        """Get definition from registry."""
        return self.definition_registry.get(definition_id)
    
    def to_collider_object(self) -> dict:
        """Export as Collider-compatible object."""
        return {
            "type": "UserObject",
            "id": str(self.id),
            "container_count": len(self.containers),
            "definition_count": len(self.definition_registry),
            "composite_version": self.composite_version,
            "has_composite": self.composite_definition is not None,
        }


# Enable forward refs
UserObject.model_rebuild()
