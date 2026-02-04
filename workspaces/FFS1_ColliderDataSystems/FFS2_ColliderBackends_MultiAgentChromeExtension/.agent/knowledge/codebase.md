# Codebase: FFS2 ColliderBackends

> Backend services and Chrome Extension source.

## Structure

```
FFS2_ColliderBackends/
├── ColliderDataServer/              ← FastAPI Data Server
│   ├── main.py
│   ├── api/routes/
│   └── core/config.py
│
├── ColliderGraphToolServer/         ← LangGraph.js / Python Runtime
│   ├── server.py
│   └── graphs/
│
├── ColliderVectorDbServer/          ← Vector embeddings (Qdrant/Chroma)
│
└── ColliderMultiAgentsChromeExtension/ ← Plasmo Source
    ├── assets/
    ├── background/ (Service Worker)
    ├── contents/ (Content Scripts)
    ├── sidepanel/
    └── popup/
```

## Developer Guide

### Running Services

**ALWAYS** use the `dev.ps1` script in the root `FFS0_Factory`.

- `.\dev.ps1 -BackendOnly` to start Data & Graph servers.

### Chrome Extension Development

1. `cd ColliderMultiAgentsChromeExtension`
2. `pnpm dev` or `npm run dev`
3. Load `build/chrome-mv3-dev` in `chrome://extensions`

### Key Patterns

- **Native Host**: The Extension uses `native_messaging` to talk to the local python host (in `scripts/`).
- **SSE**: Data updates flow via Server-Sent Events from `DataServer/api/v1/sse`.
