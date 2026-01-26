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

- **`parts/templates/`**: Stores base `AgentSpec` & `DeepAgent` templates (vstorm pattern).
- **`parts/ui/`**: Stores generic UI components (e.g., `ChatModal`, `Runner`).
- **`parts/toolsets/`**: Generic **VStorm Toolsets** (file I/O, search, etc.).

### B. Identity Separation (The Handshake)

We strictly separate **who** a user is from **what** they are doing.

- **UserID**: Represents the human identity (Authentication).
  - Scope: "I am User X."
- **AppID**: Represents a specific Application Context (Authorization).
  - Scope: "I am using App Y."
- **Flow**:
  1.  User authenticates (`UserID`).
  2.  User navigates to App (`AppID`).
  3.  Backend returns `UserContext` authorizes `UserID` → `AppID`.

### C. The Pilot (Permanent Presence)

The Pilot is the **Permanent User Interface** and core of the User Journey. It is **NOT** a transient state; it is the environment itself (initially a React Modal, eventually a Chrome Extension).

- **Nature**: Persistent, floating interface overlaying the browser.
- **Role**: Required to _open_ and interact with any App. Ideally, it is the entry point.
- **Hydration**:
  - The Pilot is "always on".
  - When an App is loaded, the Pilot "hydrates" with that App's specific `AgentSpec` (Instructions, Skills).
  - It maintains continuity across app switches.

### D. Agent Lineage

1.  **Application Agents**:
    - **Source**: Derived strictly from **Deep Agent Patterns** (Templates) found in the Factory.
    - **Equipped With**: **VStorm Toolsets** and the recursive **Knowledge System**.
2.  **Local Tools**:
    - **Source**: User's custom CLI utilities (e.g., `local-ux`).
    - **Function**: specialized local operations, separate from the unified abstract agent patterns.

---

## 2. Implementation Architecture

### Frontend (Collider Apps)

- **Framework**: React + Vite + React Flow.
- **Pilot Seat**: `ChatModal` (Persistent Overlay).
- **Logic**:
  - App Request → Backend Context (`AgentSpec` ref).
  - Pilot absorbs Context → Loads DeepAgent Pattern + Skills.

### Backend (My Tiny Data Collider)

- **Framework**: FastAPI.
- **Role**: Context Provider & Registry.

### Local Tooling (Local UX)

- **Command**: `local-ux`.
- **Scope**: Operates on `UserID` (Developer Mode).

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
