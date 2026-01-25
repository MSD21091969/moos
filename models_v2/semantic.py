"""Semantic Bridge - Vector Math and Recursive Summation.

Implements the "Bridge" between Pydantic Models and Vector Space.
"""
from __future__ import annotations
from typing import Optional, List, Any
import numpy as np
from pydantic import BaseModel, Field

# Constants from research
DEFAULT_DIM = 128

class VectorMath:
    """Math utilities for semantic vectors."""
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def vector_sum(vectors: List[np.ndarray]) -> np.ndarray:
        """Sum vectors element-wise."""
        if not vectors:
            return np.zeros(DEFAULT_DIM, dtype=np.float32)
        
        # Ensure all are same shape
        stacked = np.stack(vectors)
        return np.sum(stacked, axis=0)

    @staticmethod
    def delta_entropy(start_state: np.ndarray, end_state: np.ndarray) -> float:
        """
        Calculate semantic delta (Delta S).
        Simplified as Euclidean distance or specific semantic shift.
        """
        return float(np.linalg.norm(end_state - start_state))


class SemanticMixin(BaseModel):
    """
    Mixin for Semantic Containers.
    
    Provides:
    - embedding: The vector representation.
    - calculate_embedding(): Recursive Logic.
    """
    embedding: List[float] = Field(
        default_factory=lambda: [0.0] * DEFAULT_DIM,
        description="Semantic Vector Representation"
    )
    
    # Internal cache flag
    _semantic_dirty: bool = True

    def get_embedding_vector(self) -> np.ndarray:
        """Get embedding as numpy array."""
        return np.array(self.embedding, dtype=np.float32)

    def update_embedding(self, recursive: bool = True):
        """
        Recalculate embedding based on children (Recursive Sum).
        
        V_Container = Sum(V_Child) + V_Self
        """
        # 1. Self content embedding (if any text/description)
        # Placeholder: Using random or zero for now, 
        # in real impl call OpenAI/HF model.
        v_self = np.zeros(DEFAULT_DIM, dtype=np.float32)
        if hasattr(self, 'description') and self.description:
            # v_self = embedding_model.encode(self.description)
            pass
            
        # 2. Recursive Sum of Children
        v_children = np.zeros(DEFAULT_DIM, dtype=np.float32)
        
        # Look for "children" or "internal_definitions" depending on object type
        children: List[Any] = []
        if hasattr(self, 'internal_definitions'): # CompositeDefinition
            children = self.internal_definitions
        elif hasattr(self, 'artifacts'): # Container
            # Artifacts might have embeddings?
            pass
            
        child_vectors = []
        for child in children:
            if isinstance(child, SemanticMixin):
                if recursive:
                    child.update_embedding()
                child_vectors.append(child.get_embedding_vector())
        
        if child_vectors:
            v_children = VectorMath.vector_sum(child_vectors)
            
        # 3. Combine
        # V_Total = V_Self + V_Children
        v_total = v_self + v_children
        
        # Normalize?
        norm = np.linalg.norm(v_total)
        if norm > 0:
            v_total = v_total / norm
            
        self.embedding = v_total.tolist()
        self._semantic_dirty = False
