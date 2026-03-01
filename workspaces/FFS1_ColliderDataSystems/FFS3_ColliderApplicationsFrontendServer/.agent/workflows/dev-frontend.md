---
description: Run the FFS3 Nx frontend dev server — serves ffs6 (IDE viewer) by
default on port 4200
---

# Dev: Frontend (FFS3)

Starts the Nx dev server for the FFS3 monorepo.

## Steps

1. Install dependencies from the FFS1 workspace root (lockfile authority):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems
   pnpm install
   ```

2. Move to the FFS3 workspace:

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer
   ```

3. Serve the default app (ffs6 — IDE viewer on :4200):

   ```powershell
   pnpm nx serve ffs6
   ```

4. To serve other apps:

   ```powershell
   pnpm nx serve ffs4   # Sidepanel appnode — port 4201
   pnpm nx serve ffs5   # PiP appnode — port 4202
   ```

5. To run all apps simultaneously:

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
- Make sure ColliderDataServer is running on `:8000` and AgentRunner on `:8004`.
- Frontend env contracts are `VITE_DATA_SERVER_URL` and `VITE_AGENT_RUNNER_URL`.
- Hot module replacement (HMR) is enabled by default via Vite.
