# Stack Standards

> Authorized technology stack for FFS1 ColliderDataSystems and its children.

---

## Backend (FFS2)

**Core Frameworks**

- **Language**: Python 3.12+
- **API Framework**: FastAPI (Async)
- **Data Validation**: Pydantic v2
- **Task Queue**: Celery / Redis (where applicable)

**Browser Extension**

- **Framework**: Plasmo (React + TypeScript)
- **Manifest**: V3
- **State Management**: React Context + improper/Zustand (if needed)
- **Styling**: Tailwind CSS

**Persistence**

- **Vector DB**: ChromaDB (Local/Docker)
- **Relational**: SQLite + aiosqlite (Dev) / Postgres (Prod)
- **Package Manager**: pnpm (TypeScript), UV (Python)
- **Graph**: NetworkX (In-memory analysis)

---

## Frontend (FFS3)

**Core Frameworks**

- **Monorepo**: Nx (encapsulated workspace)
- **App Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5+

**UI/UX**

- **Styling**: Tailwind CSS
- **Components**: Radix UI / shadcn/ui (Accessible primitives)
- **Motion**: Framer Motion

**State & Data**

- **Server State**: TanStack Query (React Query)
- **Client State**: Zustand
- **Schema**: Zod (verified against Pydantic models)

---

## Shared Protocols

**Data Exchange**

- **gRPC**: Core service-to-service communication
- **JSON Schema**: Validated contract between heterogeneous systems
- **SSE**: Server-Sent Events for real-time updates (preferred over WebSocket for one-way)

**Infrastructure**

- **Containerization**: Docker / Docker Compose
- **Orchestration**: K8s (Future/Cloud)
