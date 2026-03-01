# CLAUDE.md — Collider Data Systems (FFS1)

Refer to the main factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

## FFS1 Context

- **Identity**: Governance, Schemas, and Orchestration layer for the Collider platform.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, UV.
- **Frontend**: Nx monorepo, Vite 7, React 19, TypeScript 5+, pnpm.

## Canonical References

- Root authority: `D:\FFS0_Factory\CLAUDE.md`
- Rehydration runbook: `D:\FFS0_Factory\.agent\workflows\conversation-state-rehydration.md`

## Package Management & Secrets

- **Lockfile Authority**: The FFS1 root `pnpm-lock.yaml` is canonical. FFS3 is
  a workspace member. Always run `pnpm install` from this root.
- **Secrets**: Store active API keys in
  `D:\FFS0_Factory\secrets\api_keys.env`. Local `.env` files should only
  contain non-sensitive overrides and are untracked. Rotate any keys previously
  committed to untracked files if the environment is shared.

## Service Ports

| Service                 | Port         | Path                               |
| ----------------------- | ------------ | ---------------------------------- |
| ColliderDataServer      | 8000         | `FFS2.../ColliderDataServer/`      |
| ColliderGraphToolServer | 8001 / 50052 | `FFS2.../ColliderGraphToolServer/` |
| ColliderVectorDbServer  | 8002         | `FFS2.../ColliderVectorDbServer/`  |
| SQLite Viewer (dev)     | 8003         | `sqlite_web collider.db`           |
| ColliderAgentRunner     | 8004 / 50051 | `FFS2.../ColliderAgentRunner/`     |
| NanoClawBridge          | 18789        | Claude Code WebSocket agent chat   |
| FFS3 ffs6 frontend      | 4200         | `FFS3.../apps/ffs6/`               |
| FFS3 ffs4 sidepanel     | 4201         | `FFS3.../apps/ffs4/`               |

## Context Delivery Architecture

NanoClawBridge supports **two context delivery modes**, controlled by
environment flags:

### Mode 1: Filesystem (Legacy — `USE_SDK_AGENT=false`)

```text
Extension -> POST :8004/agent/session -> AgentRunner composes ContextSet
  -> workspace_writer writes CLAUDE.md + .mcp.json + skills/*.SKILL.md
  -> returns session_id + nanoclaw_ws_url
  -> NanoClawBridge spawns Claude Code CLI with workspace context
```

### Mode 2: SDK + gRPC (New — `USE_SDK_AGENT=true`, `USE_GRPC_CONTEXT=true`)

```text
Extension/FFS4 -> POST :8004/agent/session -> AgentRunner composes ContextSet
  -> NanoClawBridge requests context via gRPC GetBootstrap (:50051)
  -> AgentRunner streams ContextChunks (system prompt, skills, tool schemas, MCP config)
  -> NanoClawBridge creates Anthropic SDK session programmatically
  -> Skills injected as JSON (no SKILL.md files), tools via MCP SSE
  -> SSE subscription for live context deltas (hot-reload mid-session)
```

### Environment Flags

```env
# NanoClawBridge
USE_SDK_AGENT=true              # SDK instead of CLI spawn
USE_GRPC_CONTEXT=true           # gRPC context instead of filesystem
GRPC_CONTEXT_ADDRESS=localhost:50051

# AgentRunner
GRPC_CONTEXT_ENABLED=true       # Start gRPC ColliderContext server
GRPC_PORT=50051
WRITE_WORKSPACE_FILES=false     # Skip file writes when gRPC active
```

## Agent Teams

When multiple nodes are selected in the FFS4 graph, NanoClawBridge can spawn an
**agent team**:

- **Leader** gets merged context from all selected nodes
- **Members** each get isolated per-node context
- Communication via mailbox pattern
- Team RPCs: `team.create`, `team.send`, `team.status`

## NanoClawBridge SDK Modules

```text
NanoClawBridge/src/
├── sdk/
│   ├── types.ts            # ComposedContext, SkillDefinition, ContextDelta
│   ├── prompt-builder.ts   # buildSystemPrompt(), applyDeltaToContext()
│   ├── tool-executor.ts    # ToolExecutor (routes to MCP/DataServer)
│   ├── anthropic-agent.ts  # AnthropicAgent (streaming agentic loop)
│   └── team-manager.ts     # TeamManager (multi-node orchestration)
├── grpc/
│   └── context-client.ts   # ContextGrpcClient (getBootstrap, streamContext)
└── sse/
    └── context-subscriber.ts # ContextSubscriber (live delta watcher)
```

## gRPC Proto (ColliderContext Service)

Defined in `proto/collider_graph.proto`. Compile: `uv run python -m proto.compile_protos`

| RPC                    | Input             | Output              |
| ---------------------- | ----------------- | ------------------- |
| StreamContext          | ContextRequest    | stream ContextChunk |
| GetBootstrap           | ContextRequest    | BootstrapResponse   |
| SubscribeContextDeltas | DeltaSubscription | stream ContextDelta |

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
- Fill in `D:\FFS0_Factory\secrets\api_keys.env` with `GEMINI_API_KEY`, `COLLIDER_USERNAME`, `COLLIDER_PASSWORD` before starting AgentRunner.
- Seed the DB: `uv run python -m src.seed` from `ColliderDataServer/`.
- Schemas shared from root `models/`.

## Architecture Docs

See `.agent/knowledge/architecture/` for detailed service docs:

- `01_ffs2_backend_services.md` — all backend services including AgentRunner
- `02_ffs2_chrome_extension.md` — extension 3-tab sidepanel + NanoClawBridge RPC
- `03_ffs3_frontend_appnodes.md` — Nx appnodes (ffs4/ffs5/ffs6)
- `04_communication_protocols.md` — all 10 protocols
