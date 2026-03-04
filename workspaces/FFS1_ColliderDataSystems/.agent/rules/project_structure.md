# Project Structure

## Workspace Hierarchy

- **FFS0**: Root governance, `.agent` inheritance provider, shared schemas.
- **FFS1**: Orchestration layer, pnpm workspace root, contract definitions.
- **FFS2**: Backend compatibility runtime — MOOS Go kernel.
  - `moos/cmd/kernel/` — Entry point
  - `moos/internal/` — Core packages (model, morphism, session, container, config, tool)
  - `moos/apps/` — Runtime surfaces (data-server, tool-server, engine, chrome-extension)
- **FFS3**: Frontend apps — Nx monorepo.
  - `apps/ffs4/` — Sidepanel (`:4201`)
  - `apps/ffs5/` — PiP (`:4202`)
  - `apps/ffs6/` — IDE Viewer (`:4200`)
  - `libs/shared-ui/` — Shared design system

## Convention

- Child app workspaces carry minimal `.agent` stubs with `display_name`, `description`, `domain`, `port`.
- Leaf workspaces inherit rules and instructions from parent; they add only app-specific knowledge.
- Shared code lives in `libs/`, app-specific code in `apps/`.
