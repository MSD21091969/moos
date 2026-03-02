# Moos

Moos is an Nx monorepo with a split architecture:

- **Node runtime apps** for backend execution (`data-server`, `tool-server`, `engine`)
- **React surface apps** for UI (`sidepanel`, `viewer`)
- **Shared TypeScript packages** for domain logic and reuse (`core`, `functors`, `store`, `shared-ui`)

This README describes the implementation structure and how the code is organized.

## Implementation at a glance

### Apps

- `apps/data-server` (`@moos/data-server`)
	- Node app built with esbuild
	- Depends on `@moos/core` and `@moos/store`
	- Entry point: `apps/data-server/src/main.ts`

- `apps/tool-server` (`@moos/tool-server`)
	- Node app built with esbuild
	- Depends on `@moos/core` and `@moos/functors`
	- Entry point: `apps/tool-server/src/main.ts`

- `apps/engine` (`@moos/engine`)
	- Node orchestration/runtime app built with esbuild
	- Depends on `@moos/core`, `@moos/functors`, `@moos/store`
	- Entry point: `apps/engine/src/main.ts`

- `apps/sidepanel` (`@moos/sidepanel`)
	- React UI surface
	- Depends on `@moos/shared-ui`

- `apps/viewer` (`@moos/viewer`)
	- React UI surface
	- Depends on `@moos/shared-ui`

### Packages

- `packages/core` (`@moos/core`)
	- Base shared domain primitives and shared contracts

- `packages/functors` (`@moos/functors`)
	- Composition helpers and higher-level reusable logic
	- Depends on `@moos/core`

- `packages/store` (`@moos/store`)
	- Shared state/data model utilities
	- Depends on `@moos/core`

- `packages/shared-ui` (`@moos/shared-ui`)
	- Shared UI components used by `sidepanel` and `viewer`

## Runtime dependency flow

Implementation dependency direction is intentionally one-way:

- `core` is the foundation
- `functors` and `store` build on `core`
- backend apps consume packages according to role:
	- `data-server` → `core` + `store`
	- `tool-server` → `core` + `functors`
	- `engine` → `core` + `functors` + `store`
- UI apps consume `shared-ui`

This separation keeps business logic reusable while keeping each app focused on its runtime responsibility.

## Surface env vars

The UI surfaces share a presence-staleness threshold env var:

- `VITE_SURFACE_STALE_THRESHOLD_SECONDS`

If unset or invalid, default behavior uses `10` seconds.

## Build and run (implementation-level)

From `moos/`:

```sh
pnpm install
pnpm nx run @moos/source:compat:build
```

Compatibility-focused root targets:

```sh
pnpm nx run @moos/source:compat:build
pnpm nx run @moos/source:compat:test
pnpm nx run @moos/source:compat:serve:backend
pnpm nx run @moos/source:compat:serve
```

To run any app or package target:

```sh
pnpm nx <target> <project>
```

Examples:

```sh
pnpm nx serve @moos/data-server
pnpm nx serve @moos/tool-server
pnpm nx serve @moos/engine
```

## Notes

- `scripts/` and `reports/` are currently empty by design after harness cleanup.
- This README is intentionally implementation-focused and avoids process/gate documentation.
