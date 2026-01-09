"""Agent Factory Runtimes - execution environments for definitions."""

from .base import AgentRuntime
from .vector_store import VectorStore
from .fat import FatRunner, fatruntime, EnvironmentManager
from .model_selector import (
    TaskType,
    detect_task_type,
    select_model,
    get_model_context,
    list_available_models,
)
from .options import OllamaOptions, get_preset, PRESETS
from .streaming import stream_chat, stream_generate, print_callback
from .function_calling import (
    to_ollama_tool,
    build_tool_registry,
    parse_tool_call,
    execute_tool,
)

__all__ = [
    # Base
    "AgentRuntime",
    "VectorStore",
    # Fat runtime
    "FatRunner",
    "fatruntime",
    "EnvironmentManager",
    # Model selection
    "TaskType",
    "detect_task_type",
    "select_model",
    "get_model_context",
    "list_available_models",
    # Options
    "OllamaOptions",
    "get_preset",
    "PRESETS",
    # Streaming
    "stream_chat",
    "stream_generate",
    "print_callback",
    # Function calling
    "to_ollama_tool",
    "build_tool_registry",
    "parse_tool_call",
    "execute_tool",
]
