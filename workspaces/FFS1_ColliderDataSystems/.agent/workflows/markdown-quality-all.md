---
description: Orchestrate markdown quality checks across FFS1, FFS2, and FFS3
---

# Markdown Quality (All FFS1 Workspaces)

Runs markdown quality workflows in sequence for:

1. FFS1 coordination docs
2. FFS2 backend/extension docs
3. FFS3 frontend docs

Use this as the single entrypoint before PRs that touch documentation across
multiple workspaces.

## Run Order

### 1) FFS1 docs

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs1
```

### 2) FFS2 docs

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs2
```

### 3) FFS3 docs

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs3
```

## Optional Auto-Fix Sweep

If you want to auto-fix safe markdown rules first, run the same three commands
with `--fix` before the verification run.

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:fix
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md
```

## Related Workflows

- `/markdown-quality` in FFS1: local FFS1 scope
- `/markdown-quality` in FFS2: backend/extension scope
- `/markdown-quality` in FFS3: frontend scope
