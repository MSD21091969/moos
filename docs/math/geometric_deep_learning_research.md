# Geometric Deep Learning for Graph Fingerprinting - Research Report

**Investigation Topic**: How to embed graph structure into fixed-dimension vectors and compare Container "shapes" using manifold distance in the Collider architecture.

**Key Challenge**: Fingerprinting Containers with variable edge counts into comparable vectors while preserving recursive structure and topology.

---

## Executive Summary

Geometric Deep Learning (GDL) provides a unified mathematical framework for processing graph-structured data through neural networks that respect geometric symmetries. For the Collider's Container/Link architecture, GDL techniques enable:

1. **Fixed-dimension embeddings** of variable-size Container graphs via message passing and pooling
2. **Manifold-based distance metrics** for comparing Container "shapes" in non-Euclidean space
3. **Graph fingerprinting** using Weisfeiler-Lehman kernels and learned representations
4. **Hierarchical graph pooling** (DiffPool) to preserve multi-level Container structure

---

## 1. Theoretical Foundations

### 1.1 Geometric Deep Learning Framework

**Core Principle**: Leverage geometric inductive biases (symmetry, invariance) to process non-Euclidean data structures.

**The "5Gs" of GDL** (Bronstein et al., 2021):

- **Grids**: Regular Euclidean domains (CNNs)
- **Groups**: Symmetry operations (equivariance)
- **Graphs**: Discrete relational structures ← Collider focus
- **Geodesics**: Shortest paths on manifolds
- **Gauges**: Local coordinate frames

**Relevance to Collider**:

- Container/Link graphs are inherently non-Euclidean
- Recursive nesting creates hierarchical manifold structure
- Definitions as "blueprints" encode symmetry groups

### 1.2 Message Passing Neural Networks (MPNN)

**Key Mechanism**: Iterative neighborhood aggregation to generate node embeddings.

**Three-Step Process**:

1. **Message Creation**: Each node generates messages from neighbors' features
2. **Message Aggregation**: Combine messages using permutation-invariant functions (sum, mean, max)
3. **Node Update**: Refine node embeddings with aggregated information

**Variable Graph Handling**:

- Aggregation functions handle variable neighbor counts
- Fixed embedding dimension maintained at each layer
- Multi-layer message passing captures k-hop neighborhoods

**Collider Application**:

```
Container_embedding = MPNN(
    node_features = [Definition types, parameter schemas],
    edge_index = Link topology (North/East/West),
    num_layers = depth of Container nesting
)
```

### 1.3 Non-Euclidean Geometry on Graphs

**Problem**: Euclidean embeddings distort hierarchical structures.

**Solution**: Hyperbolic geometry for tree-like graphs.

**Properties**:

- **Constant negative curvature**: Natural hierarchies
- **Exponential volume growth**: Accommodates scale-free graphs
- **Reduced distortion**: Better preserves graph topology

**Manifold Distance Metrics**:

- **Gromov-Hausdorff distance**: Compare latent geometries
- **Wasserstein distance**: Probability distributions on manifolds
- **Graph Laplacian**: Intrinsic manifold structure

**Collider Insight**: Container graphs may exhibit hierarchical patterns (composite Definitions → atomic Definitions) better captured in hyperbolic space.

---

## 2. Graph Fingerprinting Techniques

### 2.1 Weisfeiler-Lehman (WL) Subtree Kernel

**Mechanism**: Iterative node relabeling to create structural fingerprints.

**Algorithm**:

```
1. Initialize: Assign labels to nodes (e.g., Definition type)
2. Iterate:
   - For each node: Aggregate sorted neighbor labels
   - Hash combined label → new unique label
3. Fingerprint: Histogram of labels across all iterations
4. Similarity: Inner product of label histograms
```

**Advantages**:

- Computationally efficient: O(edges × iterations)
- Captures subtree patterns implicitly
- State-of-the-art for graph classification

**Collider Application**:

- Initial labels: `Definition.type`, `Link.direction`
- Captures repeated Container motifs (e.g., common wiring patterns)
- WL test relates to GNN expressive power (standard GNNs ≈ 1-WL)

**Limitation**: Cannot distinguish certain non-isomorphic graphs (overcome with k-WL higher-order variants).

### 2.2 Graph Isomorphism & Distance

**Graph Isomorphism**: Determine if two graphs are structurally identical.

**Applications**:

- **Exact matching**: Detect identical Container topologies
- **Subgraph isomorphism**: Find component patterns within larger Containers
- **Isomorphism distance**: Measure "how far" from isomorphic

**Relevance to Collider**:

- Detect duplicated Container logic with different IDs
- Identify canonical forms for equivalent wiring
- Verify structural invariants in Composite Definitions

---

## 3. Graph Embedding Methods

### 3.1 Shallow Embeddings (Node2Vec, MetaPath2Vec)

**Node2Vec**:

- Random walk-based embeddings
- Parameters: `p` (return likelihood), `q` (BFS vs DFS)
- Output: Fixed-dimension node vectors

**Collider Use**:

- Pre-train node embeddings for Containers
- Walk-based context captures structural neighborhoods
- Input features for downstream GNNs

**MetaPath2Vec**:

- For heterogeneous graphs (multiple node/edge types)
- Define metapaths: e.g., `Container → Link → Definition`
- Learn type-specific embeddings

### 3.2 GNN-Based Learned Embeddings

**Architecture Stack**:

```python
GNN(
    layers = [GCNConv, SAGEConv, GATConv],
    pooling = [global_mean, DiffPool],
    task = [node_classification, graph_classification]
)
```

**Layer Types**:

- **GCNConv**: Spectral graph convolution (symmetric normalization)
- **SAGEConv (GraphSAGE)**: Aggregates sampled neighborhoods
- **GATConv (Graph Attention)**: Weighted attention over neighbors

**Fixed-Dimension Output**:

- Node-level: Each layer outputs fixed `d` dimensions
- Graph-level: Pooling condenses all nodes → single vector

---

## 4. Graph Pooling for Hierarchical Structures

### 4.1 Global Pooling

**Methods**: Sum, Mean, Max over all node embeddings.

**Properties**:

- Single-step aggregation
- Fixed output size regardless of graph size
- Loses hierarchical structure

**Collider Use**: Final readout layer for Container fingerprints.

### 4.2 Hierarchical Pooling (DiffPool)

**Key Innovation**: Learnable soft cluster assignment for multi-layer GNNs.

**Process**:

```
Layer 1: Full Container graph → node embeddings
DiffPool: Cluster nodes → coarsened graph
Layer 2: Operate on clusters → refined embeddings
DiffPool: Further coarsen
...
Final: Graph-level embedding
```

**Advantages**:

- Preserves multi-resolution structure
- End-to-end differentiable
- State-of-the-art graph classification

**Collider Application**:

- Layer 1: Individual Link/Definition nodes
- Layer 2: Sub-Container clusters (local wiring groups)
- Layer 3: Full Container topology
- Captures recursive nesting naturally

**Challenges**:

- High parameter count
- Difficult to control learning
- Best for dense subgraphs

**Alternative**: Node drop pooling (TopKPooling) for sparse Containers.

---

## 5. Manifold Distance for Container Comparison

### 5.1 Distance Metrics

**Euclidean Distance** (baseline):

```python
dist = ||embed_A - embed_B||_2
```

**Cosine Similarity**:

```python
sim = (embed_A · embed_B) / (||embed_A|| × ||embed_B||)
```

**Wasserstein Distance** (distributional):

- Compare Container node feature distributions
- Accounts for structural differences beyond embeddings

**Hyperbolic Distance** (if using hyperbolic embeddings):

```python
dist_hyp = arccosh(1 + 2||u-v||² / ((1-||u||²)(1-||v||²)))
```

### 5.2 Manifold Learning

**Assumption**: Container embeddings lie on low-dimensional manifold in high-dimensional space.

**Techniques**:

- **Graph Laplacian**: Geodesic distances on similarity graph
- **Intrinsic Sliced Wasserstein**: Compare manifold geometries
- **Unfolding Kernel**: Enhance class separation via manifold properties

**Collider Insight**: Containers with similar semantics (e.g., data transformation workflows) cluster on manifold regions.

---

## 6. PyTorch Geometric Implementation Path

### 6.1 Data Representation

```python
from torch_geometric.data import Data

container_graph = Data(
    x = node_features,  # [num_nodes, feature_dim]
                        # Definition type, schema, parameters
    edge_index = edge_index,  # [2, num_edges]
                              # Link topology (source → target)
    edge_attr = edge_features,  # [num_edges, edge_dim]
                                # Link direction (N/E/W), constraints
    y = label  # Optional: Container category
)
```

### 6.2 Model Architecture

```python
import torch
from torch_geometric.nn import GCNConv, global_mean_pool

class ContainerFingerprint(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.conv3 = GCNConv(hidden_channels, out_channels)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch

        # Message passing layers
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        x = self.conv3(x, edge_index)

        # Global pooling: fixed-dimension output
        x = global_mean_pool(x, batch)

        return x  # Shape: [batch_size, out_channels]
```

### 6.3 Training for Similarity

**Loss Functions**:

- **Triplet Loss**: Learn embeddings where similar Containers are close
- **Contrastive Loss**: Positive pairs close, negative pairs apart
- **Graph Reconstruction**: Autoencode Container structure

**Example (Triplet Loss)**:

```python
def triplet_loss(anchor, positive, negative, margin=1.0):
    dist_pos = (anchor - positive).pow(2).sum(1)
    dist_neg = (anchor - negative).pow(2).sum(1)
    loss = (dist_pos - dist_neg + margin).clamp(min=0).mean()
    return loss
```

---

## 7. Collider-Specific Implementation Strategy

### 7.1 Feature Engineering

**Node Features** (Definition/Container):

- One-hot: `Definition.type` (atomic vs composite)
- Schema embedding: Parameter structure (input/output types)
- Semantic: Text embedding of `Definition.description`

**Edge Features** (Link):

- One-hot: Direction (North=0, East=1, West=2)
- Constraint encoding: Type compatibility, cardinality

### 7.2 Handling Recursive Structure

**Challenge**: Containers contain Containers (arbitrary depth).

**Approach 1 - Flattening**:

- Recursively expand all nested Containers into single graph
- Preserve depth information as node attribute
- Risk: Very large graphs for deep nesting

**Approach 2 - Hierarchical Encoding**:

- Treat nested Container as single "super-node"
- Recursively embed inner Container → use as super-node feature
- Encode multi-level topology explicitly

**Approach 3 - Graph-of-Graphs**:

- Build meta-graph where nodes are Containers, edges are containment
- Dual embeddings: Container internal structure + Container relationships

### 7.3 Variable Edge Count Normalization

**Problem**: Container A has 10 Links, Container B has 100 Links.

**Solutions**:

1. **Aggregation Functions**: Sum/mean pooling naturally handles this
2. **Attention Mechanisms**: GAT weights important Links more
3. **Normalization**: Degree-normalized adjacency in GCNConv
4. **Padding**: Not recommended (breaks permutation invariance)

---

## 8. Five Use Cases - Detailed

### 8.1 Container Similarity Search

**Scenario**: User defines new Container → find similar existing ones.

**Implementation**:

1. Embed all Containers in database → vector index (FAISS, Annoy)
2. Embed query Container → retrieve k-nearest neighbors
3. Rank by manifold distance + optional metadata filters

**Benefit**: Suggest starting templates, reduce duplication.

### 8.2 Anomaly Detection

**Scenario**: Flag unusual Container structures during validation.

**Implementation**:

1. Train autoencoder on "normal" Container graphs
2. Reconstruction error = anomaly score
3. Alert on high scores (malformed wiring, orphaned Definitions)

**Benefit**: Catch design errors, enforce architectural patterns.

### 8.3 Clustering & Recommendations

**Scenario**: Organize Container library, recommend patterns.

**Implementation**:

1. K-means on Container embeddings → clusters
2. Label clusters (e.g., "data pipelines", "UI components")
3. Recommend Containers from same cluster

**Benefit**: Improve discoverability, pattern mining.

### 8.4 Version Drift Analysis

**Scenario**: Track how Container topology evolves over versions.

**Implementation**:

1. Embed Container_v1, Container_v2
2. Compute manifold distance
3. Visualize drift trajectory in embedding space

**Benefit**: Detect breaking changes, semantic shift monitoring.

### 8.5 Duplicate Detection

**Scenario**: Identify functionally equivalent Containers with different IDs.

**Implementation**:

1. Embed all Containers
2. Cluster by proximity (tight threshold)
3. Within cluster: verify isomorphism (WL test)

**Benefit**: Deduplication, canonical form enforcement.

---

## 9. Implementation Roadmap

### Phase 1: Proof of Concept

1. Extract Container graphs → PyG Data objects
2. Train simple GCN with global mean pooling
3. Evaluate on synthetic similarity task (cosine distance)

### Phase 2: Feature Engineering

1. Define node/edge feature extractors from Pydantic models
2. Integrate semantic embeddings (Definition descriptions)
3. Handle recursive Container expansion

### Phase 3: Advanced Architectures

1. Implement DiffPool for hierarchical Containers
2. Experiment with hyperbolic embeddings
3. Train with triplet/contrastive loss

### Phase 4: Production Integration

1. Embed Containers on creation/update
2. Vector index for real-time similarity search
3. Anomaly detection in validation pipeline

### Phase 5: Evaluation

1. Human-labeled similarity dataset
2. Precision/recall metrics for search
3. Ablation studies (pooling methods, embedding dim)

---

## 10. Key References

### Foundational Papers

- **Bronstein et al. (2021)**: "Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges" - [geometricdeeplearning.com](https://geometricdeeplearning.com)
- **Weisfeiler-Lehman Kernel**: Shervashidze et al., JMLR 2011
- **Message Passing**: Gilmer et al., ICML 2017

### Architectures

- **DiffPool**: Ying et al., NeurIPS 2018
- **Graph Attention Networks (GAT)**: Veličković et al., ICLR 2018
- **GraphSAGE**: Hamilton et al., NeurIPS 2017

### Hyperbolic Methods

- **Hyperbolic Graph Neural Networks**: Liu et al., ArXiv 2019
- **Poincaré Embeddings**: Nickel & Kiela, NeurIPS 2017

### Practical Guides

- PyTorch Geometric Documentation: [pytorch-geometric.readthedocs.io](https://pytorch-geometric.readthedocs.io)
- Geometric Deep Learning Course: [YouTube - Michael Bronstein](https://www.youtube.com/geometricdeeplearning)

---

## 11. Critical Decision Points

### 11.1 Embedding Dimension

**Trade-off**: Higher dim = more expressiveness, but slower search & overfitting.

**Recommendation**: Start with 128-256 dims, tune via cross-validation.

### 11.2 Pooling Strategy

**Global**: Fast, loses hierarchy.  
**DiffPool**: Preserves structure, computationally expensive.

**Recommendation**: Global for MVP, DiffPool for complex recursive Containers.

### 11.3 Distance Metric

**Euclidean**: Simple, interpretable.  
**Hyperbolic**: Better for hierarchies, harder to implement.

**Recommendation**: Euclidean baseline, experiment with hyperbolic if hierarchical patterns emerge.

### 11.4 Supervised vs Unsupervised

**Supervised**: Requires labeled Container pairs (similar/dissimilar).  
**Unsupervised**: Autoencoder, no labels needed.

**Recommendation**: Start unsupervised (reconstruction), add supervised fine-tuning with user feedback.

---

## 12. Conclusion

**Core Answer to Key Question**:  
_"How to fingerprint a Container with variable edge counts into comparable vectors?"_

**Solution**:

1. **Message Passing GNN** generates fixed-dimension node embeddings regardless of graph size
2. **Graph Pooling** (global mean/sum or hierarchical DiffPool) aggregates variable nodes → fixed vector
3. **Manifold Distance** (Euclidean, cosine, or hyperbolic) compares embeddings in latent space
4. **WL Kernel** provides interpretable baseline for structural fingerprinting

**Next Steps**:

- Implement PyG-based Container→Embedding pipeline
- Define feature extractors from Collider Pydantic models
- Train similarity model on real Container data
- Integrate into Collider backend API (`/similarity`, `/anomaly-detect`)

**Expected Impact**:

- Enable intelligent Container search and recommendations
- Automate quality checks via anomaly detection
- Facilitate pattern mining across user workflows
- Foundation for compositional reasoning (future: predict outputs from topology)
