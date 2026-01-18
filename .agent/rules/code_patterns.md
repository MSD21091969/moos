# Factory Code Patterns

**Purpose**: Core patterns for Factory code generation  
**Related**: `math_testing.md`, `math_coding_style.md`, `math_maintenance.md`

---

## Core Models

### Container

Inherits `CategoryObject` + `ScopeEnforcer`.

```python
from models.container import Container

container = Container(
    name="MySpace",
    scope_depth=1,  # R-value
)
```

### Link

Morphism with composition support.

```python
from models.link import Link

link = Link(
    owner_id=container_a.id,      # source
    eastside_container_id=container_b.id,  # target
)

# Composition
composed = link_ab.compose(link_bc)  # A→C
```

### Definition

Functor. AtomicDefinition or CompositeDefinition.

```python
from models.definition import AtomicDefinition, CompositeDefinition, Port

atomic = AtomicDefinition(
    name="Transform",
    input_ports=[Port(name="in", type_schema={}, scope_depth=1)],
    output_ports=[Port(name="out", type_schema={}, scope_depth=1)],
)
```

### Wire

Port connection with scope validation.

```python
from models.wire import Wire

wire = Wire(source_port=port_a, target_port=port_b)
# Validates: same R-level, direction, type compatibility
```

---

## Agent Patterns

### DeepAgent

```python
from agent_factory.templates import DeepAgent

agent = DeepAgent(
    user=user,
    model="ollama:llama3.1:8b",
    toolsets=[ContainerToolset()],
)
```

### Toolset

```python
class MyToolset:
    def my_tool(self, arg: str) -> dict:
        """Tool docstring becomes description."""
        return {"result": arg}
```

---

## File Structure

```
models/           # Pydantic models only
parts/toolsets/   # Reusable tools
templates/        # Agent templates
runtimes/         # State backends
interfaces/       # UI adapters
knowledge/        # AI context (see index.md)
```

---

## Quick Rules

| Pattern     | Do                           | Don't            |
| ----------- | ---------------------------- | ---------------- |
| IDs         | `UUID`                       | `int`, `str`     |
| Scope       | Use `scope_depth` field      | Implicit nesting |
| Composition | `Link.compose()`             | Manual traversal |
| Validation  | Pydantic validators          | `__init__` logic |
| Imports     | stdlib → third-party → local | Random order     |

---

## Math Core

See `knowledge/mathematics/` for:

- Category theory (Objects, Morphisms)
- Scope mechanics (R-values, promotion)
- Boundary theory (tri-method I/O)
- Tensor graphs (matrix operations)
- Embeddings (GNN, manifold)
