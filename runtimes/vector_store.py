"""GPU-accelerated vector store using FAISS."""
import numpy as np
import faiss
import ollama
from pathlib import Path
from typing import Optional


class VectorStore:
    """
    FAISS-based vector store for RAG.
    
    Uses Ollama embeddings + FAISS for fast similarity search.
    On RTX 3060 12GB, can handle millions of vectors.
    """
    
    def __init__(
        self,
        embedding_model: str = "nomic-embed-text",
        dimension: int = 768,
        use_gpu: bool = True,
    ):
        self.embedding_model = embedding_model
        self.dimension = dimension
        self.use_gpu = use_gpu
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        
        # Try GPU if available and requested
        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                self.gpu_enabled = True
            except Exception:
                # Fall back to CPU
                self.gpu_enabled = False
        else:
            self.gpu_enabled = False
        
        # Store documents alongside vectors
        self.documents: list[str] = []
        self.metadata: list[dict] = []
    
    def _embed(self, text: str) -> np.ndarray:
        """Generate embedding for text using Ollama."""
        response = ollama.embeddings(
            model=self.embedding_model,
            prompt=text,
        )
        return np.array(response["embedding"], dtype=np.float32)
    
    def add(self, text: str, metadata: Optional[dict] = None):
        """Add a document to the store."""
        embedding = self._embed(text)
        self.index.add(embedding.reshape(1, -1))
        self.documents.append(text)
        self.metadata.append(metadata or {})
    
    def add_batch(self, texts: list[str], metadata: Optional[list[dict]] = None):
        """Add multiple documents at once (faster)."""
        embeddings = np.array([self._embed(t) for t in texts], dtype=np.float32)
        self.index.add(embeddings)
        self.documents.extend(texts)
        self.metadata.extend(metadata or [{} for _ in texts])
    
    def search(self, query: str, k: int = 5) -> list[tuple[str, float, dict]]:
        """
        Search for similar documents.
        
        Returns list of (document, distance, metadata) tuples.
        """
        query_embedding = self._embed(query).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    float(dist),
                    self.metadata[idx],
                ))
        return results
    
    def save(self, path: Path):
        """Save index and documents to disk."""
        # Convert GPU index to CPU for saving
        if self.gpu_enabled:
            cpu_index = faiss.index_gpu_to_cpu(self.index)
        else:
            cpu_index = self.index
        
        faiss.write_index(cpu_index, str(path / "index.faiss"))
        np.save(path / "documents.npy", np.array(self.documents, dtype=object))
        np.save(path / "metadata.npy", np.array(self.metadata, dtype=object))
    
    def load(self, path: Path):
        """Load index and documents from disk."""
        self.index = faiss.read_index(str(path / "index.faiss"))
        self.documents = list(np.load(path / "documents.npy", allow_pickle=True))
        self.metadata = list(np.load(path / "metadata.npy", allow_pickle=True))
        
        # Move to GPU if requested
        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                self.gpu_enabled = True
            except Exception:
                self.gpu_enabled = False
    
    @property
    def count(self) -> int:
        """Number of documents in store."""
        return len(self.documents)
    
    def __repr__(self):
        gpu_status = "GPU" if self.gpu_enabled else "CPU"
        return f"VectorStore({self.count} docs, {gpu_status})"
