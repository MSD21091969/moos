from typing import Literal, Optional, Any
from pydantic import BaseModel

class UserMessage(BaseModel):
    """Message sent by the user."""
    type: Literal["user_message"] = "user_message"
    content: str
    files: Optional[list[Any]] = None  # Placeholder for file uploads

class AgentThought(BaseModel):
    """Intermediate thought or tool call from the agent."""
    type: Literal["agent_thought"] = "agent_thought"
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None

class AgentResponse(BaseModel):
    """Final answer from the agent."""
    type: Literal["agent_response"] = "agent_response"
    content: str

class ErrorMessage(BaseModel):
    """Error message."""
    type: Literal["error"] = "error"
    detail: str
