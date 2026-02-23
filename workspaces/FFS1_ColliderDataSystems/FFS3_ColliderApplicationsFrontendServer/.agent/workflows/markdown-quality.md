---
description: Run markdown quality checks for FFS3 frontend docs and runbooks
---

# Markdown Quality (FFS3)

Use this workflow to lint and fix markdown files in the FFS3 frontend workspace.

## Scope

From `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer`:

- Includes all `**/*.md` files in FFS3.
- Excludes dependency/build folders.
- Excludes legacy/archive trees.

## Commands

### 1) Lint FFS3 docs

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs3
```

### 2) Auto-fix safe markdown rules

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs3:fix
```

### 3) Verify clean result

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs3
```

## Team Usage

Run this before frontend release docs changes or when updating runbooks under
`.agent/`.
