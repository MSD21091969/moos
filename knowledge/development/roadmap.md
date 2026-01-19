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

**Goal**: Transform the scaffolding into a functional "Data Collider" with visual editing and agentic capabilities.

### Deliverables

1.  **Pipeline Formalization**: Document and enforce the Factory -> DevAss -> App workflow.
2.  **Visual UX**: Implement `react-flow` based Graph Editor in Frontend.
3.  **Agent Integration**: Wire up `AgentRunner` to the Backend for real-time operations.
4.  **Skills**: Import `researcher` and `coder` skills from Factory to Runtime.
