# Factory Knowledge Index

## Purpose

AI-focused reference for the Factory codebase. Short, DRY, actionable.

## Folder Structure

```
knowledge/
├── index.md           # You are here
├── mathematics/       # Math Core (5 files)
│   ├── category_theory.md
│   ├── scope_mechanics.md
│   ├── boundary_theory.md
│   ├── tensor_graphs.md
│   └── geometric_embeddings.md
├── research/          # (Empty - archived to docs/)
├── development/       # (Empty - archived to docs/)
└── skills/            # (Empty - future agent skills)
```

## Quick Reference

| Topic             | File                                  | Key Concept                |
| ----------------- | ------------------------------------- | -------------------------- |
| Graph composition | `mathematics/category_theory.md`      | `Link.compose()`           |
| Scope isolation   | `mathematics/scope_mechanics.md`      | `Port.promote()`, R-values |
| Composite I/O     | `mathematics/boundary_theory.md`      | Tri-method derivation      |
| Matrix operations | `mathematics/tensor_graphs.md`        | `GraphTensor`              |
| Similarity search | `mathematics/geometric_embeddings.md` | `ScopeAwareGNN`            |

## Source Code

- Models: `models/` (Container, Link, Definition, Wire)
- Tests: `tests/validate_*.py` (65 tests, 100% pass)

## Human Docs

For narrative explanations, see `docs/` (maintained by user).
