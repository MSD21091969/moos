# CLAUDE.md — Collider Web Applications (FFS3)

Refer to the main factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

Canonical rehydration runbook: `D:\FFS0_Factory\.agent\workflows\conversation-state-rehydration.md`.

## FFS3 Context

- **Identity**: Frontend applications and UI library.
- **Tech Stack**: Nx, React 19, Vite 7.
- **Package Manager**: pnpm (explicitly set in `.vscode/settings.json`).
- **Workspace Authority**: This root is a member of the FFS1 pnpm workspace. Use the FFS1 root `pnpm-lock.yaml` as the source of truth for dependencies.
- **Environment**: See `.env.example` for required `VITE_DATA_SERVER_URL` and `VITE_AGENT_RUNNER_URL` variables.
- **Backend Dependency**: MOOS compatibility surfaces at `:8000`, `:8004`, and `:18789`.

## Architecture

- `apps/ffs6`: IDE Viewer (default).
- `apps/ffs4`: Sidepanel.
- `apps/ffs5`: PiP.
- `libs/shared-ui`: Internal design system.
- `apps/ffs4/.agent`, `apps/ffs5/.agent`, `apps/ffs6/.agent`: Minimal app-level inheritance stubs.

## Commands

- Dev: `pnpm nx serve ffs6`
- Build: `pnpm nx build ffs6`
- Typecheck: `pnpm nx run ffs6:typecheck`

## .agent Wiring

- Workspace manifest: `.agent/manifest.yaml` includes FFS1 context from `../../.agent`.
- Workspace exports: `.agent/knowledge/codebase.md`.
- App manifests (`ffs4/ffs5/ffs6`) include the FFS3 workspace `.agent` using `../../../.agent`.
