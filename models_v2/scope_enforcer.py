"""Scope enforcement mixin for hierarchical models.

Provides R-value (scope depth) management and validation.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
import warnings

from .config import MAX_RECURSION_DEPTH, RECURSION_DEPTH_WARNING


class ScopeEnforcer(BaseModel):
    """
    Mixin for models that enforce scope depth constraints.
    
    R-values:
    - R=0: UserObject (root)
    - R=1: Top-level nodes (graph holders)
    - R=2+: Nested nodes
    """
    scope_depth: int = Field(ge=0, default=0)

    @field_validator('scope_depth')
    @classmethod
    def validate_scope_depth(cls, v: int) -> int:
        """Enforce depth limits and emit warnings."""
        if v > MAX_RECURSION_DEPTH:
            raise ValueError(
                f"Scope depth {v} exceeds maximum {MAX_RECURSION_DEPTH}"
            )
        if v >= RECURSION_DEPTH_WARNING:
            warnings.warn(
                f"Deep nesting detected: R={v}. Consider flattening.",
                stacklevel=2
            )
        return v

    def validate_child_depth(self, child_depth: int) -> None:
        """Ensure child is exactly one level deeper."""
        if child_depth != self.scope_depth + 1:
            raise ValueError(
                f"Child must be at R={self.scope_depth + 1}, got R={child_depth}"
            )

    def validate_sibling_depth(self, sibling_depth: int) -> None:
        """Ensure sibling is at same level."""
        if sibling_depth != self.scope_depth:
            raise ValueError(
                f"Sibling must be at R={self.scope_depth}, got R={sibling_depth}"
            )

    def increment_depth(self, delta: int = 1) -> int:
        """Return new depth for nested element."""
        return self.scope_depth + delta

    def decrement_depth(self, delta: int = 1) -> int:
        """Return new depth for promoted element."""
        new_depth = self.scope_depth - delta
        if new_depth < 0:
            raise ValueError("Cannot decrement below R=0")
        return new_depth
