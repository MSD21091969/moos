# Neural-Symbolic AI & Vector Symbolic Architectures for Collider

**Research Investigation: Topic 5**  
**Date**: 2026-01-14  
**Focus**: Encoding recursive Container/Link graph in vector space

---

## Executive Summary

Vector Symbolic Architectures (VSA) offer a brain-inspired computational paradigm for encoding graph structures using high-dimensional vectors (hypervectors). This research evaluates VSA's potential for representing Collider's recursive Container/Link topology while maintaining compatibility with Pydantic's strict validation.

**Key Question**: How to encode `Container A inside Container B` purely in vector space while preserving Pydantic logic?

---

## 1. VSA Fundamentals

### 1.1 Core Concepts

**Hypervectors**:

- High-dimensional vectors (1,000-100,000 dimensions)
- Nearly orthogonal when randomly generated
- Enable distributed, holographic representations
- Robust to noise, efficient for parallel processing

**Fundamental Operations**:

| Operation       | Purpose                           | Example Implementation                                    |
| --------------- | --------------------------------- | --------------------------------------------------------- |
| **Binding**     | Encode associations/relationships | Element-wise multiplication (bipolar), XOR (binary)       |
| **Bundling**    | Aggregate multiple concepts       | Element-wise majority (bipolar), addition + normalization |
| **Permutation** | Encode order/sequences            | Circular shift of vector elements                         |

**Key Properties**:

- Binding preserves distance/similarity
- Bundling produces a vector similar to all constituents
- Operations are reversible (unbinding via inverse operations)

---

## 2. Python VSA Libraries

### 2.1 torchhd

**Source**: https://github.com/hyperdimensional-computing/torchhd  
**Foundation**: PyTorch (GPU-accelerated)

**Features**:

- 100x faster than other implementations
- Supports: BSC, MAP, HRR, FHRR, SBC, VTB models
- Modular framework for experimentation
- Full PyTorch ecosystem integration

**Example**:

```python
import torch
import torchhd

# Create hypervector encoder
d = 10000  # Dimensionality
encoder = torchhd.embeddings.Random(num_embeddings=1000, embedding_dim=d)

# Encode two concepts
container_a = encoder(torch.tensor(1))
container_b = encoder(torch.tensor(2))

# Bind: "A contains B"
contains_relation = torchhd.bind(container_a, container_b)

# Bundle: "Set of containers"
container_set = torchhd.bundle(container_a, container_b)
```

### 2.2 hdlib

**Source**: https://github.com/cumbof/hdlib  
**Version**: 2.0 (enhanced ML capabilities)

**Features**:

- Flexible interface for complex abstractions
- `GraphModel` for graph-based learning
- Quantum HDC implementation (via Qiskit)
- Regression, clustering, classification models

**Module Structure**:

- `hdlib.space`: Hyperdimensional space management
- `hdlib.arithmetic`: bind, bundle, permute operations
- `hdlib.model`: ML model building

---

## 3. Collider Architecture Analysis

### 3.1 Current Models (Pydantic-based)

From `shared/domain/models.py` and `ARCHITECTURE.md`:

```python
# Hierarchical: UserContainer can nest
class UserContainer(BaseModel):
    id: UUID
    owner_id: UUID
    parent_id: Optional[UUID]  # Recursive nesting
    definition_id: Optional[UUID]
    visual_x: float
    visual_y: float

# Graph topology: Link connects containers
class Link(BaseModel):
    id: UUID
    owner_id: UUID  # West container
    definition_id: Optional[UUID]
    predecessor_id: UUID  # East container
    input_mapping: Dict[str, str]
```

**Topology**:

- Links form n:m network (not 1:1 chains)
- Containers can have multiple incoming/outgoing links
- INPUT/OUTPUT boundary nodes mark subgraph edges

### 3.2 VSA Encoding Strategies

#### Strategy A: Hierarchical Binding (Container Nesting)

Encode `parent_id` relationships:

```python
import torchhd

# Base hypervectors for each container
containers = {
    uuid1: torchhd.random(10000),
    uuid2: torchhd.random(10000),
    uuid3: torchhd.random(10000),
}

# Relation vectors
PARENT_OF = torchhd.random(10000)
CONTAINS = torchhd.random(10000)

# Encode "Container A contains Container B"
# A.parent_id = None, B.parent_id = A.id
relation_vector = torchhd.bind(
    torchhd.bind(containers[A], CONTAINS),
    containers[B]
)

# Store in memory
memory = torchhd.bundle(memory, relation_vector)
```

**Query**: "What does Container A contain?"

```python
query = torchhd.bind(torchhd.bind(containers[A], CONTAINS), torchhd.inverse(CONTAINS))
# Find nearest neighbor in container space
result = find_nearest(query, containers)
```

#### Strategy B: Graph Topology Encoding (Links)

Encode predecessor/successor relationships:

```python
# Relation types
PREDECESSOR = torchhd.random(10000)
SUCCESSOR = torchhd.random(10000)
LINKED_VIA = torchhd.random(10000)

# Encode Link: owner_id → predecessor_id
link_vector = torchhd.bind(
    torchhd.bind(containers[owner], LINKED_VIA),
    containers[predecessor]
)

# Add definition context
if link.definition_id:
    link_vector = torchhd.bind(
        link_vector,
        definitions[link.definition_id]
    )

# Bundle all links for a container
container_graph = torchhd.bundle(*[link_vec for link in container.links])
```

#### Strategy C: Composite Definition Encoding

Encode `composed_from` relationships:

```python
# For composite definitions
composite_vector = torchhd.bundle(*[
    definitions[dep_id] for dep_id in definition.composed_from
])

# Bind I/O schema
composite_vector = torchhd.bind(
    composite_vector,
    encode_schema(definition.input_schema)
)
composite_vector = torchhd.bind(
    composite_vector,
    encode_schema(definition.output_schema)
)
```

---

## 4. Hybrid Architecture: VSA + Pydantic

### 4.1 Design Goals

1. **Strict Validation**: Pydantic models remain source of truth
2. **Fuzzy Reasoning**: VSA enables similarity search, analogical reasoning
3. **Dual Representation**:
   - Pydantic models for CRUD operations, validation, persistence
   - VSA vectors for semantic search, graph traversal, pattern matching

### 4.2 Proposed Integration Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional
import torch
import torchhd

class VectorizedContainer(UserContainer):
    """Extended Container with VSA representation"""

    # Pydantic fields (strict)
    id: UUID
    parent_id: Optional[UUID]
    # ... all UserContainer fields

    # VSA representation (computed property)
    _hypervector: Optional[torch.Tensor] = Field(default=None, exclude=True)

    def encode(self, encoder: torchhd.Embeddings) -> torch.Tensor:
        """Generate hypervector representation"""
        base = encoder(hash(self.id) % encoder.num_embeddings)

        # Encode parent relationship
        if self.parent_id:
            parent_vec = encoder(hash(self.parent_id) % encoder.num_embeddings)
            base = torchhd.bind(base, torchhd.bind(PARENT_OF, parent_vec))

        # Encode visual position (spatial info)
        position = encode_position(self.visual_x, self.visual_y)
        base = torchhd.bind(base, position)

        self._hypervector = base
        return base

    def similarity(self, other: 'VectorizedContainer') -> float:
        """Compute cosine similarity"""
        if self._hypervector is None or other._hypervector is None:
            raise ValueError("Must encode first")
        return torchhd.cosine_similarity(self._hypervector, other._hypervector)
```

### 4.3 Use Cases

**UC1: Semantic Container Search**

```python
# "Find containers similar to this structure"
query_container = VectorizedContainer(...)
query_vec = query_container.encode(encoder)

similarities = [
    (c, torchhd.cosine_similarity(query_vec, c._hypervector))
    for c in container_registry
]
similar_containers = sorted(similarities, key=lambda x: x[1], reverse=True)[:10]
```

**UC2: Subgraph Pattern Matching**

```python
# "Find all containers with similar dependency patterns"
pattern = torchhd.bundle(*[link.encode() for link in target_links])
matches = find_similar_patterns(pattern, container_registry, threshold=0.8)
```

**UC3: Emergent I/O Calculation**

```python
# Bundle all input schemas from dependencies
input_bundle = torchhd.bundle(*[
    encode_schema(dep.input_schema)
    for dep in composite.composed_from
])

# Query: "What emerged inputs exist?"
emerged_schema = decode_schema(input_bundle)
```

---

## 5. Challenges & Mitigations

### 5.1 Challenge: Dimensionality Choice

**Problem**: Trade-off between memory and accuracy

**Solution**:

- Start with d=10,000 (torchhd standard)
- Benchmark with Collider's typical graph sizes
- Use quantized vectors (binary/ternary) for production

### 5.2 Challenge: UUID Mapping

**Problem**: UUIDs don't have inherent semantic structure

**Mitigation**:

- Use random hypervectors per UUID (no semantic bias)
- Store UUID→hypervector mapping in registry
- Hash UUIDs to encoder indices for consistency

### 5.3 Challenge: Pydantic Integration

**Problem**: Pydantic models are strict, VSA is fuzzy

**Solution**:

- VSA as **opt-in computed field** (excluded from serialization)
- Regenerate on demand (encode on read)
- Store VSA index separately from Pydantic DB

### 5.4 Challenge: Complex Schema Encoding

**Problem**: JSON Schema is nested, recursive

**Solution**:

```python
def encode_schema(schema: dict, depth=0) -> torch.Tensor:
    """Recursively encode JSON schema to hypervector"""
    if depth > 5:  # Prevent infinite recursion
        return torchhd.random(10000)

    type_vec = TYPE_ENCODERS[schema.get('type', 'object')]

    if 'properties' in schema:
        prop_vecs = [
            torchhd.bind(
                encode_string(key),
                encode_schema(val, depth+1)
            )
            for key, val in schema['properties'].items()
        ]
        return torchhd.bind(type_vec, torchhd.bundle(*prop_vecs))

    return type_vec
```

---

## 6. References & Further Reading

### 6.1 Foundational Papers

- **Besold et al. (2021)**: "Neuro-Symbolic Artificial Intelligence: The State of the Art"  
  https://arxiv.org/abs/2105.05330
- **Kanerva (2009)**: "Hyperdimensional Computing: An Introduction to Computing in Distributed Representation with High-Dimensional Random Vectors"

- **Plate (1995)**: "Holographic Reduced Representations"

### 6.2 Python Libraries

- **torchhd**: https://github.com/hyperdimensional-computing/torchhd  
  Paper: https://www.jmlr.org/papers/v24/23-0069.html

- **hdlib 2.0**: https://github.com/cumbof/hdlib  
  Paper: https://arxiv.org/abs/2205.08812

- **vsapy**: https://github.com/pitt-rnel/vsapy

### 6.3 Related Work

- **Graph Neural Networks (GNN)**: Compare VSA vs GNN for graph encoding
- **Tensor Product Representations**: Alternative to VSA binding
- **Cognitive Architectures**: Spaun, Nengo (VSA-based cognitive models)

---

## 7. Next Steps

### 7.1 Immediate Actions

1. **Prototype**: Implement Strategy A (hierarchical binding) in `shared/topology/graph.py`
2. **Benchmark**: Test encoding/decoding speed for 100, 1000, 10000 containers
3. **Integration**: Add `encode()` method to `UserContainer` model

### 7.2 Research Questions

1. Can VSA accelerate subgraph resolution (boundary detection)?
2. How to encode `input_mapping` (dict[str, str]) in vector space?
3. Can VSA enable "container analogies" (A:B :: C:D)?

### 7.3 Experimental Design

```python
# Hypothesis: VSA can replace graph traversal for common queries
# Test: "Find all containers depending on Container X"

# Method 1: Traditional (Graph DB query)
start = time.time()
dependents_trad = graph_db.query("MATCH (x:Container)<-[:DEPENDS_ON]-(y) WHERE x.id=$id", id=X)
t_trad = time.time() - start

# Method 2: VSA (Vector similarity search)
start = time.time()
query_vec = torchhd.bind(containers[X], DEPENDS_ON)
dependents_vsa = find_knn(query_vec, container_vectors, k=100)
t_vsa = time.time() - start

# Compare: accuracy, speed, memory
```

---

## 8. Appendix: VSA Cheat Sheet

| Goal            | VSA Operation                 | Example                       |
| --------------- | ----------------------------- | ----------------------------- |
| Relate A and B  | `bind(A, B)`                  | "Container A owns Link B"     |
| Combine A and B | `bundle(A, B)`                | "Set containing A and B"      |
| Encode sequence | `permute(A, shift=1)`         | "Container A at position 1"   |
| Query relation  | `bind(A, inverse(R))`         | "What is related to A via R?" |
| Find similar    | `cosine_similarity(A, B)`     | "How similar are A and B?"    |
| Decode bundle   | `find_nearest(bundle, items)` | "Which item is most similar?" |

**Notation**:

- `⊗` = binding (circular convolution for HRR)
- `⊕` = bundling (element-wise sum or majority)
- `π` = permutation (rotation)
- `⊗⁻¹` = unbinding (inverse operation)

---

**Status**: Research complete. Awaiting feedback on integration priority.
