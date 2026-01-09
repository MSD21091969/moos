"""Base Agent - Abstract base class for all Factory agents.

All agents inherit from this to ensure consistent interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable
from pydantic import BaseModel, Field


class IOSchema(BaseModel):
    """Standard I/O schema for agent communication."""
    content: str
    metadata: dict = Field(default_factory=dict)
    source: str | None = None
    timestamp: str | None = None


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""
    agent_type: str
    model: str | None = None  # Override default model
    tools: list[str] = Field(default_factory=list)
    options: dict = Field(default_factory=dict)
    auto_ignite: bool = False


class BaseAgent(ABC):
    """
    Abstract base class for all Factory agents.
    
    Agents are configured combinations of:
    - A model adapter (which LLM to use)
    - A tool registry (what tools are available)
    - A prompt template (how to format prompts)
    """
    
    def __init__(
        self,
        name: str,
        config: AgentConfig | None = None,
    ):
        self.name = name
        self.config = config or AgentConfig(agent_type="base")
        self.history: list[dict] = []
        self._tools: dict[str, Callable] = {}
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Get the default model for this agent."""
        pass
    
    @property
    def model(self) -> str:
        """Get the active model (config override or default)."""
        return self.config.model or self.default_model
    
    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool for this agent."""
        self._tools[name] = func
    
    def get_tools(self) -> dict[str, Callable]:
        """Get all registered tools."""
        return self._tools
    
    @abstractmethod
    async def process(self, input: IOSchema) -> IOSchema:
        """Process an input and return a response."""
        pass
    
    def sync_process(self, input: IOSchema) -> IOSchema:
        """Synchronous version of process (for CLI)."""
        import asyncio
        return asyncio.run(self.process(input))
    
    def chat(self, message: str) -> str:
        """Simple chat interface."""
        input_schema = IOSchema(content=message)
        output = self.sync_process(input_schema)
        return output.content
    
    def reset(self) -> None:
        """Clear conversation history."""
        self.history = []
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} model={self.model}>"
