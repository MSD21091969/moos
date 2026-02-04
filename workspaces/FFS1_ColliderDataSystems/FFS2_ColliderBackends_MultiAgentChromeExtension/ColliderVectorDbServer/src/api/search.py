"""VectorDB search API routes."""
from fastapi import APIRouter
from pydantic import BaseModel

from src.vector import embed_text, search_similar, index_documents

router = APIRouter(prefix="/api/v1", tags=["search"])


class EmbedRequest(BaseModel):
    text: str
    document_id: str
    metadata: dict = {}


class SearchRequest(BaseModel):
    query: str
    n_results: int = 10


class IndexDocument(BaseModel):
    id: str
    text: str
    metadata: dict = {}


class IndexRequest(BaseModel):
    documents: list[IndexDocument]


@router.post("/embed")
async def embed(request: EmbedRequest):
    """Embed and store a single document."""
    result = await embed_text(
        text=request.text,
        document_id=request.document_id,
        metadata=request.metadata
    )
    return result


@router.post("/search")
async def search(request: SearchRequest):
    """Semantic search for similar documents."""
    results = await search_similar(
        query=request.query,
        n_results=request.n_results
    )
    return {"results": results}


@router.post("/index")
async def index(request: IndexRequest):
    """Bulk index documents."""
    docs = [d.model_dump() for d in request.documents]
    result = await index_documents(docs)
    return result
