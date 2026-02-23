# Versioning Strategy

> Archive legacy, start fresh with clean imports

---

## Proposed Structure

```text
D:\FFS0_Factory\
├── models/              ← NEW (clean v3)
├── sdk/                 ← NEW (clean)
├── _legacy/
│   ├── models_v2/       ← archived from ./models_v2/
│   ├── parts/           ← archived from ./parts/
│   ├── ffs2_mvp/        ← archived FFS2 backend + extension source
│   │   ├── ColliderDataServer/
│   │   ├── ColliderGraphToolServer/
│   │   ├── ColliderVectorDbServer/
│   │   └── ColliderMultiAgentsChromeExtension/
│   └── ffs3_mvp/        ← archived FFS3 frontend source
│       └── collider-frontend/
└── workspaces/          ← .agent/ folders preserved, source rebuilt clean
```

---

## Migration Steps

1. [x] Create `_legacy/` folder
2. [x] Move `models_v2/` → `_legacy/models_v2/`
3. [x] Move `parts/` → `_legacy/parts/`
4. [x] Create new `models/` with clean structure
5. [x] Create new `sdk/` with clean structure
6. [ ] Update imports in workspaces as needed
7. [x] Tag `mvp-pre-rebuild` before FFS2/FFS3 archive
8. [x] Move FFS2 backend/extension source → `_legacy/ffs2_mvp/`
9. [x] Move FFS3 frontend source → `_legacy/ffs3_mvp/`
10. [ ] Rebuild FFS2 services from scratch (see `collider_rebuild_plan.md`)
11. [ ] Rebuild FFS3 frontend from scratch (see `collider_rebuild_plan.md`)

---

## Version Naming

| Version | Location | Status |
| ------------- | ---------------------- | ------------------ |
| v2 (legacy) | `_legacy/models_v2/` | Archived reference |
| v3 (new) | `models/` | Active development |
| FFS2 MVP | `_legacy/ffs2_mvp/` | Archived reference |
| FFS3 MVP | `_legacy/ffs3_mvp/` | Archived reference |
| FFS2 v2 (new) | FFS2 service dirs | Clean rebuild |
| FFS3 v2 (new) | FFS3 collider-frontend | Clean rebuild |

---

## Git Strategy

- Tag current state: `git tag v2-legacy`
- Tag pre-rebuild state: `git tag mvp-pre-rebuild`
- Commit archive move
- Begin clean development on fresh slate
- `.agent/` folders are never archived (workspace metadata, not source code)
