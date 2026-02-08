from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """
    Mirror of ChatMessage in parts/templates/frontend/chat_store.ts
    """
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str
    metadata: Optional[dict[str, Any]] = None

class ChatRequest(BaseModel):
    """
    Standard request envelope for the chat endpoint.
    """
    message: str = Field(description="The new message content from the user")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
