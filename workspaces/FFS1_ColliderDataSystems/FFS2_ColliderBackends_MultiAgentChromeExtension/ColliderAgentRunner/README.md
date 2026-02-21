# ColliderAgentRunner

> Local pydantic-ai agent — composes ContextSets from OpenClaw bootstrap data and streams LLM responses to the Chrome extension sidepanel.

**Port**: 8004
**Model**: `claude-sonnet-4-6` (Anthropic)

---

## What It Does

The AgentRunner bridges the Chrome extension's **WorkspaceBrowser** to the Collider backend:

1. Accepts a `ContextSet` (role + node IDs + vector query) via `POST /agent/session`
2. Authenticates as the chosen role against ColliderDataServer
3. Bootstraps each selected node via OpenClaw (`GET /openclaw/bootstrap/{id}`)
4. Merges all node contexts — leaf-wins dict strategy (later node IDs win)
5. Optionally discovers additional tools via GraphToolServer vector search
6. Builds a unified system prompt and caches it as a session (4h TTL)
7. Streams LLM responses to the extension via `GET /agent/chat` (SSE)

---

## Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | Liveness probe |
| `/agent/session` | POST | Compose ContextSet → session_id |
| `/agent/chat` | GET | SSE stream (session_id preferred, node_id legacy) |
| `/tools/discover` | GET | Proxy to GraphToolServer vector discover |

---

## Setup

### 1 — Secrets

Fill in `D:\FFS0_Factory\secrets\api_keys.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
COLLIDER_USERNAME=your_seeded_user
COLLIDER_PASSWORD=your_password

# Optional: per-role pre-seeded accounts
# Falls back to COLLIDER_USERNAME/PASSWORD if blank
COLLIDER_SUPERADMIN_USERNAME=
COLLIDER_SUPERADMIN_PASSWORD=
COLLIDER_COLLIDER_ADMIN_USERNAME=
COLLIDER_COLLIDER_ADMIN_PASSWORD=
COLLIDER_APP_ADMIN_USERNAME=
COLLIDER_APP_ADMIN_PASSWORD=
COLLIDER_APP_USER_USERNAME=
COLLIDER_APP_USER_PASSWORD=
```

### 2 — Start

```powershell
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderAgentRunner
uv run uvicorn src.main:app --reload --port 8004
```

Verify: <http://localhost:8004/health>

### 3 — Prerequisites

ColliderDataServer (:8000) and ColliderGraphToolServer (:8001) must be running first.

---

## ContextSet Schema

```python
class ContextSet(BaseModel):
    role: Literal["superadmin", "collider_admin", "app_admin", "app_user"]
    app_id: str                        # ACL boundary application
    node_ids: list[str]                # nodes to bootstrap and merge
    vector_query: str | None = None    # semantic tool discovery
    visibility_filter: list[str] = ["global", "group"]
    depth: int | None = None           # bootstrap depth (None = full subtree)
```

---

## Source Layout

```
src/
├── main.py                  ← FastAPI app + all routes
├── schemas/
│   └── context_set.py       ← ContextSet, SessionPreview, SessionResponse
├── core/
│   ├── config.py            ← Settings (reads secrets/api_keys.env)
│   ├── auth_client.py       ← Per-role JWT cache + login
│   ├── collider_client.py   ← OpenClaw bootstrap + tool execution
│   ├── graph_tool_client.py ← GraphToolServer vector discover proxy
│   └── session_store.py     ← In-memory session cache (4h TTL)
└── agent/
    ├── runner.py            ← compose_context_set(), run_session_stream()
    └── tools.py             ← build_tools() → pydantic-ai Tool wrappers
```

---

## Configuration

All settings via `pydantic-settings` — env file priority (highest first):

1. Environment variables
2. `D:/FFS0_Factory/secrets/api_keys.env`
3. `../.env` (FFS2 shared)
4. `.env` (local override)

Key settings:

| Setting | Default | Description |
| --- | --- | --- |
| `agent_model` | `claude-sonnet-4-6` | Anthropic model ID |
| `data_server_url` | `http://localhost:8000` | ColliderDataServer base URL |
| `graph_tool_url` | `http://localhost:8001` | ColliderGraphToolServer base URL |
| `port` | `8004` | Server port |
