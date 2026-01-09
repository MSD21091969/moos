"""Model Adapter - Multi-model interface for agents.

Provides a unified interface for switching between models.
"""
from typing import AsyncGenerator, Callable
from enum import Enum
import ollama

from runtimes.model_selector import TaskType, detect_task_type, MODEL_CAPABILITIES
from runtimes.options import OllamaOptions, get_preset


class ModelAdapter:
    """
    Adapter for using multiple Ollama models.
    
    Handles model selection, options, and streaming.
    """
    
    def __init__(
        self,
        default_model: str = "qwen3:14b",
        auto_select: bool = True,
    ):
        self.default_model = default_model
        self.auto_select = auto_select
        self.models = MODEL_CAPABILITIES
    
    def select(self, query: str, task_type: TaskType | None = None) -> str:
        """
        Select the best model for a query.
        
        Args:
            query: The user query
            task_type: Override detected task type
            
        Returns:
            Model name to use
        """
        if not self.auto_select:
            return self.default_model
        
        detected = task_type or detect_task_type(query)
        
        # Map task types to best models
        model_map = {
            TaskType.GENERAL: "qwen3:14b",
            TaskType.CODE: "codellama:13b",
            TaskType.MATH: "phi4:14b",
            TaskType.REASONING: "deepseek-r1:14b",
            TaskType.VISION: "gemma3:12b",
        }
        
        return model_map.get(detected, self.default_model)
    
    def get_options(self, preset: str = "reasoning") -> dict:
        """Get Ollama options for a preset."""
        return get_preset(preset).to_ollama_dict()
    
    def chat(
        self,
        model: str,
        messages: list[dict],
        options: dict | None = None,
    ) -> str:
        """
        Send a chat request to Ollama.
        
        Args:
            model: Model name
            messages: Chat messages
            options: Ollama options
            
        Returns:
            Response content
        """
        response = ollama.chat(
            model=model,
            messages=messages,
            options=options,
        )
        return response["message"]["content"]
    
    def stream(
        self,
        model: str,
        messages: list[dict],
        options: dict | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> str:
        """
        Stream a chat response.
        
        Args:
            model: Model name
            messages: Chat messages
            options: Ollama options
            callback: Called for each token
            
        Returns:
            Complete response
        """
        full_response = ""
        
        for chunk in ollama.chat(
            model=model,
            messages=messages,
            options=options,
            stream=True,
        ):
            content = chunk.get("message", {}).get("content", "")
            full_response += content
            if callback:
                callback(content)
        
        return full_response
    
    async def async_chat(
        self,
        model: str,
        messages: list[dict],
        options: dict | None = None,
    ) -> str:
        """Async version of chat (for backend use)."""
        client = ollama.AsyncClient()
        response = await client.chat(
            model=model,
            messages=messages,
            options=options,
        )
        return response["message"]["content"]
    
    async def async_stream(
        self,
        model: str,
        messages: list[dict],
        options: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """Async streaming generator."""
        client = ollama.AsyncClient()
        async for chunk in await client.chat(
            model=model,
            messages=messages,
            options=options,
            stream=True,
        ):
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    
    def list_models(self) -> list[str]:
        """List available models."""
        return list(self.models.keys())
    
    def get_model_info(self, model: str) -> dict:
        """Get info about a model."""
        return self.models.get(model, {})
