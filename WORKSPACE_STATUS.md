# Factory Workspace Status

> **Session Recap (2026-01-26)**:
>
> 1. **V-Storm Architecture Implemented**:
>    - **Identity Separation**: Backend now strictly separates User Identity from App Context.
>    - **Registry**: `backend/auth.py` dynamically maps AppIDs to `parts/skills/*.md`.
>    - **Pilot Hydration**: Frontend Pilot now fetches its configuration and skills from the backend upon initialization, injecting them into the System Prompt.
> 2. **Documentation**:
>    - `ARCHITECTURE.md` updated to v1.2.0 (Implemented).
>    - `walkthrough.md` created for verification.
> 3. **Next Steps**: Verify implementation using `walkthrough.md`.

---

> **Version**: 2.2.0 | **Updated**: 2026-01-26

---

## Quick Start

```bash
# From D:\factory
uv run local-ux agent              # Workspace agent
uv run local-ux pilot container    # Container pilot
uv run local-ux pilot studio       # Studio pilot
uv run local-ux info               # Show config
```

---

## Architecture

```
D:\factory\
├── .agent/                    # Agent context (root)
├── parts/                     # SDK components
│   ├── templates/             # AgentSpec, DeepAgent
│   ├── interfaces/            # DeepAgentCLI
│   └── runtimes/local_ux/     # CLI entry points
├── secrets/                   # API keys (not committed)
└── workspaces/
    ├── collider_apps/         # Data Collider apps
    └── maassen_hochrath/      # Agatha agent workspace
```

### 3-Tier Application (my-tiny-data-collider)

| Tier          | Service                    | Port | Status |
| ------------- | -------------------------- | ---- | ------ |
| **Control**   | Backend (FastAPI + SQLite) | 8000 | ✅     |
| **User**      | Frontend (React/Vite)      | 5173 | ✅     |
| **Execution** | Runtime (Mock)             | 8001 | ⚠️     |

---

## Agent Systems

### Workspace Agents

**Purpose**: IDE-integrated assistants for development tasks  
**Config**: `.agent/` folder hierarchy  
**Command**: `local-ux agent`

```
.agent/
├── manifest.yaml      # Inheritance
├── instructions/      # System prompt
├── rules/             # Constraints
├── knowledge/         # Domain context
├── workflows/         # Task sequences
└── configs/           # Settings
```

**Inheritance**: Factory → Workspace → Application

### Application Pilots

**Purpose**: Collider-specific agents for container/canvas management  
**Config**: `shared/collider_sdk/pilots/{id}/`  
**Command**: `local-ux pilot {id}`

| Pilot       | Purpose                           |
| ----------- | --------------------------------- |
| `container` | Container navigation, permissions |
| `studio`    | Canvas editing, file operations   |

---

## Key Components

| Component           | Location                             | Purpose                  |
| ------------------- | ------------------------------------ | ------------------------ |
| `AgentSpec`         | `parts/templates/agent_spec.py`      | Base agent configuration |
| `DeepAgentCLI`      | `parts/interfaces/cli_interface.py`  | Rich terminal UI         |
| `ColliderPilotSpec` | `shared/collider_sdk/pilots/base.py` | Pilot configuration      |
| `load_pilot()`      | `shared/collider_sdk/pilots/`        | Load pilot from folder   |

---

## Environment

| Variable              | Value                  |
| --------------------- | ---------------------- |
| `FACTORY_ROOT`        | `D:\factory`           |
| `DATALAKE`            | `I:\DATALAKE`          |
| `GEMINI_API_KEY`      | `secrets/api_keys.env` |
| `COLLIDER_PILOTS_DIR` | (optional override)    |

---

## Status

| Component         | Status                     |
| ----------------- | -------------------------- |
| Factory `.agent/` | ✅ 6 rules, 2 instructions |
| Local UX CLI      | ✅ `local-ux` command      |
| Backend API       | ✅ SQLite persistence      |
| Frontend UI       | ✅ React/Vite              |
| Pilots            | ✅ container, studio       |
| Runtime           | ⚠️ Config issue            |

---

## Related Docs

- [.agent/index.md](.agent/index.md) - Agent context documentation
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) - **Single Source of Truth**
