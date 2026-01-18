# Tensor Graphs

## Concept

Flat node index → GPU-ready tensors for O(1) operations.

## Implementation (models_v2)

### GraphTensor

```python
from models_v2 import Graph, GraphTensor

graph = Graph(name="example", owner_id=uuid4())
# ... add nodes and edges ...

tensor = graph.to_tensor()  # or GraphTensor.from_graph(graph)
```

### Core Operations

| Operation    | Method                          | Complexity |
| ------------ | ------------------------------- | ---------- |
| Adjacency    | `tensor.adjacency`              | O(1)       |
| Reachability | `tensor.reachability()`         | O(N²)      |
| Boundary     | `tensor.boundary_indices()`     | O(N)       |
| Predecessors | `tensor.predecessors(idx)`      | O(N)       |
| Successors   | `tensor.successors(idx)`        | O(N)       |
| Scope filter | `tensor.scope_adjacency(depth)` | O(N²)      |

### GPU Acceleration

```python
gpu_data = tensor.to_gpu()  # Requires CuPy
# gpu_data["adjacency"] is CuPy array
```

## Node Embeddings

```python
embeddings = graph.embed_nodes(method="structural")
similarity = embeddings[n1.id].similarity(embeddings[n2.id])
```

### EmbeddingIndex (fast search)

```python
from models_v2 import EmbeddingIndex

index = EmbeddingIndex(embeddings)
similar = index.search_by_id(node_id, top_k=5)
```

## Related Files

- `models_v2/graph_tensor.py`
- `models_v2/node_embedding.py`
