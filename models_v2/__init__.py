"""Collider Models v2 - Definition-Centric Architecture.

Core objects:
- Definition (AtomicDefinition, CompositeDefinition) - THE CORE
- Graph, Node, Edge - topology management
- Port, Wire - I/O interface
- ColliderGraphBuilder - graph construction API

No Container model - graph logic handles topology.
"""
from .config import (
    MAX_RECURSION_DEPTH,
    VALIDATE_CATEGORY_LAWS,
    VALIDATE_BOUNDARY_TRI_METHOD,
)
from .categorical_base import (
    CategoryObject,
    Morphism,
    Functor,
    compose_morphisms,
    verify_associativity,
    verify_identity_laws,
)
from .scope_enforcer import ScopeEnforcer
from .port import Port
from .node import Node
from .edge import Edge, WireSpec
from .wire import Wire
from .graph import Graph
from .definition import Definition, AtomicDefinition, CompositeDefinition
from .composite_boundary import BoundaryDerivation, derive_composite_boundary
from .identity import UserObject
from .dynamic import DefinitionObject, schema_to_python_type
from .container import Container, ArtifactReference, AccessControlEntry

# Builder modules
from .edge_condition import (
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
from .step_node import StepNode, EmptyNode
from .decision_node import DecisionNode, DecisionBranch
from .subgraph_node import SubgraphNode
from .collider_graph import ColliderGraph
from .builder import ColliderGraphBuilder, ColliderState, create_builder

# Tensor layer
from .graph_tensor import GraphTensor
from .node_embedding import NodeEmbedding, EmbeddingGenerator, EmbeddingIndex


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
    # Identity
    "UserObject",
    # Dynamic Models
    "DefinitionObject",
    "schema_to_python_type",
    # Container/Session
    "Container",
    "ArtifactReference",
    "AccessControlEntry",
]
