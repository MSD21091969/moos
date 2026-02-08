"""Standard DeepAgent Template.

This is the standard Agent class that all Factory-produced agents should use.
It wraps `pydantic-ai` with the Factory's `models_v2` context.
"""
from typing import Optional, List, Any, Type
from pydantic_ai import Agent
from pydantic_ai.models import Model
from agent_factory.models_v2 import UserObject, Container

class DeepAgent:
    """The Industrial Standard Agent Class."""
    
    def __init__(
        self,
        name: str,
        model: str | Any,  # String alias or Model object
        user: Optional[UserObject] = None,
        toolsets: Optional[List[Any]] = None,
        skills: Optional[List[str]] = None, # markdown content of skills
        system_prompt: str = ""
    ):
        self.name = name
        self.user = user or UserObject(auth_id="guest", email="guest@localhost")
        self.model = model
        self.system_prompt = system_prompt
        self.skills = skills or []
        
        # Initialize internal Pydantic-AI Agent
        self._agent = Agent(
            model=self.model,
            system_prompt=self._build_instructions(),
            deps_type=Any # We inject context manually for now
        )
        
        # Register Tools
        if toolsets:
            for tools in toolsets:
                # Assuming toolset is a class instance with @tool decorated methods
                # or a list of functions. Pydantic-AI is flexible.
                # For now, we assume simple list or object with .tools property
                if hasattr(tools, 'tools'):
                     for t in tools.tools:
                         self._agent.tool(t)
                else:
                    # Provide the object itself to inspect methods? 
                    # Simpler to just assume it's a list for V1
                    pass

    def _build_instructions(self) -> str:
        """Compose the System Prompt from Skills and Context."""
        parts = [
            f"You are {self.name}.",
            self.system_prompt,
            "\n## YOUR SKILLS",
        ]
        if self.skills:
            parts.extend(self.skills)
            
        parts.append("\n## CONTEXT")
        parts.append(f"User: {self.user.email}")
        
        return "\n".join(parts)

    async def run(self, prompt: str) -> Any:
        """Execute the agent."""
        # Simple run wrapper
        return await self._agent.run(prompt)

    @classmethod
    def from_spec(cls, spec: "AgentSpec", user: Optional[UserObject] = None) -> "DeepAgent":
        """
        Create a DeepAgent runtime from a configuration spec.
        
        Args:
            spec: The AgentSpec configuration (loaded)
            user: The user context
        """
        # Load tools dynamically
        toolsets = []
        for tool_path in spec.tools:
            try:
                # Dynamic import implementation
                # Assuming toolpath is like "parts.toolsets.filesystem"
                import importlib
                module = importlib.import_module(tool_path)
                toolsets.append(module)
            except ImportError as e:
                print(f"Warning: Failed to load tool {tool_path}: {e}")

        return cls(
            name=spec.name,
            model=spec.model,
            user=user,
            toolsets=toolsets,
            skills=spec.knowledge + spec.rules, # Treat knowledge/rules as skills
            system_prompt=spec.instructions
        )
