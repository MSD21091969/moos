# Math Testing Rules

## Core Rule

**100% Law Compliance**: All category theory laws must pass before merge.

## Test Suites

| Suite               | File                                    | Tests |
| ------------------- | --------------------------------------- | ----- |
| Category Laws       | `tests/validate_category_laws.py`       | 12    |
| Scope Isolation     | `tests/validate_scope_isolation.py`     | 15    |
| Boundary Derivation | `tests/validate_boundary_derivation.py` | 9     |
| Tensor Operations   | `tests/validate_graph_tensors.py`       | 9     |
| Embeddings          | `tests/validate_embeddings.py`          | 10    |
| Integration         | `tests/validate_integration.py`         | 10    |

## Run All Tests

```powershell
python tests/validate_category_laws.py
python tests/validate_scope_isolation.py
python tests/validate_boundary_derivation.py
python tests/validate_graph_tensors.py
python tests/validate_embeddings.py
python tests/validate_integration.py
```

## Property-Based Testing

When adding new math operations, consider Hypothesis-style property tests:

- **Associativity**: `(a ∘ b) ∘ c == a ∘ (b ∘ c)`
- **Identity**: `a ∘ id == a`
- **Scope Preservation**: `promoted.scope_depth == original.scope_depth - 1`

## Failure Policy

If any category law test fails, the math core is broken. Do not proceed until fixed.
