# Link Topology: West → North → East

## The Link Model

```python
class Link(BaseModel):
    id: UUID

    # === VERTICAL (Attachment) ===
    owner_id: UUID              # West container
    eastside_container_id: UUID # East container
    description: str            # WHY dependency exists

    # === NORTH (Definition Reference) ===
    definition_id: UUID | None

    # === HORIZONTAL (Peer Topology) ===
    predecessors: list[UUID]    # Links before this one
    successors: list[UUID]      # Links after this one
    is_input_boundary: bool
    is_output_boundary: bool

    # === UX ===
    visual_x: float
    visual_y: float
```

## Three Axes

### VERTICAL: West → East

**Attachment relationship**: Which containers are connected

- `owner_id` = West container (owns this Link)
- `eastside_container_id` = East container (dependency)
- `description` = Semantic reason for dependency

### NORTH: Definition

**Behavior reference**: What happens at this edge

- `definition_id` = Which Definition defines behavior
- **NULL when**: Link created but not yet defined
- **SET when**: User attaches Definition to Link

### HORIZONTAL: Predecessors/Successors

**Peer topology**: Execution order within graph

- `predecessors` = Links that must execute BEFORE this one
- `successors` = Links that execute AFTER this one
- **Empty for R=1**: Workspace view has no peer edges
- **Populated for R>1**: Internal graph has full topology

## Boundary Detection

```python
def is_input_boundary(link: Link) -> bool:
    """Link is input boundary if no predecessors."""
    return len(link.predecessors) == 0

def is_output_boundary(link: Link) -> bool:
    """Link is output boundary if no successors."""
    return len(link.successors) == 0
```

## Topology Population

### From UX Grid

```python
def populate_topology_from_layout(containers: list[Container]):
    """Convert visual layout to execution topology."""
    # Collect all Links
    all_links = []
    for container in containers:
        all_links.extend(container.links)

    # For each Link, find predecessors/successors
    for link in all_links:
        # Find incoming Links (predecessors)
        link.predecessors = [
            other.id for other in all_links
            if other.eastside_container_id == link.owner_id
        ]

        # Find outgoing Links (successors)
        link.successors = [
            other.id for other in all_links
            if other.owner_id == link.eastside_container_id
        ]

        # Mark boundaries
        link.is_input_boundary = len(link.predecessors) == 0
        link.is_output_boundary = len(link.successors) == 0
```

## Visual Representation

```
Container A (West)
    ├─ Link 1 ─→ Container B (East)
    │   ├─ definition_id: UUID (North)
    │   ├─ predecessors: [] (input boundary)
    │   └─ successors: [Link 2]
    │
    └─ Link 2 ─→ Container C (East)
        ├─ definition_id: UUID (North)
        ├─ predecessors: [Link 1]
        └─ successors: [] (output boundary)
```

## Integration with pydantic-graph

- **Link** → pydantic-graph **Edge**
- `predecessors`/`successors` → Graph edge list
- `is_input_boundary` → Graph start nodes
- `is_output_boundary` → Graph end nodes

See: `knowledge/research/pydantic_graph/model_mapping.md`

## Key Rules

1. **Link is the edge**: All relationships live on Link, NOT Container
2. **Definition on Link**: `definition_id` field (not on Container)
3. **Topology from peers**: `predecessors`/`successors` define execution order
4. **Visual coords**: `visual_x`/`visual_y` for UX layout, NOT execution order
