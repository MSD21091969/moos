# Factory Domain Knowledge

## The Factory

The Factory is the meta-research facility that sits OUTSIDE the Collider.
It provides:

- Models and base classes
- Runtime environments
- Definition templates
- Pattern analysis

## Core Entities

### Definition (Recursive)

```python
class Definition:
    children: list["Definition"]  # Recursive
    inputs: list[IOSchema]
    outputs: list[IOSchema]
```

Definitions can be:

- **Atomic**: Single, no children
- **Composite**: Has children, emerged from dependencies

### Container (Recursive)

```python
class Container:
    definition: Definition
    subgraph: list["Container"]  # Recursive
    predecessors: list[UUID]
    successors: list[UUID]
```

When a container is defined:

1. Its successors (dependents) get redefined
2. Composite definitions emerge
3. Complexity rises

### UserObject

```python
class UserObject:
    containers: list[Container]  # R=1 (root)
    definition_registry: dict[UUID, Definition]
    container_registry: dict[UUID, Container]
    composite_definition: Definition  # Emerged
```

## Three Recursions

| Entity              | Recursive Over     |
| ------------------- | ------------------ |
| Definition          | children           |
| Container           | subgraph           |
| CompositeDefinition | emerged from graph |

## @FatRuntime

Decorator and manager for running definitions:

```python
@fatruntime
class MyAgent:
    pass

runner = FatRunner.from_db(def_id)
runner.ignite(**inputs)
```

## Gödel API

The outside observer with methods:

- `assess_delta(current, proposed)` → Assessment
- `harvest_emerged(containers)` → list[Definition]
- `test_generations(def, versions)` → results
- `analyze_patterns()` → patterns
