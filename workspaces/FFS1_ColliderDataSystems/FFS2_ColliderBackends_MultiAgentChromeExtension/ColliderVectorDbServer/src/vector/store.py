"""Simple in-memory vector store for MVP (no external deps)."""
import numpy as np
from typing import Optional


# In-memory storage
_documents: dict[str, dict] = {}


async def embed_text(text: str, document_id: str, metadata: dict = None):
    """Store text with simple hash-based 'embedding' for MVP."""
    # MVP: Use text directly, no real embedding
    _documents[document_id] = {
        "text": text,
        "metadata": metadata or {},
    }
    return {"id": document_id, "status": "indexed"}


async def search_similar(query: str, n_results: int = 10) -> list[dict]:
    """Simple keyword search for MVP."""
    query_lower = query.lower()
    results = []
    
    for doc_id, doc in _documents.items():
        text_lower = doc["text"].lower()
        # Simple relevance: count query words found
        score = sum(1 for word in query_lower.split() if word in text_lower)
        if score > 0:
            results.append({
                "id": doc_id,
                "document": doc["text"],
                "metadata": doc["metadata"],
                "distance": 1.0 / (score + 1),  # Lower = better match
            })
    
    # Sort by distance (lower = better)
    results.sort(key=lambda x: x["distance"])
    return results[:n_results]


async def index_documents(documents: list[dict]):
    """Bulk index documents."""
    for d in documents:
        _documents[d["id"]] = {
            "text": d["text"],
            "metadata": d.get("metadata", {}),
        }
    return {"count": len(documents), "status": "indexed"}
