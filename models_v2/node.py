"""Node model - graph position with definition reference.

Nodes are positions in the graph topology. They reference Definitions
for execution logic. No recursion - scope is just an attribute.
"""
from __future__ import annotations
from uuid import UUID, uuid4
from typing import Optional
from pydantic import Field

from .categorical_base import CategoryObject
from .scope_enforcer import ScopeEnforcer


class Node(CategoryObject, ScopeEnforcer):
    """
    Graph node - topology position with definition reference.
    
    A Node is a position in the graph that:
    - Has identity (UUID from CategoryObject)
    - Has scope depth (R-value from ScopeEnforcer)
    - References a Definition (what happens here)
    - Has visual hints (for UI layout)
    
    Nodes do NOT contain other nodes. Scope depth is just an attribute
    used for validation at edge creation time.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    
    # What this node does (optional - can be placeholder)
    definition_id: Optional[UUID] = None
    
    # Which graph owns this node
    graph_id: UUID
    
    # Visual layout hints (for UI)
    visual_x: float = 0.0
    visual_y: float = 0.0
    
    # Optional metadata
    description: str = ""
