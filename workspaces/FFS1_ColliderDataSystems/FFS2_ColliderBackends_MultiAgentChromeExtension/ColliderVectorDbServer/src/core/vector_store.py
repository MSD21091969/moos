"""Numpy-based Vector Store Implementation.

Replaces chromadb due to compatibility issues.
Simple in-memory store with disk persistence using JSON/Pickle.
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """Lightweight vector store using numpy and sentence-transformers."""

    def __init__(self, persist_directory: str = "./vector_data"):
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.persist_dir / "metadata.json"
        self.vectors_file = self.persist_dir / "vectors.npy"
        
        self.model_name = "all-MiniLM-L6-v2"
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model: {e}")
            self.model = None

        # In-memory storage
        self.metadata: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        
        self._load()

    def _load(self):
        """Load data from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self.metadata = []
        else:
            self.metadata = []

        if self.vectors_file.exists():
            try:
                self.vectors = np.load(self.vectors_file)
            except Exception as e:
                logger.error(f"Failed to load vectors: {e}")
                self.vectors = None
        else:
            self.vectors = None
            
        # Verify alignment
        if self.vectors is not None and len(self.metadata) != len(self.vectors):
            logger.warning("Metadata and vectors misalignment! Resetting.")
            self.metadata = []
            self.vectors = None

    def _save(self):
        """Save data to disk."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
            
            if self.vectors is not None:
                np.save(self.vectors_file, self.vectors)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def index_tool_full(
        self,
        tool_name: str,
        description: str,
        origin_node_id: str,
        owner_user_id: str,
        params_schema_json: str,
    ) -> bool:
        """Add or update a tool in the vector index."""
        if not self.model:
            logger.error("Embedding model not initialized.")
            return False

        try:
            # Construct document text
            document = f"{tool_name}: {description}\nParameters: {params_schema_json}"
            
            # Compute embedding
            embedding = self.model.encode(document)
            
            # Check if exists (update)
            idx = -1
            for i, meta in enumerate(self.metadata):
                if meta["tool_name"] == tool_name and meta["origin_node_id"] == origin_node_id:
                    idx = i
                    break
            
            meta_entry = {
                "tool_name": tool_name,
                "description": description,
                "origin_node_id": origin_node_id,
                "owner_user_id": owner_user_id,
                "document": document, # Store doc for debug/retrieval if needed
            }

            if idx >= 0:
                # Update
                self.metadata[idx] = meta_entry
                self.vectors[idx] = embedding
            else:
                # Add new
                self.metadata.append(meta_entry)
                if self.vectors is None:
                    self.vectors = np.array([embedding])
                else:
                    self.vectors = np.vstack([self.vectors, embedding])
            
            self._save()
            return True

        except Exception as e:
            logger.error(f"Failed to index tool {tool_name}: {e}")
            return False

    def search_tools(
        self,
        query: str,
        limit: int = 5,
        owner_user_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Search for tools semantically."""
        if not self.model or self.vectors is None or len(self.metadata) == 0:
            return []

        try:
            query_embedding = self.model.encode(query)
            
            # Cosine similarity
            # unexpected shape for vectors? vectors should be (N, D), query (D,)
            # similarity = (A . B) / (|A| * |B|)
            # sentence-transformers embeddings are usually normalized? 
            # If not, we should normalize. They are usually normalized if normalize_embeddings=True content-wise but explicit dot product requires checks.
            # Default encode doesn't normalize unless specified? actually typical models output normalized vectors or close to it.
            # Let's do explicit cosine similarity.
            
            norm_vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)
            norm_query = query_embedding / np.linalg.norm(query_embedding)
            
            scores = np.dot(norm_vectors, norm_query)
            
            # Get top k indices
            top_k_indices = np.argsort(scores)[::-1][:limit]
            
            results = []
            for idx in top_k_indices:
                score = float(scores[idx])
                meta = self.metadata[idx]
                
                # Apply filters
                if owner_user_id and meta.get("owner_user_id") != owner_user_id:
                    continue
                    
                results.append({
                    "tool_name": meta["tool_name"],
                    "description": meta["description"],
                    "origin_node_id": meta["origin_node_id"],
                    "score": score,
                })
            
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_tool(self, tool_name: str, origin_node_id: str | None = None) -> bool:
        """Remove a tool from the vector index."""
        if self.vectors is None:
            return False
            
        try:
            indices_to_remove = []
            for i, meta in enumerate(self.metadata):
                if meta["tool_name"] == tool_name:
                    if origin_node_id is None or meta["origin_node_id"] == origin_node_id:
                        indices_to_remove.append(i)
            
            if not indices_to_remove:
                return False
                
            # Sort descending to remove correctly
            for i in sorted(indices_to_remove, reverse=True):
                del self.metadata[i]
                
            mask = np.ones(len(self.vectors), dtype=bool)
            mask[indices_to_remove] = False
            self.vectors = self.vectors[mask]
            
            if len(self.vectors) == 0:
                self.vectors = None
                
            self._save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tool {tool_name}: {e}")
            return False

# Global instance
store = VectorStore(persist_directory="./vector_data")
