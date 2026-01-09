"""Factory Parts - Reusable components for building agents.

Parts are the building blocks that Agents combine:
- BaseAgent: Abstract agent class
- ModelAdapter: Multi-model interface
- ToolRegistry: Unified tool management
- PromptTemplate: Template system
- IOSchema: Standard I/O format
"""

from .base_agent import BaseAgent, IOSchema, AgentConfig
from .model_adapter import ModelAdapter
from .tool_registry import ToolRegistry
from .prompt_template import (
    PromptTemplate,
    PromptSection,
    godel_template,
    chat_template,
    maintenance_template,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "IOSchema",
    "AgentConfig",
    # Model
    "ModelAdapter",
    # Tools
    "ToolRegistry",
    # Prompts
    "PromptTemplate",
    "PromptSection",
    "godel_template",
    "chat_template",
    "maintenance_template",
]
