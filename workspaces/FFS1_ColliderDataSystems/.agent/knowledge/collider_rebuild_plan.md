# Rebuild Collider Application from Scratch

## Table of Contents

- [Executive Summary](#executive-summary)
- [Choose Your Path](#choose-your-path)
- [Prerequisites & Setup](#prerequisites--setup)
- [Technology Stack](#technology-stack)
- [Critical Understanding: FFS4-8 .agent Folders](#critical-understanding-ffs4-8-agent-folders)
- [Three Domains Architecture](#three-domains-architecture)
- [Rebuild Scope](#rebuild-scope)
- [Phase 0: Foundation Setup](#phase-0-foundation-setup)
- [Phase 1: ColliderDataServer Foundation](#phase-1-colliderdataserver-foundation)
- [Phase 2: ColliderGraphToolServer & ColliderVectorDbServer](#phase-2-collidergraphtoolserver--collidervectordbserver)
- [Phase 3: ColliderMultiAgentsChromeExtension](#phase-3-collidermultiagentschromeextension)
- [Phase 4: Frontend Monorepo (Nx/Next.js)](#phase-4-frontend-monorepo-nxnextjs)
- [Phase 5: Integration & End-to-End Verification](#phase-5-integration--end-to-end-verification)
- [Build Automation & Scripts](#build-automation--scripts)
- [Testing Strategy](#testing-strategy)
- [CI/CD Pipeline](#cicd-pipeline)
- [Critical Architectural Considerations](#critical-architectural-considerations)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Quick Reference Commands](#quick-reference-commands)
- [Glossary](#glossary)
- [Success Criteria](#success-criteria)

---

## Executive Summary

Rebuild all components of the Collider application (FFS2 backend services, FFS2 Chrome Extension, and FFS3 frontend monorepo) from scratch, properly aligned with the .agent architecture and the Three Domains pattern.

---

## Choose Your Path

### Path A: MVP-First (Recommended for New Users)

**Goal**: Get a working system quickly with minimal components

**Best for**: Testing concepts, learning architecture, validating ideas

**Quick Steps:**
1. Backend: DataServer only (skip GraphTool/VectorDB initially)
2. Minimal database schema (Users, Apps, Nodes)
3. Chrome Extension: Basic sidepanel only (no agents)
4. Frontend: Single Next.js page (skip Nx initially)

**Follow this path:**
1. [Phase 0: Foundation Setup](#phase-0-foundation-setup) - Full
2. [Phase 1: ColliderDataServer](#phase-1-colliderdataserver-foundation) - Sections 1.1-1.4 only
3. [Phase 3: Chrome Extension](#phase-3-collidermultiagentschromeextension) - Section 3.3 (Sidepanel) only
4. [Phase 4: Frontend](#phase-4-frontend-monorepo-nxnextjs) - Section 4.4 (Portal) only

**MVP Exit Criteria:**
- [ ] DataServer running on port 8000
- [ ] Database seeded with 4 applications
- [ ] Sidepanel displays app list from DataServer
- [ ] Portal page renders applications

### Path B: Full Production Rebuild

**Goal**: Complete, production-ready system with all services

**Best for**: Production deployments, full feature set

**Follow all phases sequentially:** Phase 0 through Phase 5.

---

## Prerequisites & Setup

### Prerequisites Matrix

| Component  | Required | Version | Installation                             | Verification       |
| ---------- | -------- | ------- | ---------------------------------------- | ------------------ |
| Python     | Required | 3.11+   | [python.org](https://python.org)         | `python --version` |
| uv         | Required | Latest  | `pip install uv`                         | `uv --version`     |
| PostgreSQL | Required | 14+     | [postgresql.org](https://postgresql.org) | `psql --version`   |
| Node.js    | Required | 20+     | [nodejs.org](https://nodejs.org)         | `node --version`   |
| pnpm       | Required | 8+      | `npm install -g pnpm`                    | `pnpm --version`   |
| Docker     | Optional | Latest  | [docker.com](https://docker.com)         | `docker --version` |
| Git        | Required | 2.40+   | [git-scm.com](https://git-scm.com)       | `git --version`    |

### Environment Variables

Create a `.env` file in each backend service directory:

```env
# ColliderDataServer/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/collider
FIREBASE_PROJECT_ID=your-firebase-project
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
SSE_KEEPALIVE_INTERVAL=30

# ColliderGraphToolServer/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/collider
OPENAI_API_KEY=your-api-key

# ColliderVectorDbServer/.env
CHROMADB_PERSIST_DIRECTORY=./chroma_data
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Initial Database Setup

```powershell
# Create the database
psql -U postgres -c "CREATE DATABASE collider;"

# Verify connection
psql -U postgres -d collider -c "SELECT 1;"
```

---

## Technology Stack

### Backend

| Component  | Version  | Notes             |
| ---------- | -------- | ----------------- |
| Python     | 3.11+    | 3.12 recommended  |
| FastAPI    | 0.115.0+ | Async-first       |
| Pydantic   | 2.10.0+  | V2 required       |
| SQLAlchemy | 2.0+     | Async support     |
| PostgreSQL | 14+      | 16 recommended    |
| ChromaDB   | 0.4+     | Vector embeddings |
| NetworkX   | 3.0+     | Graph operations  |

### Chrome Extension

| Component    | Version | Notes                 |
| ------------ | ------- | --------------------- |
| Plasmo       | Latest  | Manifest V3           |
| React        | 19.0.0+ | Latest stable         |
| TypeScript   | 5.9.2+  | Strict mode           |
| Zustand      | 5.0+    | State management      |
| Tailwind CSS | 4.0+    | Utility-first styling |

### Frontend

| Component      | Version | Notes                 |
| -------------- | ------- | --------------------- |
| Nx             | 22.4.5+ | Monorepo tooling      |
| Next.js        | 16.0.1+ | App Router only       |
| React          | 19.0.0+ | Latest stable         |
| TypeScript     | 5.9.2+  | Strict mode           |
| TanStack Query | 5.0+    | Server state          |
| Zustand        | 5.0+    | Client state          |
| Radix UI       | Latest  | Accessible primitives |
| Tailwind CSS   | 4.0+    | Utility-first styling |

### Communication

- gRPC for service-to-service
- SSE for real-time streaming (preferred over WebSocket for one-way)
- WebSocket for bi-directional (workflows)
- Native Messaging for FILESYST domain

---

## Critical Understanding: FFS4-8 .agent Folders

**Key Insight:** FFS4-8 are **IDE workspace contexts for code assist**, NOT the applications themselves.

- **FFS4-8 `.agent/` folders** = Frontend workspace contexts (for IDE code completion, documentation)
- **Application runtime data** = Lives in backend database (`nodes.container` JSONB field)
- These are **separate concerns**: IDE context vs runtime application data
- During seeding, we load FFS4-8 .agent contexts and inject them into database as starting containers

## Three Domains Architecture

| Domain       | Storage                       | Backend          | Purpose                      |
| ------------ | ----------------------------- | ---------------- | ---------------------------- |
| **FILESYST** | `.agent/` folders on disk     | Native Messaging | IDE workspace contexts       |
| **CLOUD**    | `nodes.container` JSONB in DB | Data Server      | Cloud workspace applications |
| **ADMIN**    | `users.container` JSONB in DB | Data Server      | User accounts & admin        |

## Rebuild Scope

### FFS2 - Backend & Extension (Rebuild All)
1. `ColliderDataServer` (FastAPI - Port 8000)
2. `ColliderGraphToolServer` (FastAPI WebSocket - Port 8001)
3. `ColliderVectorDbServer` (FastAPI - Port 8002)
4. `ColliderMultiAgentsChromeExtension` (Plasmo/React)

### FFS3 - Frontend (Rebuild All)
1. `collider-frontend` (Nx monorepo with Next.js)

### Keep As-Is
- FFS4-8 `.agent/` folders (IDE workspace contexts)
- FFS9-10 placeholder folders
- All `.agent/` hierarchy (FFS0, FFS1, FFS2, FFS3)

---

## Phase 0: Foundation Setup

**Goal:** All prerequisites installed, database created, environment configured, project scaffolded.

### 0.1 Verify All Prerequisites

Run each verification command from the [Prerequisites Matrix](#prerequisites-matrix) above. All must pass before proceeding.

### 0.2 Create Database

```powershell
psql -U postgres -c "CREATE DATABASE collider;"
psql -U postgres -c "CREATE DATABASE collider_test;"
```

### 0.3 Initialize Python Projects

```powershell
# ColliderDataServer
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv init
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic pydantic-settings python-dotenv

# ColliderGraphToolServer
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderGraphToolServer
uv init
uv add fastapi uvicorn[standard] websockets networkx

# ColliderVectorDbServer
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderVectorDbServer
uv init
uv add fastapi uvicorn[standard] chromadb sentence-transformers
```

### 0.4 Initialize Frontend Projects

```powershell
# Chrome Extension
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension
pnpm install

# Frontend Monorepo
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend
pnpm install
```

### 0.5 Configure Environment Files

Create `.env` files in each backend service directory as shown in [Environment Variables](#environment-variables) above.

**Exit Criteria:**
- [ ] All prerequisites installed and verified
- [ ] PostgreSQL running with `collider` and `collider_test` databases created
- [ ] All Python projects initialized with `uv` and dependencies installed
- [ ] All TypeScript projects initialized with `pnpm` and dependencies installed
- [ ] Environment variables configured in `.env` files
- [ ] All services can start without import errors (even if endpoints are stubs)

---

## Phase 1: ColliderDataServer Foundation

**Goal:** Establish database-backed API with proper domain separation.

### 1.1 Database Schema

**File:** `ColliderDataServer/src/db/models.py`

Core models:
- `User` - with `container` JSONB field (ADMIN domain)
- `AdminAccount` - admin-specific settings
- `Application` - with `domain` field ("FILESYST", "CLOUD", "ADMIN")
- `Node` - with `container` JSONB field (CLOUD domain), `parent_id` for tree structure
- `AppPermission` - application-level permissions

Key schema features:
- JSONB `container` field stores full `.agent` structure (manifest, instructions, rules, skills, tools, knowledge, workflows, configs)
- GIN indexes on JSONB for fast queries
- Tree path materialization for efficient node queries

### 1.2 Alembic Migrations

**Directory:** `ColliderDataServer/alembic/versions/`

Migration strategy:
```bash
alembic init alembic
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 1.3 FastAPI Application

**File:** `ColliderDataServer/src/main.py`

Routers to implement:
- `/api/v1/auth` - Firebase token verification
- `/api/v1/users` - User CRUD, ADMIN container access
- `/api/v1/apps` - Application CRUD, filtered by permissions
- `/api/v1/apps/{app_id}/nodes` - Node CRUD, tree navigation
- `/api/v1/apps/{app_id}/tree` - Full tree retrieval
- `/api/v1/permissions` - Permission management
- `/api/v1/sse` - Server-Sent Events for real-time updates
- `/api/v1/secrets` - Encrypted secrets management

CORS configuration:
- Allow `http://localhost:3000`, `http://localhost:3001`
- Allow `chrome-extension://.*` (regex for dynamic extension IDs)

### 1.4 Database Seeding

**File:** `ColliderDataServer/src/seed.py`

Seed applications with containers loaded from FFS4-8 IDE contexts:

| App ID         | Display Name          | Domain   | Source .agent Context  |
| -------------- | --------------------- | -------- | ---------------------- |
| `application0` | Root Portal           | CLOUD    | FFS4 (Sidepanel)       |
| `applicationx` | Collider IDE          | FILESYST | FFS6 (IDE)             |
| `applicationz` | Account Manager       | ADMIN    | FFS7 (Admin)           |
| `application1` | My Tiny Data Collider | CLOUD    | FFS8 (Cloud workspace) |

**Container loading logic:**
```python
def load_agent_container(agent_path: Path) -> dict:
    """Load .agent/ folder structure into database container format."""
    return {
        "manifest": load_yaml(agent_path / "manifest.yaml"),
        "instructions": load_markdown_files(agent_path / "instructions"),
        "rules": load_markdown_files(agent_path / "rules"),
        "skills": load_markdown_files(agent_path / "skills"),
        "tools": load_json_files(agent_path / "tools"),
        "knowledge": load_markdown_files(agent_path / "knowledge"),
        "workflows": load_json_files(agent_path / "workflows"),
        "configs": load_yaml(agent_path / "configs/defaults.yaml")
    }
```

**Critical Files:**
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer\src\db\models.py`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer\src\main.py`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer\src\api\nodes.py`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer\src\seed.py`

**Common Issues & Solutions:**

| Issue              | Symptom                                          | Solution                                                                             |
| ------------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Missing asyncpg    | `ModuleNotFoundError: No module named 'asyncpg'` | `uv add asyncpg`                                                                     |
| DB not created     | `database "collider" does not exist`             | `psql -U postgres -c "CREATE DATABASE collider;"`                                    |
| Migration conflict | `Target database is not up to date`              | `alembic stamp head` then re-migrate                                                 |
| JSONB index error  | Slow container queries                           | Verify GIN index: `CREATE INDEX idx_nodes_container ON nodes USING GIN (container);` |

**Exit Criteria:**
- [ ] DataServer running on port 8000 without errors
- [ ] `/health` endpoint returns 200
- [ ] All API endpoints responding (auth, users, apps, nodes, tree, permissions, sse, secrets)
- [ ] Database seeded with 4 applications
- [ ] Each application has container loaded from FFS4-8 `.agent/` contexts
- [ ] CORS allows requests from localhost:3000 and chrome-extension origins
- [ ] `pytest tests/` passes with 80%+ coverage on core logic

---

## Phase 2: ColliderGraphToolServer & ColliderVectorDbServer

**Goal:** Supporting services for workflow execution and semantic search.

### 2.1 GraphToolServer (Port 8001)

**Purpose:** Workflow execution engine with streaming progress

WebSocket protocol at `ws://localhost:8001/ws/workflow`:

Client -> Server messages:
- `execute_workflow` - Run a workflow with input
- `query_graph` - Graph traversal queries
- `ai_inference` - LLM inference requests

Server -> Client messages:
- `workflow_progress` - Step-by-step progress updates
- `workflow_result` - Final result
- `ai_chunk` - Streaming AI responses

**Key implementation:**
```python
# src/main.py
@app.websocket("/ws/workflow")
async def workflow_websocket(websocket: WebSocket):
    await websocket.accept()
    handler = WorkflowHandler(websocket)

    try:
        while True:
            message = await websocket.receive_json()
            await handler.handle_message(message)
    except WebSocketDisconnect:
        await handler.cleanup()
```

### 2.2 VectorDbServer (Port 8002)

**Purpose:** Semantic search using real embeddings (not keyword MVP)

Endpoints:
- `POST /api/v1/search` - Semantic search in tools/skills/knowledge
- `POST /api/v1/embed` - Generate embeddings
- `POST /api/v1/index` - Index documents

**Embedding model:** Sentence Transformers (`all-MiniLM-L6-v2`)
**Storage:** ChromaDB (persistent collections)

Collections:
- `tools` - All tool definitions
- `skills` - All skill definitions
- `knowledge` - All knowledge documents

**Critical Files:**
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderGraphToolServer\src\main.py`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderVectorDbServer\src\main.py`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderVectorDbServer\src\embeddings\generator.py`

**Common Issues & Solutions:**

| Issue               | Symptom                                        | Solution                                                                                                                         |
| ------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| WebSocket rejected  | `403 Forbidden` on WebSocket connect           | Check CORS/origin headers in middleware                                                                                          |
| ChromaDB lock       | `sqlite3.OperationalError: database is locked` | Ensure single ChromaDB client instance                                                                                           |
| Model download slow | First embedding call hangs                     | Pre-download model: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` |
| Port conflict       | `Address already in use`                       | `netstat -ano                                                                                                                    | findstr ":8001"` and kill the process |

**Exit Criteria:**
- [ ] GraphToolServer running on port 8001
- [ ] `/health` endpoint returns 200
- [ ] WebSocket connection accepts and echoes messages
- [ ] At least one workflow can execute end-to-end
- [ ] VectorDbServer running on port 8002
- [ ] `/health` endpoint returns 200
- [ ] Semantic search returns relevant results from seeded data
- [ ] Embedding generation works with `all-MiniLM-L6-v2`
- [ ] `pytest tests/` passes for both services

---

## Phase 3: ColliderMultiAgentsChromeExtension

**Goal:** Chrome extension with context management and multi-agent architecture.

### 3.1 Background Service Worker (Context Manager)

**Core architecture:** Service Worker acts as central orchestrator

**File:** `src/background/index.ts`

Components:
- **ContextManager** - Manages tab contexts, routes messages to agents
- **DOMAgent** - Browser DOM manipulation
- **CloudAgent** - CLOUD domain operations (workflows, tools)
- **FileSystAgent** - FILESYST domain (native messaging)

**Context switching flow:**
```
Tab activation -> Load app context from DataServer ->
Merge MAIN_CONTEXT + TAB_CONTEXT ->
Notify all agents -> Update sidepanel
```

**SSE connection:** Background maintains persistent connection to `http://localhost:8000/api/v1/sse` for real-time updates

### 3.2 Agent Implementations

**DOMAgent** (`src/background/agents/dom-agent.ts`):
- Query DOM via content scripts
- Mutate DOM
- Observe DOM changes

**CloudAgent** (`src/background/agents/cloud-agent.ts`):
- Execute workflows (WebSocket to GraphToolServer)
- Search tools (VectorDbServer)
- Load CLOUD domain containers

**FileSystAgent** (`src/background/agents/filesyst-agent.ts`):
- Read/write files via Native Messaging Host
- Load FILESYST .agent contexts
- IDE integration

### 3.3 Sidepanel UI (App 0)

**File:** `src/sidepanel/index.tsx`

Layout:
- Left: **Appnode Browser** (tree view of nodes)
- Right: **Main Agent Seat** (chat/interaction)

State management: Zustand store for app tree, selected node, SSE updates

### 3.4 Native Messaging Host

**File:** `native-host/host.py`

Python script for FILESYST domain file operations:
- `read_file` - Read file contents
- `write_file` - Write file contents
- `list_dir` - List directory contents

Communication: Chrome Native Messaging protocol (stdin/stdout with length prefix)

**Critical Files:**
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension\src\background\index.ts`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension\src\background\context-manager.ts`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension\src\sidepanel\index.tsx`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension\native-host\host.py`

**Common Issues & Solutions:**

| Issue                       | Symptom                         | Solution                                                                                                          |
| --------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Service Worker crashes      | Extension icon grayed out       | Open `chrome://extensions` -> Service Worker -> Console; check for uncaught promise rejections                    |
| CORS errors                 | `Access blocked by CORS policy` | Verify backend CORS includes `chrome-extension://` regex; check manifest `host_permissions`                       |
| Native Messaging fails      | `Native host has exited`        | Verify registry key (Windows): `HKCU\Software\Google\Chrome\NativeMessagingHosts\`; check Python path in manifest |
| SSE disconnects             | Real-time updates stop          | Add reconnection logic with exponential backoff in background script                                              |
| Content script not injected | `Cannot access contents of url` | Check manifest `content_scripts.matches` patterns; reload extension after changes                                 |

**Exit Criteria:**
- [ ] Extension loads in Chrome without errors
- [ ] Service Worker starts and stays alive
- [ ] ContextManager connects to DataServer SSE
- [ ] Sidepanel opens and displays app tree from DataServer
- [ ] DOMAgent can query page DOM via content script
- [ ] CloudAgent connects to GraphToolServer WebSocket
- [ ] FileSystAgent communicates via Native Messaging Host
- [ ] Context switching works when changing tabs
- [ ] All agents respond to messages from the ContextManager

---

## Phase 4: Frontend Monorepo (Nx/Next.js)

**Goal:** Nx-managed frontend with shared libraries and portal application.

### 4.1 Nx Workspace Structure

```
collider-frontend/
├── apps/
│   ├── portal/          # Next.js App 1 (My Tiny Data Collider)
│   └── portal-e2e/      # Playwright E2E tests
├── libs/
│   ├── api-client/      # Type-safe API client for all 3 servers
│   ├── node-container/  # NodeContainer types, validator, merger
│   └── shared-ui/       # Radix UI components (Button, Card, Tree)
```

### 4.2 API Client Library

**File:** `libs/api-client/src/index.ts`

Export clients:
- `DataServerClient` - REST API for apps, nodes, users, permissions
- `GraphServerClient` - WebSocket for workflows
- `VectorServerClient` - REST API for semantic search

**Key methods:**
```typescript
// DataServerClient
listApps(): Promise<Application[]>
getAppTree(appId: string): Promise<NodeTree>
getNode(appId: string, nodeId: string): Promise<Node>
createNode(appId: string, node: NodeCreate): Promise<Node>
connectSSE(onMessage: (event: MessageEvent) => void): EventSource

// GraphServerClient
connect(onMessage: (data: any) => void): WebSocket
executeWorkflow(workflowId: string, input: any): void

// VectorServerClient
search(query: string, collection: string): Promise<SearchResults>
```

### 4.3 Node Container Library

**File:** `libs/node-container/src/types.ts`

```typescript
interface NodeContainer {
  manifest: Record<string, any>
  instructions: string[]
  rules: string[]
  skills: string[]
  tools: Tool[]
  knowledge: string[]
  workflows: Workflow[]
  configs: Record<string, any>
}
```

**File:** `libs/node-container/src/merger.ts`

`ContainerMerger.merge(parent, child)` - Deep merge following inheritance rules

### 4.4 Portal Application

**File:** `apps/portal/src/app/page.tsx`

Homepage:
- List applications from DataServer
- Display as cards with domain-based color coding
- Navigate to app detail pages

**Module resolution fix:**
```json
// tsconfig.base.json
{
  "compilerOptions": {
    "paths": {
      "@collider/api-client": ["libs/api-client/src/index.ts"],
      "@collider/node-container": ["libs/node-container/src/index.ts"],
      "@collider/shared-ui": ["libs/shared-ui/src/index.ts"]
    }
  }
}
```

**Critical Files:**
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend\libs\api-client\src\data-server.ts`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend\libs\node-container\src\merger.ts`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend\apps\portal\src\app\page.tsx`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend\tsconfig.base.json`

**Common Issues & Solutions:**

| Issue              | Symptom                                      | Solution                                                                   |
| ------------------ | -------------------------------------------- | -------------------------------------------------------------------------- |
| Module resolution  | `Cannot find module '@collider/api-client'`  | Check `tsconfig.base.json` paths; run `nx reset && pnpm install`           |
| Nx cache stale     | Build uses old code                          | `nx reset` to clear cache                                                  |
| Port conflict      | `EADDRINUSE: address already in use :::3000` | `netstat -ano                                                              | findstr ":3000"` and kill the process |
| Hydration mismatch | React hydration error in console             | Ensure server/client render same content; check for `typeof window` guards |

**Exit Criteria:**
- [ ] Nx workspace builds without errors: `nx build portal`
- [ ] All shared libraries build: `nx run-many --target=build --projects=api-client,node-container,shared-ui`
- [ ] Portal runs on port 3000: `nx dev portal`
- [ ] Portal displays 4 applications fetched from DataServer
- [ ] Domain-based color coding renders correctly
- [ ] Navigation to app detail pages works
- [ ] Module resolution for `@collider/*` imports works
- [ ] `nx test portal` passes
- [ ] `nx lint portal` passes

---

## Phase 5: Integration & End-to-End Verification

**Goal:** All components working together as a complete system.

### 5.1 End-to-End Verification Checklist

1. **DataServer:** List applications returns 4 apps (App 0, X, Z, 1)
2. **Container loading:** Each app has full `.agent` structure in container field
3. **Chrome Extension:** Sidepanel displays app tree from DataServer
4. **SSE:** Real-time updates when nodes change
5. **Workflow execution:** GraphToolServer executes workflow, streams progress
6. **Vector search:** Semantic search finds relevant tools
7. **Native messaging:** FileSystAgent reads/writes local files
8. **Frontend portal:** Displays apps, navigates to app detail pages

### 5.2 Integration Tests

```powershell
# Start all services
.\scripts\start-all.ps1

# Wait for health checks
.\scripts\health-check.ps1

# Run integration tests
pytest tests/integration/ -v -m integration
nx e2e portal-e2e
```

**Exit Criteria:**
- [ ] All 3 backend servers running simultaneously without errors
- [ ] Chrome Extension connects to all backends
- [ ] Frontend portal fetches and displays data from DataServer
- [ ] SSE real-time updates propagate to Chrome Extension and Frontend
- [ ] Workflow execution streams progress via WebSocket
- [ ] Vector search returns relevant results
- [ ] Native messaging host communicates with extension
- [ ] All integration tests pass
- [ ] All E2E tests pass

---

## Build Automation & Scripts

### PowerShell Scripts (Windows)

Reference scripts to create in `scripts/`:

- `scripts/setup-dev.ps1` - Complete environment setup (install deps, create DB, run migrations)
- `scripts/start-all.ps1` - Start all services in parallel
- `scripts/test-all.ps1` - Run complete test suite across all services
- `scripts/health-check.ps1` - Verify all services are running and healthy

### Makefile (Universal)

```makefile
.PHONY: setup start stop test health lint

setup:           ## Complete dev environment setup
	uv sync --all-extras
	pnpm install
	psql -U postgres -c "CREATE DATABASE IF NOT EXISTS collider;"
	cd ColliderDataServer && alembic upgrade head

start:           ## Start all services in background
	@echo "Starting all services..."
	powershell -File scripts/start-all.ps1

stop:            ## Stop all services
	@echo "Stopping all services..."
	powershell -Command "Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process"

test:            ## Run all tests
	cd ColliderDataServer && pytest tests/ -v --cov=src
	cd ColliderGraphToolServer && pytest tests/ -v --cov=src
	cd ColliderVectorDbServer && pytest tests/ -v --cov=src
	cd collider-frontend && nx run-many --target=test --all

health:          ## Check service health
	@curl -sf http://localhost:8000/health && echo " DataServer OK" || echo " DataServer FAILED"
	@curl -sf http://localhost:8001/health && echo " GraphToolServer OK" || echo " GraphToolServer FAILED"
	@curl -sf http://localhost:8002/health && echo " VectorDbServer OK" || echo " VectorDbServer FAILED"

lint:            ## Run linters
	cd ColliderDataServer && ruff check src/
	cd ColliderGraphToolServer && ruff check src/
	cd ColliderVectorDbServer && ruff check src/
	cd collider-frontend && nx run-many --target=lint --all
```

### Docker Compose (Optional)

```yaml
# docker-compose.yml
version: "3.9"
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: collider
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  data-server:
    build: ./ColliderDataServer
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/collider

  graph-server:
    build: ./ColliderGraphToolServer
    ports:
      - "8001:8001"
    depends_on:
      - postgres

  vector-server:
    build: ./ColliderVectorDbServer
    ports:
      - "8002:8002"
    volumes:
      - chromadata:/app/chroma_data

volumes:
  pgdata:
  chromadata:
```

---

## Testing Strategy

### Testing Pyramid

```
         /\
        /E2E\          Playwright (Critical user flows)
       /------\
      / Integ  \       API integration, Service-to-service
     /----------\
    /   Unit     \     Models, Utils, Components
   /--------------\
```

### Backend Testing (Python)

**Framework:** Pytest + pytest-asyncio

```powershell
# Unit tests
pytest tests/test_models.py -v

# Integration tests
pytest tests/test_api/ -v -m integration

# Coverage report
pytest --cov=src --cov-report=html --cov-fail-under=80

# Single test file
pytest tests/test_api/test_nodes.py -v -k "test_create_node"
```

**Test Fixtures Example:**
```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/collider_test")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_application():
    return {
        "id": "application1",
        "display_name": "My Tiny Data Collider",
        "domain": "CLOUD",
        "container": {
            "manifest": {"name": "test-app"},
            "instructions": [],
            "rules": [],
            "skills": [],
            "tools": [],
            "knowledge": [],
            "workflows": [],
            "configs": {}
        }
    }

@pytest.fixture
def sample_node(sample_application):
    return {
        "application_id": sample_application["id"],
        "path": "/root/child1",
        "container": {"manifest": {"name": "child-node"}}
    }
```

### Frontend Testing (TypeScript)

**Framework:** Vitest (unit) + Playwright (E2E)

```powershell
# Unit tests for a library
nx test shared-ui

# Unit tests for portal
nx test portal

# All unit tests
nx run-many --target=test --all

# E2E tests
nx e2e portal-e2e

# E2E with headed browser (for debugging)
nx e2e portal-e2e --headed
```

**Component Test Example:**
```typescript
// libs/shared-ui/src/components/AppCard.test.tsx
import { render, screen } from '@testing-library/react'
import { AppCard } from './AppCard'

describe('AppCard', () => {
  it('renders application name', () => {
    render(<AppCard app={{ id: 'app1', displayName: 'Test App', domain: 'CLOUD' }} />)
    expect(screen.getByText('Test App')).toBeInTheDocument()
  })

  it('applies domain-based color', () => {
    render(<AppCard app={{ id: 'app1', displayName: 'Test App', domain: 'ADMIN' }} />)
    expect(screen.getByTestId('app-card')).toHaveClass('border-red-500')
  })
})
```

### Chrome Extension Testing

```powershell
# Unit tests
cd ColliderMultiAgentsChromeExtension
pnpm test

# Watch mode
pnpm test --watch
```

### Test Data Management

```powershell
# Create test database
psql -U postgres -c "CREATE DATABASE collider_test;"

# Run migrations on test database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/collider_test alembic upgrade head

# Seed test data
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/collider_test python -m src.seed

# Reset test database
psql -U postgres -c "DROP DATABASE IF EXISTS collider_test; CREATE DATABASE collider_test;"
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        service: [ColliderDataServer, ColliderGraphToolServer, ColliderVectorDbServer]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: collider_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: cd ${{ matrix.service }} && uv sync --all-extras
      - name: Run linter
        run: cd ${{ matrix.service }} && uv run ruff check src/
      - name: Run type checker
        run: cd ${{ matrix.service }} && uv run mypy src/
      - name: Run tests
        run: cd ${{ matrix.service }} && uv run pytest tests/ -v --cov=src --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/collider_test
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ${{ matrix.service }}/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: pnpm/action-setup@v4
        with:
          version: 8
      - name: Install dependencies
        run: cd collider-frontend && pnpm install --frozen-lockfile
      - name: Lint
        run: cd collider-frontend && nx run-many --target=lint --all
      - name: Unit tests
        run: cd collider-frontend && nx run-many --target=test --all
      - name: Build
        run: cd collider-frontend && nx build portal

  extension-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: pnpm/action-setup@v4
        with:
          version: 8
      - name: Install dependencies
        run: cd ColliderMultiAgentsChromeExtension && pnpm install --frozen-lockfile
      - name: Lint
        run: cd ColliderMultiAgentsChromeExtension && pnpm lint
      - name: Tests
        run: cd ColliderMultiAgentsChromeExtension && pnpm test
      - name: Build production
        run: cd ColliderMultiAgentsChromeExtension && pnpm build
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0
    hooks:
      - id: prettier
        types_or: [typescript, javascript, json, yaml, markdown]
```

Install pre-commit hooks:
```powershell
pip install pre-commit
pre-commit install
```

---

## Critical Architectural Considerations

### 1. Domain Separation
- FILESYST contexts stay in `.agent/` folders
- CLOUD/ADMIN contexts go in database
- Never mix: IDE workspace context != runtime app data

### 2. Container Inheritance
- Root exports -> Child includes
- Deep merge strategy for instructions, rules, skills
- Tools/workflows can be overridden by ID

### 3. Communication Boundaries
- Extension <-> DataServer: REST + SSE
- Extension <-> GraphToolServer: WebSocket
- Extension <-> VectorDbServer: REST
- Extension <-> FILESYST: Native Messaging
- Service-to-service: gRPC (future)

### 4. Database Container Schema

```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    parent_id UUID REFERENCES nodes(id),
    path VARCHAR(512) NOT NULL,
    container JSONB NOT NULL,  -- Full .agent structure
    metadata JSONB,
    UNIQUE(application_id, path)
);

CREATE INDEX idx_nodes_container ON nodes USING GIN (container);
CREATE INDEX idx_nodes_app_id ON nodes(application_id);
CREATE INDEX idx_nodes_parent_id ON nodes(parent_id);
CREATE INDEX idx_nodes_path ON nodes(path);
```

### 5. ApplicationConfig vs .agent Context

| Aspect          | ApplicationConfig               | .agent Context                 |
| --------------- | ------------------------------- | ------------------------------ |
| Purpose         | Backend governance              | Workspace intelligence         |
| Contains        | API rules, rate limits, secrets | Instructions, tools, workflows |
| Storage         | Application table               | Node.container JSONB           |
| Access          | Admin only                      | Service Worker fetches         |
| Sent to browser | Never                           | Yes (hydrates agent)           |

---

## Troubleshooting Guide

### Backend Issues

#### Database Connection Errors
**Symptom:** `psycopg2.OperationalError: could not connect to server`
**Solutions:**
1. Verify PostgreSQL is running: `Get-Service postgresql*` (Windows) or `pg_isready` (cross-platform)
2. Check connection string in `.env` matches your local setup
3. Test connection: `psql -U postgres -d collider -c "SELECT 1;"`
4. Ensure `pg_hba.conf` allows local connections

#### Alembic Migration Fails
**Symptom:** `Target database is not up to date`
**Solutions:**
1. Check current revision: `alembic current`
2. Show migration history: `alembic history`
3. Reset (dev only): `psql -U postgres -c "DROP DATABASE collider; CREATE DATABASE collider;" && alembic upgrade head`
4. Stamp current (if manually applied): `alembic stamp head`

#### Import Errors on Startup
**Symptom:** `ModuleNotFoundError` when starting a service
**Solutions:**
1. Ensure you're in the correct directory (service root)
2. Run `uv sync` to install/synchronize dependencies
3. Check `pyproject.toml` for missing packages
4. Verify Python version: `python --version` (must be 3.11+)

#### Slow JSONB Queries
**Symptom:** Container queries taking > 100ms
**Solutions:**
1. Verify GIN index exists: `\d+ nodes` in psql
2. Add path-specific indexes for common queries
3. Use `EXPLAIN ANALYZE` to identify slow queries
4. Consider partial indexes for specific container keys

### Frontend Issues

#### Module Resolution Errors
**Symptom:** `Cannot find module '@collider/api-client'`
**Solutions:**
1. Check `tsconfig.base.json` paths configuration matches actual file locations
2. Rebuild Nx cache: `nx reset && pnpm install`
3. Verify the library is built: `nx build api-client`
4. Check for circular dependencies: `nx graph`

#### Build Failures
**Symptom:** `nx build portal` fails with type errors
**Solutions:**
1. Run `nx lint portal` first to catch simple issues
2. Check that shared libs are built before the app
3. Verify all imports use `@collider/*` paths (not relative)
4. Run `pnpm install` to ensure all packages are resolved

#### Hydration Mismatch
**Symptom:** React hydration error in browser console
**Solutions:**
1. Ensure server and client render identical content
2. Wrap browser-only code in `typeof window !== 'undefined'` checks
3. Use `useEffect` for client-only state initialization
4. Check for date/time formatting differences between server and client

### Chrome Extension Issues

#### Service Worker Crashes
**Symptom:** Extension icon grayed out, "Service Worker inactive"
**Solutions:**
1. Open `chrome://extensions` -> find extension -> click "Service Worker" link -> check Console
2. Look for uncaught promise rejections (add `.catch()` to all async calls)
3. Avoid top-level `await` in service worker entry
4. Check for memory leaks (large objects in global scope)

#### CORS Errors
**Symptom:** `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`
**Solutions:**
1. Verify backend CORS includes `chrome-extension://` regex pattern in allowed origins
2. Check manifest.json `host_permissions` includes backend URLs
3. Use the background service worker for API calls (not content scripts)
4. Check the specific CORS header missing (Origin, Methods, Headers)

#### Native Messaging Fails
**Symptom:** `Error when communicating with the native messaging host`
**Solutions:**
1. Windows: Check registry key at `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.collider.host`
2. Verify the manifest JSON points to correct Python executable path
3. Ensure Python script is executable and has correct shebang
4. Test the host script directly: `echo '{"type":"ping"}' | python native-host/host.py`
5. Check Chrome's internal logs at `chrome://extensions` errors tab

#### Content Script Not Injected
**Symptom:** `Unchecked runtime.lastError: Cannot access contents of URL`
**Solutions:**
1. Check manifest `content_scripts.matches` patterns
2. Ensure the page URL matches allowed patterns
3. Reload the extension after manifest changes
4. Protected pages (`chrome://`, `chrome-extension://`) cannot be injected

### Performance Issues

#### Slow Database Queries
**Solutions:**
1. Add indexes on frequently-queried columns:
   ```sql
   CREATE INDEX idx_nodes_app_id ON nodes(application_id);
   CREATE INDEX idx_nodes_path ON nodes(path);
   ```
2. Use `EXPLAIN ANALYZE` to identify slow queries
3. Enable connection pooling (SQLAlchemy pool settings)
4. Consider materialized views for complex tree queries

#### High Memory Usage (VectorDbServer)
**Solutions:**
1. Use a smaller embedding model if MiniLM is too large
2. Limit ChromaDB collection size
3. Configure batch sizes for bulk embedding operations
4. Check for memory leaks in persistent connections

### Common Pitfalls

- Not running migrations after schema changes (`alembic upgrade head`)
- Hardcoded `localhost` URLs instead of environment variables
- Not handling async errors in service worker (crashes the entire worker)
- Forgetting to rebuild after code changes (use `--reload` flag for uvicorn, watch mode for frontend)
- Committing `.env` files with secrets to git
- Not clearing Nx cache after changing workspace configuration
- Using `any` type instead of `unknown` or proper generics
- Forgetting to update CORS when extension ID changes
- Not handling WebSocket reconnection after server restart

---

## Quick Reference Commands

### Starting Services

```powershell
# Start all backend services (each in a separate terminal)
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension

# Terminal 1: DataServer
cd ColliderDataServer && uv run uvicorn src.main:app --reload --port 8000

# Terminal 2: GraphToolServer
cd ColliderGraphToolServer && uv run uvicorn src.main:app --reload --port 8001

# Terminal 3: VectorDbServer
cd ColliderVectorDbServer && uv run uvicorn src.main:app --reload --port 8002

# Terminal 4: Chrome Extension (dev mode)
cd ColliderMultiAgentsChromeExtension && pnpm dev

# Terminal 5: Frontend Portal
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend
nx dev portal
```

### Health Checks

```powershell
# Backend health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Frontend (check if running)
curl http://localhost:3000
```

### Database Operations

```powershell
# Reset database (CAUTION: destroys all data)
psql -U postgres -c "DROP DATABASE IF EXISTS collider; CREATE DATABASE collider;"
cd ColliderDataServer && alembic upgrade head && python -m src.seed

# Inspect database
psql -U postgres -d collider -c "SELECT id, display_name, domain FROM applications;"
psql -U postgres -d collider -c "SELECT COUNT(*) FROM nodes;"
psql -U postgres -d collider -c "SELECT path, container->>'manifest' FROM nodes LIMIT 5;"

# Run migrations
cd ColliderDataServer && alembic upgrade head
cd ColliderDataServer && alembic revision --autogenerate -m "description"
```

### Testing

```powershell
# Backend tests
cd ColliderDataServer && uv run pytest tests/ -v --cov=src
cd ColliderGraphToolServer && uv run pytest tests/ -v
cd ColliderVectorDbServer && uv run pytest tests/ -v

# Frontend tests
cd collider-frontend && nx test portal
cd collider-frontend && nx run-many --target=test --all
cd collider-frontend && nx e2e portal-e2e

# Extension tests
cd ColliderMultiAgentsChromeExtension && pnpm test
```

### Linting & Formatting

```powershell
# Python
ruff check src/ --fix
ruff format src/
mypy src/

# TypeScript/Frontend
cd collider-frontend && nx run-many --target=lint --all
npx prettier --write "**/*.{ts,tsx,json}"
```

### Debugging

```powershell
# Check running services
netstat -ano | findstr ":8000 :8001 :8002 :3000"

# Backend logs with debug level
uvicorn src.main:app --log-level debug --port 8000

# Nx dependency graph (opens in browser)
cd collider-frontend && nx graph

# Check Nx workspace
cd collider-frontend && nx show projects
```

### Dependency Management

```powershell
# Python (uv)
uv add <package>
uv sync
uv sync --upgrade

# Node (pnpm)
pnpm add <package>
pnpm install
pnpm update

# Rebuild from scratch
rm -rf node_modules .nx && pnpm install
uv sync --reinstall
```

---

## Glossary

### Architecture Concepts

**Three Domains**: FILESYST (on-disk `.agent/` folders), CLOUD (database-stored workspaces), ADMIN (user accounts)

**Container**: JSONB field storing full `.agent` structure (manifest, instructions, rules, skills, tools, knowledge, workflows, configs)

**Container Inheritance**: Child nodes inherit and merge parent containers using deep merge strategy

**Context Manager**: Background service worker component managing tab contexts and routing messages to appropriate agents

**.agent Folder**: Workspace metadata directory containing manifest, instructions, rules, skills, tools, knowledge, workflows, and configs

### Technical Terms

**SSE**: Server-Sent Events - HTTP-based protocol for one-way real-time updates from server to client

**Native Messaging**: Chrome Extension API for communicating with a native application (Python host) on the user's machine

**Tree Materialization**: Storing full paths (e.g., `/root/parent/child`) for efficient tree queries without recursive joins

**GIN Index**: Generalized Inverted Index - PostgreSQL index type optimized for fast JSONB containment queries

**Plasmo**: Framework for building Chrome extensions with React and TypeScript (Manifest V3)

**Nx**: Monorepo build system providing caching, dependency graph, and task orchestration for frontend projects

### Abbreviations

| Abbreviation | Full Term                                       |
| ------------ | ----------------------------------------------- |
| FFS          | Factory File System (workspace identifier)      |
| CRUD         | Create, Read, Update, Delete                    |
| API          | Application Programming Interface               |
| REST         | Representational State Transfer                 |
| JSON         | JavaScript Object Notation                      |
| JSONB        | JSON Binary (PostgreSQL optimized JSON storage) |
| SQL          | Structured Query Language                       |
| ORM          | Object-Relational Mapping                       |
| E2E          | End-to-End                                      |
| CI/CD        | Continuous Integration / Continuous Deployment  |
| MVP          | Minimum Viable Product                          |
| UI/UX        | User Interface / User Experience                |
| IDE          | Integrated Development Environment              |
| SSE          | Server-Sent Events                              |
| CORS         | Cross-Origin Resource Sharing                   |
| DOM          | Document Object Model                           |
| gRPC         | Google Remote Procedure Call                    |

---

## Success Criteria

### System-Level
- [ ] All 3 backend servers running without errors
- [ ] Database seeded with 4 applications (App 0, X, Z, 1)
- [ ] Each application has container loaded from FFS4-8 `.agent/` contexts
- [ ] Chrome Extension connects to all backends
- [ ] Sidepanel displays app tree with proper navigation
- [ ] SSE real-time updates working
- [ ] Workflow execution streams progress
- [ ] Vector search returns semantically relevant results
- [ ] Native messaging reads/writes local files
- [ ] Frontend portal builds and runs
- [ ] Frontend displays applications from DataServer

### Quality Gates
- [ ] Backend test coverage >= 80% on core logic
- [ ] All linters pass (Ruff, ESLint, Prettier)
- [ ] Type checkers pass (Mypy strict, TypeScript strict)
- [ ] No `any` types in TypeScript code
- [ ] All API endpoints have Google-style docstrings
- [ ] All exported components have TSDoc comments
- [ ] CI pipeline passes on all branches
