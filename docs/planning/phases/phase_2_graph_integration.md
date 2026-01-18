# Phase 2: Graph Integration 🚧 ACTIVE

## Objective

Integrate pydantic-graph (beta) with Container/Link/Definition models to provide graph execution, topology management, and composite Definition I/O aggregation.

## Duration

Start: 2026-01-14  
Target: TBD (research-driven)

## Research Foundation

**Completed**: Gemini 3.0 Deep Research on pydantic-graph  
**Findings**: `knowledge/research/pydantic_graph/findings.md`  
**Recommendation**: Use **pydantic-graph.beta** for parallel execution and enhanced I/O typing

## Deliverables

### 2.1: Model Mapping ⏳

**Goal**: Map Container/Link/Definition to pydantic-graph constructs

- [ ] Create `parts/graph/` module
- [ ] Implement `container_to_graph()` converter
- [ ] Implement `graph_to_container()` deserializer
- [ ] Handle R=1 vs R>1 distinction
- [ ] Map Link.predecessors/successors to Graph edges

**Reference**: `knowledge/research/pydantic_graph/model_mapping.md`

### 2.2: Graph Builder ⏳

**Goal**: Programmatic graph construction from UX layout

- [ ] Implement `GraphBuilder` wrapper
- [ ] Add `populate_topology_from_visual()` algorithm
- [ ] Topological sort for execution order
- [ ] DAG validation (cycle detection)
- [ ] Boundary detection (input/output nodes)

**Reference**: `knowledge/development/graph_integration_roadmap.md`

### 2.3: Graph Execution ⏳

**Goal**: Execute Container graphs with DeepAgent nodes

- [ ] Inject DeepAgent instances as node executors
- [ ] Implement `execute_container_graph()` runtime
- [ ] Handle parallel execution (Fork/Join)
- [ ] State tracking with `GraphRun`
- [ ] Error handling and rollback

**Reference**: `knowledge/development/execution_strategy.md`

### 2.4: Persistence Integration ⏳

**Goal**: Store pydantic-graph structures in SQLite

- [ ] Extend `ColliderBackend` with graph serialization
- [ ] Round-trip: DB ↔ pydantic-graph
- [ ] Persist `GraphRun` state
- [ ] Query API for graph introspection

### 2.5: Visualization ⏳

**Goal**: Generate Mermaid diagrams with visual hints

- [ ] Implement `graph_to_mermaid()` with positioning
- [ ] Use Link.visual_x/visual_y for layout
- [ ] Integration with existing Collider UI

## Success Criteria

✅ Can create pydantic-graph from Container/Link  
✅ Can execute graph with DeepAgent-powered nodes  
✅ Can persist graphs to SQLite  
✅ Can generate Mermaid diagrams  
✅ All tests passing

## Dependencies

- `pydantic-graph.beta` (add to pyproject.toml)
- Existing models (Container, Link, Definition)
- Existing backends (ColliderBackend)
- DeepAgent template

## Risks & Mitigations

**Risk**: pydantic-graph.beta API changes  
**Mitigation**: Pin version, monitor releases

**Risk**: Performance with large graphs  
**Mitigation**: Implement pagination, lazy loading

**Risk**: Complex nested graphs (R>1)  
**Mit igation**: Start with R=1, iterate

## Next Phase

→ **Phase 3: Composite Definitions** - I/O aggregation and UX topology builder
