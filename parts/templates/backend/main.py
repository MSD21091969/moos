"""
Unified Backend Template
Includes:
- WebSocket Manager (ConnectionManager)
- Session/Container CRUD
- Chat Endpoint
- Global Exception Handlers
"""
import json
import logging
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# Import Factory Models directly (The Kit)
from agent_factory.models_v2 import Container, UserObject, ArtifactReference
from agent_factory.parts.runtimes.runner import AgentRunner
from .websocket_manager import manager
from .deps import get_agent_runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="Unified Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Memory Store (Replace with SQLite in production) ---
containers: Dict[str, Container] = {}
# Seed one container
seed_id = str(uuid4())
containers[seed_id] = Container(
    id=seed_id,
    owner_id="guest",
    name="Welcome Project",
    context={"system": "Initial State"}
)

class CreateSessionRequest(BaseModel):
    name: str
    definition_id: Optional[str] = None

# --- REST Endpoints ---

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "containers": len(containers)}

@app.get("/api/session", response_model=List[Container])
async def list_sessions():
    """List all containers."""
    return list(containers.values())

@app.get("/api/session/{container_id}", response_model=Container)
async def get_session(container_id: str):
    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Session not found")
    return containers[container_id]

@app.post("/api/session", response_model=Container)
async def create_session(request: CreateSessionRequest):
    """Create a new 'Container' (Session)."""
    new_id = str(uuid4())
    container = Container(
        id=new_id,
        owner_id="guest", # Todo: Auth
        name=request.name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    containers[new_id] = container
    logger.info(f"Created session {new_id}: {request.name}")
    return container

# --- WebSocket Endpoint (The Pilot Link) ---

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # Instantiate Pilot for this connection (Simple ephemeral pilot for Phase C)
    # In production, this would load from a persistent session store
    from agent_factory.parts.agents import create_collider_pilot
    pilot = create_collider_pilot() 
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {client_id}: {data}")
            
            try:
                # Parse Message
                payload = json.loads(data)
                user_content = payload.get("content", "")
                
                # Echo as ACK (Immediate Feedback)
                await manager.active_connections[client_id].send_json({
                    "type": "ack",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Run Pilot
                # Note: This is blocking in this simple version. 
                # Use pilot.run_stream for streaming in future.
                result = await pilot.run(user_content)
                
                # Send Response
                await manager.active_connections[client_id].send_json({
                    "type": "pilot_message",
                    "content": result.data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except json.JSONDecodeError:
                # Fallback for plain text
                await manager.active_connections[client_id].send_json({
                    "type": "error",
                    "content": "Invalid JSON format. Send {type: 'user_message', content: '...'}"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
