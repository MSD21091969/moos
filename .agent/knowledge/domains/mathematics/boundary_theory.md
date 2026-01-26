# Boundary Derivation

## Problem

Given internal graph topology, derive the composite I/O interface.

## Tri-Method Validation

Three independent methods MUST agree:

### 1. Operad Algebra

```
Boundary = All Inputs - Wired Inputs
```

Unsatisfied "needs" of internal nodes.

### 2. Set Theory (with promotion)

```
Inputs  = ∪(node.inputs) - internal_wires.targets
Outputs = ∪(node.outputs) - internal_wires.sources
```

Includes promoted ports (R+1 → R).

### 3. Data Flow Analysis

- **Reaching Definitions**: Which outputs reach boundary?
- **Live Variable Analysis**: Which inputs are needed from outside?

## Implementation

```python
from models_v2 import BoundaryDerivation

derivation = BoundaryDerivation(
    internal_definitions=[def1, def2],
    internal_wires=[wire1, wire2]
)

inputs, outputs = derivation.derive_boundary()
```

## Related Files

- `models_v2/composite_boundary.py`
- `models_v2/definition.py` → `CompositeDefinition`
