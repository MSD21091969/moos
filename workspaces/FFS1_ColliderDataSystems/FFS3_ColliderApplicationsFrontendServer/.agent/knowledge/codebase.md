# FFS3 Codebase

> Nx monorepo with Vite + React 19 applications.

## Structure

```text
FFS3_ColliderApplicationsFrontendServer/   ← This IS the Nx workspace root
├── apps/
│   ├── ffs4/                              ← Sidepanel appnode
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── app.tsx                ← Root component
│   │   │   │   ├── app.module.css
│   │   │   │   └── nx-welcome.tsx         ← Nx scaffold placeholder
│   │   │   ├── main.tsx                   ← Entry point
│   │   │   └── styles.css
│   │   ├── index.html
│   │   ├── vite.config.mts
│   │   ├── project.json                   ← Nx project config
│   │   └── tsconfig.json
│   ├── ffs5/                              ← PiP appnode (same structure)
│   │   └── ...
│   └── ffs6/                              ← IDE viewer appnode (default project)
│       └── ...
├── libs/
│   └── shared-ui/                         ← @collider/shared-ui
│       ├── src/
│       │   ├── lib/
│       │   │   ├── shared-ui.tsx
│       │   │   └── shared-ui.spec.tsx
│       │   └── index.ts                   ← Public API barrel
│       ├── vite.config.mts
│       ├── project.json
│       └── tsconfig.json
├── nx.json                                ← @nx/vite plugin, defaultProject: ffs6
├── package.json                           ← ffs3-monorepo, React 19, Vite 7, Vitest 4
├── tsconfig.base.json                     ← Base TypeScript config
└── pnpm-lock.yaml
```

## Key Files

| File                     | Purpose                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| `nx.json`                | Nx workspace config. Default project: `ffs6`. Plugin: `@nx/vite`. |
| `package.json`           | Root deps: `react@19`, `vite@7`, `vitest@4`, `@nx/*` packages.    |
| `tsconfig.base.json`     | Base TS config. Path aliases for `@collider/shared-ui`.           |
| `apps/*/project.json`    | Per-app Nx targets: `build`, `serve`, `test`, `lint`.             |
| `apps/*/vite.config.mts` | Per-app Vite config. Port defaults (ffs6 = 4200).                 |

## Appnode Concept

Each app in `apps/` is an **appnode** — a frontend view that renders workspace nodes from the DB:

| App  | Role                                        | Default Port   |
| ---- | ------------------------------------------- | -------------- |
| ffs4 | Sidepanel: agent seat, app tree browser     | 4201           |
| ffs5 | PiP: Picture-in-Picture communication       | 4202           |
| ffs6 | IDE viewer: renders selected workspace node | 4200 (default) |

The node-container's `metadata_.frontend_app` field determines which appnode renders a given workspace.

## Shared Library

`libs/shared-ui` is consumed via TypeScript path alias:

```typescript
import { SharedUi } from '@collider/shared-ui';
```

Path defined in `tsconfig.base.json`:

```json
{
  "paths": {
    "@collider/shared-ui": ["libs/shared-ui/src/index.ts"]
  }
}
```

## Developer Guide

### Setup

```bash
cd FFS3_ColliderApplicationsFrontendServer
pnpm install
```

### Dev Server

```bash
nx serve ffs6          # Start default app (port 4200)
nx serve ffs4          # Start sidepanel app
nx serve ffs5          # Start PiP app
```

### Build & Test

```bash
nx build ffs6          # Production build
nx test ffs6           # Run Vitest tests
nx lint ffs6           # ESLint
nx run-many -t build   # Build all apps
```

### Add New App

```bash
nx g @nx/react:app apps/ffs7       # New Vite + React app
```
