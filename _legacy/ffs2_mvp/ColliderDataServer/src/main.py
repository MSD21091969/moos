"""Collider Data Server - FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.db import init_db
from src.api import (
    auth_router,
    apps_router,
    nodes_router,
    sse_router,
    users_router,
    secrets_router,
)


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - init/shutdown."""
    # Startup
    await init_db()
    print(f"Collider Data Server starting on {settings.host}:{settings.port}")
    yield
    # Shutdown
    print("Collider Data Server shutting down")


app = FastAPI(
    title="Collider Data Server",
    version="0.1.0",
    description="REST + SSE API for Collider",
    lifespan=lifespan,
)

# CORS - allow configured origins + all chrome extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(apps_router, prefix="/api/v1")
app.include_router(nodes_router, prefix="/api/v1")
app.include_router(sse_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(secrets_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "collider-data-server"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
