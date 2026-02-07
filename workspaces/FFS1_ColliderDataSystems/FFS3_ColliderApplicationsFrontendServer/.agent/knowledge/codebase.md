# Codebase: FFS3 ColliderFrontend

> Nx monorepo with Next.js applications and shared libraries.

## Role

Hosts the web-based "AppNodes" when they are not running inside the Chrome Extension sidepanel or are being developed in isolation.

## Structure

```
FFS3_ColliderApplicationsFrontendServer/
├── collider-frontend/           ← Nx workspace root
│   ├── apps/
│   │   └── portal/             ← Main Next.js app
│   └── libs/
│       ├── api-client/         ← @collider/api-client
│       ├── shared-ui/          ← @collider/shared-ui
│       └── node-container/     ← @collider/node-container
│
├── FFS4_...Sidepanel/           ← Browser companion UI
├── FFS5_...PictureInPicture/    ← Main agent seat
├── FFS6_...IDE/                 ← FILESYST domain app
├── FFS7_...Account/             ← ADMIN domain app
├── FFS8_...my-tiny-data/        ← CLOUD domain app
├── FFS9_...website1/            ← Future CLOUD app
└── FFS10_...website2/           ← Future CLOUD app
```

## Developer Guide

### Running the Frontend

```bash
cd collider-frontend
pnpm install
pnpm dev       # Starts Next.js dev server
```

### Nx Commands

```bash
npx nx build portal          # Build the portal app
npx nx test portal           # Run tests
npx nx graph                 # View dependency graph
```

## Key Apps

- **FFS4 Sidepanel**: The browser companion UI.
- **FFS6 IDE**: The FILESYST domain visualization.
- **FFS7 Admin**: The ADMIN domain account management.
- **FFS8 my-tiny-data-collider**: Main CLOUD domain app.
