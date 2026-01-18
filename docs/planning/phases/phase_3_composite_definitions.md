# Phase 3: Composite Definitions 📋 PLANNED

## Objective

Implement composite Definition creation with I/O aggregation from dependency boundaries and UX grid-based topology building.

## Duration

Target: After Phase 2 completion

## Prerequisites

- ✅ Phase 1: Foundation complete
- ⏳ Phase 2: Graph Integration complete

## Deliverables

### 3.1: Boundary Detection

**Goal**: Auto-detect input/output boundaries from Link topology

- [ ] Implement `find_input_boundaries()` (predecessors == [])
- [ ] Implement `find_output_boundaries()` (successors == [])
- [ ] Mark Links with `is_input_boundary`, `is_output_boundary`
- [ ] Validate boundary consistency

### 3.2: I/O Aggregation Algorithm

**Goal**: Merge schemas from boundary Definitions

- [ ] Implement `aggregate_input_schemas()` from input boundaries
- [ ] Implement `aggregate_output_schemas()` from output boundaries
- [ ] Handle schema conflicts (overlapping fields)
- [ ] Validate type compatibility
- [ ] Generate combined Pydantic schema

**Reference**: `knowledge/development/composite_definitions.md`

### 3.3: Graph Structure Building

**Goal**: Build `graph_nodes`, `graph_edges` from Link topology

- [ ] Extract all Link IDs from selection
- [ ] Build edge list from `predecessors`/`successors`
- [ ] Validate DAG (no cycles)
- [ ] Populate `composed_from` list

### 3.4: UX Grid Topology Builder

**Goal**: Convert visual layout to execution topology

- [ ] Implement `populate_topology_from_grid()` algorithm
- [ ] Use Position.x, Position.y for spatial analysis
- [ ] Detect parallel branches (same Y coordinate)
- [ ] Populate `predecessors`/`successors` from visual edges
- [ ] Visualize execution order overlay

### 3.5: Composite Definition UI

**Goal**: User workflow for creating composite Definitions

- [ ] "Select Containers" mode in UI
- [ ] Visual boundary highlighting
- [ ] I/O schema preview
- [ ] "Create Composite" button
- [ ] Validation feedback

## Success Criteria

✅ Can select Containers on UX grid  
✅ System auto-detects boundaries  
✅ I/O schemas correctly aggregated  
✅ Composite Definition created and persisted  
✅ Can attach composite to parent Link

## Dependencies

- Phase 2: pydantic-graph integration
- UX grid system
- Definition registry

## Next Phase

→ **Phase 4: Multi-Agent Workflows** - Agents building graphs programmatically
