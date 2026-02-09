"""WebRTC signaling server for user-to-user communication."""

from __future__ import annotations

import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/rtc", tags=["rtc"])

# Room management
rooms: Dict[str, Set[WebSocket]] = {}
user_connections: Dict[str, WebSocket] = {}


@router.websocket("/")
async def websocket_rtc_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for WebRTC signaling.

    Message types:
    - join: { type: 'join', userId: string, roomId: string }
    - offer: { type: 'offer', sdp: string, targetUserId: string }
    - answer: { type: 'answer', sdp: string, targetUserId: string }
    - ice: { type: 'ice', candidate: object, targetUserId: string }
    """
    await websocket.accept()
    user_id: str | None = None
    room_id: str | None = None

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "join":
                user_id = data.get("userId")
                room_id = data.get("roomId")

                # Register user connection
                user_connections[user_id] = websocket

                # Add to room
                if room_id not in rooms:
                    rooms[room_id] = set()
                rooms[room_id].add(websocket)

                logger.info(f"User {user_id} joined room {room_id}")

                # Notify user of successful join
                await websocket.send_json(
                    {
                        "type": "joined",
                        "userId": user_id,
                        "roomId": room_id,
                    }
                )

            elif msg_type in ["offer", "answer", "ice"]:
                target_user_id = data.get("targetUserId")
                if target_user_id in user_connections:
                    target_ws = user_connections[target_user_id]
                    # Forward message to target user
                    await target_ws.send_json(data)
                    logger.debug(
                        f"Forwarded {msg_type} from {user_id} to {target_user_id}"
                    )
                else:
                    logger.warning(f"Target user {target_user_id} not found")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"User {target_user_id} not connected",
                        }
                    )

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if user_id and user_id in user_connections:
            del user_connections[user_id]
        if room_id and room_id in rooms:
            rooms[room_id].discard(websocket)
            if not rooms[room_id]:
                del rooms[room_id]
                logger.info(f"Room {room_id} is now empty")
