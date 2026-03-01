# ColliderAgentRunner

> Context hydration service — composes Collider node bootstraps into NanoClaw workspace sessions.
> **Chat is handled by NanoClawBridge directly** (ws://127.0.0.1:18789).

Canonical docs (DRY):

- `D:\FFS0_Factory\CLAUDE.md`
- `D:\FFS0_Factory\.agent\workflows\conversation-state-rehydration.md`
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\CLAUDE.md`

**Port**: 8004

---

## What It Does

The AgentRunner bridges the Chrome extension to NanoClaw by composing Collider
context:

### Session Agent (WorkspaceBrowser tab)

1. Accepts a `ContextSet` (role + node IDs + vector query) via `POST /agent/session`
2. Authenticates as the chosen role against ColliderDataServer
3. Bootstraps each selected node via NanoClaw (`GET /agent/bootstrap/{id}`)
4. Optionally prepends ancestor node context (root-first) when `inherit_ancestors=true`
5. Merges all node contexts — leaf-wins dict strategy (later node IDs win)
6. Optionally discovers additional tools via GraphToolServer vector search
7. **Writes workspace files** (CLAUDE.md + .mcp.json, skills/) to `~/.nanoclaw/workspaces/collider`
8. Returns `session_id` + `nanoclaw_ws_url` with auth token for Chrome extension
9. **NanoClawBridge handles all chat** — extension connects via WebSocket

### Root Agent (RootAgentPanel tab)

1. Auto-composes from `Application.root_node_id` with full subtree depth
2. Authenticates as `superadmin` role
3. Writes workspace files to `~/.nanoclaw/workspaces/collider-root`
4. Longer session TTL (24h) — persists across panel open/close

---

## Endpoints

| Endpoint              | Method | Purpose                                           |
| --------------------- | ------ | ------------------------------------------------- |
| `/health`             | GET    | Liveness probe                                    |
| `/agent/session`      | POST   | Compose ContextSet → session_id + nanoclaw_ws_url |
| `/agent/root/session` | POST   | Auto-compose from app root_node_id → session_id   |
| `/tools/discover`     | GET    | Proxy to GraphToolServer vector discover          |

> **Note**: Chat is handled by NanoClawBridge at `ws://127.0.0.1:18789`. The session endpoints
> return `nanoclaw_ws_url` with an auth token that the Chrome extension uses to connect directly.

---

## Setup

### 1 — Secrets

Fill in `D:\FFS0_Factory\secrets\api_keys.env`:

```bash
# LLM provider (gemini | anthropic | google-vertex)
COLLIDER_AGENT_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...

# For google-vertex (Claude on GCP, ADC auth):
# COLLIDER_AGENT_PROVIDER=google-vertex
# VERTEX_PROJECT_ID=your-gcp-project
# VERTEX_REGION=us-east5

# For anthropic direct (requires paid API credits):
# COLLIDER_AGENT_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Collider auth
COLLIDER_USERNAME=Sam
COLLIDER_PASSWORD=Sam

# Optional: per-role pre-seeded accounts (fall back to above if blank)
COLLIDER_SUPERADMIN_USERNAME=Sam
COLLIDER_SUPERADMIN_PASSWORD=Sam
```

### 2 — Start

```powershell
cd workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderAgentRunner
uv run uvicorn src.main:app --reload --port 8004
```

Verify: <http://localhost:8004/health>

### 3 — Prerequisites

ColliderDataServer (:8000) and ColliderGraphToolServer (:8001) must be running
first.

---

## ContextSet Schema

```python
class ContextSet(BaseModel):
    role: Literal["superadmin", "collider_admin", "app_admin", "app_user"]
    app_id: str                                    # ACL boundary application
    node_ids: list[str]                            # nodes to bootstrap and merge
    vector_query: str | None = None                # semantic tool discovery
    visibility_filter: list[str] = ["global", "group"]
    depth: int | None = None                       # bootstrap depth (None = full subtree)
    inherit_ancestors: bool = False                # prepend parent node contexts root-first
```

---

## Multi-Provider Support

The runner selects the LLM provider from `COLLIDER_AGENT_PROVIDER`:

| Provider        | Env var             | Default model       |
| --------------- | ------------------- | ------------------- |
| `gemini`        | `GEMINI_API_KEY`    | `gemini-2.5-flash`  |
| `anthropic`     | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| `google-vertex` | ADC (gcloud)        | `claude-sonnet-4-6` |

Override the model with `COLLIDER_AGENT_MODEL=gemini-2.5-pro`.

> **Note**: `COLLIDER_AGENT_*` prefix avoids collision with the shared FFS2 `AGENT_MODEL` env var.

---

## Source Layout

```text
src/
├── main.py                  ← FastAPI app + session endpoints
├── api/
│   └── root.py              ← POST /agent/root/session (root orchestrator)
├── schemas/
│   └── context_set.py       ← ContextSet, SessionPreview, SessionResponse
├── core/
│   ├── config.py            ← Settings (reads api_keys.env; COLLIDER_AGENT_* vars)
│   ├── auth_client.py       ← Per-role JWT cache + login
│   ├── collider_client.py   ← NanoClaw bootstrap + ancestors + tool execution
│   ├── graph_tool_client.py ← GraphToolServer vector discover proxy
│   ├── session_store.py     ← In-memory session cache (4h TTL; 24h for root)
│   └── workspace_writer.py  ← Writes CLAUDE.md + .mcp.json, skills/ to NanoClaw workspace
└── agent/
    └── runner.py            ← compose_context_set() → ComposedContext dataclass
```

---

## Configuration

All settings via `pydantic-settings`. Config is read from (in order):

1. Environment variables
2. `D:/FFS0_Factory/secrets/api_keys.env`
3. `.env` (local override)

Key settings:

| Env var                   | Default                 | Description                                       |
| ------------------------- | ----------------------- | ------------------------------------------------- |
| `COLLIDER_AGENT_PROVIDER` | `anthropic`             | Supported: `gemini`, `anthropic`, `google-vertex` |
| `COLLIDER_AGENT_MODEL`    | *(per-provider)*        | Override model name                               |
| `PORT`                    | `8004`                  | Server port                                       |
| `DATA_SERVER_URL`         | `http://localhost:8000` | ColliderDataServer base URL                       |

> **Note**: `COLLIDER_AGENT_*` replaces the legacy `AGENT_MODEL`. Ensure `PORT` (8004) is used instead of `AGENT_RUNNER_PORT`.
