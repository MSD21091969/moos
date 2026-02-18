# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Context System

Every workspace has an `.agent/` folder containing architecture docs, rules, and instructions. **Always read `.agent/index.md` first** when working in any workspace.

Key files:

- `.agent/index.md` — workspace identity and purpose
- `.agent/manifest.yaml` — inheritance and exports
- `.agent/instructions/agent_system.md` — role and architecture
- `.agent/rules/` — coding standards and constraints
- `.agent/knowledge/architecture/` — layered architecture docs (in FFS1)

## Workspace Map

```
FFS0_Factory/                  Python agent-factory package (UV, pyproject.toml)
├── models/                    Pydantic models (v3, active)
├── sdk/                       SDK components
└── workspaces/
    ├── FFS1_ColliderDataSystems/       Schemas, governance, orchestration
    │   ├── FFS2_...ChromeExtension/    3 FastAPI servers + Chrome ext (Plasmo)
    │   └── FFS3_...FrontendServer/     Nx monorepo (Vite 7 + React 19, Next.js optional)
    │       ├── apps/ffs4              Sidepanel appnode
    │       ├── apps/ffs5              PiP appnode
    │       ├── apps/ffs6              IDE viewer appnode (default project)
    │       └── libs/shared-ui         Shared components + XYFlow
    └── maassen_hochrath/               IADORE personal AI workspace (Ollama, BakLLaVA)
```

## Tech Stack

**Python** (FFS0, FFS1, FFS2): Python 3.12+, UV, FastAPI, Pydantic v2, SQLAlchemy async, aiosqlite, ChromaDB, Ruff, Mypy strict, Pytest
**TypeScript** (FFS3): Nx, Vite 7, React 19, TS 5+, XYFlow, Zustand, React Router, CSS Modules, ESLint, Vitest
**Chrome Extension** (FFS2): Plasmo, Manifest V3, React + TypeScript, LangGraph.js

## Servers

- ColliderDataServer — port 8000 (REST + SSE, async SQLite via aiosqlite)
- ColliderGraphToolServer — port 8001 (WebSocket workflow executor, Pydantic AI)
- ColliderVectorDbServer — port 8002 (ChromaDB semantic search)
- FFS3 Frontend — port 4200 (ffs6 default), 4201 (ffs4), 4202 (ffs5)

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Python: Google docstrings, Ruff formatting, 80% test coverage on core
- TypeScript: TSDoc, strict mode, no `any`, Interfaces for props
- Only modify files under `D:\FFS0_Factory\`
- Check `.agent/` context before modifying any workspace
