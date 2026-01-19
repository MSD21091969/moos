# Agent Factory - Workspace Guide

> **Current Phase**: Phase 7 - Visual UX & Agent Integration
> **Role**: The "Amazon of Parts" for the ecosystem.

## 1. Core Mission

This workspace is the **Single Source of Truth** and **Parts Supplier** for the ecosystem.

1.  **Core Architecture**: `models_v2` (Definition-Centric Pattern).
2.  **Runtime Primitives**: `AgentRunner` (Standardized Execution).
3.  **Components**: `parts/` (Distributable Agents, Skills, Templates).

It **SUPPLIES** parts to:

- `dev-assistant`: The **Proving Ground** (Headless Client) for verifying parts.
- `my-tiny-data-collider`: The **End User Application** (Product) assembled from parts.

## 2. Workspace Structure

```
D:\agent-factory/
├── models_v2/           # THE CORE: Graph, Node, Definition, UserObject
├── parts/               # THE CATALOG: Distributable Components
│   ├── runtimes/        # Execution logic (AgentRunner)
│   ├── skills/          # Generic Tools (Research, Coding, Vision)
│   └── templates/       # Architecture Blueprints (Backend, Persistence)
├── knowledge/           # AI Knowledge Base (Specs, Progress, Roadmap)
└── dev.ps1              # Tri-Server Startup Script (Reference)
```

## 3. The Pipeline (Factory -> DevAss -> App)

1.  **Design & Build** (Factory): Create generic, reusable parts in `agent-factory`.
2.  **Verify** (Dev-Assistant): Import the part in `dev-assistant` scripts to verify functionality in isolation.
3.  **Assemble** (Collider): Import the verified part into `my-tiny-data-collider` for production use.

## 4. Technology Stack

- **Language**: Python 3.12+ (uv managed).
- **Frameworks**: Pydantic-AI, Pydantic-Deep.
- **Core Lib**: `models_v2` (Local Package).
