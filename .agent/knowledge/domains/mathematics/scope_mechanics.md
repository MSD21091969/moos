# Scope Mechanics

## R-Values (Scope Depth)

Every node has `scope_depth` (R-value):

- R=0: Root level (UserObject owns)
- R=1: First nesting level
- R=n: Deeper nesting

## Rules

### 1. Same-Scope Wiring

Edges only connect nodes at same R:

```python
Node(scope_depth=0) ──► Node(scope_depth=0)  # ✓
Node(scope_depth=0) ──► Node(scope_depth=1)  # ✗ Error
```

### 2. Port Promotion

To cross scope, promote port:

```python
port_r2 = Port(scope_depth=2)
port_r1 = port_r2.promote()  # R=1
```

### 3. Flat Index

All nodes stored flat, UI derives nesting:

```python
nodes = [N(R=0), N(R=1), N(R=1), N(R=2)]
# UI groups visually by R
```

## GPU Benefits

Flat structure → Adjacency matrix:

```text
     N0  N1  N2  N3
N0 [ 0   1   1   0 ]
N1 [ 0   0   0   1 ]
N2 [ 0   0   0   1 ]
N3 [ 0   0   0   0 ]
```

Scope isolation = block-diagonal (zeros between R-levels).

## Related Files

- `models_v2/scope_enforcer.py`
- `models_v2/node.py`
- `models_v2/port.py`
