# CLAUDE.md — Collider Web Applications (FFS3)

Refer to the main factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

Canonical rehydration runbook: `D:\FFS0_Factory\.agent\workflows\conversation-state-rehydration.md`.

## FFS3 Context

- **Identity**: Frontend applications and UI library.
- **Tech Stack**: Nx, React 19, Vite 7.
- **Package Manager**: pnpm (explicitly set in `.vscode/settings.json`).
- **Workspace Authority**: This root is a member of the FFS1 pnpm workspace. Use the FFS1 root `pnpm-lock.yaml` as the source of truth for dependencies.
- **Environment**: See `.env.example` for required `VITE_DATA_SERVER_URL` and `VITE_AGENT_RUNNER_URL` variables.

## Architecture

- `apps/ffs6`: IDE Viewer (default).
- `apps/ffs4`: Sidepanel.
- `apps/ffs5`: PiP.
- `libs/shared-ui`: Internal design system.

## Commands

- Dev: `pnpm nx serve ffs6`
- Build: `pnpm nx build ffs6`
- Typecheck: `pnpm nx run ffs6:typecheck`
