"""Advanced runtime configuration for Ollama models."""
from pydantic import BaseModel, Field
from typing import Optional


class OllamaOptions(BaseModel):
    """
    Advanced options for Ollama model execution.
    
    See: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
    """
    # Sampling parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1)
    
    # Context
    num_ctx: int = Field(default=8192, ge=128)  # Context window
    num_predict: int = Field(default=-1)  # Max tokens (-1 = unlimited)
    
    # Repetition control
    repeat_penalty: float = Field(default=1.1, ge=0.0)
    repeat_last_n: int = Field(default=64, ge=0)
    
    # Performance
    num_gpu: int = Field(default=-1)  # -1 = auto, 0 = CPU only
    num_thread: int = Field(default=0)  # 0 = auto
    
    # Stop sequences
    stop: list[str] = Field(default_factory=list)
    
    def to_ollama_dict(self) -> dict:
        """Convert to Ollama options dict."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
            "repeat_penalty": self.repeat_penalty,
            "repeat_last_n": self.repeat_last_n,
            "num_gpu": self.num_gpu,
            "num_thread": self.num_thread,
            "stop": self.stop,
        }


# Preset configurations
PRESETS = {
    "precise": OllamaOptions(
        temperature=0.1,
        top_p=0.85,
        repeat_penalty=1.2,
    ),
    "creative": OllamaOptions(
        temperature=0.9,
        top_p=0.95,
        top_k=60,
    ),
    "code": OllamaOptions(
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.0,
        num_ctx=16384,
    ),
    "reasoning": OllamaOptions(
        temperature=0.3,
        top_p=0.9,
        num_ctx=32768,
        num_predict=4096,
    ),
    "math": OllamaOptions(
        temperature=0.1,
        top_p=0.8,
        repeat_penalty=1.0,
    ),
}


def get_preset(name: str) -> OllamaOptions:
    """Get a preset configuration."""
    return PRESETS.get(name, OllamaOptions())
