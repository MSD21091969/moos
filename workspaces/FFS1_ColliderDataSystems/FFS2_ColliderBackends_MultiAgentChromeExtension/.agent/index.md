# FFS2 ColliderBackends - Agent Context

> Backend services and Chrome Extension implementation.

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\.agent\`

## Hierarchy

```
FFS0_Factory                     (Root)
  └── FFS1_ColliderDataSystems   (IDE Context)
        └── FFS2_ColliderBackends (This Workspace)
```

## Purpose

Specific context for:

- ColliderDataServer (FastAPI on :8000)
- ColliderGraphToolServer (WebSocket on :8001)
- ColliderVectorDbServer (Vector search on :8002)
- ColliderMultiAgentsChromeExtension (Plasmo)

## Contents

- **instructions/**: Backend-specific coding guides (inherits from FFS1).
- **knowledge/**: Codebase documentation.
- **skills/**: Backend-specific skills (inherits from FFS1).
- **tools/**: Backend-specific tools (inherits from FFS1).
- **configs/**: Backend-specific configs (inherits from FFS1).
- **workflows/**: Deployment and testing workflows (inherits from FFS1).

## Component Folders

```
ColliderDataServer/              # REST/SSE API server
ColliderGraphToolServer/         # WebSocket/Agents server
ColliderVectorDbServer/          # Vector search server
ColliderMultiAgentsChromeExtension/  # Plasmo extension
```
