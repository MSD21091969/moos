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

---

## Phase 4.5: Collider Backend (Next)

**Goal**: Working backend to build/test graphs before visual UX.

### Deliverables

| Component        | Purpose                          |
| ---------------- | -------------------------------- |
| `backend/api/`   | FastAPI routes for graph CRUD    |
| `backend/db/`    | Fast database (SQLite or DuckDB) |
| `backend/cli.py` | Terminal CLI for graph ops       |
| Python scripts   | Build graphs programmatically    |

### Testing Plan

1. Build graphs via Python scripts
2. Test via CLI commands
3. Integrate with Collider Pilot (tools/workflows)
4. Validate with real agent execution

### Database Options

| Option | Pros                      | Cons                      |
| ------ | ------------------------- | ------------------------- |
| SQLite | Simple, file-based        | Limited concurrent writes |
| DuckDB | Analytics-optimized, fast | Less mature               |
| LiteFS | SQLite + replication      | Requires setup            |

**Recommendation**: SQLite for simplicity, move to LiteFS for production.

---

## Phase 5: Agent Integration

After backend is working:

- `agent_binding.py` — StepNode ↔ Agent
- `tool_generator.py` — Definition → Tools

---

## Phase 6: Visual UX

After agents work:

- React + Three.js frontend
- WebSocket real-time sync
- 3D graph editor
