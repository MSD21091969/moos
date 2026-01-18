"""Collider Models v2 - Definition-Centric Architecture.

Core objects:
- Definition (AtomicDefinition, CompositeDefinition) - THE CORE
- Graph, Node, Edge - topology management
- Port, Wire - I/O interface
- ColliderGraphBuilder - graph construction API

No Container model - graph logic handles topology.
"""
from models_v2.config import (
    MAX_RECURSION_DEPTH,
    VALIDATE_CATEGORY_LAWS,
    VALIDATE_BOUNDARY_TRI_METHOD,
)
from models_v2.categorical_base import (
    CategoryObject,
    Morphism,
    Functor,
    compose_morphisms,
    verify_associativity,
    verify_identity_laws,
)
from models_v2.scope_enforcer import ScopeEnforcer
from models_v2.port import Port
from models_v2.node import Node
from models_v2.edge import Edge, WireSpec
from models_v2.wire import Wire
from models_v2.graph import Graph
from models_v2.definition import Definition, AtomicDefinition, CompositeDefinition
from models_v2.composite_boundary import BoundaryDerivation, derive_composite_boundary

# Builder modules
from models_v2.edge_condition import (
    EdgeCondition,
    CompositeCondition,
    when_equal,
    when_greater,
    when_less,
    when_true,
    when_false,
    when_none,
    when_contains,
)
from models_v2.step_node import StepNode, EmptyNode
from models_v2.decision_node import DecisionNode, DecisionBranch
from models_v2.subgraph_node import SubgraphNode
from models_v2.collider_graph import ColliderGraph
from models_v2.builder import ColliderGraphBuilder, ColliderState, create_builder

# Tensor layer
from models_v2.graph_tensor import GraphTensor
from models_v2.node_embedding import NodeEmbedding, EmbeddingGenerator, EmbeddingIndex


__all__ = [
    # Config
    "MAX_RECURSION_DEPTH",
    "VALIDATE_CATEGORY_LAWS",
    "VALIDATE_BOUNDARY_TRI_METHOD",
    # Category Theory
    "CategoryObject",
    "Morphism",
    "Functor",
    "compose_morphisms",
    "verify_associativity",
    "verify_identity_laws",
    # Scope
    "ScopeEnforcer",
    # Core Objects
    "Port",
    "Node",
    "Edge",
    "WireSpec",
    "Wire",
    "Graph",
    # Definition - THE CORE
    "Definition",
    "AtomicDefinition",
    "CompositeDefinition",
    # Boundary Derivation
    "BoundaryDerivation",
    "derive_composite_boundary",
    # Builder API
    "ColliderGraphBuilder",
    "ColliderState",
    "create_builder",
    "ColliderGraph",
    "StepNode",
    "EmptyNode",
    "DecisionNode",
    "DecisionBranch",
    "SubgraphNode",
    # Edge Conditions
    "EdgeCondition",
    "CompositeCondition",
    "when_equal",
    "when_greater",
    "when_less",
    "when_true",
    "when_false",
    "when_none",
    "when_contains",
    # Tensor Layer
    "GraphTensor",
    "NodeEmbedding",
    "EmbeddingGenerator",
    "EmbeddingIndex",
]
