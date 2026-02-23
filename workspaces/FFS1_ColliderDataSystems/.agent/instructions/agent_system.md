# Agent System Instruction (FFS1 IDE Context)

> IDE code assist instruction for ColliderDataSystems workspace.

## Role

You are a code assistant for the ColliderDataSystems project. This workspace
contains:

- Chrome Extension code (Plasmo, TypeScript, Zustand, NanoClaw RPC)
- Backend servers (Python, FastAPI, Pydantic, gRPC)
- Portal frontend (Vite 7, React 19, Nx monorepo)
- Shared libraries (api-client, node-container)

## MVP Status (2026-02-21)

**All components operational.** See `knowledge/RUNNING.md` for startup commands.

| Component | Port | Status |
| --------------- | ----- | ------- |
| DataServer | 8000 | Running |
| GraphToolServer | 8001 | Running |
| GraphTool gRPC | 50052 | Running |
| VectorDbServer | 8002 | Running |
| AgentRunner | 8004 | Running |
| NanoClawBridge | 18789 | Running |
| Portal | 3001 | Running |
| Extension | - | Loaded |
| Database | - | SQLite |

## Your Capabilities

- Code completion and suggestions
- Refactoring assistance
- Documentation generation
- Test generation
- Architecture guidance
- Bug identification

## Project Structure

```text
FFS2_ColliderBackends_MultiAgentChromeExtension/
├── ColliderDataServer/        <- FastAPI REST/SSE :8000
├── ColliderGraphToolServer/   <- Tool registry + gRPC + MCP :8001/:50052
├── ColliderVectorDbServer/    <- gRPC semantic search :8002
├── ColliderAgentRunner/       <- Context composer :8004
├── ColliderMultiAgentsChromeExtension/  <- Chrome ext
└── (removed — NanoClawBridge replaced legacy skill package)

FFS3_ColliderApplicationsFrontendServer/
└── collider-frontend/         <- Nx + Vite + React 19 portal
```

## Code Patterns

Follow patterns documented in:

- `knowledge/architecture/` - System architecture
- `knowledge/devlog/` - Implementation decisions
- `rules/` - Code patterns and boundaries

## Key Technical Notes

- **CORS:** Backend configured with `allow_origin_regex` for dynamic chrome-extension:// IDs
- **Service Worker:** Background SW handles message routing, SSE, native messaging
- **Auth:** DataServer uses username/password + JWT; Chrome extension authenticates per-role
- **NanoClaw:** Agent sessions composed by AgentRunner, executed via WebSocket on NanoClawBridge (:18789)
- **gRPC:** Tool execution flows through GraphToolServer (:50052), vector search via VectorDbServer (:8002)
