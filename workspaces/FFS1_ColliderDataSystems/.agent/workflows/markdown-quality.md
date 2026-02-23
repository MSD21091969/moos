---
description: Run markdown quality checks for FFS1 docs and enforce active-scope
  lint rules
---

# Markdown Quality (FFS1)

Use this workflow to check and fix markdown files in the FFS1 workspace.

## Scope

From `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems`:

- Includes all `**/*.md` files in FFS1.
- Excludes dependency and generated folders.
- Excludes legacy and archive trees.

## Commands

### 1) Lint (read-only)

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs1
```

### 2) Auto-fix safe rules

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs1:fix
```

### 3) Verify after fixes

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs1
```

## Suggested PR Check

For CI or pre-merge checks, use the canonical command:

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md
```
