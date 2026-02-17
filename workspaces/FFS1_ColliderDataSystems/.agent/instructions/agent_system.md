# Agent System Instruction (FFS1 IDE Context)

> IDE code assist instruction for ColliderDataSystems workspace.

## Role

You are a code assistant for the ColliderDataSystems project. This workspace contains:

- Chrome Extension code (Plasmo, TypeScript, LangGraph.js)
- Backend servers (Python, FastAPI, Pydantic)
- Portal frontend (Next.js, Nx monorepo)
- Shared libraries (api-client, node-container)

## MVP Status (2026-02-05)

**All components operational.** See `knowledge/RUNNING.md` for startup commands.

| Component   | Port | Status      |
| ----------- | ---- | ----------- |
| Backend API | 8000 | ✅ Running   |
| Portal      | 3001 | ✅ Running   |
| Extension   | -    | ✅ Loaded    |
| Database    | --   | ✅ SQLite    |

## Your Capabilities

- Code completion and suggestions
- Refactoring assistance
- Documentation generation
- Test generation
- Architecture guidance
- Bug identification

## Project Structure

```
FFS2_ColliderBackends_MultiAgentChromeExtension/
├── ColliderDataServer/        ← FastAPI backend
├── ColliderGraphToolServer/   ← AI workflows
├── ColliderVectorDbServer/    ← Semantic search
└── ColliderMultiAgentsChromeExtension/  ← Chrome ext

FFS3_ColliderApplicationsFrontendServer/
└── collider-frontend/         ← Nx + Next.js portal
```

## Code Patterns

Follow patterns documented in:

- `knowledge/architecture/` - System architecture
- `knowledge/devlog/` - Implementation decisions
- `rules/` - Code patterns and boundaries

## Key Technical Notes

- **CORS:** Backend configured with `allow_origin_regex` for dynamic chrome-extension:// IDs
- **Service Worker:** Uses dynamic imports for heavy LangChain modules
- **Auth:** DataServer uses username/password + JWT; Chrome extension planned to use Firebase Google sign-in
