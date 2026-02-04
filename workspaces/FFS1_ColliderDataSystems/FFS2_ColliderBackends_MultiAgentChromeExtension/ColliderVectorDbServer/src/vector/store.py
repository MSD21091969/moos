"""ChromaDB vector store wrapper."""
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings


settings = get_settings()

# Initialize ChromaDB client
chroma_client = chromadb.Client(ChromaSettings(
    persist_directory=settings.chroma_persist_dir,
    anonymized_telemetry=False,
))

# Default collection for tools/knowledge
default_collection = chroma_client.get_or_create_collection(
    name="collider_knowledge",
    metadata={"hnsw:space": "cosine"}
)


async def embed_text(text: str, document_id: str, metadata: dict = None):
    """Embed and store text."""
    default_collection.add(
        documents=[text],
        ids=[document_id],
        metadatas=[metadata or {}]
    )
    return {"id": document_id, "status": "indexed"}


async def search_similar(query: str, n_results: int = 10) -> list[dict]:
    """Search for similar documents."""
    results = default_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return [
        {
            "id": id_,
            "document": doc,
            "metadata": meta,
            "distance": dist
        }
        for id_, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0] if results.get("distances") else [0] * len(results["ids"][0])
        )
    ]


async def index_documents(documents: list[dict]):
    """Bulk index documents."""
    default_collection.add(
        documents=[d["text"] for d in documents],
        ids=[d["id"] for d in documents],
        metadatas=[d.get("metadata", {}) for d in documents]
    )
    return {"count": len(documents), "status": "indexed"}
