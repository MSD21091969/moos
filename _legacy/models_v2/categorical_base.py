"""Category theory foundation for Collider models v2.

Provides base classes enforcing:
- Category laws (associativity, identity, composition closure)
- Functor properties (F(g∘f) = F(g)∘F(f), F(id) = id)
- Morphism composition with type safety
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from typing import Protocol, TypeVar, Generic, Optional, Any
from pydantic import BaseModel, model_validator
from typing_extensions import Self


# ============================================================================
# CATEGORY OBJECTS
# ============================================================================

class CategoryObject(BaseModel):
    """
    Base class for objects in category C_Collider.
    
    Objects have identity (UUID) and equality based on that identity.
    """
    id: UUID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CategoryObject):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ============================================================================
# MORPHISMS
# ============================================================================

class Morphism(BaseModel, ABC):
    """
    Base class for morphisms in C_Collider.

    Morphisms are arrows between objects satisfying:
    1. Composition: f: A→B, g: B→C implies g∘f: A→C exists
    2. Associativity: (h∘g)∘f = h∘(g∘f)
    3. Identity: ∃ id_A: A→A such that f∘id_A = f = id_B∘f
    """
    source: UUID  # Domain object
    target: UUID  # Codomain object

    @abstractmethod
    def compose(self, other: Morphism) -> Optional[Morphism]:
        """
        Compose morphisms: self ∘ other
        
        Requires: self.source == other.target
        Returns: Morphism(source=other.source, target=self.target)
        """
        pass

    @classmethod
    @abstractmethod
    def identity(cls, obj_id: UUID) -> Morphism:
        """Create identity morphism id_A: A → A"""
        pass

    def is_identity(self) -> bool:
        """Check if this is an identity morphism"""
        return self.source == self.target


# ============================================================================
# FUNCTORS
# ============================================================================

T_Source = TypeVar('T_Source', bound=CategoryObject)
T_Target = TypeVar('T_Target', bound=CategoryObject)


class Functor(Protocol, Generic[T_Source, T_Target]):
    """
    Functor F: C → D between categories.

    Laws:
    1. Identity preservation: F(id_A) = id_F(A)
    2. Composition preservation: F(g∘f) = F(g)∘F(f)
    """

    def apply_object(self, obj: T_Source) -> T_Target:
        """Map object from source to target category"""
        ...

    def apply_morphism(self, morphism: Morphism) -> Morphism:
        """Map morphism from source to target category"""
        ...

    def preserves_identity(self, obj: T_Source) -> bool:
        """Verify F(id_A) = id_F(A)"""
        ...

    def preserves_composition(self, f: Morphism, g: Morphism) -> bool:
        """Verify F(g∘f) = F(g)∘F(f)"""
        ...


# ============================================================================
# COMPOSITION UTILITIES
# ============================================================================

def compose_morphisms(morphisms: list[Morphism]) -> Optional[Morphism]:
    """Compose chain of morphisms: h∘g∘f"""
    if not morphisms:
        return None
    if len(morphisms) == 1:
        return morphisms[0]

    result = morphisms[0]
    for morphism in morphisms[1:]:
        composed = result.compose(morphism)
        if composed is None:
            return None
        result = composed
    return result


def verify_associativity(f: Morphism, g: Morphism, h: Morphism) -> bool:
    """Verify (h∘g)∘f = h∘(g∘f)"""
    left_composed = h.compose(g)
    if left_composed is None:
        return False
    left_result = left_composed.compose(f)

    right_composed = g.compose(f)
    if right_composed is None:
        return False
    right_result = h.compose(right_composed)

    return left_result == right_result


def verify_identity_laws(morphism: Morphism) -> bool:
    """Verify f∘id_source = f = id_target∘f"""
    id_source = morphism.identity(morphism.source)
    id_target = morphism.identity(morphism.target)

    left_compose = morphism.compose(id_source)
    right_compose = id_target.compose(morphism)

    return (left_compose == morphism) and (right_compose == morphism)
