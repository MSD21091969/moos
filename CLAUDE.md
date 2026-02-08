# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Context System

Every workspace has an `.agent/` folder containing architecture docs, rules, and instructions. **Always read `.agent/index.md` first** when working in any workspace.

Key files:
- `.agent/index.md` — workspace identity and purpose
- `.agent/manifest.yaml` — inheritance and exports
- `.agent/instructions/agent_system.md` — role and architecture
- `.agent/rules/` — coding standards and constraints
- `.agent/knowledge/architecture/` — layered architecture docs

## Workspace Map

```
FFS0_Factory/                  Python agent-factory package (UV, pyproject.toml)
├── models/                    Pydantic models (v3, active)
├── sdk/                       SDK components
├── _legacy/                   Archived v2 models/parts
└── workspaces/
    ├── FFS1_ColliderDataSystems/       Schemas, governance, orchestration
    │   ├── FFS2_...ChromeExtension/    3 FastAPI servers + Chrome ext (Plasmo)
    │   └── FFS3_...FrontendServer/     Nx monorepo (Next.js 16, React 19)
    │       ├── FFS4  Sidepanel app spec
    │       ├── FFS5  PiP agent seat spec
    │       ├── FFS6  Filesystem IDE spec
    │       ├── FFS7  Admin app spec
    │       └── FFS8  Cloud app spec
    └── maassen_hochrath/               IADORE personal AI workspace (Ollama, BakLLaVA)
```

## Tech Stack

**Python** (FFS0, FFS1, FFS2): Python 3.12+, UV, FastAPI, Pydantic v2, SQLAlchemy, ChromaDB, Ruff, Mypy strict, Pytest
**TypeScript** (FFS3): Nx, Next.js 16, React 19, TS 5+, Tailwind, Radix/shadcn, Zustand, TanStack Query, ESLint, Prettier, Vitest, Playwright
**Chrome Extension** (FFS2): Plasmo, Manifest V3, React + TypeScript

## Servers

- ColliderDataServer — port 8000 (REST + SSE, async PostgreSQL)
- ColliderGraphToolServer — port 8001 (WebSocket workflow executor, Gemini AI)
- ColliderVectorDbServer — port 8002 (ChromaDB semantic search)
- Next.js Portal — port 3000

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Schemas defined in FFS1, propagate down — never duplicate
- Python: Google docstrings, Ruff formatting, 80% test coverage on core
- TypeScript: TSDoc, strict mode, no `any`, Interfaces for props
- Only modify files under `D:\FFS0_Factory\`
- Check `.agent/` context before modifying any workspace
