# FFS3 Codebase Knowledge

## Stack

- **Framework**: Nx 22, Vite 7, React 19, TypeScript 5.9
- **State**: Zustand (graphStore, sessionStore, contextStore)
- **Graph Viz**: @xyflow/react (XYFlow)
- **Styling**: TailwindCSS 4, CSS Modules
- **Testing**: Vitest 4, jsdom environment
- **Package Manager**: pnpm (lockfile in FFS1 root)

## Applications

| App  | Port | Purpose                                                 |
| ---- | ---- | ------------------------------------------------------- |
| ffs6 | 4200 | IDE Viewer — full-screen workspace graph + detail views |
| ffs4 | 4201 | Chrome Extension Sidepanel — agent chat + compact graph |
| ffs5 | 4202 | Picture-in-Picture — minimal floating agent UI          |

## Backend Dependencies

- **Data API** → `http://localhost:8000` (MOOS data-server)
- **Agent Runner** → `http://localhost:8004` (MOOS agent compat)
- **WebSocket** → `ws://localhost:18789` (NanoClaw WS bridge, morphism push)

## Required Environment Variables

- `VITE_DATA_SERVER_URL` — e.g. `http://localhost:8000`
- `VITE_AGENT_RUNNER_URL` — e.g. `http://localhost:8004`

## Architecture Patterns

- **Morphism-driven state**: Backend pushes category-theory morphisms (ADD, LINK, MUTATE, UNLINK) via WebSocket. Frontend applies them to Zustand store → XYFlow reactively renders.
- **No REST polling**: Graph updates arrive as live WebSocket events.
- **Store-first**: All UI state flows through Zustand stores. Components subscribe to slices.
- **Nx workspace**: Shared code in `libs/shared-ui`. Each app has its own `project.json`, `vite.config.mts`.

## Key Files (ffs4 as reference)

```
ffs4/src/
├── stores/graphStore.ts       # Zustand: applyMorphisms(), setActiveState(), reset()
├── stores/graphStore.spec.ts  # 22 vitest tests (all morphism types + edge cases)
├── components/graph/          # WorkspaceGraph.tsx (XYFlow + WebSocket)
├── components/agent/          # AgentChat, TeamPanel
├── hooks/useGraphData.ts      # Tree → XYFlow node/edge conversion
├── lib/api.ts                 # REST client
├── lib/nanoclaw-client.ts     # WebSocket RPC client
└── app/app.tsx                # Layout: toolbar + graph (60%) + chat (40%)
```
