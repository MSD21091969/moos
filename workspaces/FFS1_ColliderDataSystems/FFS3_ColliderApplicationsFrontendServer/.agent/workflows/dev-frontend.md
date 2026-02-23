---
description: Run the FFS3 Nx frontend dev server — serves ffs6 (IDE viewer) by
default on port 4200
---

# Dev: Frontend (FFS3)

Starts the Nx dev server for the FFS3 monorepo.

## Steps

1. Install dependencies (first time or after `package.json` changes):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer
   pnpm install
   ```

2. Serve the default app (ffs6 — IDE viewer on :4200):

   ```powershell
   pnpm nx serve ffs6
   ```

3. To serve other apps:

   ```powershell
   pnpm nx serve ffs4   # Sidepanel appnode — port 4201
   pnpm nx serve ffs5   # PiP appnode — port 4202
   ```

4. To run all apps simultaneously:

   ```powershell
   pnpm nx run-many --target=serve --projects=ffs4,ffs5,ffs6 --parallel
   ```

## Other Useful Commands

```powershell
# Run tests for all apps
pnpm nx run-many --target=test --all

# Lint all apps
pnpm nx run-many --target=lint --all

# Build for production
pnpm nx build ffs6
```

## Notes

- `ffs6` is the default project (set in `nx.json`).
- Make sure ColliderDataServer is running on `:8000` — the apps fetch from `VITE_API_BASE`.
- Hot module replacement (HMR) is enabled by default via Vite.
