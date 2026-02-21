# CLAUDE.md — Collider Data Systems (FFS1)

Refer to the main factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

## FFS1 Context

- **Identity**: Governance, Schemas, and Orchestration layer for the Collider platform.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, UV.
- **Frontend**: Nx monorepo, Vite 7, React 19, TypeScript 5+, pnpm.

## Service Ports

| Service | Port | Path |
| --- | --- | --- |
| ColliderDataServer | 8000 | `FFS2.../ColliderDataServer/` |
| ColliderGraphToolServer | 8001 | `FFS2.../ColliderGraphToolServer/` |
| ColliderVectorDbServer | 8002 | `FFS2.../ColliderVectorDbServer/` |
| SQLite Viewer (dev) | 8003 | `sqlite_web collider.db` |
| ColliderAgentRunner | 8004 | `FFS2.../ColliderAgentRunner/` |
| FFS3 ffs6 frontend | 4200 | `FFS3.../apps/ffs6/` |

## MVP State

The OpenClaw agent is operational. The Chrome extension sidepanel (`ColliderMultiAgentsChromeExtension`) hosts a **WorkspaceBrowser** that lets users compose a **ContextSet** (role + nodes + vector query) and chat with a pydantic-ai agent backed by `claude-sonnet-4-6`.

Key data flow: Extension → `POST :8004/agent/session` → AgentRunner bootstraps nodes via OpenClaw → returns `session_id` → Extension streams chat via `GET :8004/agent/chat?session_id=...`.

## Development

- Run services using `dev-start.md` in `.agent/workflows/`.
- Fill in `D:\FFS0_Factory\secrets\api_keys.env` with `ANTHROPIC_API_KEY`, `COLLIDER_USERNAME`, `COLLIDER_PASSWORD` before starting AgentRunner.
- Seed the DB: `uv run python seed.py` from `ColliderDataServer/`.
- Schemas shared from root `models/`.
- Keep `pnpm-lock.yaml` up to date.

## Architecture Docs

See `.agent/knowledge/architecture/` for detailed service docs:

- `01_ffs2_backend_services.md` — all four backend services including AgentRunner
- `02_ffs2_chrome_extension.md` — extension message passing + WorkspaceBrowser
- `03_ffs3_frontend_appnodes.md` — Nx appnodes (ffs4/ffs5/ffs6)
- `04_communication_protocols.md` — protocol stack
