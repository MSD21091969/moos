"""Collider GraphTool Server - FastAPI + WebSocket application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.ws import websocket_handler


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    print(f"Collider GraphTool Server starting on {settings.host}:{settings.port}")
    yield
    print("Collider GraphTool Server shutting down")


app = FastAPI(
    title="Collider GraphTool Server",
    version="0.1.0",
    description="WebSocket Workflow Executor for Collider",
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


@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for workflow execution."""
    await websocket_handler(websocket, session_id)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "collider-graphtool-server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
