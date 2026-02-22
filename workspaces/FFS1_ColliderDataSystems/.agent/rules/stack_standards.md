---
description: Authorized technology stack — Python/FastAPI (FFS2), Nx/Vite/React 19 (FFS3), ChromaDB, aiosqlite, Plasmo extension, NanoClaw
activation: always
---

# Stack Standards

> Authorized technology stack for FFS1 ColliderDataSystems and its children.

---

## Backend (FFS2)

**Core Frameworks**

- **Language**: Python 3.12+
- **API Framework**: FastAPI (Async)
- **Data Validation**: Pydantic v2
- **AI Agent**: pydantic-ai (ColliderAgentRunner)
- **gRPC**: grpcio / grpcio-tools (tool execution, vector search)

**Browser Extension**

- **Framework**: Plasmo (React + TypeScript)
- **Manifest**: V3
- **State Management**: Zustand (appStore)
- **Styling**: Tailwind CSS
- **Agent Protocol**: NanoClaw WebSocket (nanoclaw-rpc.ts)

**Persistence**

- **Vector DB**: ChromaDB (Local/Docker)
- **Relational**: SQLite + aiosqlite
- **Package Manager**: pnpm (TypeScript), UV (Python)
- **Graph**: NetworkX (In-memory analysis)

---

## Frontend (FFS3)

**Core Frameworks**

- **Monorepo**: Nx (encapsulated workspace)
- **App Framework**: Vite 7
- **UI Library**: React 19
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

- **gRPC**: Service-to-service communication (live on :50052, :8002)
- **WebSocket**: NanoClawBridge agent communication (:18789)
- **REST**: Client ↔ server APIs (DataServer :8000, AgentRunner :8004)
- **MCP/SSE**: IDE tool access (GraphToolServer)
- **SSE**: Server-Sent Events for real-time data updates
- **JSON Schema**: Validated contract between heterogeneous systems

**Infrastructure**

- **Containerization**: Docker / Docker Compose
- **Orchestration**: K8s (Future/Cloud)
