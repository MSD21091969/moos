"""FatRuntime - Decorator and manager for running definitions.

@fatruntime makes any class ignitable in custom environments.
"""
from __future__ import annotations
import functools
from typing import Any, Callable, TypeVar
from uuid import UUID

from models import Definition, Container


T = TypeVar("T")


class FatRunner:
    """
    Runtime manager that ignites definitions.
    
    Pulls from shared DB, extracts subgraph, runs in environment.
    """
    
    def __init__(self, definition: Definition, environment: str = "default"):
        self.definition = definition
        self.environment = environment
        self._is_ignited = False
        self._context: dict = {}
    
    @classmethod
    def from_db(cls, definition_id: UUID) -> "FatRunner":
        """Load a definition from shared DB."""
        # TODO: Connect to actual DB
        # For now, create a placeholder
        definition = Definition(
            id=definition_id,
            name=f"def_{definition_id}",
        )
        return cls(definition)
    
    @classmethod
    def from_container(cls, container: Container) -> "FatRunner":
        """Create runner from a container's definition."""
        if not container.definition:
            raise ValueError(f"Container {container.name} has no definition")
        return cls(container.definition)
    
    def ignite(self, **inputs) -> dict:
        """
        Ignite the definition into graph action.
        
        For composite definitions, recursively ignites children.
        """
        self._is_ignited = True
        
        results = {}
        
        if self.definition.is_atomic:
            # Run atomic definition
            results = self._run_atomic(**inputs)
        else:
            # Run composite: children first, then aggregate
            for child in self.definition.children:
                child_runner = FatRunner(child, self.environment)
                child_result = child_runner.ignite(**inputs)
                results[str(child.id)] = child_result
        
        return results
    
    def _run_atomic(self, **inputs) -> dict:
        """Run an atomic definition."""
        # Execute the code if present
        if self.definition.code:
            # Safe exec with limited globals
            local_vars: dict = {"inputs": inputs}
            try:
                exec(self.definition.code, {"__builtins__": {}}, local_vars)
                return {"result": local_vars.get("result"), "status": "success"}
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        return {"status": "no_code"}
    
    @property
    def is_ignited(self) -> bool:
        return self._is_ignited


def fatruntime(cls: type[T]) -> type[T]:
    """
    Decorator that makes a class ignitable via FatRunner.
    
    Usage:
        @fatruntime
        class MyAgent:
            def run(self, **inputs):
                return {"result": "done"}
    
    Then:
        runner = MyAgent.__fatrunner__
        runner.ignite(x=1, y=2)
    """
    # Create a definition from the class
    definition = Definition(
        name=cls.__name__,
        description=cls.__doc__ or "",
    )
    
    # Attach FatRunner to the class
    cls.__fatrunner__ = FatRunner(definition)  # type: ignore
    cls.__definition__ = definition  # type: ignore
    
    return cls


class EnvironmentManager:
    """Manages custom environments for running definitions."""
    
    ENVIRONMENTS = {
        "default": {},
        "frontend": {"framework": "react", "ssr": False},
        "server": {"framework": "fastapi", "workers": 4},
        "sandbox": {"isolated": True, "timeout": 10},
    }
    
    @classmethod
    def get_config(cls, name: str) -> dict:
        return cls.ENVIRONMENTS.get(name, cls.ENVIRONMENTS["default"])
    
    @classmethod
    def register(cls, name: str, config: dict) -> None:
        cls.ENVIRONMENTS[name] = config
