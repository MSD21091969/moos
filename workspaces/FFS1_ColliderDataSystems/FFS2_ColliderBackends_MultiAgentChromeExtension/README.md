# Collider MVP - Startup Scripts

## Prerequisites

1. PostgreSQL running on localhost:5432
2. Create database: `createdb collider`
3. Node.js 20+ and pnpm installed
4. Python 3.11+ with uv installed

## Quick Start

### 1. Install Dependencies

```powershell
# Backend servers
cd ColliderDataServer && uv sync && cd ..
cd ColliderGraphToolServer && uv sync && cd ..
cd ColliderVectorDbServer && uv sync && cd ..

# Chrome Extension
cd ColliderMultiAgentsChromeExtension && pnpm install && cd ..
```

### 2. Start Servers (3 terminals)

```powershell
# Terminal 1: Data Server
cd ColliderDataServer
uv run python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: VectorDB Server
cd ColliderVectorDbServer
uv run python -m uvicorn src.main:app --reload --port 8002

# Terminal 3: GraphTool Server
cd ColliderGraphToolServer
uv run python -m uvicorn src.main:app --reload --port 8001
```

### 3. Seed Database

```powershell
cd ColliderDataServer
uv run python -m src.seed
```

### 4. Start Chrome Extension

```powershell
cd ColliderMultiAgentsChromeExtension
pnpm dev
```

Then load `build/chrome-mv3-dev` in Chrome (chrome://extensions → Load unpacked)

## Health Checks

- Data Server: http://localhost:8000/health
- GraphTool: http://localhost:8001/health
- VectorDB: http://localhost:8002/health

## Test API

```bash
# List apps
curl http://localhost:8000/api/v1/apps

# Get node
curl "http://localhost:8000/api/v1/apps/application1/nodes?path=/"

# Search (VectorDB)
curl -X POST http://localhost:8002/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "dashboard", "n_results": 5}'
```
