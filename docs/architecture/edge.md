# Edge Architecture (models_v2)

> Replaces `Link` from v1

## Core Concept

Edge is a **morphism** between nodes. Carries wire specifications for port-level connections.

## Properties

| Property         | Type           | Purpose               |
| ---------------- | -------------- | --------------------- |
| `id`             | UUID           | Unique identifier     |
| `source_node_id` | UUID           | Origin node           |
| `target_node_id` | UUID           | Destination node      |
| `wire_specs`     | list[WireSpec] | Port-to-port mappings |

## WireSpec

Maps specific ports between nodes:

```python
WireSpec(
    source_port_id=uuid1,
    target_port_id=uuid2
)
```

## Scope Validation

Edges can only connect nodes at the **same scope depth**:

```python
# Valid: same scope
Node(scope_depth=0) ──Edge──► Node(scope_depth=0)

# Invalid: scope mismatch
Node(scope_depth=0) ──Edge──► Node(scope_depth=1)  # Error!
```

Use **port promotion** to cross scopes.

## Edge Conditions

Serializable conditions for conditional routing:

```python
from models_v2 import EdgeCondition, when_equal

cond = when_equal("state.role", "admin")
# Evaluates: ctx.state.role == "admin"
```

Operators: `eq`, `ne`, `gt`, `lt`, `contains`, `matches`, `is_true`, `is_none`

## Related Files

- `models_v2/edge.py`
- `models_v2/edge_condition.py`
- `models_v2/wire.py`
