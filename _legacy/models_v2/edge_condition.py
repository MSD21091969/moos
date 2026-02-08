"""Edge conditions - serializable predicates for conditional edges.

Provides picklable condition objects that can be:
- Stored in database/JSON
- Evaluated at runtime
- Composed with AND/OR logic
"""
from __future__ import annotations
from typing import Any, Callable, Literal, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# Supported comparison operators
OperatorType = Literal[
    "eq",       # ==
    "ne",       # !=
    "gt",       # >
    "gte",      # >=
    "lt",       # <
    "lte",      # <=
    "contains", # in (for strings/lists)
    "matches",  # regex match
    "is_none",  # is None
    "is_not_none",  # is not None
    "is_true",  # bool(value) == True
    "is_false", # bool(value) == False
]


def _get_nested_attr(obj: Any, path: str) -> Any:
    """
    Get nested attribute from object using dot notation.
    
    Example: _get_nested_attr(ctx, "state.user.id")
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AttributeError(f"Cannot resolve path '{path}' at '{part}'")
    return current


# Operator implementations
OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "contains": lambda a, b: b in a,
    "matches": lambda a, b: bool(__import__("re").match(b, str(a))),
    "is_none": lambda a, _: a is None,
    "is_not_none": lambda a, _: a is not None,
    "is_true": lambda a, _: bool(a) is True,
    "is_false": lambda a, _: bool(a) is False,
}


class EdgeCondition(BaseModel):
    """
    Serializable edge condition using field path + operator + value.
    
    Example:
        condition = EdgeCondition(
            field_path="state.user.role",
            operator="eq",
            value="admin"
        )
        
        # Evaluates: ctx.state.user.role == "admin"
        result = condition.evaluate(ctx)
    """
    id: UUID = Field(default_factory=uuid4)
    field_path: str = Field(..., description="Dot-notation path to value, e.g. 'state.count'")
    operator: OperatorType
    value: Any = Field(default=None, description="Comparison value (unused for is_none/is_true)")
    
    def evaluate(self, ctx: Any) -> bool:
        """
        Evaluate condition against execution context.
        
        Args:
            ctx: StepContext from pydantic-graph or similar object
            
        Returns:
            True if condition passes, False otherwise
        """
        try:
            actual = _get_nested_attr(ctx, self.field_path)
            op_fn = OPERATORS[self.operator]
            return op_fn(actual, self.value)
        except (AttributeError, KeyError, TypeError):
            # Path resolution failed - condition fails
            return False
    
    def __and__(self, other: EdgeCondition) -> CompositeCondition:
        """Combine with AND: condition1 & condition2"""
        return CompositeCondition(
            logic="and",
            conditions=[self, other]
        )
    
    def __or__(self, other: EdgeCondition) -> CompositeCondition:
        """Combine with OR: condition1 | condition2"""
        return CompositeCondition(
            logic="or",
            conditions=[self, other]
        )


class CompositeCondition(BaseModel):
    """
    Logical combination of multiple conditions.
    
    Example:
        # (role == admin) AND (active == True)
        combined = EdgeCondition(field_path="role", operator="eq", value="admin") & \
                   EdgeCondition(field_path="active", operator="is_true")
    """
    id: UUID = Field(default_factory=uuid4)
    logic: Literal["and", "or"]
    conditions: list[Union[EdgeCondition, "CompositeCondition"]]
    
    def evaluate(self, ctx: Any) -> bool:
        """Evaluate all conditions with specified logic."""
        if self.logic == "and":
            return all(c.evaluate(ctx) for c in self.conditions)
        else:  # or
            return any(c.evaluate(ctx) for c in self.conditions)
    
    def __and__(self, other: Union[EdgeCondition, CompositeCondition]) -> CompositeCondition:
        """Chain with AND."""
        return CompositeCondition(
            logic="and",
            conditions=[self, other]
        )
    
    def __or__(self, other: Union[EdgeCondition, CompositeCondition]) -> CompositeCondition:
        """Chain with OR."""
        return CompositeCondition(
            logic="or", 
            conditions=[self, other]
        )


# Type alias for any condition
AnyCondition = Union[EdgeCondition, CompositeCondition]


# Convenience factory functions
def when_equal(field_path: str, value: Any) -> EdgeCondition:
    """Shorthand: field == value"""
    return EdgeCondition(field_path=field_path, operator="eq", value=value)


def when_greater(field_path: str, value: Any) -> EdgeCondition:
    """Shorthand: field > value"""
    return EdgeCondition(field_path=field_path, operator="gt", value=value)


def when_less(field_path: str, value: Any) -> EdgeCondition:
    """Shorthand: field < value"""
    return EdgeCondition(field_path=field_path, operator="lt", value=value)


def when_true(field_path: str) -> EdgeCondition:
    """Shorthand: bool(field) is True"""
    return EdgeCondition(field_path=field_path, operator="is_true")


def when_false(field_path: str) -> EdgeCondition:
    """Shorthand: bool(field) is False"""
    return EdgeCondition(field_path=field_path, operator="is_false")


def when_none(field_path: str) -> EdgeCondition:
    """Shorthand: field is None"""
    return EdgeCondition(field_path=field_path, operator="is_none")


def when_contains(field_path: str, value: Any) -> EdgeCondition:
    """Shorthand: value in field"""
    return EdgeCondition(field_path=field_path, operator="contains", value=value)
