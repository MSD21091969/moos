from __future__ import annotations

from sentence_transformers import SentenceTransformer

from src.core.config import settings


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers."""

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        return self.embed([text])[0]


# Singleton
embedding_generator = EmbeddingGenerator()
