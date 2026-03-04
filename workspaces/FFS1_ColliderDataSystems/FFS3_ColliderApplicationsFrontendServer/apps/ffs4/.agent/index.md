# ffs4 Agent Context — Sidepanel

Chrome Extension sidepanel app embedded via iframe in the `agent` view tab.

## Architecture

- **Layout**: Toolbar + graph canvas (60%) + agent chat panel (40%)
- **State**: Zustand stores (graphStore, sessionStore, contextStore)
- **Graph**: XYFlow with custom NodeCard nodes, WebSocket-driven updates
- **Chat**: NanoClaw WebSocket RPC at `:18789`
- **Data**: REST API at `:8000`, Agent API at `:8004`

## Key Stores

- `graphStore` — Morphism-driven (ADD/LINK/MUTATE/UNLINK), 22 vitest tests
- `sessionStore` — Agent session lifecycle
- `contextStore` — Active context tracking

Inherits from FFS3 workspace `.agent`.
