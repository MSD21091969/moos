# Definition System: Atomic vs Composite

## The Definition Model

```python
class Definition(BaseModel):
    id: UUID
    name: str
    version: int
    type: Literal["atomic", "composite"]

    # I/O CONTRACT
    input_schema: dict  # Pydantic schema
    output_schema: dict

    # GRAPH STRUCTURE (composite only)
    graph_nodes: list[UUID]      # Link IDs
    graph_edges: list[dict]      # [{source, target, mapping}]
    input_boundary: list[UUID]   # Entry Link IDs
    output_boundary: list[UUID]  # Exit Link IDs

    # ATOMIC ONLY
    source_code: str | None      # Pydantic AI agent script

    # COMPOSITE ONLY
    composed_from: list[UUID]    # Contributing Definition IDs
```

## Atomic Definitions

**Characteristics**:

- Zero-graph (no internal structure)
- `source_code` contains PydanticAI agent implementation
- I/O schema from code's request/response Pydantic models
- Directly executable

**Example**:

```python
atomic_def = Definition(
    name="TextProcessor",
    type="atomic",
    input_schema={"text": {"type": "string"}},
    output_schema={"result": {"type": "string"}},
    source_code="""
from pydantic_ai import Agent

agent = Agent('ollama:llama3.1')

@agent.tool
async def process(text: str) -> str:
    return text.upper()
""",
    graph_nodes=[],  # Empty for atomic
    graph_edges=[],
)
```

## Composite Definitions

**Characteristics**:

- Full subgraph structure
- NO source_code (execution comes from child Definitions)
- I/O schema **emerged** from boundary aggregation
- Graph structure from Link topology

**Example**:

```python
composite_def = Definition(
    name="DataPipeline",
    type="composite",
    input_schema={"x": {"type": "integer"}},  # From input boundary
    output_schema={"result": {"type": "boolean"}},  # From output boundary
    graph_nodes=[link_a.id, link_b.id, link_c.id],
    graph_edges=[
        {"source": link_a.id, "target": link_b.id},
        {"source": link_b.id, "target": link_c.id},
    ],
    input_boundary=[link_a.id],  # No predecessors
    output_boundary=[link_c.id],  # No successors
    composed_from=[def_a.id, def_b.id, def_c.id],
)
```

## I/O Schema Emergence

### For Atomic Definitions

Extract from Pydantic models in source_code:

```python
# From agent code
class InputModel(BaseModel):
    x: int

class OutputModel(BaseModel):
    y: str

# Becomes
input_schema = InputModel.model_json_schema()
output_schema = OutputModel.model_json_schema()
```

### For Composite Definitions

Aggregate from boundary nodes:

```python
def create_composite_io(
    input_boundary_links: list[Link],
    output_boundary_links: list[Link],
    definition_registry: dict[UUID, Definition]
) -> tuple[dict, dict]:
    """Aggregate I/O from boundaries."""
    # Input: Merge all input boundary Definition inputs
    input_schema = {}
    for link in input_boundary_links:
        definition = definition_registry[link.definition_id]
        input_schema.update(definition.input_schema)

    # Output: Merge all output boundary Definition outputs
    output_schema = {}
    for link in output_boundary_links:
        definition = definition_registry[link.definition_id]
        output_schema.update(definition.output_schema)

    return input_schema, output_schema
```

## Graph Structure

### Atomic (Zero-Graph)

```
Definition (atomic)
├─ graph_nodes: []
├─ graph_edges: []
├─ input_boundary: []
└─ output_boundary: []
```

### Composite (Full Subgraph)

```
Definition (composite)
├─ graph_nodes: [link_a.id, link_b.id, link_c.id]
├─ graph_edges: [
│   {source: link_a.id, target: link_b.id},
│   {source: link_b.id, target: link_c.id}
│  ]
├─ input_boundary: [link_a.id]
└─ output_boundary: [link_c.id]
```

## Definition Lifecycle

### 1. Create Atomic Definition

```python
# User writes PydanticAI code
atomic_def = Definition(
    type="atomic",
    source_code="...",
    input_schema=extract_from_code(),
    output_schema=extract_from_code(),
)
```

### 2. Attach to Link

```python
link.definition_id = atomic_def.id
```

### 3. Create Composite from Selection

```python
# User selects containers on UX grid
selected_containers = [container_a, container_b, container_c]

# Extract topology
all_links = extract_all_links(selected_containers)
input_boundary = [l for l in all_links if not l.predecessors]
output_boundary = [l for l in all_links if not l.successors]

# Aggregate I/O
input_schema, output_schema = create_composite_io(
    input_boundary,
    output_boundary,
    user.definition_registry
)

# Create composite Definition
composite_def = Definition(
    type="composite",
    input_schema=input_schema,
    output_schema=output_schema,
    graph_nodes=[l.id for l in all_links],
    graph_edges=build_edges_from_topology(all_links),
    input_boundary=[l.id for l in input_boundary],
    output_boundary=[l.id for l in output_boundary],
    composed_from=[l.definition_id for l in all_links],
)
```

### 4. Attach Composite to Parent Link

```python
parent_link.definition_id = composite_def.id
# Now parent_link represents entire subgraph as single node
```

## Integration with pydantic-graph

- **Atomic Definition** → pydantic-graph **Step node** (executes source_code)
- **Composite Definition** → pydantic-graph **Graph** (subgraph)
- **input/output_schema** → Graph `InputT`/`OutputT` types
- **graph_nodes/edges** → Graph structure

See: `knowledge/research/pydantic_graph/model_mapping.md`

## Key Rules

1. **Atomic = code**: Has `source_code`, NO graph structure
2. **Composite = graph**: NO `source_code`, HAS graph structure
3. **I/O emergence**: Composite schemas come from boundary aggregation
4. **Immutable**: Once created, Definitions don't change (version instead)
