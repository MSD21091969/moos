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
├── FFS4_...Sidepanel/           ← .agent/ context only (code in FFS2 Chrome Extension)
├── FFS5_...PictureInPicture/    ← .agent/ context only (code in FFS2 Chrome Extension)
├── FFS6_...IDE/                 ← FILESYST domain app
├── FFS7_...Account/             ← ADMIN domain app
├── FFS8_...my-tiny-data/        ← CLOUD domain app
├── FFS9_...website1/            ← Future CLOUD app (placeholder)
└── FFS10_...website2/           ← Future CLOUD app (placeholder)
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

- **FFS4 Sidepanel**: Browser companion UI with Appnode Browser + AI Pilot/Agent Seat *(code in FFS2 Chrome Extension)*
- **FFS5 PiP**: User-to-user communications (WebRTC video/audio calls) *(code in FFS2 Chrome Extension)*
- **FFS6 IDE**: FILESYST domain - local file system access via native messaging
- **FFS7 Admin**: ADMIN domain - account management and permissions
- **FFS8 my-tiny-data-collider**: Main CLOUD domain app - personal data collection

## Important Architecture Note

**FFS4 and FFS5 Implementation Location:**
- FFS4 (Sidepanel) and FFS5 (PiP) are **conceptual application spaces** within FFS3
- Their actual **implementation code lives in FFS2** Chrome Extension:
  ```
  FFS2_ColliderBackends_MultiAgentChromeExtension/
  └── ColliderMultiAgentsChromeExtension/
      └── src/
          ├── sidepanel.tsx              # FFS4 entry point
          ├── pipWindow.tsx              # FFS5 entry point
          └── components/
              ├── sidepanel/             # FFS4 components
              └── pip/                   # FFS5 components
  ```
- FFS4 and FFS5 folders in FFS3 contain **only .agent/ context** (documentation, AI instructions)

**FFS6-8 Implementation Location:**
- These are **Nx applications** within the collider-frontend monorepo
- Actual code: `FFS3_ColliderApplicationsFrontendServer/collider-frontend/apps/`
