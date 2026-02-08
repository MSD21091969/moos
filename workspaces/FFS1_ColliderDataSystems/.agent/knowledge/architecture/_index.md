# Agent Architecture

> **The `.agent` structure IS the workspace** — ready for user and agent to execute, edit, or otherwise engage.

## Quick Reference

| Doc                                    | Purpose                   |
| -------------------------------------- | ------------------------- |
| [00_overview.md](./00_overview.md)     | Core concepts             |
| [01_components.md](./01_components.md) | Unified component pattern |
| [02_domains.md](./02_domains.md)       | Three domains             |
| [07_templates.md](./07_templates.md)   | Topology & Hydration      |

## Core Principle

```
.agent/ = workspace state
       = purpose + relations + capabilities
       = ready for execution
```

All components (tools, workflows, apps) are the **same pattern at different scales**.
