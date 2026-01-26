# Collider Architecture (Single Source of Truth)

> **Status**: Planning Phase
> **Version**: 1.1.0 (Corrected)
> **Last Updated**: 2026-01-26

---

## 1. Core Concepts (The "Handwritten ABCs")

The architecture maps to three fundamental pillars derived from the "Handwritten ABC" insights.

### A. The Factory (Pattern Store)

**Location**: `d:/factory/parts/`
The Factory is the warehouse for reusable **Deep Agent** patterns. It stores components that define _how_ agents work, which are then hydrated with specific toolsets and knowledge.

- **`parts/templates/`**: Stores the base `DeepAgent` template (The "DNA" for all agents).
- **`parts/skills/`**: Stores granular `Skills.md` (The "Job Training").
- **`parts/ui/`**: Stores generic UI components (e.g., `ChatModal`).

### B. Identity Separation (The Layered System)

We distinguish between the **Base System** and the **Accumulated Skills**.

- **User Identity**: The authenticated human.
- **AppID**: Represents a **Skill Set** (Capabilities).
- **Admin Override**: Admins inherently possess _all_ AppIDs/Skills (Dev Purpose).
- **Layering**:
  1.  **Base Layer**: The `DeepAgent` System Instruction (Core behavior).
  2.  **Skill Layer**: `AppID`s act as "Permissions" to load specific **Skills.md**.
  3.  **Result**: The Agent is the _sum_ of the Base + Accumulated Skills from all active `AppID`s.

### C. The Pilot (First-Class Citizen)

The Pilot is the **Permanent Agent Container** and core of the User Journey.

- **Nature**: First-class citizen with its own IDENTITY and BASE INSTRUCTION.
- **Universality**:
  - **In Browser**: Pilot runs in `ChatModal`. Hydrates with `AppID` skills (e.g., Data Analysis).
  - **In CLI**: Pilot runs as `local-ux`. Hydrates with `Workspace` skills (e.g., File Management).
- **Smart Cache (Context Memory)**:
  - The Pilot **remembers** previous and simultaneous App Contexts.
  - It maintains a **Solid User Journey** with conversation history across switches.
  - It does _not_ hard reset; it updates its "Active Skills" dynamically while retaining memory.

### D. Agent Lineage (V-Storm Pattern)

1.  **DeepAgent Pattern**:
    - The single ancestor for all agents (CLI and Web).
    - Defined in `d:/factory/parts/templates/DeepAgent`.
2.  **Strict Separation**:
    - **Skills**: Markdown files in `parts/skills/` (The "Job Training").
    - **Tools**: Python modules in `parts/toolsets/` (The "Hands").
3.  **AppID Mapping**:
    - `AppID` -> List of `Skill IDs` (Markdown) + List of `Tool IDs` (Python).

---

## 2. Implementation Architecture

### Frontend (Collider Apps)

- **Framework**: React + Vite + React Flow.
- **Pilot Seat**: `ChatModal` (Persistent Agent Container).
- **Logic**:
  - Pilot Initialization (Base `DeepAgent` Spec).
  - Context Request → Backend checks `AppID`s.
  - Backend returns List of `Skills`.
  - Pilot injects `Skills` → Becomes "The Data Collider Agent".

### Backend (My Tiny Data Collider)

- **Framework**: FastAPI.
- **Role**: Identity Provider & Skill Registry.
- **Flow**: User -> Auth -> `Get_Authorized_Skills()` -> Return `[Skill_A, Skill_B]`.

### Local Tooling (Local UX)

- **Command**: `local-ux`.
- **Role**: The "Developer's Pilot".
- **Logic**:
  - Pilot Initialization (Base `DeepAgent` Spec).
  - Context: Current Directory (`.agent/`).
  - Pilot injects `Workspace Skills` (File Ops, Git).

---

## 3. Directory Structure Alignment

```
d:/factory/
├── parts/                  # (A) The Store
│   ├── templates/          # DeepAgent Templates
│   └── ui/                 # Permanent ChatModal
├── workspaces/
    └── collider_apps/
        └── applications/
            └── my-tiny-data-collider/
                ├── backend/ # (B) Registry & Context
                └── frontend/# (C) Permanent Pilot
```

---

_This document is the Single Source of Truth for all architectural decisions. Do not modify without User approval._
