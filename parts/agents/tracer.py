"""Tracer Agent.

A simple agent used to verify the CI/CD pipeline.
It uses a TestModel to ensure deterministic behavior without needing a running LLM.
"""

from typing import Optional
from pydantic_ai.models.test import TestModel
from parts.templates.deep_agent import DeepAgent
from agent_factory.models_v2 import UserObject


class TracerAgent(DeepAgent):
    """A minimal agent for pipeline verification."""

    def __init__(self, user: Optional[UserObject] = None):
        # Use TestModel for deterministic "Hello World"
        model = TestModel()

        super().__init__(
            name="TracerAgent",
            model=model,
            user=user,
            system_prompt="You are a tracer bullet. Respond with 'PONG'.",
        )

    # We can add custom methods here to verify inheritance works across the pipeline
    def ping(self) -> str:
        return "PONG"
