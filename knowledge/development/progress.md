# Development Progress

## Current Phase: Backend Implementation

### Completed

- [x] **models_v2** architecture (Definition-centric, no Container)
- [x] **ColliderGraphBuilder** (pydantic-graph/beta integration)
- [x] **Phase 4: Tensor Layer** (GPU-ready operations)
  - GraphTensor (adjacency, reachability, boundary)
  - NodeEmbedding (128-dim vectors, similarity)
  - Graph.to_tensor() and embed_nodes()

### In Progress

- [ ] **Phase 4.5: Collider Backend**
  - [ ] FastAPI basic API
  - [ ] Fast database (SQLite/LiteFS or DuckDB)
  - [ ] Python script graph building
  - [ ] CLI tool
  - [ ] Pilot integration testing

### Pending

- [ ] Phase 5: Agent Integration
- [ ] Phase 6: Visual UX

## Architecture Decisions

| Decision            | Rationale                       |
| ------------------- | ------------------------------- |
| Flat index          | O(1) tensor ops, GPU-ready      |
| Definition as core  | Agent tool interface            |
| pydantic-graph/beta | Builder pattern, cleaner        |
| 128-dim embeddings  | Balance of expressiveness/speed |

## models_v2 Files (19 total)

| File                                  | Purpose                  |
| ------------------------------------- | ------------------------ |
| `builder.py`                          | ColliderGraphBuilder API |
| `collider_graph.py`                   | Topology + executor      |
| `graph_tensor.py`                     | GPU tensor operations    |
| `node_embedding.py`                   | Vector embeddings        |
| `step_node.py`                        | Executable nodes         |
| `decision_node.py`                    | Conditional branching    |
| `subgraph_node.py`                    | Nested graphs            |
| `edge_condition.py`                   | Serializable conditions  |
| `graph.py`, `node.py`, `edge.py`      | Core topology            |
| `definition.py`, `port.py`, `wire.py` | I/O interface            |
