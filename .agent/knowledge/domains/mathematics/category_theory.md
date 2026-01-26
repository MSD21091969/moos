# Category Theory in models_v2

## Core Mappings

| Math Concept     | models_v2 Object    |
| ---------------- | ------------------- |
| Object           | Node                |
| Morphism         | Edge                |
| Functor          | Definition          |
| Quotient Functor | CompositeDefinition |

## Category Laws

### Identity

Every node has identity morphism (self-loop, not stored).

### Composition

```
f: A → B, g: B → C  ⟹  g∘f: A → C
```

Edge composition preserves wire specs.

### Associativity

```
h∘(g∘f) = (h∘g)∘f
```

Verified by `verify_associativity()`.

## Symmetric Monoidal Category

Collider graphs form SMC:

- **Tensor product** (⊗): Parallel composition
- **Composition** (∘): Sequential composition

```
       ┌─────┐
A ──►──┤  f  ├──►── B
       └─────┘       ⊗ (parallel)
       ┌─────┐
C ──►──┤  g  ├──►── D
       └─────┘
```

## Related Files

- `models_v2/categorical_base.py`
- `models_v2/graph.py`
