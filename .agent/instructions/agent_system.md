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

All derivable via `create_model()` → discoverable in registry.

## Three Domains

| Domain   | Apps            | Context Source            |
| -------- | --------------- | ------------------------- |
| FILESYST | IDE (App X)     | `.agent/` folders         |
| CLOUD    | Apps 1-N        | `node.container` field    |
| ADMIN    | Account (App Z) | `account.container` field |

## FFS Hierarchy

```
FFS0_Factory/
├── .agent/                          ← This context (ROOT)
├── models_v2/                       ← Core Pydantic models
├── parts/                           ← SDK catalog
│
└── workspaces/
    └── FFS1_ColliderDataSystems/    ← IDE workspace
        ├── FFS2.../                 ← Backends
        └── FFS3.../                 ← Frontend + Apps
```

## Key Principles

1. **`.agent/` = workspace state** — ready for execution
2. **Components scale** — Tool/Workflow/App are same pattern
3. **User workflows = templates** — via `create_model()` derivation
4. **Single source of truth** — Knowledge flows down from root

## Inheritance

Child workspaces inherit via `manifest.yaml`:

- `rules/` — sandbox, identity, code_patterns
- `configs/` — users, api_providers, defaults

## Running

See `FFS1_ColliderDataSystems/.agent/knowledge/RUNNING.md`

---

_v2.0.0 — 2026-02-07_
