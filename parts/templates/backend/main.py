import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn

from .models import ChatRequest, ChatMessage
from .deps import get_agent_runner
from agent_factory.parts.runtimes.runner import AgentRunner

app = FastAPI(title="Backend API Template")

# CORS - Allow all for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    runner: AgentRunner = Depends(get_agent_runner)
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    """
    async def event_generator():
        try:
            # Prepare dependencies (user_input, history)
            # Deps are managed by the runner's internal agent configuration usually, 
            # or passed here if per-request deps are needed.
            # detailed implementation depends on the specific Agent.
            
            # For this template, we assume a simple run
            # We convert Pydantic models to dicts/compatible format for the runner history if needed
            # But the runner signature expects list.
            
            history_data = [m.model_dump() for m in request.history]
            
            async for event in runner.run(
                user_input=request.message,
                deps={}, # Deps would be injected here in a real app
                history=history_data
            ):
                # Format event for SSE
                yield {
                    "event": "message", 
                    "data": json.dumps(event.model_dump())
                }
                
        except Exception as e:
            # Emit error event
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
