# Factory Workspace Status

> **Session Recap (2026-01-27)**:
>
> 1. **Global Dev Orchestrator**: Central `dev.ps1` at factory root
>    - `.\dev.ps1 collider` / `.\dev.ps1 studio` / `.\dev.ps1 -Status`
>    - Auto-syncs `.env.development` to project frontends
>    - Port management: kills existing processes before start
> 2. **Centralized Environment Config**: `d:\factory\.env.development`
>    - `VITE_DEV_SKIP_AUTH=true/false` controls login bypass
>    - Test users: superuser@test.com, lola@test.com, menno@test.com (pw: test123)
> 3. **Auth System Fixed**: snake_case→camelCase mapping in AuthContext
> 4. **Chrome Extension**: Pilot Seat working in side panel
>
> **Previous (2026-01-27 AM)**: Chrome Extension "Pilot Seat" first release

---

> **Version**: 2.4.0 | **Updated**: 2026-01-27

---

## Quick Start

```powershell
# From D:\factory
.\dev.ps1 collider           # Start Collider (backend + frontend)
.\dev.ps1 studio             # Start Agent Studio
.\dev.ps1 -Status            # Check running services
.\dev.ps1 -Stop              # Stop all services

# Edit auth settings
code .env.development        # VITE_DEV_SKIP_AUTH=true/false
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
| **User**      | Chrome Extension (Pilot)   | -    | ✅ NEW |
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

| Component            | Status                     |
| -------------------- | -------------------------- |
| Factory `.agent/`    | ✅ 6 rules, 2 instructions |
| Local UX CLI         | ✅ `local-ux` command      |
| Backend API          | ✅ SQLite persistence      |
| Frontend UI          | ✅ React/Vite              |
| **Chrome Extension** | ✅ Pilot Seat LIVE         |
| Pilots               | ✅ container, studio       |
| Runtime              | ⚠️ Config issue            |

---

## Related Docs

- [.agent/index.md](.agent/index.md) - Agent context documentation
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) - **Single Source of Truth**
