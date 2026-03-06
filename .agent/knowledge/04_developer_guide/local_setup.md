# Local Setup

## Machine as Semantic Functor

Your development machine is a functor from the abstract mo:os category to a
physical execution environment:

```
F_local : (containers, wires) → (processes, ports, files)
```

| Abstract (Graph)    | Physical (Machine)                          |
| ------------------- | ------------------------------------------- |
| Container URN       | Docker container or host process            |
| Wire                | Network connection (port mapping)           |
| state_payload       | Config file, environment variable, DB row   |
| morphism_log        | Postgres table in docker volume             |
| Workspace container | Directory on disk (e.g., `D:\FFS0_Factory`) |

## Prerequisites

- **OS**: Windows 11 (development), Linux (Docker containers)
- **Go**: 1.23+ (kernel development)
- **Node/pnpm**: Node 20+, pnpm 9+ (FFS3 frontend)
- **Docker**: Docker Desktop with WSL2 backend
- **Postgres**: Via Docker (postgres:16-alpine)
- **Git**: For version control of functorial code (separated from metadata)

## Docker Compose Stack

From `moos/docker-compose.dev.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    # Graph truth lives here

  moos-kernel:
    build: .
    ports:
      - "8000:8000"    # Data compatibility (REST API)
      - "8001:8001"    # Tool server
      - "8004:8004"    # Agent compatibility
      - "8080:8080"    # MCP/SSE endpoint
      - "18789:18789"  # NanoClaw WebSocket bridge
```

## Startup Sequence

```bash
# 1. Start Postgres (graph truth)
cd workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos
docker compose -f docker-compose.dev.yml up -d postgres

# 2. Start MOOS kernel (morphism executor)
docker compose -f docker-compose.dev.yml up -d moos-kernel
# Or for development: go run ./cmd/server

# 3. Start frontend (UI_Lens functor)
cd ../../FFS3_ColliderApplicationsFrontendServer
pnpm install    # from FFS1 root (lockfile authority)
pnpm nx serve ffs6   # IDE viewer on :4200
pnpm nx serve ffs4   # Sidepanel on :4201
pnpm nx serve ffs5   # PiP on :4202
```

## Port Map

| Port  | Service            | Graph Role                     |
| ----- | ------------------ | ------------------------------ |
| 5432  | Postgres           | Graph truth (containers+wires) |
| 8000  | MOOS Data API      | Protocol functor (REST)        |
| 8001  | MOOS Tool Server   | Tool morphism dispatch         |
| 8004  | MOOS Agent API     | Agent session morphisms        |
| 8080  | MOOS MCP/SSE       | MCP protocol functor           |
| 18789 | NanoClaw WS Bridge | Protocol functor (WebSocket)   |
| 4200  | FFS6 IDE Viewer    | UI_Lens functor                |
| 4201  | FFS4 Sidepanel     | UI_Lens functor (graph view)   |
| 4202  | FFS5 PiP           | UI_Lens functor (minimal)      |

## Environment Variables

Create `.env` in the MOOS root (not tracked in git — code separated from config):

```env
DATABASE_URL=postgres://moos:moos@localhost:5432/moos?sslmode=disable
GEMINI_API_KEY=...        # LLM provider (default)
ANTHROPIC_API_KEY=...     # LLM provider (alternate)
```

API keys stored in `D:\FFS0_Factory\secrets\api_keys.env` (gitignored).