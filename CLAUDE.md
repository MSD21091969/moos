# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Context System

Use the rehydrated minimal `.agent` chain as canonical context wiring.

Read order:
1. `D:\FFS0_Factory\CLAUDE.md`
2. Workspace `CLAUDE.md`
3. Workspace `.agent/index.md`
4. Workspace `.agent/manifest.yaml` (`includes`/`exports`)

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

- **Language**: Go 1.23+
- **Router**: Chi
- **WebSocket**: gorilla/websocket
- **DB**: pgx/v5 (Postgres), go-redis/v9
- **LLM Integration**: Category-theory morphism pipeline (ADD/LINK/MUTATE/UNLINK)
- **Providers**: Gemini (default), Anthropic (net/http), OpenAI (planned)
- **Test Suite**: 46 Go tests (94% model coverage), 22 vitest frontend tests

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
