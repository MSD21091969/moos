# Stack Standards

## Backend (MOOS)

- **Language**: Go 1.23+
- **Router**: Chi
- **WebSocket**: gorilla/websocket
- **DB**: pgx/v5 (Postgres), go-redis/v9
- **LLM Pipeline**: Category-theory morphism pipeline (ADD/LINK/MUTATE/UNLINK)
- **Providers**: Gemini (default), Anthropic (net/http), OpenAI (planned)
- **Apps**: `data-server` (:8000), `tool-server` (:8001), `engine` (lib), MCP/SSE (:8080)

## Frontend (FFS3)

- **Framework**: Nx 22, Vite 7, React 19, TypeScript 5.9
- **Styling**: TailwindCSS 4, CSS Modules
- **State**: Zustand (morphism-driven stores)
- **Graph**: @xyflow/react
- **Testing**: Vitest 4 (jsdom)

## Ports Contract

| Port  | Service |
| ----- | ------- |
| 8000  | MOOS Data Compatibility |
| 8001  | MOOS Tool Server |
| 8004  | MOOS Agent Compatibility |
| 8080  | MOOS MCP/SSE |
| 18789 | NanoClaw WebSocket Bridge |
| 4200  | FFS6 IDE Viewer |
| 4201  | FFS4 Sidepanel |
| 4202  | FFS5 PiP |
