# Communication Architecture

## Active Service Endpoints

- FFS3 to backend data API via `:8000` (REST).
- Agent session compatibility via `:8004` (REST).
- WebSocket bridge (morphism push + NanoClaw RPC) via `:18789`.
- MCP/SSE endpoint via `:8080`.
- Tool server via `:8001` (internal tool execution).

## Data Flow

- LLM providers return morphism envelopes → MOOS parses → dispatches to graph DB.
- Morphisms are pushed to connected frontends via WebSocket at `:18789`.
- Frontend Zustand stores apply morphisms reactively → XYFlow renders.
