# Node Architecture (models_v2)

> Replaces `Container` from v1

## Core Concept

Node is a **position in the graph**. It references a Definition but doesn't own logic.

```
Node ──(definition_id)──► Definition ──► Agent/Code
```

## Properties

| Property        | Type  | Purpose                                        |
| --------------- | ----- | ---------------------------------------------- |
| `id`            | UUID  | Unique identifier                              |
| `name`          | str   | Display name                                   |
| `definition_id` | UUID? | Links to Definition (optional for empty nodes) |
| `graph_id`      | UUID  | Parent graph                                   |
| `scope_depth`   | int   | R-value for hierarchy                          |
| `visual_x/y`    | float | Position for Three.js                          |

## Node Types

| Type     | Class          | Has Definition? | Has Code?       |
| -------- | -------------- | --------------- | --------------- |
| Empty    | `EmptyNode`    | No              | No              |
| Step     | `StepNode`     | Optional        | Yes (handler)   |
| Decision | `DecisionNode` | No              | Branching logic |
| Subgraph | `SubgraphNode` | Yes (derived)   | Inner graph     |

## Flat Index Design

All nodes stored flat with `scope_depth` attribute:

```python
nodes = [
    Node(name="outer", scope_depth=0),
    Node(name="inner1", scope_depth=1),
    Node(name="inner2", scope_depth=1),
]
```

UI derives visual nesting. Enables:

- GPU tensor operations
- O(1) adjacency matrix
- Fast boundary detection

## Related Files

- `models_v2/node.py`
- `models_v2/step_node.py`
- `models_v2/decision_node.py`
- `models_v2/subgraph_node.py`
