# Architecture Overview

> **Core Insight**: The `.agent` folder IS the workspace and its state.

## What is `.agent/`?

A `.agent/` folder defines a **workspace** — a self-contained context that:

- Has **purpose** (what it does)
- Has **relations** (links to other workspaces)
- Is **ready for execution** (agent or user can engage immediately)

## Folder Structure

```
.agent/
├── manifest.yaml       ← Inheritance, permissions, graph binding
├── index.md            ← Identity and purpose
│
├── instructions/       ← WHO (role, capabilities)
├── rules/              ← WHAT constraints apply
├── skills/             ← HOW to do complex tasks
├── tools/              ← WHAT atomic actions available
├── workflows/          ← WHAT sequences to run
├── configs/            ← SETTINGS for this workspace
└── knowledge/          ← REFERENCE docs
```

## Key Properties

| Property       | Meaning                                           |
| -------------- | ------------------------------------------------- |
| **State**      | `.agent/` fully describes current workspace state |
| **Executable** | Agent can run immediately with this context       |
| **Composable** | Workspaces can nest (parent/child)                |
| **Derivable**  | Workflows become tools via `create_model()`       |

## Product of a Workspace

A **capable container** (depending on `.agent/` purpose) produces:

1. **Workflows** → become tools via `create_model()`
2. **Tool definitions** → discoverable in registry
3. **Sub-workspaces** → new nodes in graph

User-made workflows are **equivalent to admin templates** — simpler clusters but same architecture.
