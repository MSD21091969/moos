"""Factory Templates - Base classes for agents and specs."""

from .agent_spec import AgentSpec, load_agent_spec
from .deep_agent import DeepAgent

__all__ = ["AgentSpec", "DeepAgent", "load_agent_spec"]
