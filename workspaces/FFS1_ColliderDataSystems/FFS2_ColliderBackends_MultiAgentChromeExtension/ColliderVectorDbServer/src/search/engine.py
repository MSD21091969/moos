from __future__ import annotations

from pathlib import Path

import chromadb

from src.core.config import settings
from src.embeddings.generator import embedding_generator

COLLECTION_NAMES = ["tools", "skills", "knowledge"]


class SearchEngine:
    """Semantic search engine wrapping ChromaDB."""

    def __init__(self) -> None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collections: dict[str, chromadb.Collection] = {}
        for name in COLLECTION_NAMES:
            self._collections[name] = self._client.get_or_create_collection(
                name=name, metadata={"hnsw:space": "cosine"}
            )

    def index(
        self,
        collection: str,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> int:
        """Index documents into a collection."""
        if collection not in self._collections:
            self._collections[collection] = self._client.get_or_create_collection(
                name=collection, metadata={"hnsw:space": "cosine"}
            )
        embeddings = embedding_generator.embed(documents)
        self._collections[collection].upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(ids)

    def search(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """Search for similar documents in a collection."""
        if collection not in self._collections:
            return []
        query_embedding = embedding_generator.embed_single(query)
        results = self._collections[collection].query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        items = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                item = {"id": doc_id}
                if results["documents"] and results["documents"][0]:
                    item["document"] = results["documents"][0][i]
                if results["distances"] and results["distances"][0]:
                    item["distance"] = results["distances"][0][i]
                if results["metadatas"] and results["metadatas"][0]:
                    item["metadata"] = results["metadatas"][0][i]
                items.append(item)
        return items


# Singleton
search_engine = SearchEngine()
