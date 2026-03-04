# FFS3 Agent Context

FFS3 is the frontend application layer: Nx monorepo with Vite 7 + React 19.

## Applications

- `apps/ffs6` — IDE Viewer (default, `:4200`)
- `apps/ffs4` — Chrome Extension Sidepanel (`:4201`)
- `apps/ffs5` — Picture-in-Picture (`:4202`)
- `libs/shared-ui` — Internal design system

## Loads from FFS1

- `instructions/agent_system.md`
- `rules/communication_architecture.md`, `rules/stack_standards.md`, `rules/code_quality.md`
- `workflows/cross-service-validation-gates.md`

## Exports to App Stubs

- `knowledge/codebase.md` — architecture reference for ffs4/ffs5/ffs6

## Backend Dependency

All frontends connect to MOOS compatibility surfaces at `:8000`, `:8004`, and `:18789`.
