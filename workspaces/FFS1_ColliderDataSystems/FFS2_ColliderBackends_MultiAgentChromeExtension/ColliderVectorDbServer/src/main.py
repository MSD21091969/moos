from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Collider VectorDB Server",
    version="0.1.0",
)


class SearchRequest(BaseModel):
    collection: str = "tools"
    query: str
    n_results: int = 5


class EmbedRequest(BaseModel):
    texts: list[str]


class IndexRequest(BaseModel):
    collection: str = "tools"
    ids: list[str]
    documents: list[str]
    metadatas: list[dict] | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "collider-vectordb-server"}


@app.post("/api/v1/search")
async def search(body: SearchRequest):
    from src.search.engine import search_engine

    results = search_engine.search(
        collection=body.collection,
        query=body.query,
        n_results=body.n_results,
    )
    return {"results": results, "query": body.query, "collection": body.collection}


@app.post("/api/v1/embed")
async def embed(body: EmbedRequest):
    from src.embeddings.generator import embedding_generator

    embeddings = embedding_generator.embed(body.texts)
    return {"embeddings": embeddings, "count": len(embeddings)}


@app.post("/api/v1/index")
async def index(body: IndexRequest):
    from src.search.engine import search_engine

    count = search_engine.index(
        collection=body.collection,
        ids=body.ids,
        documents=body.documents,
        metadatas=body.metadatas,
    )
    return {"indexed": count, "collection": body.collection}
