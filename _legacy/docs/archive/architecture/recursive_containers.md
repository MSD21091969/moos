# Recursive Container Architecture

## Pattern: R=0 → R=1 → R>1

### R=0: UserObject (Root)

```python
class UserObject(BaseModel):
    id: UUID
    workspace_id: UUID | None
    definition_registry: dict[UUID, Definition]
```

**Role**: Pure ownership context, NOT a space  
**Holds**: Account info, registries, workspace reference  
**NOT displayed**: As graph or visual node

### R=1: First Space (Workspace View)

```python
class UserWorkspaceContainer(BaseModel):
    owner_id: UUID  # → UserObject
    owned_container_ids: list[UUID]  # R=1 containers
```

**Role**: View layer between UserObject and Containers  
**Displays**: R=1 containers as gallery (no peer edges)  
**I/O Only**: Shows input/output boundaries from Definitions

### R>1: Nested Spaces (Peer Topology)

```python
class Container(BaseModel):
    name: str
    links: list[Link]  # Dependencies (peer topology enabled)
    position: Position  # UX coordinates
```

**Role**: Actual space with internal graph  
**Topology**: `enable_peer_topology=True` → predecessors/successors populated  
**Recursive**: Can contain nested Containers

## Key Rules

1. **R=1 containers** (viewed from workspace):

   - No peer edges (predecessors/successors empty)
   - Pure I/O boundaries
   - Displayed as gallery items

2. **R>1 containers** (internal view):

   - Full peer topology (predecessors/successors populated)
   - Graph structure visible
   - Execution order defined

3. **Links own relationships**:
   - NO `definition_id` on Container
   - ALL relationships through Link
   - Link is the relational edge

## Code Example

```python
# R=0: UserObject
user = UserObject(auth_id="local", email="user@localhost")

# R=1: Workspace (view layer)
workspace = user.create_workspace()

# R=1: First container (no peer edges)
container_a = Container(name="Container A")
workspace.add_container(container_a.id)

# Add dependency with R=1 view (no peer topology)
container_b = Container(name="Container B")
link = container_a.add_linked_container(
    container_b,
    enable_peer_topology=False  # R=1 view
)
# link.predecessors == []
# link.successors == []

# R>1: Internal view (with peer topology)
container_c = Container(name="Container C")
link2 = container_b.add_linked_container(
    container_c,
    enable_peer_topology=True  # R>1 internal graph
)
# link2.predecessors = [container_a.id]
# link2.successors = [...]
```

## Visual Representation

```
UserObject (R=0)
  └── UserWorkspaceContainer (View Layer)
       ├── Container A (R=1, no peers)
       ├── Container B (R=1, no peers)
       └── Container C (R=1, no peers)
            ├── Container D (R>1, WITH peers)
            └── Container E (R>1, WITH peers)
                 └── ... (recursive nesting)
```

## Integration with pydantic-graph

- **R=1 containers**: Map to Graph start/end nodes (I/O boundaries)
- **R>1 containers**: Map to full Graph with internal topology
- **Recursion preserved**: pydantic-graph.beta supports nested graphs

See: `knowledge/research/pydantic_graph/model_mapping.md`
