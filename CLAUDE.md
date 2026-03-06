# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Context System & The "Three Claudes"

Due to the size of the repository, we use a hierarchical context system to prevent AI context pollution.
Read order for AI Agents:
1. `D:\FFS0_Factory\CLAUDE.md` (Root / Factory conventions)
2. Workspace `CLAUDE.md` (Backend vs Frontend specifics)
   - `workspaces/FFS1_ColliderDataSystems/CLAUDE.md` -> Loads Go 1.23 / MOOS backend context.
   - `workspaces/FFS1.../FFS3_ColliderApplicationsFrontendServer/CLAUDE.md` -> Loads Vite/React/Nx frontend context.
3. Workspace `.agent/index.md` & `.agent/manifest.yaml`

Canonical runbook:
- `.agent/workflows/conversation-state-rehydration.md`

## Workspace Map

```text
FFS0_Factory/
├── .agent/                               Root inheritance/governance context
│   └── knowledge/                        Canonical knowledge base (v3.0)
│       ├── 01_foundations/               Categorical model & axioms
│       ├── 02_architecture/              System architecture & functors
│       ├── 03_implementation/            DB schema, security, impl details
│       ├── 04_developer_guide/           Setup, tools, models, app templates
│       ├── superset/                     v2 ontology (JSON + CSV)
│       ├── papers/                       Reference papers (category theory, RAG)
│       ├── _legacy/                      Pre-v3.0 knowledge (archived)
│       └── MANIFESTO.md                  Project manifesto
├── sdk/                                  Seeder + runtime support utilities
├── scripts/                              Utility scripts (git-push-all, etc.)
└── workspaces/
    ├── FFS1_ColliderDataSystems/         Governance + shared contracts
    │   ├── FFS2_...ChromeExtension/
    │   │   └── moos/                     Active backend — Go kernel runtime
    │   └── FFS3_...FrontendServer/       Nx frontend workspace (ffs4/ffs5/ffs6)
    └── maassen_hochrath/                 Legacy reference / archive
```

## Knowledge Base (v3.0)

The canonical knowledge lives in `.agent/knowledge/`. Key documents:

| Document            | Path               | Description                                                                |
| ------------------- | ------------------ | -------------------------------------------------------------------------- |
| **foundations.md**  | `01_foundations/`  | Categorical model: connections = morphisms, 5 axioms, edge density formula |
| **architecture.md** | `02_architecture/` | 5 genuine functors (FileSystem, UI_Lens, Embedding, Structure, Benchmark)  |
| **v2 ontology**     | `superset/`        | 13 objects, 13 morphisms (incl. CAN_FORK), 5 functors, 4 NTs               |
| **MANIFESTO.md**    | root               | Project vision and principles                                              |

Corrected categorical model (v3.0):
- Connections = **morphisms** (NOT functors)
- Fan-out = coslice, Fan-in = slice
- Container OWNS = full subcategory
- Σ (collapse) = catamorphism
- Protocol = morphism-level routing (NOT a functor)

## Active Runtime Surfaces

| Surface                   | Port  | Owner |
| ------------------------- | ----- | ----- |
| MOOS data compatibility   | 8000  | FFS2  |
| MOOS tool/MCP server      | 8080  | FFS2  |
| MOOS agent compatibility  | 8004  | FFS2  |
| MOOS NanoClaw WS bridge   | 18789 | FFS2  |
| FFS3 IDE viewer (ffs6)    | 4200  | FFS3  |
| FFS3 sidepanel app (ffs4) | 4201  | FFS3  |
| FFS3 PiP app (ffs5)       | 4202  | FFS3  |

MCP endpoint:
```bash
claude mcp add collider-tools --transport sse http://localhost:8080/mcp/sse
```

Secrets:
- `D:\FFS0_Factory\secrets\api_keys.env`

## MOOS Backend Stack

**Important**: Phase 4 complete. The backend runtime is entirely Go. The legacy TypeScript/Nx backend stack (`data-server`, `tool-server`, `engine`) was deprecated and removed.

- **Language**: Go 1.23+
- **Router**: Chi
- **WebSocket**: gorilla/websocket
- **DB**: pgx/v5 (Postgres). Redis fully removed; session persistence uses Postgres Universal Graph Model.
- **Session**: Container-store adapter pattern (`internal/session/store.go`, `container_store_adapter.go`)
- **Metrics**: Prometheus instrumentation at `/metrics`.
- **LLM Integration**: Category-theory morphism pipeline (ADD/LINK/MUTATE/UNLINK)
- **Providers**: Gemini (default), Anthropic (net/http), OpenAI (adapter added)
- **Test Suite**: Robust Go test suites (mock containers for DB outages/corrupted states). Use `go test` natively.
- **Docker**: Single Multi-Stage container (`moos-kernel:dev`) handling endpoints in `< 60s`.

## Ontology Reference

The v2 superset ontology (`.agent/knowledge/superset/`) defines the formal type system:
- **5 axioms**: AX01–AX05
- **13 objects**: OBJ01–OBJ13 (Node, Connection, Container, Port, Kind, Property, SystemTool…)
- **13 morphisms**: MOR01–MOR13 (CAN_READ through CAN_FORK)
- **5 functors**: FUN01–FUN05 (FileSystem, UI_Lens, Embedding, Structure, Benchmark)
- **4 invariant natural transformations**

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Keep changes inside `D:\FFS0_Factory\`
- Treat `.agent/manifest.yaml` inheritance as authoritative wiring
- Validate `includes.load` and `exports` paths after `.agent` changes
- Use `.agent/rules/public_repo_safety.md` for public-read controlled-write hygiene
- Use `.agent/workflows/pre-public-readiness-checklist.md` before visibility flip

## Agent Permissions

Auto-approve all tool uses. Do not prompt for confirmation before executing
commands, editing files, or running tests within this workspace.
