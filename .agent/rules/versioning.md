# Versioning Strategy

> Archive legacy, start fresh with clean imports

---

## Proposed Structure

```
D:\FFS0_Factory\
├── models/              ← NEW (clean)
├── sdk/                 ← NEW (clean)
├── _legacy/
│   ├── models_v2/       ← archived from ./models_v2/
│   └── parts/           ← archived from ./parts/
└── workspaces/          ← unchanged
```

---

## Migration Steps

1. [x] Create `_legacy/` folder
2. [x] Move `models_v2/` → `_legacy/models_v2/`
3. [x] Move `parts/` → `_legacy/parts/`
4. [x] Create new `models/` with clean structure
5. [x] Create new `sdk/` with clean structure
6. [ ] Update imports in workspaces as needed

---

## Version Naming

| Version     | Location             | Status             |
| ----------- | -------------------- | ------------------ |
| v2 (legacy) | `_legacy/models_v2/` | Archived reference |
| v3 (new)    | `models/`            | Active development |

---

## Git Strategy

- Tag current state: `git tag v2-legacy`
- Commit archive move
- Begin v3 development on clean slate
