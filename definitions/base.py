"""Base definition model for all Collider agents."""
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class KnowledgeConfig(BaseModel):
    """Knowledge base configuration."""
    model_config = ConfigDict(frozen=True)
    
    knowledge_dir: Path | None = None
    embedding_model: str = "nomic-embed-text"


class ReasoningConfig(BaseModel):
    """Reasoning behavior configuration."""
    model_config = ConfigDict(frozen=True)
    
    chain_of_thought: bool = True
    max_history: int = 20
    collider_aware: bool = False


class ModelConfig(BaseModel):
    """LLM model configuration."""
    model_config = ConfigDict(frozen=True)
    
    model_name: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7


class ColliderAgentDefinition(BaseModel):
    """
    Base definition for all Collider agents.
    
    This is the immutable specification that defines WHAT an agent is.
    The runtime (HOW) executes this definition.
    """
    model_config = ConfigDict(frozen=True)
    
    # Identity
    name: str
    version: int = 1
    description: str = ""
    
    # Core configuration
    system_prompt: str
    knowledge: KnowledgeConfig | None = None
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    
    # Capabilities
    tool_names: list[str] = Field(default_factory=list)
    
    # Authentication (for Collider ecosystem)
    is_authenticated: bool = False
    
    def to_collider_object(self) -> dict:
        """Export as Collider-compatible object."""
        return {
            "type": "AgentDefinition",
            "name": self.name,
            "version": self.version,
            "spec": self.model_dump(),
        }
