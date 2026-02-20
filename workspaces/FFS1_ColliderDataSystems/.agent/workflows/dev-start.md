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
   uv run python -m src.main
   ```

4. Start the FFS3 frontend dev server (ffs6 default on :4200):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer
   pnpm nx serve ffs6
   ```

5. Start SQLite Web Viewer (on :8003):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
   uv run sqlite_web collider.db -p 8003 -H 0.0.0.0
   ```

6. Connect Claude Code to the Collider MCP server (once GraphToolServer is running on :8001):

   ```powershell
   claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse
   ```

   Then `claude mcp list` to verify. All group/global-visibility tools in the GraphToolServer
   registry appear as native tools in Claude Code.

## Verify

- DataServer: http://localhost:8000/docs
- GraphToolServer: http://localhost:8001/docs (+ MCP at /mcp/sse)
- VectorDbServer: http://localhost:8002/docs
- SQL Viewer: http://localhost:8003
- Frontend (ffs6): http://localhost:4200
- Claude Code MCP: `claude mcp list` → collider-tools
