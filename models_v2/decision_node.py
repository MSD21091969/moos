"""Decision node - conditional branching in graphs.

Provides declarative routing based on runtime values.
"""
from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from models_v2.node import Node
from models_v2.edge_condition import EdgeCondition, CompositeCondition, AnyCondition

if TYPE_CHECKING:
    from models_v2.step_node import StepNode
    from models_v2.subgraph_node import SubgraphNode


# Type for any target node
TargetNode = Union["StepNode", "DecisionNode", "SubgraphNode"]


class DecisionBranch(BaseModel):
    """
    Single branch in a decision node.
    
    Example:
        branch = DecisionBranch(
            label="admin_path",
            condition=EdgeCondition(field_path="state.role", operator="eq", value="admin"),
            target_node_id=admin_step.id
        )
    """
    id: UUID = Field(default_factory=uuid4)
    label: str = Field(..., description="Human-readable branch name")
    condition: AnyCondition = Field(..., description="Condition that activates this branch")
    target_node_id: UUID = Field(..., description="ID of target node when condition is true")
    priority: int = Field(default=0, description="Lower = evaluated first (for overlapping conditions)")
    
    def evaluate(self, ctx: Any) -> bool:
        """Check if this branch should be taken."""
        return self.condition.evaluate(ctx)


class DecisionNode(BaseModel):
    """
    Conditional branching node.
    
    Evaluates branches in priority order, takes first matching branch.
    If no branch matches, raises error (or use catch-all branch with is_true).
    
    Example:
        decision = DecisionNode(
            node=Node(name="route_by_role", ...),
            branches=[
                DecisionBranch(label="admin", condition=when_equal("role", "admin"), target_node_id=...),
                DecisionBranch(label="user", condition=when_equal("role", "user"), target_node_id=...),
                DecisionBranch(label="default", condition=when_true("any"), target_node_id=...)
            ]
        )
    """
    
    # Topology
    node: Node
    
    # Branches (evaluated in priority order)
    branches: list[DecisionBranch] = Field(default_factory=list)
    
    # Fallback behavior
    fallback_node_id: UUID | None = Field(
        default=None, 
        description="Target if no branch matches (alternative to catch-all)"
    )
    
    class Config:
        arbitrary_types_allowed = True
    
    # ========================================================================
    # CONVENIENCE PROPERTIES
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        return self.node.id
    
    @property
    def name(self) -> str:
        return self.node.name
    
    @property
    def scope_depth(self) -> int:
        return self.node.scope_depth
    
    # ========================================================================
    # BRANCH MANAGEMENT
    # ========================================================================
    
    def add_branch(
        self,
        label: str,
        condition: AnyCondition,
        target_node_id: UUID,
        priority: int = 0
    ) -> DecisionBranch:
        """Add a branch to this decision node."""
        branch = DecisionBranch(
            label=label,
            condition=condition,
            target_node_id=target_node_id,
            priority=priority
        )
        self.branches.append(branch)
        # Sort by priority
        self.branches.sort(key=lambda b: b.priority)
        return branch
    
    def evaluate(self, ctx: Any) -> UUID | None:
        """
        Evaluate branches and return target node ID.
        
        Returns:
            UUID of target node, or fallback, or None if no match
        """
        # Branches already sorted by priority
        for branch in self.branches:
            if branch.evaluate(ctx):
                return branch.target_node_id
        
        # No match - use fallback
        return self.fallback_node_id
    
    def get_all_target_ids(self) -> set[UUID]:
        """Get all possible target node IDs (for graph building)."""
        targets = {b.target_node_id for b in self.branches}
        if self.fallback_node_id:
            targets.add(self.fallback_node_id)
        return targets
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_topology_dict(self) -> dict:
        """Export for Three.js visualization."""
        return {
            "id": str(self.node.id),
            "name": self.node.name,
            "type": "decision",
            "scope_depth": self.node.scope_depth,
            "visual_x": self.node.visual_x,
            "visual_y": self.node.visual_y,
            "branches": [
                {
                    "label": b.label,
                    "target_id": str(b.target_node_id),
                    "priority": b.priority
                }
                for b in self.branches
            ],
            "fallback_id": str(self.fallback_node_id) if self.fallback_node_id else None
        }
