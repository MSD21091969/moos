# FFS0 Factory - Agent System Instruction

> Root workspace instruction for all child workspaces.

## Role

You are assisting in the FFS0_Factory root workspace. This is the top-level container for:

- Agent Studio (AI development tools)
- Collider Data Systems (FFS1)
- Supporting infrastructure

## Workspace Structure

```
FFS0_Factory/
├── .agent/                          ← This context (root)
├── agent-studio/                    ← AI development tools
├── docs/                            ← Documentation
├── models_v2/                       ← Data models
├── parts/                           ← Shared components
├── secrets/                         ← Credentials (gitignored)
└── workspaces/
    └── FFS1_ColliderDataSystems/    ← Collider system
        ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
        │   ├── ColliderDataServer/      ← FastAPI backend (:8000)
        │   ├── ColliderGraphToolServer/ ← AI workflows (:8001)
        │   ├── ColliderVectorDbServer/  ← Semantic search (:8002)
        │   └── ColliderMultiAgentsChromeExtension/  ← Plasmo extension
        └── FFS3_ColliderApplicationsFrontendServer/
            └── collider-frontend/       ← Nx monorepo (Next.js Portal)
```

## MVP Status (2026-02-05)

**Operational Components:**
- Backend API Server (FastAPI :8000) ✅
- Portal Frontend (Next.js :3001) ✅
- Chrome Extension (Plasmo) ✅
- PostgreSQL Database (:5432) ✅

**Running Guide:** See `FFS1_ColliderDataSystems/.agent/knowledge/RUNNING.md`

## Inheritance

This workspace exports rules and configs to all children:

- `rules/` - Coding patterns, sandbox, identity
- `configs/` - Users, API providers, defaults

Child workspaces inherit via their `manifest.yaml`.

## Key Rules

- Follow code patterns in `rules/`
- Respect sandbox boundaries
- Use established identity patterns
- Check devlog entries before making architectural changes

