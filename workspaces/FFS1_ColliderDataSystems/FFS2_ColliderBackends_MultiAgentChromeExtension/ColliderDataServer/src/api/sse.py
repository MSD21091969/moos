from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/sse", tags=["sse"])

# In-memory client queues — keyed by client ID
_clients: dict[str, asyncio.Queue] = {}


async def broadcast_event(event_type: str, data: dict) -> None:
    """Broadcast an SSE event to all connected clients."""
    for queue in _clients.values():
        await queue.put({"event": event_type, "data": data})


@router.get("/")
async def sse_stream(request: Request):
    """SSE stream endpoint. Each client gets its own queue."""
    client_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _clients[client_id] = queue

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    yield {"event": "keepalive", "data": ""}
        finally:
            _clients.pop(client_id, None)

    return EventSourceResponse(event_generator())
