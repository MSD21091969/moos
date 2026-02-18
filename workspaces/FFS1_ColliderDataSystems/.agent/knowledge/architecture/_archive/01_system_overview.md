# System Overview

> Collider Data Systems is an AI/human workspace framework that services frontend applications through context-aware, container-based agent orchestration.

## What It Is

A Chrome extension + backend system that:

1. Manages hierarchical **workspaces** (called NodeContainers) that define agent behavior
2. Runs **AI agents** in the browser service worker, routed by workspace context
3. Serves **domain-specific frontend applications** through workspace-driven routing
4. Syncs workspace state between local filesystems and cloud backends

The core thesis: **workspaces ARE the applications**. Backend workspace context determines which frontend to load, what agents can do, and how systems connect.

---

## The `.agent/` Pattern

The `.agent/` folder is the universal workspace primitive. Every workspace at every scale uses the same structure:

```
.agent/
├── manifest.yaml       # Identity, inheritance, exports
├── instructions/       # Natural language directives for agents
├── rules/              # Constraints and standards
├── skills/             # Composable agent capabilities
├── tools/              # Tool definitions (JSON schemas)
├── knowledge/          # Reference documentation
├── workflows/          # Multi-step execution plans
└── configs/            # Structured configuration (YAML/JSON)
```

This structure maps 1:1 to the `NodeContainer` data type used throughout the system:

```typescript
interface NodeContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: Record<string, unknown>[];
  knowledge: string[];
  workflows: Record<string, unknown>[];
  configs: Record<string, unknown>;
}
```

A `.agent/` folder on disk and a `NodeContainer` in the database are the same concept at different scales. Local FILESYST workspaces use folders; CLOUD and ADMIN workspaces store containers as JSON in SQLite.

---

## Manifest Inheritance

Workspaces form a hierarchy through `manifest.yaml` inheritance:

```
FFS0_Factory/.agent/manifest.yaml
    │ exports: rules/sandbox.md, rules/code_patterns.md, ...
    ▼
FFS1_ColliderDataSystems/.agent/manifest.yaml
    │ includes: ../../.agent (factory)
    │ exports: instructions/agent_system.md, configs/domains.yaml, ...
    ▼
FFS2/.agent/manifest.yaml          FFS4/.agent/manifest.yaml
    (backends + extension)              (sidepanel app)
```

**Manifest fields:**

| Field | Purpose |
|-------|---------|
| `name` | Workspace identifier |
| `version` | Semantic version |
| `inheritance.strategy` | `deep_merge`, `replace`, or `disabled` |
| `includes` | Parent `.agent/` paths to inherit from |
| `local` | Paths to local context directories |
| `exports` | Files this workspace exposes to children |
| `secrets` | Runtime-injected secret names |
| `permissions` | Auth and role requirements |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER (Chrome)                             │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   Service Worker     │  │   Sidepanel / Content Scripts       │  │
│  │                      │  │                                     │  │
│  │ • ContextManager     │  │ • Imports from @collider/*          │  │
│  │ • CloudAgent         │◄─┤ • App selector + Tree/Agent views  │  │
│  │ • DomAgent           │  │ • Zustand state management         │  │
│  │ • FilesystAgent      │  │                                     │  │
│  │ • SSE listener       │  └─────────────────────────────────────┘  │
│  │ • Message router     │                                           │
│  └──────┬───────────────┘                                           │
│         │                                                           │
└─────────┼───────────────────────────────────────────────────────────┘
          │ REST / SSE / WebSocket / Native Messaging / WebRTC
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND SERVICES                             │
│                                                                     │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    │
│  │ ColliderData     │ │ ColliderGraph    │ │ ColliderVector   │    │
│  │ Server :8000     │ │ ToolServer :8001 │ │ DbServer :8002   │    │
│  │                  │ │                  │ │                  │    │
│  │ FastAPI + SQLite │ │ WebSocket        │ │ FastAPI +        │    │
│  │ REST + SSE + RTC │ │ Workflow + Graph │ │ ChromaDB         │    │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### NodeContainer as Universal Unit

Everything in the system is a NodeContainer:

- A **user account** has a `container` field (ADMIN context, secrets, settings)
- An **application node** has a `container` field (agent instructions, tools, workflows)
- A **local workspace** has a `.agent/` folder (same structure on disk)

### Three Domains

| Domain | Source | Backend | Description |
|--------|--------|---------|-------------|
| FILESYST | `.agent/` folders | Native Messaging | Local IDE workspace sync |
| CLOUD | `node.container` JSON | Data Server REST | Cloud application workspaces |
| ADMIN | `user.container` JSON | Data Server REST | Account management |

### Context-Driven Routing

The service worker's `ContextManager` determines which frontend application to load based on the active workspace's domain type. When a user selects an application, the system broadcasts a `CONTEXT_CHANGED` message that triggers the appropriate domain-specific viewer.

### Workspace-As-Application

FFS4-8 are simultaneously:
- **Workspaces**: Each has a `.agent/` folder with its own manifest, knowledge, configs
- **npm packages**: Each has an `app/` directory with `package.json`, built as a Vite library
- **Frontend applications**: Each exports React components consumed by the Chrome extension
