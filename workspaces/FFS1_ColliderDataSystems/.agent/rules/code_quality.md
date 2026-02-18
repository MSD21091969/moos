---
description: Enforced coding standards for reliability and maintainability across Python (FFS2) and TypeScript (FFS3)
activation: always
---

# Code Quality & Best Practices

> Enforced coding standards for reliability and maintainability.

---

## Polyglot Standards

### Documentation

- **Requirement**: All public API endpoints (FastAPI) and exported components (React) must have documentation.
- **Format**:
  - Python: Google-style Docstrings.
  - TypeScript: TSDoc (`/** ... */`).
- **Diagrams**: MermaidJS diagrams in Markdown for complex flows.

### Version Control

- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`).
- **Scope**: One logical change per commit.

---

## Python (FFS2 Backend)

### Liniting & Formatting

- **Linter**: `Ruff` (Fast, replacing Flake8/Isort).
- **Formatter**: `Black` (Strict).
- **Type Checking**: `Mypy` (Strict mode enabled).

### Testing

- **Framework**: `Pytest`.
- **Async**: `pytest-asyncio`.
- **Coverage**: Minimum 80% coverage on core logic modules.

---

## TypeScript / Javascript (FFS3 + FFS2 Extension)

### Linting & Formatting

- **Linter**: `ESLint`.
- **Formatter**: `Prettier`.
- **Strict Mode**: `tsconfig.json` must have `"strict": true`.

### Testing

- **Unit**: `Vitest` (Faster than Jest, native ESM).
- **Integration**: `Playwright` (for E2E browser testing).

### React Patterns

- **Hooks**: Custom hooks for logic; Components for view only.
- **Props**: Defined via Interfaces (not Types), reducing intersection complexity.
- **No `any`**: Explicit unknown or generic constraints.

---

## Project Structure (Directories)

- **`src/`**: Source code only.
- **`tests/`**: Mirror source structure.
- **`docs/`**: Architecture decision records (ADRs).
- **`.agent/`**: AI Context (Rules, Knowledge, Instructions).
