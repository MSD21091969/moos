"""
Model Configuration
===================
Unified model configuration with sensible defaults.

Default: Gemini 2.5 Flash via google-vertex provider
Override via environment variables: LLM_PROVIDER, LLM_MODEL
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

# Supported model providers for pydantic-ai format
ModelProvider = Literal[
    "google-vertex",  # Google Vertex AI (Gemini models)
    "gemini",  # Google AI Studio (direct Gemini API)
    "ollama",  # Local Ollama
    "openai",  # OpenAI API
    "anthropic",  # Anthropic API
    "test",  # Test mode (no actual API calls)
]


class ModelConfig(BaseModel):
    """
    Unified model configuration for Collider agents.

    Usage:
        config = ModelConfig.from_env()
        model_string = config.to_pydantic_ai_string()
        # -> "google-vertex:gemini-2.5-flash"

    Environment Variables:
        LLM_PROVIDER: Provider name (default: "google-vertex")
        LLM_MODEL: Model name (default: "gemini-2.5-flash")

    For frontend (Vite):
        VITE_LLM_PROVIDER, VITE_LLM_MODEL, VITE_GEMINI_API_KEY
    """

    provider: ModelProvider = Field(
        default="google-vertex", description="Model provider for pydantic-ai format"
    )
    name: str = Field(default="gemini-2.5-flash", description="Model name/identifier")

    # Optional overrides
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, ge=1)

    @classmethod
    def from_env(cls) -> "ModelConfig":
        """
        Create ModelConfig from environment variables.

        Reads:
            LLM_PROVIDER (default: google-vertex)
            LLM_MODEL (default: gemini-2.5-flash)
            LLM_TEMPERATURE (default: 0.7)
            LLM_MAX_TOKENS (default: 8192)
        """
        return cls(
            provider=os.getenv("LLM_PROVIDER", "google-vertex"),  # type: ignore
            name=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
        )

    def to_pydantic_ai_string(self) -> str:
        """
        Format for pydantic-ai Agent model parameter.

        Returns:
            String in format "provider:model-name"
            e.g., "google-vertex:gemini-2.5-flash"
        """
        return f"{self.provider}:{self.name}"

    def to_frontend_config(self) -> dict:
        """
        Export config for frontend consumption.

        Returns:
            Dict with provider, model, temperature, maxTokens
        """
        return {
            "provider": self.provider,
            "model": self.name,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }


# =============================================================================
# Default Configurations
# =============================================================================

# Production default: Gemini 2.5 Flash via Vertex AI
DEFAULT_MODEL = ModelConfig()

# Development fallback: Local Ollama
DEV_MODEL = ModelConfig(
    provider="ollama",
    name="llama3.2:7b",
)

# Test mode: No API calls
TEST_MODEL = ModelConfig(
    provider="test",
    name="test-model",
)


def get_model_config() -> ModelConfig:
    """
    Get the appropriate ModelConfig based on environment.

    Checks TDC_ENV:
        - "test" -> TEST_MODEL
        - "dev" with no LLM_PROVIDER -> DEV_MODEL (Ollama)
        - Otherwise -> from_env() (respects LLM_PROVIDER/LLM_MODEL)
    """
    env = os.getenv("TDC_ENV", "dev")

    if env == "test":
        return TEST_MODEL

    # If LLM_PROVIDER is explicitly set, use it
    if os.getenv("LLM_PROVIDER"):
        return ModelConfig.from_env()

    # Otherwise use default (Gemini 2.5 Flash)
    return DEFAULT_MODEL
