"""Collider VectorDB Server - FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.api import search_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    print(f"Collider VectorDB Server starting on {settings.host}:{settings.port}")
    yield
    print("Collider VectorDB Server shutting down")


app = FastAPI(
    title="Collider VectorDB Server",
    version="0.1.0",
    description="Semantic Search API for Collider",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(search_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "collider-vectordb-server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
