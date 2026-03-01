# FFS3 ColliderFrontend - Agent Context

> Frontend Application Server (Nx + Vite + React 19)

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\.agent\`

## Hierarchy

```text
FFS0_Factory                     (Root)
  └── FFS1_ColliderDataSystems   (IDE Context)
        └── FFS3_ColliderFrontend (This Workspace = Nx monorepo root)
```

## Purpose

Specific context for the frontend monorepo, which delivers **appnodes** —
frontend views that render workspace nodes from the DB:

- **apps/ffs4** — Sidepanel appnode: agent seat, app tree, workspace browser
- **apps/ffs5** — PiP appnode: Picture-in-Picture communication window (WebRTC)
- **apps/ffs6** — IDE viewer appnode: renders selected workspace node (default project)
- **libs/shared-ui** — Shared UI components, utilities, and XYFlow graph visualization

Each app is a Vite + React 19 appnode. The NodeContainer
`metadata_.frontend_app` field determines which appnode renders a given
workspace node.

## Contents

- **instructions/**: Frontend coding guides (inherits from FFS1).
- **knowledge/**: Codebase documentation.
- **skills/**: Frontend-specific skills (inherits from FFS1).
- **tools/**: Frontend-specific tools (inherits from FFS1).
- **configs/**: Frontend-specific configs (inherits from FFS1).
- **workflows/**: Frontend build and test workflows (inherits from FFS1).
