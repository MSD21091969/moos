import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai.exceptions import UnexpectedModelBehavior

from app.deps import get_deps
from app.agents.coordinator import coordinator
from app.models import UserMessage, AgentResponse, AgentThought, ErrorMessage

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Full Stack Deep Agent")

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")
    
    deps = get_deps()
    
    try:
        while True:
            # Receive text from client (JSON)
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                user_msg = UserMessage(**data)
            except Exception as e:
                logger.error(f"Invalid message format: {e}")
                await websocket.send_json(ErrorMessage(detail="Invalid JSON format").model_dump())
                continue

            logger.info(f"Received message: {user_msg.content}")

            # Run the agent stream
            try:
                # We use run_stream to get tokens/tool calls in real-time
                # Note: pydantic-deep agent.run_stream usage
                async with coordinator.run_stream(user_msg.content, deps=deps) as result:
                    async for chunk in result.stream():
                        # Stream tokens to frontend
                        logger.info(f"Chunk: {chunk!r}")  # Debug log
                        await websocket.send_json({
                            "type": "token",
                            "content": str(chunk) 
                        })
                        
                # After stream, get final result
                # Note: In pydantic-ai >0.0.18, usage might vary. 
                # If get_data() is missing, we trust the accumulated chunks or use .final_result if available
                # For this demo, let's rely on the accumulated text we streamed.
                
                # To be safe and since we streamed everything, we can just send a "done" message
                # or try to access the final result properly if we need structured data.
                # Let's assume for now we just want to close the thought process.
                
                await websocket.send_json(AgentResponse(content="[Done]").model_dump())
                
            except UnexpectedModelBehavior as e:
                logger.error(f"Model Error: {e}")
                await websocket.send_json(ErrorMessage(type="error", detail=str(e)).model_dump())
            except Exception as e:
                logger.error(f"Agent Error: {e}")
                await websocket.send_json(ErrorMessage(type="error", detail=str(e)).model_dump())

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
