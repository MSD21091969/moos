# Copilot Instructions — FFS0 Factory (Collider Ecosystem)

## Project Overview

This is a monorepo (`D:\FFS0_Factory`) for the **Collider** multi-agent ecosystem. It contains nested workspaces (FFS0-FFS10) with Python backends, a Next.js frontend, and a Chrome extension.

Full architecture docs live in `.agent/` folders at each workspace level. Always check `.agent/index.md` and `.agent/knowledge/architecture/` for context before making changes.

## Workspace Hierarchy

```
FFS0_Factory/              Root — Python agent-factory package (UV)
└── workspaces/
    ├── FFS1_ColliderDataSystems/     Governance, schemas, orchestration (.agent metadata)
    │   ├── FFS2_.../                 Backend services + Chrome extension
    │   │   ├── ColliderDataServer/src/           Python FastAPI (Port 8000)
    │   │   ├── ColliderGraphToolServer/src/      Python FastAPI (Port 8001)
    │   │   ├── ColliderVectorDbServer/src/       Python FastAPI (Port 8002)
    │   │   └── ColliderMultiAgentsChromeExtension/src/  TypeScript/React (Plasmo)
    │   │
    │   └── FFS3_.../                 Next.js Nx monorepo
    │       ├── collider-frontend/apps/portal/src/       Main Next.js app (Port 3000)
    │       ├── collider-frontend/libs/                  Shared React libraries
    │       └── FFS4-FFS10/                             App specs (.agent metadata + mockups ONLY)
    │
    └── maassen_hochrath/             IADORE personal AI workspace
```

### Important: Actual Source Code Locations

**DO NOT LOOK FOR CODE IN:** FFS0, FFS1, FFS4-FFS10 roots (metadata/specs only)

**ACTUAL SOURCE CODE IS AT:**

- **Python Backends:** `FFS2_*/[ServiceName]/src/` (3 FastAPI servers)
- **Chrome Extension:** `FFS2_*/ColliderMultiAgentsChromeExtension/src/`
- **Frontend Portal:** `FFS3_*/collider-frontend/apps/portal/src/`
- **Shared UI/Logic:** `FFS3_*/collider-frontend/libs/*/src/`

## Tech Stack

### Python (FFS0, FFS1, FFS2 backends)

- Python 3.12+, UV package manager
- FastAPI (async), Pydantic v2, SQLAlchemy
- ChromaDB (vectors), PostgreSQL (relational), NetworkX (graphs)
- Linter/Formatter: Ruff. Type checker: Mypy (strict)
- Testing: Pytest + pytest-asyncio. Min 80% coverage on core logic.

### TypeScript (FFS3 frontend, FFS2 Chrome extension)

- Nx monorepo, Next.js 16 (App Router), React 19, TypeScript 5+
- Tailwind CSS, Radix UI / shadcn/ui, Framer Motion
- State: Zustand (client), TanStack Query (server)
- Linter: ESLint. Formatter: Prettier. `strict: true` in tsconfig.
- Testing: Vitest (unit), Playwright (E2E)
- Chrome extension: Plasmo framework, Manifest V3

## Code Quality Rules

1. **Conventional Commits**: `feat:`, `fix:`, `chore:` — one logical change per commit
2. **Python docstrings**: Google-style on all public API endpoints
3. **TypeScript docs**: TSDoc (`/** */`) on all exported components
4. **No `any`**: Use `unknown` or generic constraints
5. **React**: Custom hooks for logic, components for view only. Props via Interfaces, not Types.
6. **Directory conventions**: `src/` for source, `tests/` mirroring src structure, `.agent/` for AI context

## Architecture Principles

1. `.agent/` = workspace state — ready for execution
2. Components scale: Tool (atomic JSON schema) → Workflow (YAML sequence) → Application (graph)
3. Single source of truth — schemas defined in FFS1, propagate down to FFS2/FFS3
4. Inherit, don't duplicate — use `.agent/manifest.yaml` includes
5. Three domains: FILESYST (IDE), CLOUD (apps), ADMIN (account)

## Data Flow

1. Schemas defined in FFS1 (Pydantic/Protobuf)
2. FFS2 implements the API contract (FastAPI servers on ports 8000-8002)
3. FFS3 consumes the API contract (Next.js frontend)
4. Changes to the data model must propagate from FFS1 down

## Servers & Code Locations

| Server                  | Port | Source Code Location                         |
| ----------------------- | ---- | -------------------------------------------- |
| ColliderDataServer      | 8000 | FFS2/ColliderDataServer/src/                 |
| ColliderGraphToolServer | 8001 | FFS2/ColliderGraphToolServer/src/            |
| ColliderVectorDbServer  | 8002 | FFS2/ColliderVectorDbServer/src/             |
| Next.js Portal          | 3000 | FFS3/collider-frontend/apps/portal/src/      |
| Chrome Extension        | N/A  | FFS2/ColliderMultiAgentsChromeExtension/src/ |

## Sandbox

Only modify files under `D:\FFS0_Factory\`. Do not access system paths, `C:\Windows\`, `C:\Program Files\`, or `%USERPROFILE%\` unless explicitly asked.
