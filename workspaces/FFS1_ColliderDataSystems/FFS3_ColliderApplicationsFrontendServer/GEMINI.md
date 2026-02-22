# GEMINI.md — Collider Web Applications (FFS3)

Refer to the main factory instructions at `D:\FFS0_Factory\GEMINI.md`.

## FFS3 Context

- **Identity**: Frontend applications and UI library.
- **Tech Stack**: Nx, React 19, Vite 7.
- **Package Manager**: pnpm (explicitly set in `.vscode/settings.json`).

## Architecture

- `apps/ffs6`: IDE Viewer (default).
- `apps/ffs4`: Sidepanel.
- `apps/ffs5`: PiP.
- `libs/shared-ui`: Internal design system.

## Commands

- Dev: `pnpm nx serve ffs6`
- Build: `pnpm nx build ffs6`
- Test: `pnpm nx test ffs6`
