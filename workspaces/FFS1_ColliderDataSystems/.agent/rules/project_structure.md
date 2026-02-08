# Project Structure & Governance

> Relationship between FFS workspaces in the Collider ecosystem.

---

## Hierarchy

### FFS1: ColliderDataSystems (The Parent)

- **Role**: Governance, Orchestration, Shared Schemas.
- **Artifacts**: gRPC Protobufs, Shared Configs, Global Rules.
- **Responsibilities**:
  - Definition of the "Collider" Data Model.
  - Hosting the Central Knowledge Graph.
  - Managing User Identity & Auth.

### FFS2: ColliderBackends (The Engine)

- **Role**: Intelligence & Execution.
- **Components**:
  - `ColliderDataServer`: REST/gRPC API.
  - `ColliderGraphToolServer`: Agent Runtime.
  - `ChromeExtension`: Browser Interface / Sensor.
- **Dependency**: Inherits Rules/Schemas from **FFS1**.

### FFS3: ColliderFrontend (The Interface)

- **Role**: Human-AI Interaction Layer.
- **Components**:
  - `Portal`: Next.js Web Application.
  - `Visualizer`: Canvas-based Graph Explorer.
- **Dependency**: Consumes APIs from **FFS2**; Inherits Rules from **FFS1**.

---

## Dependency Flow

1. **Schemas** defined in FFS1 (Protobuf/Pydantic).
2. **Generators** build Types (TS/Py) for FFS2 & FFS3.
3. **FFS2** implements the API contract.
4. **FFS3** consumes the API contract.

_Changes to the Data Model must propagate from FFS1 down._

---

## Agent Context Responsibilities

- **Identity**: Managed by FFS1/Admin.
- **Session**: Managed by FFS2 (Redis/Memory).
- **Presentation**: Managed by FFS3 (Client State).
