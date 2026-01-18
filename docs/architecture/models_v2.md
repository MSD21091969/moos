# models_v2 Architecture

> Definition-centric architecture. No Container model.

## Core Objects

| Object         | Role                       | File            |
| -------------- | -------------------------- | --------------- |
| **Definition** | Functor - I/O interface    | `definition.py` |
| **Graph**      | Owns nodes/edges, topology | `graph.py`      |
| **Node**       | Graph position             | `node.py`       |
| **Edge**       | Morphism between nodes     | `edge.py`       |
| **Port**       | I/O slot with type         | `port.py`       |

## Builder API

```python
from models_v2 import ColliderGraphBuilder

g = ColliderGraphBuilder(name="MyFlow")
step1 = g.add_empty_node("step1")
step2 = g.add_empty_node("step2")
g.connect(g.start, step1.id)
g.connect(step1.id, step2.id)
g.connect(step2.id, g.end)

graph = g.build()
```

## Tensor Operations

```python
tensor = graph.topology.to_tensor()
reach = tensor.reachability()
inputs, outputs = tensor.boundary_indices()
```

## Embeddings

```python
embeddings = graph.topology.embed_nodes()
similarity = embeddings[id1].similarity(embeddings[id2])
```

## Node Types

| Type     | Class          | Purpose         |
| -------- | -------------- | --------------- |
| Empty    | `EmptyNode`    | Placeholder     |
| Step     | `StepNode`     | Executable code |
| Decision | `DecisionNode` | Branching       |
| Subgraph | `SubgraphNode` | Nested graph    |

## File Structure (19 files)

```
models_v2/
├── __init__.py
├── config.py
├── categorical_base.py
├── scope_enforcer.py
├── port.py
├── node.py
├── edge.py
├── wire.py
├── graph.py
├── definition.py
├── composite_boundary.py
├── edge_condition.py
├── step_node.py
├── decision_node.py
├── subgraph_node.py
├── collider_graph.py
├── builder.py
├── graph_tensor.py
└── node_embedding.py
```
