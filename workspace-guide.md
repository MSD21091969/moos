# Agent Factory - Workspace Guide

> **Current Phase**: Phase 5 - Factory as Supplier
> **Role**: The "Amazon of Parts" for the ecosystem.

## 1. Core Mission

This workspace is the **Single Source of Truth** for:

1.  **Core Architecture**: `models_v2` (Definition-Centric Pattern).
2.  **Runtime Primitives**: `AgentRunner` (Standardized Execution).
3.  **Components**: Use `parts/` to distribute generic skills, agents, and templates.

It **SUPPLIES** parts to:

- `dev-assistant` (The Headless Client / Proving Ground).
- `my-tiny-data-collider` (The End User Application).

## 2. Workspace Structure

```
D:\agent-factory/
├── models_v2/           # THE CORE: Graph, Node, Definition, UserObject
├── parts/               # THE CATALOG: Distributable Components
│   ├── runtimes/        # Execution logic (AgentRunner)
│   ├── skills/          # Generic Tools (Google, Git)
│   └── templates/       # Architecture Blueprints (Frontend Store, Backend API)
├── knowledge/           # AI Knowledge Base (Math, Specs, Progress)
├── docs/                # Human Documentation (Maintained by User)
├── agent-studio/        # (Legacy) Reference implementation
└── dev.ps1              # Tri-Server Startup Script
```

## 3. Workflow

1.  **Build/Refine Part**: Create or update a part in `agent-factory/parts`.
2.  **Verify Locally**: Use `dev-assistant` to import and test the part.
3.  **Ship**: Once verified, the part is ready for `my-tiny-data-collider`.

## 4. Technology Stack

- **Language**: Python 3.12+ (uv managed).
- **Frameworks**: Pydantic-AI, Pydantic-Deep.
- **Core Lib**: `models_v2` (Local Package).

## 5. Environment

- **Startup**: Run `.\dev.ps1` to start the Tri-Server environment.
