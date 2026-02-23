---
description: Run markdown lint and safe auto-fix for FFS2 backend and extension
  docs
---

# Markdown Quality (FFS2)

Use this workflow for markdown quality in FFS2 backend and Chrome extension docs.

## Scope

From `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension`:

- Includes all `**/*.md` files in FFS2.
- Excludes dependency/build folders.
- Excludes legacy/archive trees.

## Commands

### 1) Lint FFS2 docs

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs2
```

### 2) Apply safe auto-fixes

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs2:fix
```

### 3) Re-run lint

```powershell
cd D:\FFS0_Factory
pnpm --dir workspaces/FFS1_ColliderDataSystems run lint:md:ffs2
```

## Operational Notes

- Keep this check near `/dev-stop` and `/test-extension-ux` before release work.
- Prefer fixing structure rules first, then line-length policy decisions.
