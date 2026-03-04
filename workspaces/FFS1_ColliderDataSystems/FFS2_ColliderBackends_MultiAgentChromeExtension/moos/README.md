# mo:os - Universal Graph Runtime

`mo:os` is an advanced AI OS layer that treats all application state, model events, and tooling interactions as Universal Graph objects via a strict Morphism pipeline (ADD/MUTATE/URLINK/LINK).

## Architecture

After Phase 4 alignment, `mo:os` leverages a persistent dual-stack setup:
- **Go Kernel**: Core persistent engine, event-loop daemon, morphism executor, and REST/WebSocket bridge.
- **Frontend Surface Apps**: FFS4, FFS5, FFS6 (React, Tailwind, Zustand) powered by Vite.
- **PostgreSQL**: Unified Universal Graph database. 

## Getting Started (for New Developers in < 15 Min)

### 1. Prerequisites
- Docker Engine & `docker-compose`
- Git

### 2. Stand Up Default Daemon
Run the system natively using the Docker sandbox from the `moos` directory:
```bash
docker compose -f docker-compose.dev.yml up -d
```
*Expected: The Go APIs, UI Servers, and Postgres instance will boot cleanly in < 60 seconds.*

### 3. Verify System Health
Check that the unified nodes are reporting functional status:
- REST API (Kernel): `http://127.0.0.1:8000/health`
- Go Metrics: `http://127.0.0.1:8000/metrics`
- UI Sandbox (FFS6): `http://127.0.0.1:4200`

### 4. Running Kernels Locally (Without Full Stack Docker)
If you wish to do backend Go engine development independently:
```bash
export MOOS_BEARER_TOKEN="dev-token"
export ENFORCE_DEBUG="true"
go run ./cmd/kernel
```

## Running the Test Suites

To execute unit and structural integration tests for the backend pipeline:
```bash
go test ./... -v
```

## Packages 
- `cmd/kernel`: The primary endpoint daemon 
- `internal/container`: Postgres Database structure interactions
- `internal/session`: URN / Message event loops tracking contexts
- `internal/morphism`: Universal Object modification execution
- `internal/tool`: MCP protocol interfaces natively executed via JSON

*(Node.js abstractions successfully evicted in Phase 4 setup).*
