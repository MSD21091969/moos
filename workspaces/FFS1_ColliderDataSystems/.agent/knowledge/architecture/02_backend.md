# Backend

> Server infrastructure: Data Server, GraphTool Server, VectorDB Server, Frontend Server.

## Server Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVERS                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  DATA SERVER    │  │ GRAPHTOOL       │  │ VECTORDB        │              │
│  │  (FastAPI)      │  │ SERVER          │  │ SERVER          │              │
│  │  Port: 8000     │  │ (Pyd AI Graph)  │  │                 │              │
│  │                 │  │ Port: 8001      │  │  Port: 8002     │              │
│  │  • CRUD nodes   │  │                 │  │  • Tool search  │              │
│  │  • CRUD users   │  │  • Graph ops    │  │  • Semantic     │              │
│  │  • SSE events   │  │  • Workflow     │  │    matching     │              │
│  │  • Auth verify  │  │    execution    │  │  • GPU accel    │              │
│  │                 │  │  • AI inference │  │                 │              │
│  │  REST + SSE     │  │                 │  │  REST/gRPC      │              │
│  │                 │  │  WebSocket      │  │                 │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│           └────────────────────┴────────────────────┘                        │
│                                │                                             │
│                         ┌──────┴──────┐                                      │
│                         │ PostgreSQL  │                                      │
│                         │ Port: 5432  │                                      │
│                         └─────────────┘                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │                    FRONTEND (Portal)                                      ││
│  │         Next.js app on Port 3001 (my-tiny-data-collider)                 ││
│  └──────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Server

**Location:** `ColliderDataServer/`  
**Tech:** FastAPI + Pydantic  
**Protocol:** REST + SSE  
**Port:** 8000

### Configuration

Environment variables (`.env`):
```env
COLLIDER_ENV=development
COLLIDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/collider
COLLIDER_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
FIREBASE_AUTH_ENABLED=false
```

### CORS Setup

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",  # Dynamic extension IDs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Endpoints

| Endpoint          | Method    | Purpose                  |
| ----------------- | --------- | ------------------------ |
| `/health`         | GET       | Health check             |
| `/api/v1/auth/verify` | POST  | Verify token, return user |
| `/api/v1/context` | GET/POST  | Read/write nodecontainer |
| `/api/v1/nodes`   | CRUD      | Node operations          |
| `/api/v1/users`   | CRUD      | User/account operations  |
| `/api/v1/apps`    | CRUD      | Application management   |
| `/api/v1/sse`     | GET (SSE) | Real-time events         |

### SSE Events

Used for user-context related updates:

- Permission changes
- Context updates
- Node modifications
- App config changes

---

## GraphTool Server

**Tech:** Pydantic AI Graph
**Protocol:** WebSocket

### Endpoints

| Endpoint       | Protocol  | Purpose                       |
| -------------- | --------- | ----------------------------- |
| `/ws/graph`    | WebSocket | Graph queries, mutations      |
| `/ws/workflow` | WebSocket | Workflow execution, streaming |

### Responsibilities

- Graph operations (traverse, query, mutate)
- AI inference
- Workflow execution
- Streaming responses to agent

---

## VectorDB Server

**Tech:** Vector database (GPU-accelerated)
**Protocol:** REST or gRPC

### Purpose

- Tool search (semantic matching)
- Finding relevant tools for agent context
- Similarity search across knowledge

---

## Frontend Server

**Tech:** Static file server
**Purpose:** Hosts versioned React applications

Applications are delivered to browser:

- `my-tiny-data-collider`
- Future CLOUD domain apps

---

## Database Schema

### PostgreSQL Tables

```sql
-- ACCOUNTS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    profile JSONB DEFAULT '{}',
    container JSONB DEFAULT '{}',  -- ADMIN .agent context (secrets, perms)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE admin_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id VARCHAR(64) UNIQUE NOT NULL,
    owner_id UUID REFERENCES admin_accounts(id) ON DELETE SET NULL,
    display_name VARCHAR(255),
    config JSONB DEFAULT '{}',  -- ApplicationConfig (backend-only)
    root_node_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PERMISSIONS (app-level only)
CREATE TABLE app_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    can_read BOOLEAN DEFAULT false,
    can_write BOOLEAN DEFAULT false,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, application_id)
);

-- CONTAINER NODES
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    path VARCHAR(512) NOT NULL,
    container JSONB DEFAULT '{}',  -- .agent context
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(application_id, path)
);

-- FK for root_node
ALTER TABLE applications
ADD CONSTRAINT fk_root_node FOREIGN KEY (root_node_id) REFERENCES nodes(id);

-- INDEXES
CREATE INDEX idx_nodes_application ON nodes(application_id);
CREATE INDEX idx_nodes_parent ON nodes(parent_id);
CREATE INDEX idx_nodes_path ON nodes(path);
CREATE INDEX idx_permissions_user ON app_permissions(user_id);
```

### Pydantic Models

```python
class AdminContainer(BaseModel):
    permissions: list[str] = []
    secrets: dict[str, str] = {}  # Encrypted
    settings: dict = {}

class ApplicationConfig(BaseModel):
    """Backend-only (never sent to browser)"""
    api_rules: dict = {}
    rate_limits: dict = {}  # App-level only

class NodeContainer(BaseModel):
    manifest: dict = {}
    instructions: list[str] = []
    rules: list[str] = []
    skills: list[str] = []
    tools: list[dict] = []
    knowledge: list[str] = []
    workflows: list[dict] = []
    configs: dict = {}
```

### Key Endpoints

| Endpoint                  | Method | Purpose                                 |
| ------------------------- | ------ | --------------------------------------- |
| `/api/v1/auth/verify`     | POST   | Verify token, return user + permissions |
| `/api/v1/apps`            | GET    | List apps (filtered by permission)      |
| `/api/v1/apps/{id}/nodes` | GET    | Get node by path                        |
| `/api/v1/apps/{id}/nodes` | POST   | Create node                             |
| `/api/v1/sse`             | GET    | SSE stream                              |
