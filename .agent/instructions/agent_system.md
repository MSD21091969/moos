# FFS0 Factory - Agent System Instruction

> Root workspace instruction. Inherited by all child workspaces.

## Role

You are assisting in the **FFS0_Factory** root workspace — the top-level container for the Collider ecosystem.

## Architecture Model

```
.agent/ = workspace state = ready for execution
```

All components (tools, workflows, applications) are the **same pattern at different scales**:

- **Tool**: Atomic function (JSON schema)
- **Workflow**: Sequence of tools (YAML+Markdown)
- **Application**: Template cluster (graph)

All derivable via `create_model()` — discoverable in registry.

## Three Domains

| Domain   | Apps            | Context Source            |
| -------- | --------------- | ------------------------- |
| FILESYST | IDE (App X)     | `.agent/` folders         |
| CLOUD    | Apps 1-N        | `node.container` field    |
| ADMIN    | Account (App Z) | `account.container` field |

## x1z Application

The Collider system itself is application **x1z** — a self-hosting recursive tree:

- **Container-nodes** (DB): rows in `nodes` table with `path`, `container` JSON, `metadata_`
- **View-components** (FFS6): Vite + React pages that render container-nodes
- These are two separate but related graphs (NOT 1:1)
- `metadata_` field links nodes to frontend: `frontend_app`, `frontend_route`
- Node tree: `/`, `/admin`, `/admin/assign-roles`, `/admin/grant-permission`

## FFS Hierarchy

```
FFS0_Factory/
├── .agent/                          <- This context (ROOT)
├── models/                          <- Core Pydantic models
├── sdk/                             <- SDK catalog
│
└── workspaces/
    └── FFS1_ColliderDataSystems/    <- IDE workspace
        ├── FFS2.../                 <- Backends
        └── FFS3.../                 <- Frontend + Apps
```

## Key Principles

1. **`.agent/` = workspace state** — ready for execution
2. **Components scale** — Tool/Workflow/App are same pattern
3. **User workflows = templates** — via `create_model()` derivation
4. **Single source of truth** — Knowledge flows down from root

## Inheritance

Child workspaces inherit via `manifest.yaml`:

- `rules/` — sandbox, identity, code_patterns, env_and_secrets
- `configs/` — users, api_providers, defaults

## Running

See `FFS1_ColliderDataSystems/.agent/knowledge/RUNNING.md`

## NanoClaw Agent Integration

Agent sessions are composed by **ColliderAgentRunner** (:8004), which bootstraps node
contexts from the DataServer and writes workspace files to `~/.nanoclaw/workspaces/`.
The **NanoClawBridge** (:18789) spawns Claude Code CLI processes and streams events
back to the Chrome Extension via WebSocket. Tools execute through MCP on the
GraphToolServer (:8001/mcp/sse).

---

_v4.0.0 — 2026-02-22_
