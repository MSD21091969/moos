# Phase 7 Specification: Collider Pilots & Dynamic Definitions

> **Status**: Draft (User Proposing)
> **Focus**: Runtime Context, Tool Discovery, and Artifact Interfaces

## 1. The Collider Pilot Family

A new class of User-Faced Agents designed to guide the user and interact with the graph topology.

### Core Responsibilities

1.  **User Guidance**: Frontend-integrated assistance.
2.  **Graph Querying**: Identifying "Clusters" (Subgraphs) based on topological properties (e.g., high edge:node ratio) or user selection.
3.  **Tool usage**: Treating these clusters as "stateless data machines" (tools).

## 2. Dynamic Definition Objects

Instead of static tools, Pilots use **Definition Objects** derived from graph clusters.

- **Origin**: Created from a Cluster/Subgraph.
- **Mechanism**: Uses `pydantic.create_model` to dynamically generate I/O schemas based on the cluster's inputs/outputs.
- **Integration**: These objects are injected into the Pilot's "Tool Discovery" context (Deep Agent pattern).
- **Role**: Defines the "Dependency" or "Tool" that the Pilot operates on.

## 3. Worker Tiers

### A. Backend Workers (Maintenance)

- **Role**: Graph maintenance and indexing.
- **Task**: Indexing description fields and edges to Clusters.
- **Storage**: Stored as "Subnodes" (Flat Index) via `GraphBuilder`.

### B. Runtime Workers (Execution)

- **Role**: "Doing the job at the leaves".
- **Target**: Atomic Definitions (scripts/tools).
- **Contract**: Strict Pydantic declaration of Logic, Models, Methods, and I/O.
- **Nature**: Stateless data machines.

## 4. The "Container" Concept (Refined)

**Previous Misconception**: Container as a build-time dependency.
**New Definition**: Container as a **User Interface & Artifact Lifecycle Object**.

- **Timing**: Instantiated _after_ a Pilot run.
- **Role**: Holds artifacts (Canvases, Results) produced by the run.
- **Persistence**: Exists post-runtime to allow users to view/share results.
- **Analogy**: "The object holding the canvas in Agent Studio."
- **Future**: Bridge between Local Workspace and Shared Network.

## 6. The Container Bridge (Session & Artifacts)

The `Container` is the bridge between the **User**, the **Pilot**, and the **Artifacts**.

### A. Core Models (`models_v2/container.py`)

These models align with the Agent Studio `sqlite` schema but are defined as portable Pydantic objects.

1.  **UserObject**: Identity and Auth.
    - `id`: UUID
    - `email`: str
    - `role`: str (ADMIN, ACCOUNTUSER)

2.  **Container**: The Session Context.
    - `id`: UUID
    - `owner_id`: UUID (User)
    - `definition_id`: UUID (The Graph/Tool Definition used)
    - `artifacts`: List[ArtifactReference] (Canvases, Files)
    - `context`: Dict (Chat history, shared state)
    - `acl`: List[AccessControlEntry]

### B. Lifecycle

1.  **Creation (POST)**: User creates a Container (e.g., "Project X").
2.  **Runtime**: Pilot is instantiated _within_ the Container context. Pilot tools (DefinitionObjects) are loaded.
3.  **Execution**: Pilot runs, modifies artifacts (e.g., updates a Canvas).
4.  **Persistence**: Artifacts are saved to the Container.
5.  **Sharing**: ACLs allow other users to view/edit the Container content.

### C. Registry

A `ContainerRegistry` (likely in Backend) manages the CRUD and ACL checks for these objects.
