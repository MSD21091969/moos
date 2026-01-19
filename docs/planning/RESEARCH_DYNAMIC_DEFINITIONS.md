# Research: Dynamic Definition Objects & Recursive Topology

> **Status**: Approved Design
> **Based on**: `models_v2` core and Pydantic v2 `create_model`

## 1. conceptual Alignment

The user identified a key pattern:

> _"The pydantic I/O of a cluster define the fields of what i call a definitionobject... instantiated from pydantic's create_model class."_

This aligns perfectly with our `CompositeDefinition` architecture:

1.  **Topology (Recursive)**: `CompositeDefinitions` contain graphs of other definitions.
2.  **Boundary (Flattened)**: `derive_composite_boundary` flattens the deep topology into a set of "Surface Ports".
3.  **Model (Dynamic)**: `DefinitionObject` takes these Surface Ports and maps them to a Pydantic Model.

## 2. Implementation Strategy

### A. The Schema Mapper (`schema_adapter.py`)

We need a robust utility to convert `Port.type_schema` (JSON Schema) into Python Types compatible with `create_model`.

```python
def json_schema_to_python(schema: dict) -> type:
    # Maps {"type": "string"} -> str
    # Maps {"type": "object", "title": "MyType"} -> DynamicModel
    # recurses for nested types
```

### B. The Definition Object (`dynamic.py`)

```python
class DefinitionObject:
    def __init__(self, definition: Definition):
        self.definition = definition
        self._input_model = None
        self._output_model = None

    @property
    def InputModel(self) -> Type[BaseModel]:
        if not self._input_model:
            fields = {
                p.name: (json_schema_to_python(p.type_schema), ... if not p.is_optional else None)
                for p in self.definition.input_ports
            }
            self._input_model = create_model(f"{self.definition.name}Input", **fields)
        return self._input_model

    def to_tool(self) -> Callable:
        """Exposes this definition as a PydanticAI compatible function."""
        async def run_tool(ctx: RunContext, input_data: self.InputModel) -> self.OutputModel:
            # 1. Adapter: Model -> Port Map
            # 2. Execution: Runtime.execute(self.definition, input_data)
            # 3. Adapter: Port Map -> Model
            pass
        return run_tool
```

## 3. The Recursion "Trick"

The recursion exists in the **Data Structure** (`CompositeDefinition`), not the `DefinitionObject`.
The `DefinitionObject` is a **Lens** that views the _Result_ of the recursion (the Boundary).
This simplifies the metaprogramming significantly—we don't need to recursively build models, we just build the model for the _Interface_.

## 4. Impact on Collider Pilot

The `ColliderPilot` will effectively be "Metaprogrammed" at runtime.
Instead of:
`tools=[search, calculate]`
It will be:
`tools=[def_obj_A.to_tool(), def_obj_B.to_tool()]`

This allows the Pilot to "feel" the shape of the graph clusters it is manipulating.
