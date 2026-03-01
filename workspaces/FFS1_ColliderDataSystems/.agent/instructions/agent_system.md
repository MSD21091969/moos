# Agent System Instruction (MO:OS Context)

> IDE code assist instruction for MO:OS / ColliderDataSystems workspace.

## Identity & Category Theory (MO:OS)

You are a code assistant operating within the
**MO:OS (Meta-Operating System) Harness**. The architecture of this system is
fundamentally built on functional programming and category theory principles.

This filesystem (`FFS` folders) is not just a repository; it is a **pure function** mapping human-authorable state into graph-addressable runtime context.

### The Functorial Model

1. **The Graph as the Monad:**
   The core unit of state is the `NodeContainer`. Both users and applications are modeled identically as trees of these containers.
   - `UserContext` = `[RootContainerID]` (A list of permitted root seeds)
   - `Application` = A sub-graph of `NodeContainers` (Access-controlled content)

2. **Hydration (The Functor):**
   The `FFS` filesystem is the **authoring format** (the source category).
   The database is the **runtime format** (the target category).
   The `Seeder` acts as the functor mapping `f: Filesystem -> Database`,
   ensuring that the tree structure and context hierarchy are preserved.

3. **Application 1XZ (my-tiny-data-collider):**
   The current workspace (FFS1-6) represents a specific template closure.
   When hydrated, this template produces a specific `ContainerList`
   representing application `1XZ`.

4. **Context Composition (The Fold):**
   Context is never monolithic. When an agent is instantiated, the
   `AgentRunner` performs a `fold` (or reduce) operation up the path from the
   selected leaf node to the `SubRootContext` (app `1XZ`), and finally to the
   absolute root (`MO:OS harness main loop`). The result is a pure, immutable
   context stream pushed to the LLM agent via gRPC.

## Technical Stack (2026 NanoClaw Era)

**Component Status & Mapping:**

| Component       | Port  | Role                                     |
| --------------- | ----- | ---------------------------------------- |
| DataServer      | 8000  | Pure state mutations (CRUD), Hydration   |
| GraphToolServer | 8001  | Tool Registry & execution routing (gRPC) |
| VectorDbServer  | 8002  | Semantic search mapping (ChromaDB)       |
| AgentRunner     | 8004  | Context Reducer & Streamer (gRPC)        |
| NanoClawBridge  | 18789 | Agent Runtime (WebSocket side-effects)   |
| Frontend (ffs6) | 4200  | Pure visual projection of DB state       |

## Development Rules (Functional First)

1. **Structure == Data**: Changes to `.agent` folders must reflect valid state mutations that can be cleanly mapped to DB fields via the seeder function.
2. **No Global State (Monolithic Context)**: Everything is graph-addressable.
   The agent only receives the precise context projected by the
   `AgentRunner`'s reduce function for a given node.
3. **Event-Driven Context**: Context reaches the runtime purely via gRPC delta
   streams (`AgentRunner` -> `NanoClawBridge`), ensuring the agent always reacts
   to the latest immutable state snapshot.

*(Refer to `D:\FFS0_Factory\CLAUDE.md` and `.agent/workflows/conversation-state-rehydration.md` for primary directives.)*
