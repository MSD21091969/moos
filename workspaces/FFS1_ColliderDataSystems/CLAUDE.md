# CLAUDE.md — Collider Data Systems (FFS1)

Refer to the main factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

## FFS1 Context

- **Identity**: Governance, Schemas, and Orchestration layer for the Collider platform.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, UV.
- **Frontend**: Nx monorepo, Vite 7, React 19, TypeScript 5+, pnpm.
- **.agent state**: Minimal rehydrated inheritance backbone for FFS2/FFS3.

## Runtime Status (2026-03-02)

- **Active backend runtime for FFS3**: `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos`
- **FFS2 backend folders** under
  `FFS2_ColliderBackends_MultiAgentChromeExtension/` are **reference-only** for
  contract parity and historical context.
- FFS3 client behavior remains unchanged and is served by MOOS compatibility
  surfaces.

## Canonical References

- Root authority: `D:\FFS0_Factory\CLAUDE.md`
- Rehydration runbook: `D:\FFS0_Factory\.agent\workflows\conversation-state-rehydration.md`
- FFS1 context index: `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\index.md`

## Package Management & Secrets

- **Lockfile Authority**: The FFS1 root `pnpm-lock.yaml` is canonical. FFS3 is
  a workspace member. Always run `pnpm install` from this root.
- **Secrets**: Store active API keys in
  `D:\FFS0_Factory\secrets\api_keys.env`. Local `.env` files should only
  contain non-sensitive overrides and are untracked. Rotate any keys previously
  committed to untracked files if the environment is shared.

## Service Ports

### Active (MOOS-owned)

| Service                     | Port  | Path                                                                                                                        |
| --------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------- |
| MOOS Data Compatibility     | 8000  | `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\apps\data-server` |
| MOOS Tool Server            | 8001  | `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\apps\tool-server` |
| MOOS Engine                 | app   | `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\apps\engine`      |
| MOOS Agent Compatibility    | 8004  | `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\apps\data-server` |
| MOOS NanoClaw Compatibility | 18789 | `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\apps\data-server` |
| FFS3 ffs6 frontend          | 4200  | `FFS3.../apps/ffs6/`                                                                                                        |
| FFS3 ffs4 sidepanel         | 4201  | `FFS3.../apps/ffs4/`                                                                                                        |

### Legacy Reference (FFS2 — retired runtime)

| Service                 | Port         | Path                               |
| ----------------------- | ------------ | ---------------------------------- |
| ColliderDataServer      | 8000         | `FFS2.../ColliderDataServer/`      |
| ColliderGraphToolServer | 8001 / 50052 | `FFS2.../ColliderGraphToolServer/` |
| ColliderVectorDbServer  | 8002         | `FFS2.../ColliderVectorDbServer/`  |
| SQLite Viewer (dev)     | 8003         | `sqlite_web collider.db`           |
| ColliderAgentRunner     | 8004 / 50051 | `FFS2.../ColliderAgentRunner/`     |
| NanoClawBridge          | 18789        | Claude Code WebSocket agent chat   |

## Context Delivery Architecture

MOOS compatibility runtime is the active path for FFS3:

- `:8000` data/API compatibility
- `:8004` agent-session compatibility
- `:18789` NanoClaw-compatible WebSocket bridge

## FFS4 Sidepanel Architecture

FFS4 (`localhost:4201`) is the XYFlow graph workspace browser + agent chat. Chrome extension embeds FFS4 via iframe in the `agent` view tab.

```text
FFS4/src/
├── stores/          # Zustand: graphStore, sessionStore, contextStore
├── components/
│   ├── graph/       # WorkspaceGraph (ReactFlow), NodeCard (custom node)
│   └── agent/       # AgentChat, TeamPanel
├── hooks/           # useGraphData (tree -> XYFlow conversion)
├── lib/             # api.ts (REST), nanoclaw-client.ts (WebSocket RPC)
└── app/app.tsx      # Toolbar + graph (60%) + chat (40%) layout
```

## Development

- Run services using `dev-start.md` in `.agent/workflows/`.
- Use MOOS root compatibility targets from `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos`:
  - `pnpm nx run @moos/source:compat:build`
  - `pnpm nx run @moos/source:compat:test`
  - `pnpm nx run @moos/source:compat:serve:backend`
- Schemas shared from root `models/`.

## Minimal .agent Contract

FFS1 is the inheritance provider for FFS2 and FFS3.

Required FFS1 exports (see `.agent/manifest.yaml`):
- `instructions/agent_system.md`
- `instructions/filesyst_domain.md`
- `skills/ide_code_assist.md`
- `tools/filesyst_tools.json`
- `rules/stack_standards.md`
- `rules/communication_architecture.md`
- `rules/code_quality.md`
- `rules/project_structure.md`
- `workflows/cross-service-validation-gates.md`
- `workflows/dev-start.md`
- `workflows/markdown-quality.md`
- `workflows/markdown-quality-all.md`
