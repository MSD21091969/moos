"""
WebSocket Connection Manager Template
Source: Agent Studio Reference Implementation
"""
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # active_connections: user_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # active_editors: canvas_id -> set(user_id)
        self.active_editors: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove user from all canvas locations
        empty_canvasses = []
        for canvas_id, editors in self.active_editors.items():
            if user_id in editors:
                editors.remove(user_id)
                if not editors:
                    empty_canvasses.append(canvas_id)
        
        for cid in empty_canvasses:
            del self.active_editors[cid]
            
    async def join_canvas(self, user_id: str, canvas_id: str):
        if canvas_id not in self.active_editors:
            self.active_editors[canvas_id] = set()
        self.active_editors[canvas_id].add(user_id)
        await self.broadcast_presence()

    async def leave_canvas(self, user_id: str, canvas_id: str):
        if canvas_id in self.active_editors:
            if user_id in self.active_editors[canvas_id]:
                self.active_editors[canvas_id].remove(user_id)
                if not self.active_editors[canvas_id]:
                    del self.active_editors[canvas_id]
        await self.broadcast_presence()

    async def broadcast_presence(self):
        """Broadcast the current list of active editors for all canvasses."""
        # Convert sets to lists for JSON serialization
        presence_data = {
            cid: list(editors) 
            for cid, editors in self.active_editors.items()
        }
        
        message = {
            "type": "presence_update",
            "editors": presence_data
        }
        
        # Broadcast to all connected clients
        to_remove = []
        for uid, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send presence to {uid}: {e}")
                to_remove.append(uid)
        
        # Cleanup broken connections
        for uid in to_remove:
            self.disconnect(uid)

manager = ConnectionManager()
