from typing import Any, AsyncGenerator, Optional, Dict
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_deep import DeepAgentDeps

class AgentEvent(BaseModel):
    """Standard event emitted by AgentRunner"""
    type: str  # 'token', 'tool_call', 'tool_result', 'final_result', 'error'
    data: Any

class AgentRunner:
    """
    Standardized backend execution runner for Operational Agents.
    Designed to be called by both CLI (Dev-Assistant) and API (Collider).
    """
    def __init__(self, agent: Agent):
        self.agent = agent

    async def run(
        self, 
        user_input: str, 
        deps: DeepAgentDeps,
        history: Optional[list] = None
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Execute the agent loop with standardized event emission.
        """
        try:
            # Note: This uses the standard pydantic-ai streaming interface
            async with self.agent.run_stream(user_input, deps=deps, message_history=history) as result:
                async for chunk in result.stream():
                    # Check for tool calls or text tokens
                    # (Simplified adapter logic - real impl would inspect chunk types)
                    if isinstance(chunk, str):
                        yield AgentEvent(type="token", data=chunk)
                    else:
                        yield AgentEvent(type="chunk", data=chunk)
                
                # Final usage/result would be emitted here
                
        except Exception as e:
            yield AgentEvent(type="error", data=str(e))
