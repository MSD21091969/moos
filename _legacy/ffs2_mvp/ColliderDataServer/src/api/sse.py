"""SSE (Server-Sent Events) endpoint."""
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(tags=["sse"])

# Global event queue for broadcasting
event_queues: list[asyncio.Queue] = []


async def event_generator():
    """Generate SSE events."""
    queue: asyncio.Queue = asyncio.Queue()
    event_queues.append(queue)
    
    try:
        # Send initial heartbeat
        yield {"event": "connected", "data": "{}"}
        
        while True:
            # Wait for events or send heartbeat every 30s
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": "{}"}
    finally:
        event_queues.remove(queue)


@router.get("/sse")
async def sse_endpoint():
    """SSE endpoint for real-time events."""
    return EventSourceResponse(event_generator())


async def broadcast_event(event_type: str, data: dict):
    """Broadcast an event to all connected SSE clients."""
    import json
    event = {"event": event_type, "data": json.dumps(data)}
    for queue in event_queues:
        await queue.put(event)
