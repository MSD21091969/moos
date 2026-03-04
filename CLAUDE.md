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
├── sdk/                                  Seeder + runtime support utilities
└── workspaces/
    ├── FFS1_ColliderDataSystems/         Governance + shared contracts
    │   ├── FFS2_...ChromeExtension/
    │   │   └── moos/                     Active backend compatibility runtime
    │   └── FFS3_...FrontendServer/       Nx frontend workspace (ffs4/ffs5/ffs6)
    └── maassen_hochrath/
```

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

**Important**: We are heavily in Phase 4 now. The backend runtime is entirely Go. The legacy TypeScript/Nx backend stack (`data-server`, `tool-server`, `engine`) was deprecated and removed.

- **Language**: Go 1.23+
- **Router**: Chi
- **WebSocket**: gorilla/websocket
- **DB**: pgx/v5 (Postgres). Note: Redis is deprecated for session management; session persistence relies entirely on Postgres Universal Graph Model.
- **Metrics**: Prometheus instrumentation at `/metrics`.
- **LLM Integration**: Category-theory morphism pipeline (ADD/LINK/MUTATE/UNLINK)
- **Providers**: Gemini (default), Anthropic (net/http), OpenAI (planned)
- **Test Suite**: Robust Go test suites (incorporating mock containers for DB outages/corrupted states). Use native `go test` rather than TS counterparts.
- **Docker**: Single Multi-Stage container (`moos-kernel:dev`) handling endpoints in `< 60s`.

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
