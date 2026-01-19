"""Agent Factory - Clean architecture for multi-agent systems."""
__version__ = "0.3.0"

# models_v2 is the core package
from .models_v2 import (
    Graph,
    Node,
    Edge,
    Definition,
    AtomicDefinition,
    CompositeDefinition,
    ColliderGraphBuilder,
    GraphTensor,
    NodeEmbedding,
)

__all__ = [
    "__version__",
    "Graph",
    "Node",
    "Edge",
    "Definition",
    "AtomicDefinition",
    "CompositeDefinition",
    "ColliderGraphBuilder",
    "GraphTensor",
    "NodeEmbedding",
]
