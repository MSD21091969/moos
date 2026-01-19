"""Node embeddings - fixed-dimension vectors for nodes.

Enables similarity search, clustering, and GNN input.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
from uuid import UUID
import numpy as np
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .node import Node
    from .graph import Graph


# Default embedding dimension (power of 2 for efficiency)
EMBEDDING_DIM = 128


class NodeEmbedding(BaseModel):
    """
    Fixed-dimension vector representation of a node.
    
    Enables:
    - Cosine similarity search
    - Graph neural network input
    - Semantic clustering
    
    Example:
        emb1 = NodeEmbedding(node_id=id1, vector=[0.1, 0.2, ...])
        emb2 = NodeEmbedding(node_id=id2, vector=[0.15, 0.22, ...])
        sim = emb1.similarity(emb2)  # 0.95
    """
    
    node_id: UUID
    node_name: str = ""
    vector: list[float] = Field(default_factory=lambda: [0.0] * EMBEDDING_DIM)
    
    @property
    def dimension(self) -> int:
        return len(self.vector)
    
    def as_array(self) -> np.ndarray:
        """Get vector as numpy array."""
        return np.array(self.vector, dtype=np.float32)
    
    def similarity(self, other: "NodeEmbedding") -> float:
        """
        Cosine similarity between embeddings.
        
        Returns:
            Value in [-1, 1], where 1 = identical direction
        """
        a = self.as_array()
        b = other.as_array()
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def distance(self, other: "NodeEmbedding") -> float:
        """
        Euclidean distance between embeddings.
        
        Returns:
            Distance >= 0
        """
        return float(np.linalg.norm(self.as_array() - other.as_array()))


class EmbeddingGenerator:
    """
    Generate embeddings from node properties and graph structure.
    
    Methods:
    - Structural: Based on degree, depth, position
    - Content: Based on definition text (requires external embedder)
    - Hybrid: Combined structural + content
    
    Example:
        gen = EmbeddingGenerator(method="structural")
        embeddings = gen.embed_graph(graph)
        similar = gen.find_similar(embeddings, query_id, top_k=5)
    """
    
    def __init__(
        self,
        method: str = "structural",
        dimension: int = EMBEDDING_DIM,
        content_embedder: Optional[Callable[[str], list[float]]] = None
    ):
        self.method = method
        self.dimension = dimension
        self.content_embedder = content_embedder
    
    def embed_node(
        self,
        node: "Node",
        graph: "Graph",
        position_in_graph: int = 0
    ) -> NodeEmbedding:
        """
        Generate embedding for a single node.
        
        Args:
            node: The node to embed
            graph: Parent graph (for structural features)
            position_in_graph: Node's index in graph
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        
        # Structural features (first 32 dims)
        in_degree = len(graph.get_edges_to(node.id))
        out_degree = len(graph.get_edges_from(node.id))
        scope = node.scope_depth
        
        vec[0] = in_degree / 10.0  # Normalized
        vec[1] = out_degree / 10.0
        vec[2] = scope / 5.0
        vec[3] = (in_degree + out_degree) / 20.0  # Total degree
        vec[4] = 1.0 if in_degree == 0 else 0.0  # Is input?
        vec[5] = 1.0 if out_degree == 0 else 0.0  # Is output?
        vec[6] = position_in_graph / max(len(graph.nodes), 1)  # Position
        
        # Hash of name for uniqueness (dims 8-15)
        name_hash = hash(node.name) % (2**32)
        for i in range(8):
            vec[8 + i] = ((name_hash >> (i * 4)) & 0xF) / 16.0
        
        # Content embedding (dims 32-127)
        if self.method in ("content", "hybrid") and self.content_embedder:
            # Embed definition name/description if available
            text = node.name
            if node.definition_id:
                # Would get definition text here
                pass
            
            content_vec = self.content_embedder(text)
            content_slice = content_vec[:min(len(content_vec), 96)]
            vec[32:32 + len(content_slice)] = content_slice
        
        return NodeEmbedding(
            node_id=node.id,
            node_name=node.name,
            vector=vec.tolist()
        )
    
    def embed_graph(self, graph: "Graph") -> dict[UUID, NodeEmbedding]:
        """
        Generate embeddings for all nodes in graph.
        
        Returns:
            Dict mapping node_id → NodeEmbedding
        """
        embeddings = {}
        for i, node in enumerate(graph.nodes):
            embeddings[node.id] = self.embed_node(node, graph, i)
        return embeddings
    
    def find_similar(
        self,
        embeddings: dict[UUID, NodeEmbedding],
        query_id: UUID,
        top_k: int = 5
    ) -> list[tuple[UUID, float]]:
        """
        Find most similar nodes to query.
        
        Returns:
            List of (node_id, similarity) sorted by similarity descending
        """
        if query_id not in embeddings:
            return []
        
        query = embeddings[query_id]
        similarities = []
        
        for nid, emb in embeddings.items():
            if nid != query_id:
                sim = query.similarity(emb)
                similarities.append((nid, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class EmbeddingIndex:
    """
    Fast similarity search index for node embeddings.
    
    Uses numpy broadcasting for efficient nearest-neighbor queries.
    For very large graphs, consider using FAISS or Annoy.
    """
    
    def __init__(self, embeddings: dict[UUID, NodeEmbedding]):
        self.node_ids = list(embeddings.keys())
        self.matrix = np.array([
            embeddings[nid].as_array() for nid in self.node_ids
        ])
        # Normalize for cosine similarity
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        self.normalized = self.matrix / norms
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[tuple[UUID, float]]:
        """
        Find top-k most similar nodes to query vector.
        
        Args:
            query_vector: 1D array of same dimension as embeddings
            top_k: Number of results
            
        Returns:
            List of (node_id, similarity) pairs
        """
        # Normalize query
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []
        query_normalized = query_vector / query_norm
        
        # Compute all similarities at once
        similarities = self.normalized @ query_normalized
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [
            (self.node_ids[i], float(similarities[i]))
            for i in top_indices
        ]
    
    def search_by_id(self, node_id: UUID, top_k: int = 5) -> list[tuple[UUID, float]]:
        """Find nodes similar to a given node."""
        if node_id not in self.node_ids:
            return []
        
        idx = self.node_ids.index(node_id)
        query = self.matrix[idx]
        
        results = self.search(query, top_k + 1)  # +1 to exclude self
        return [(nid, sim) for nid, sim in results if nid != node_id][:top_k]
