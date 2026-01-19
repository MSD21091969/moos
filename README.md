# Agent Factory

**The Source of Truth for the Collider Ecosystem.**

This repository acts as the **Parts Supplier**. It defines the core architecture (`models_v2`) and provides standard components (`parts`) for downstream applications.

## Architecture

- **`models_v2`**: The Definition-Centric Graph & Tensor Kernel.
- **`parts/runtimes`**: Standardized execution loops (`AgentRunner`).
- **`parts/skills`**: Reusable generic tools (Google, Git, Docker).
- **`parts/templates`**: Blueprints for Frontend/Backend agents.

## Usages

Installed as a python package:

```toml
dependencies = [
    "agent-factory @ file:///D:/agent-factory"
]
```

## Status

- **Phase**: 5 (Application Expansion)
- **Health**: Verified (Supply Chain Active)
