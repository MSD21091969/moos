# ffs6 Agent Context — IDE Viewer

Primary full-screen workspace application (default Nx project).

## Architecture

- **Views**: AdminDashboard, NodeDetails + additional view components
- **Graph**: Full XYFlow workspace visualization
- **State**: Shared Zustand stores (same pattern as ffs4)
- **Default port**: `:4200`

## Commands

- Dev: `pnpm nx serve ffs6`
- Build: `pnpm nx build ffs6`
- Typecheck: `pnpm nx run ffs6:typecheck`

Inherits from FFS3 workspace `.agent`.
