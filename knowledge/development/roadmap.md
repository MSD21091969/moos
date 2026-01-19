# Collider Development Roadmap

## Completed Phases

### Phase 1-3: Foundation + Graph Builder ✅

- `models_v2/` architecture
- `ColliderGraphBuilder` API
- Flat index, serializable conditions

### Phase 4: Tensor Layer ✅

- `GraphTensor` for GPU operations
- `NodeEmbedding` for similarity search
- Adjacency matrix, reachability

### Phase 5: Application Expansion (Completed) ✅

- **Backend Template**: FastAPI + SSE (`parts/templates/backend`).
- **Tool Migration**: Generic skills moved to Factory.
- **Agent Studio**: Confirmed as Reference Implementation.

### Phase 6: Application Assembly (Completed) ✅

- **Collider Backend**: Instantiated from Factory Template.
- **Collider Frontend**: Re-initialized with React+Vite+Tailwind.
- **Verification**: Full stack healthy (Frontend, Backend, Runtime).

---

## Phase 7: Visual UX & Agent Integration (Active)

**Goal**: Transform the scaffolding into a functional "Data Collider" where "Pilots" drive "Clusters" of tools.

### Deliverables

1.  **Collider Pilot Family**: User-faced agents context-aware of Graph Clusters.
2.  **Dynamic Definitions**: `DefinitionObject` utilizing `pydantic.create_model` to wrap Subgraphs as Tools.
3.  **Visual UX**: `react-flow` Canvas for selecting Clusters and viewing "Container" artifacts.
4.  **Runtime**: Workers for Graph Maintenance (Backend) and Leaf Execution (Runtime).
