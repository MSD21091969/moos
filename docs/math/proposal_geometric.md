# Hierarchical Embedding Models - Architecture Design

**Goal**: Design Pydantic base models for `SemanticContainer` with hierarchical graph embeddings that respect scope_depth boundaries, enable GPU-accelerated vector operations, and integrate with pydantic-graph for GNN execution.

---

## User Review Required

> [!IMPORTANT]
> This design introduces **GPU-accelerated tensor fields** in Pydantic models using `pydantic-tensor` for validation. GPU operations occur at the node implementation level (PyTorch/TF), not in pydantic-graph orchestration.

> [!WARNING] > **Depth decay mitigation**: Uses learnable decay factors and skip-connections. This adds complexity but prevents over-smoothing in deep Container hierarchies.

> [!CAUTION] > **Memory considerations**: Recursive embedding composition requires careful batching for GPU memory efficiency. Large Container graphs (>1000 nodes) may need streaming or checkpoint strategies.

---

## Proposed Changes

### Component 1: Core Embedding Infrastructure

#### [NEW] [embedding_models.py](file:///d:/agent-factory/collider/embeddings/models.py)

**Base classes for all embedding types**:

```python
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, Literal, Union, TypeVar, Generic
import torch
from torch import Tensor
import numpy as np
from enum import Enum

class EmbeddingSpace(str, Enum):
    """Geometric space for embeddings"""
    EUCLIDEAN = "euclidean"
    HYPERBOLIC = "hyperbolic"  # For hierarchical structures
    SPHERICAL = "spherical"    # For normalized similarity


class BaseEmbedding(BaseModel):
    """
    Base class for all embedding types.
    Uses pydantic-tensor for GPU tensor validation.
    """
    vector: Tensor = Field(
        ...,
        description="Embedding vector (CPU or GPU tensor)"
    )
    dimension: int = Field(ge=1, le=2048)
    space: EmbeddingSpace = EmbeddingSpace.EUCLIDEAN

    # Metadata
    creation_timestamp: float = Field(default_factory=lambda: time.time())
    gradient_enabled: bool = Field(
        default=False,
        description="Whether to track gradients for training"
    )

    class Config:
        arbitrary_types_allowed = True  # For torch.Tensor

    @field_validator('vector')
    @classmethod
    def validate_tensor(cls, v: Tensor, info) -> Tensor:
        """Ensure tensor is correct shape"""
        if v.dim() != 1:
            raise ValueError(f"Embedding must be 1D tensor, got {v.dim()}D")
        dim = info.data.get('dimension')
        if dim and v.shape[0] != dim:
            raise ValueError(
                f"Tensor shape {v.shape[0]} doesn't match dimension {dim}"
            )
        return v

    @computed_field
    @property
    def device(self) -> str:
        """Current device (cpu/cuda)"""
        return str(self.vector.device)

    def to(self, device: Union[str, torch.device]) -> 'BaseEmbedding':
        """Move embedding to device"""
        return self.model_copy(
            update={'vector': self.vector.to(device)}
        )

    def normalize(self) -> 'BaseEmbedding':
        """L2 normalization for cosine similarity"""
        norm = torch.norm(self.vector, p=2)
        if self.space == EmbeddingSpace.SPHERICAL:
            # Already normalized, verify
            assert torch.isclose(norm, torch.tensor(1.0)), \
                "Spherical embedding not unit normalized"
        return self.model_copy(
            update={'vector': self.vector / norm}
        )
```

**Depth-aware embedding with decay**:

```python
class DepthAwareEmbedding(BaseEmbedding):
    """
    Embedding that accounts for scope_depth (R) position.
    Implements learnable decay factor to mitigate over-smoothing.
    """
    scope_depth: int = Field(
        ge=0,
        description="R value (0=UserObject, 1+=nested Containers)"
    )
    decay_factor: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Exponential decay per depth level (0.9 recommended)"
    )
    parent_embedding: Optional['DepthAwareEmbedding'] = Field(
        default=None,
        description="Reference to parent Container's embedding (R-1)"
    )

    @computed_field
    @property
    def depth_weighted_vector(self) -> Tensor:
        """
        Apply exponential decay based on depth.
        Formula: v_weighted = v * (decay_factor ^ scope_depth)

        Prevents deep nested Containers from dominating aggregations.
        """
        weight = self.decay_factor ** self.scope_depth
        return self.vector * weight

    def compose_with_parent(
        self,
        composition_mode: Literal['concat', 'sum', 'residual'] = 'residual'
    ) -> 'DepthAwareEmbedding':
        """
        Compose child embedding with parent (skip-connection).

        Args:
            composition_mode:
                - 'concat': [parent | child] (doubles dimension)
                - 'sum': parent + child (requires same dim)
                - 'residual': child + α*parent (learnable α, prevents over-smoothing)
        """
        if self.parent_embedding is None:
            return self

        parent_vec = self.parent_embedding.vector
        child_vec = self.vector

        if composition_mode == 'concat':
            composed = torch.cat([parent_vec, child_vec])
            new_dim = self.dimension * 2
        elif composition_mode == 'sum':
            assert parent_vec.shape == child_vec.shape, \
                "Parent and child must have same dimension for sum"
            composed = parent_vec + child_vec
            new_dim = self.dimension
        elif composition_mode == 'residual':
            # Residual with learned weight (stored in decay_factor)
            alpha = self.decay_factor
            composed = child_vec + alpha * parent_vec
            new_dim = self.dimension

        return DepthAwareEmbedding(
            vector=composed,
            dimension=new_dim,
            space=self.space,
            scope_depth=self.scope_depth,
            decay_factor=self.decay_factor,
            parent_embedding=self.parent_embedding.parent_embedding  # Chain upward
        )
```

---

### Component 2: Port Signature Embeddings

#### [MODIFY] [embedding_models.py](file:///d:/agent-factory/collider/embeddings/models.py)

**Port embedding as sub-vector**:

```python
from typing import Literal

class PortEmbedding(BaseEmbedding):
    """
    Embedding for individual Port within Container interface.
    Encodes: direction, scope_depth, type schema.
    """
    direction: Literal['North', 'East', 'West'] = Field(
        description="Link direction (N=input, E=sibling, W=output)"
    )
    port_scope_depth: int = Field(
        ge=0,
        description="Scope depth where this Port is visible"
    )
    type_schema: dict = Field(
        description="Pydantic schema of parameter type"
    )

    # Embedding sub-vectors (concatenated to form full vector)
    direction_embedding: Tensor = Field(description="One-hot or learned")
    depth_embedding: Tensor = Field(description="Positional encoding")
    type_embedding: Tensor = Field(description="Schema structure encoding")

    @computed_field
    @property
    def full_vector(self) -> Tensor:
        """Concatenate sub-vectors into full Port embedding"""
        return torch.cat([
            self.direction_embedding,
            self.depth_embedding,
            self.type_embedding
        ])

    @classmethod
    def from_port_spec(
        cls,
        direction: str,
        scope_depth: int,
        type_schema: dict,
        embedding_dim: int = 64
    ) -> 'PortEmbedding':
        """
        Factory method to create PortEmbedding from Port specification.

        Embedding strategy:
        - Direction: One-hot (3-dim) → project to embedding_dim//4
        - Depth: Sinusoidal positional encoding (embedding_dim//4)
        - Type: Schema hash → learned embedding lookup (embedding_dim//2)
        """
        # Direction encoding (one-hot → projection)
        dir_map = {'North': 0, 'East': 1, 'West': 2}
        dir_onehot = torch.zeros(3)
        dir_onehot[dir_map[direction]] = 1.0
        dir_emb = torch.nn.Linear(3, embedding_dim//4)(dir_onehot)

        # Depth encoding (sinusoidal)
        depth_emb = cls._positional_encoding(scope_depth, embedding_dim//4)

        # Type encoding (schema fingerprint)
        type_hash = hash(json.dumps(type_schema, sort_keys=True)) % 10000
        type_emb = torch.nn.Embedding(10000, embedding_dim//2)(
            torch.tensor([type_hash])
        ).squeeze()

        full_vec = torch.cat([dir_emb, depth_emb, type_emb])

        return cls(
            vector=full_vec,
            dimension=embedding_dim,
            direction=direction,
            port_scope_depth=scope_depth,
            type_schema=type_schema,
            direction_embedding=dir_emb,
            depth_embedding=depth_emb,
            type_embedding=type_emb
        )

    @staticmethod
    def _positional_encoding(depth: int, dim: int) -> Tensor:
        """Sinusoidal positional encoding for depth"""
        pe = torch.zeros(dim)
        position = torch.tensor([depth], dtype=torch.float)
        div_term = torch.exp(
            torch.arange(0, dim, 2).float() *
            -(math.log(10000.0) / dim)
        )
        pe[0::2] = torch.sin(position * div_term)
        pe[1::2] = torch.cos(position * div_term)
        return pe


class PortSignature(BaseModel):
    """
    Complete interface signature (all Ports) of a Container.
    Used for comparing Containers by interface compatibility.
    """
    north_ports: list[PortEmbedding] = Field(default_factory=list)
    east_ports: list[PortEmbedding] = Field(default_factory=list)
    west_ports: list[PortEmbedding] = Field(default_factory=list)

    @computed_field
    @property
    def signature_embedding(self) -> Tensor:
        """
        Aggregate all Port embeddings into single signature vector.
        Uses permutation-invariant pooling (sum).
        """
        all_ports = self.north_ports + self.east_ports + self.west_ports
        if not all_ports:
            return torch.zeros(64)  # Empty signature

        # Stack and sum (permutation invariant)
        port_vectors = torch.stack([p.full_vector for p in all_ports])
        return torch.sum(port_vectors, dim=0)

    def similarity_to(self, other: 'PortSignature') -> float:
        """
        Cosine similarity between Port signatures.
        Measures interface compatibility regardless of implementation.
        """
        sig1 = self.signature_embedding
        sig2 = other.signature_embedding
        return torch.nn.functional.cosine_similarity(
            sig1.unsqueeze(0),
            sig2.unsqueeze(0)
        ).item()
```

---

### Component 3: Hierarchical Container Embeddings

#### [NEW] [semantic_container.py](file:///d:/agent-factory/collider/embeddings/semantic_container.py)

**Main semantic Container model**:

```python
from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, global_mean_pool

class SemanticContainer(BaseModel):
    """
    Container with hierarchical graph embedding.
    Integrates Definition topology, Port signatures, and recursive depth.
    """
    # Core Container identity
    container_id: str = Field(description="Unique Container identifier")
    scope_depth: int = Field(
        ge=0,
        description="R value (nesting level)"
    )
    definition_type: str = Field(description="Atomic or Composite")

    # Graph structure (for GNN processing)
    graph_data: Optional[Data] = Field(
        default=None,
        description="PyTorch Geometric Data object (nodes=Definitions, edges=Links)"
    )

    # Embeddings
    structural_embedding: DepthAwareEmbedding = Field(
        description="Graph topology embedding (from GNN)"
    )
    port_signature: PortSignature = Field(
        description="Interface embedding (I/O types)"
    )
    semantic_embedding: Optional[Tensor] = Field(
        default=None,
        description="Text embedding of Definition.description (optional)"
    )

    # Hierarchical references
    parent_container: Optional['SemanticContainer'] = Field(
        default=None,
        description="Parent Container (R-1) if nested"
    )
    child_containers: list['SemanticContainer'] = Field(
        default_factory=list,
        description="Nested Containers (R+1) if composite"
    )

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def full_embedding(self) -> Tensor:
        """
        Compose all embedding types into unified Container fingerprint.

        Composition: [structural | port_sig | semantic?]
        """
        embeddings = [
            self.structural_embedding.depth_weighted_vector,
            self.port_signature.signature_embedding
        ]

        if self.semantic_embedding is not None:
            embeddings.append(self.semantic_embedding)

        return torch.cat(embeddings)

    @computed_field
    @property
    def embedding_dimension(self) -> int:
        """Total dimension of full_embedding"""
        return self.full_embedding.shape[0]

    def to_gpu(self) -> 'SemanticContainer':
        """Move all tensors to GPU"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        updates = {
            'structural_embedding': self.structural_embedding.to(device),
            'graph_data': self.graph_data.to(device) if self.graph_data else None
        }

        # Update Port embeddings
        port_sig = self.port_signature
        for port_list in [port_sig.north_ports, port_sig.east_ports, port_sig.west_ports]:
            for i, port in enumerate(port_list):
                port_list[i] = port.to(device)

        if self.semantic_embedding is not None:
            updates['semantic_embedding'] = self.semantic_embedding.to(device)

        return self.model_copy(update=updates)

    def compute_structural_embedding(
        self,
        gnn_model: torch.nn.Module,
        message_passing_steps: int = 3
    ) -> 'SemanticContainer':
        """
        Run GNN on graph_data to generate structural_embedding.

        Args:
            gnn_model: Pre-trained GNN (e.g., GCNConv stack)
            message_passing_steps: Depth of message passing (careful: over-smoothing)

        Returns:
            Updated SemanticContainer with new structural_embedding
        """
        if self.graph_data is None:
            raise ValueError("graph_data required for GNN computation")

        # Run GNN forward pass
        x = gnn_model(self.graph_data.x, self.graph_data.edge_index)

        # Global pooling to get graph-level embedding
        batch = torch.zeros(x.shape[0], dtype=torch.long)  # Single graph
        graph_embedding = global_mean_pool(x, batch)

        # Create DepthAwareEmbedding
        structural_emb = DepthAwareEmbedding(
            vector=graph_embedding.squeeze(),
            dimension=graph_embedding.shape[1],
            scope_depth=self.scope_depth,
            decay_factor=0.9,  # Default decay
            parent_embedding=self.parent_container.structural_embedding
                if self.parent_container else None
        )

        return self.model_copy(
            update={'structural_embedding': structural_emb}
        )

    def recursive_embed_children(
        self,
        gnn_model: torch.nn.Module,
        aggregation: Literal['mean', 'sum', 'max'] = 'mean'
    ) -> Tensor:
        """
        Recursively embed all child Containers and aggregate.
        Handles arbitrary depth nesting.

        Args:
            gnn_model: Shared GNN model for all levels
            aggregation: How to combine child embeddings

        Returns:
            Aggregated embedding of entire Container hierarchy
        """
        # Base case: no children (atomic Container)
        if not self.child_containers:
            return self.full_embedding

        # Recursive case: embed children first
        child_embeddings = []
        for child in self.child_containers:
            # Recursively compute child's full hierarchy embedding
            child_emb = child.recursive_embed_children(gnn_model, aggregation)
            child_embeddings.append(child_emb)

        # Aggregate children
        child_stack = torch.stack(child_embeddings)
        if aggregation == 'mean':
            children_agg = torch.mean(child_stack, dim=0)
        elif aggregation == 'sum':
            children_agg = torch.sum(child_stack, dim=0)
        elif aggregation == 'max':
            children_agg = torch.max(child_stack, dim=0).values

        # Combine this Container's embedding with aggregated children
        # Use residual connection to preserve own structure
        return self.full_embedding + 0.5 * children_agg
```

---

### Component 4: Graph Shape Comparison

#### [NEW] [graph_comparator.py](file:///d:/agent-factory/collider/embeddings/graph_comparator.py)

**Manifold distance metrics**:

```python
import torch
from torch import Tensor
from typing import Literal, Tuple
import math

class GraphShapeComparator:
    """
    Compare Container graph shapes using manifold distance metrics.
    Respects scope boundaries and hierarchical structure.
    """

    @staticmethod
    def euclidean_distance(emb1: Tensor, emb2: Tensor) -> float:
        """Standard L2 distance"""
        return torch.norm(emb1 - emb2, p=2).item()

    @staticmethod
    def cosine_similarity(emb1: Tensor, emb2: Tensor) -> float:
        """Cosine similarity (angle-based, scale-invariant)"""
        return torch.nn.functional.cosine_similarity(
            emb1.unsqueeze(0),
            emb2.unsqueeze(0)
        ).item()

    @staticmethod
    def hyperbolic_distance(u: Tensor, v: Tensor, curvature: float = -1.0) -> float:
        """
        Poincaré ball distance for hierarchical Containers.

        Formula: d(u,v) = arccosh(1 + 2||u-v||²/((1-||u||²)(1-||v||²)))

        Assumes embeddings are in Poincaré ball (||x|| < 1)
        """
        u_norm_sq = torch.sum(u ** 2)
        v_norm_sq = torch.sum(v ** 2)
        diff_norm_sq = torch.sum((u - v) ** 2)

        # Ensure within Poincaré ball
        assert u_norm_sq < 1.0 and v_norm_sq < 1.0, \
            "Hyperbolic embeddings must satisfy ||x|| < 1"

        dist = torch.acosh(
            1.0 + 2.0 * diff_norm_sq / ((1.0 - u_norm_sq) * (1.0 - v_norm_sq))
        )

        return (abs(curvature) ** 0.5) * dist.item()

    @staticmethod
    def wasserstein_distance(
        container1: 'SemanticContainer',
        container2: 'SemanticContainer'
    ) -> float:
        """
        Approximation of Wasserstein distance between Container node distributions.
        Uses Sinkhorn algorithm for efficiency.
        """
        # Extract node embeddings from graph_data
        if container1.graph_data is None or container2.graph_data is None:
            raise ValueError("graph_data required for Wasserstein distance")

        X1 = container1.graph_data.x  # [N1, feature_dim]
        X2 = container2.graph_data.x  # [N2, feature_dim]

        # Uniform weights
        a = torch.ones(X1.shape[0]) / X1.shape[0]
        b = torch.ones(X2.shape[0]) / X2.shape[0]

        # Cost matrix (pairwise distances)
        M = torch.cdist(X1, X2, p=2)

        # Sinkhorn iterations (simplified)
        K = torch.exp(-M / 0.1)  # Temperature = 0.1
        u = torch.ones_like(a)
        for _ in range(100):
            v = b / (K.T @ u)
            u = a / (K @ v)

        # Approximate Wasserstein distance
        dist = torch.sum(u.unsqueeze(1) * K * v.unsqueeze(0) * M)
        return dist.item()

    @staticmethod
    def scope_aware_distance(
        container1: 'SemanticContainer',
        container2: 'SemanticContainer',
        depth_penalty: float = 0.1
    ) -> Tuple[float, dict]:
        """
        Distance metric that penalizes depth mismatch.

        Returns (distance, breakdown):
            - distance: Combined metric
            - breakdown: {'structural': X, 'port': Y, 'depth_penalty': Z}
        """
        # Structural distance (graph topology)
        struct_dist = GraphShapeComparator.euclidean_distance(
            container1.structural_embedding.vector,
            container2.structural_embedding.vector
        )

        # Port signature distance (interface)
        port_dist = 1.0 - GraphShapeComparator.cosine_similarity(
            container1.port_signature.signature_embedding,
            container2.port_signature.signature_embedding
        )

        # Depth penalty
        depth_diff = abs(container1.scope_depth - container2.scope_depth)
        depth_cost = depth_penalty * depth_diff

        total_distance = struct_dist + port_dist + depth_cost

        return total_distance, {
            'structural': struct_dist,
            'port': port_dist,
            'depth_penalty': depth_cost
        }

    @staticmethod
    def hierarchical_similarity(
        container1: 'SemanticContainer',
        container2: 'SemanticContainer',
        mode: Literal['topology_only', 'interface_only', 'full'] = 'full'
    ) -> float:
        """
        Hierarchical similarity score [0, 1] considering full Container trees.

        Args:
            mode:
                - 'topology_only': Compare graph structure only
                - 'interface_only': Compare Port signatures only
                - 'full': Combine all factors
        """
        if mode == 'interface_only':
            return container1.port_signature.similarity_to(
                container2.port_signature
            )

        # Recursive similarity (account for children)
        own_sim = GraphShapeComparator.cosine_similarity(
            container1.full_embedding,
            container2.full_embedding
        )

        if not container1.child_containers and not container2.child_containers:
            # Leaf nodes
            return own_sim

        # Compare child sets (if both have children)
        if container1.child_containers and container2.child_containers:
            # Pairwise child similarities (greedy matching)
            child_sims = []
            for c1 in container1.child_containers:
                best_match = max(
                    GraphShapeComparator.hierarchical_similarity(c1, c2, mode)
                    for c2 in container2.child_containers
                )
                child_sims.append(best_match)
            avg_child_sim = sum(child_sims) / len(child_sims)

            # Weight: 60% own structure, 40% children
            return 0.6 * own_sim + 0.4 * avg_child_sim
        else:
            # One has children, other doesn't → structural mismatch penalty
            return own_sim * 0.5
```

---

### Component 5: pydantic-graph Integration

#### [NEW] [gnn_workflow.py](file:///d:/agent-factory/collider/embeddings/gnn_workflow.py)

**Embedding computation as pydantic-graph workflow**:

```python
from pydantic_graph import Graph, GraphDef
from pydantic import BaseModel
import torch

class EmbeddingWorkflowInputs(BaseModel):
    """Inputs to GNN embedding workflow"""
    container_graph: Data  # PyG graph
    scope_depth: int
    parent_embedding: Optional[Tensor] = None


class EmbeddingWorkflowOutputs(BaseModel):
    """Outputs from GNN embedding workflow"""
    container_embedding: DepthAwareEmbedding
    port_signature: PortSignature


# Define workflow nodes
class GraphFeatureExtractor(BaseModel):
    """Extract node/edge features from Container graph"""
    def execute(self, inputs: EmbeddingWorkflowInputs) -> dict:
        # Extract Definition types, schemas, Link directions
        # Convert to tensor features
        pass


class GNNMessagePassing(BaseModel):
    """Run message passing with scope boundary respect"""

    gnn_model: torch.nn.Module

    def execute(self, features: dict) -> dict:
        # Message passing with masking for scope boundaries
        # Nodes at different depths don't directly exchange messages
        pass


class HierarchicalPooling(BaseModel):
    """Pool node embeddings to graph-level"""

    pooling_strategy: Literal['global_mean', 'diffpool', 'topk']

    def execute(self, node_embeddings: Tensor, graph: Data) -> Tensor:
        if self.pooling_strategy == 'global_mean':
            return global_mean_pool(node_embeddings, graph.batch)
        elif self.pooling_strategy == 'diffpool':
            # Hierarchical pooling (preserves structure)
            pass


class PortSignatureExtractor(BaseModel):
    """Extract and embed Port signatures"""

    def execute(self, graph: Data, scope_depth: int) -> PortSignature:
        # Identify boundary nodes (unsatisfied ports)
        # Create PortEmbedding for each
        pass


# Define workflow graph
embedding_workflow = GraphDef(
    graph={
        'feature_extract': GraphFeatureExtractor(),
        'message_pass': GNNMessagePassing(gnn_model=...),
        'pool': HierarchicalPooling(pooling_strategy='global_mean'),
        'port_extract': PortSignatureExtractor(),
        'compose': ...  # Combine into SemanticContainer
    },
    edges=[
        ('feature_extract', 'message_pass'),
        ('message_pass', 'pool'),
        ('feature_extract', 'port_extract'),
        (['pool', 'port_extract'], 'compose')
    ]
)

# Execute workflow
async def embed_container(
    container_graph: Data,
    scope_depth: int
) -> SemanticContainer:
    """Run embedding workflow on Container"""
    inputs = EmbeddingWorkflowInputs(
        container_graph=container_graph,
        scope_depth=scope_depth
    )

    graph = Graph(embedding_workflow)
    result = await graph.run(inputs)

    return result.container_embedding
```

---

### Component 6: Dynamic Definition with Embeddings

#### [NEW] [dynamic_embedding.py](file:///d:/agent-factory/collider/embeddings/dynamic_embedding.py)

**create_model() with embedded fingerprints**:

```python
from pydantic import create_model
from typing import Type

def create_definition_with_embedding(
    definition_name: str,
    parameters: dict,
    embedding: SemanticContainer
) -> Type[BaseModel]:
    """
    Dynamically create Definition model with embedded fingerprint.

    Args:
        definition_name: Name of Definition class
        parameters: Parameter schema
        embedding: Pre-computed semantic embedding

    Returns:
        Dynamic Pydantic model with __embedding__ attribute
    """
    # Base fields from parameters
    fields = {
        param_name: (param_type, ...)
        for param_name, param_type in parameters.items()
    }

    # Add metadata fields
    fields['__embedding__'] = (SemanticContainer, embedding)
    fields['__fingerprint_hash__'] = (
        str,
        embedding.full_embedding.numpy().tobytes().hex()[:16]
    )

    DynamicDefinition = create_model(
        definition_name,
        **fields
    )

    # Add similarity search method
    def find_similar(cls, other: 'DynamicDefinition', threshold: float = 0.8) -> bool:
        """Check if two Definitions are similar via embeddings"""
        sim = GraphShapeComparator.cosine_similarity(
            cls.__embedding__.full_embedding,
            other.__embedding__.full_embedding
        )
        return sim >= threshold

    DynamicDefinition.find_similar = classmethod(find_similar)

    return DynamicDefinition
```

---

## Verification Plan

### Automated Tests

**Unit Tests** (`test_embeddings.py`):

```bash
pytest collider/embeddings/tests/test_embeddings.py -v
```

Tests:

- `test_depth_aware_embedding_decay()`: Verify depth weighting
- `test_port_embedding_composition()`: Port signature aggregation
- `test_hierarchical_similarity()`: Recursive Container comparison
- `test_gpu_tensor_validation()`: pydantic-tensor with CUDA

**Integration Tests** (`test_semantic_container.py`):

```bash
pytest collider/embeddings/tests/test_semantic_container.py -v
```

Tests:

- `test_gnn_embedding_computation()`: Full GNN workflow
- `test_scope_boundary_message_passing()`: Depth-aware propagation
- `test_dynamic_definition_fingerprinting()`: create_model() integration

### Manual Verification

1. **GPU Acceleration Test**:

   ```python
   # Load Container graph
   container = load_container('composite_definition_example')
   semantic = SemanticContainer.from_container(container)

   # Move to GPU
   semantic_gpu = semantic.to_gpu()
   print(f"Device: {semantic_gpu.device}")  # Should show 'cuda:0'

   # Compute embedding (should use GPU)
   import time
   start = time.time()
   embedded = semantic_gpu.compute_structural_embedding(gnn_model)
   print(f"GPU time: {time.time() - start:.3f}s")
   ```

2. **Similarity Search Test**:

   ```python
   # Create two similar Containers with different depths
   container_a = create_workflow_container(R=1)
   container_b = create_workflow_container(R=2)  # Nested deeper

   # Compute similarity
   sim = GraphShapeComparator.hierarchical_similarity(
       container_a.semantic,
       container_b.semantic,
       mode='full'
   )
   print(f"Similarity: {sim:.3f}")  # Should be high despite depth diff
   ```

3. **Depth Decay Visualization**:

   ```python
   # Create nested Container hierarchy (R=0 to R=5)
   root = create_nested_hierarchy(max_depth=5)

   # Extract embeddings at each level
   embeddings_by_depth = {}
   def extract_recursive(container, depth=0):
       embeddings_by_depth[depth] = container.structural_embedding.depth_weighted_vector
       for child in container.child_containers:
           extract_recursive(child, depth+1)

   extract_recursive(root)

   # Plot decay effect
   import matplotlib.pyplot as plt
   norms = [emb.norm().item() for emb in embeddings_by_depth.values()]
   plt.plot(range(6), norms)
   plt.xlabel('Scope Depth (R)')
   plt.ylabel('Embedding Norm (after decay)')
   plt.title('Depth Decay Factor Effect')
   plt.show()
   ```

---

## Critical Implementation Notes

### Memory Management for Large Graphs

For Containers with >1000 nodes:

```python
class BatchedSemanticContainer(SemanticContainer):
    """Memory-efficient batched processing"""

    def compute_structural_embedding_batched(
        self,
        gnn_model: torch.nn.Module,
        batch_size: int = 256
    ) -> 'SemanticContainer':
        """Process graph in batches to fit GPU memory"""
        # Use NeighborLoader from PyG
        from torch_geometric.loader import NeighborLoader

        loader = NeighborLoader(
            self.graph_data,
            num_neighbors=[10, 10],  # 2-hop neighborhood
            batch_size=batch_size
        )

        embeddings = []
        for batch in loader:
            batch_emb = gnn_model(batch.x, batch.edge_index)
            embeddings.append(batch_emb)

        # Aggregate batches
        full_embedding = torch.cat(embeddings, dim=0)
        # ... pool to graph-level
```

### Scope Boundary Enforcement in Message Passing

```python
def scope_aware_message_passing(
    x: Tensor,
    edge_index: Tensor,
    node_depths: Tensor
) -> Tensor:
    """
    Only propagate messages between nodes at same scope_depth.
    Prevents cross-scope information leakage.
    """
    # Create mask: edge valid if source_depth == target_depth
    source_depths = node_depths[edge_index[0]]
    target_depths = node_depths[edge_index[1]]
    valid_edges = (source_depths == target_depths)

    # Filter edge_index
    filtered_edge_index = edge_index[:, valid_edges]

    # Standard message passing on filtered graph
    return GCNConv(...)(x, filtered_edge_index)
```
