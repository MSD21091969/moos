---
description: Start all Collider services for local development (DataServer, GraphToolServer, VectorDbServer, frontend)
---

# Start Dev Environment

Starts all FFS1 services in the correct order for local development.

## Steps

1. Start the ColliderDataServer (REST/SSE API on :8000):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
   uv run uvicorn src.main:app --reload --port 8000
   ```

2. Start the ColliderGraphToolServer (WebSocket on :8001):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderGraphToolServer
   uv run uvicorn src.main:app --reload --port 8001
   ```

3. Start the ColliderVectorDbServer (Vector search on :8002):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderVectorDbServer
   uv run uvicorn src.main:app --reload --port 8002
   ```

4. Start the FFS3 frontend dev server (ffs6 default on :4200):
   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer
   pnpm nx serve ffs6
   ```

## Verify

- DataServer: http://localhost:8000/docs
- GraphToolServer: http://localhost:8001/docs
- VectorDbServer: http://localhost:8002/docs
- Frontend (ffs6): http://localhost:4200
