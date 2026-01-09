"""Subgraph Igniter - FatRunner that powers container subgraphs.

This is the manager class that runs definitions (atomic or composite)
within a container's subgraph.
"""
from typing import Any
from pathlib import Path

from parts import BaseAgent, IOSchema, ModelAdapter, ToolRegistry
from models import Definition, Container
from runtimes.fat import FatRunner


class SubgraphIgniter:
    """
    Powers container subgraphs by igniting their definitions.
    
    This is the runtime manager that:
    1. Takes a container with a subgraph
    2. Loads the definitions for each node
    3. Ignites them via FatRunner
    4. Manages data flow between nodes
    """
    
    def __init__(
        self,
        container: Container,
        environment: str = "runtime",
    ):
        self.container = container
        self.environment = environment
        self.runners: dict[str, FatRunner] = {}
        self.adapter = ModelAdapter()
    
    def ignite(self) -> dict[str, Any]:
        """
        Ignite all definitions in the container's subgraph.
        
        Returns:
            Dict of node_id -> FatRunner
        """
        if not self.container.subgraph:
            return {}
        
        results = {}
        
        # Ignite each container in the subgraph
        for node_id, sub_container in self.container.subgraph.items():
            if sub_container.definition:
                runner = FatRunner.from_container(
                    sub_container,
                    environment=self.environment,
                )
                self.runners[node_id] = runner
                results[node_id] = f"Ignited: {sub_container.definition.name}"
        
        return results
    
    async def execute(self, input_data: dict) -> dict:
        """
        Execute the subgraph with input data.
        
        Follows the DAG structure to process data through nodes.
        
        Args:
            input_data: Initial input to the graph
            
        Returns:
            Output from the final node(s)
        """
        if not self.runners:
            self.ignite()
        
        # Simple linear execution for now
        # TODO: Implement proper DAG traversal
        current_data = input_data
        
        for node_id, runner in self.runners.items():
            definition = runner.definition
            if definition:
                # Execute the definition
                result = await runner.execute_async(current_data)
                current_data = result
        
        return current_data
    
    def get_status(self) -> dict:
        """Get status of all runners."""
        return {
            "container": self.container.name,
            "environment": self.environment,
            "nodes": list(self.runners.keys()),
            "ignited": len(self.runners),
        }
    
    def shutdown(self):
        """Shutdown all runners."""
        self.runners.clear()


class RuntimeServer:
    """
    Server that manages multiple SubgraphIgniters.
    
    This is the central runtime that:
    - Creates igniters for containers
    - Routes requests to appropriate igniter
    - Manages lifecycle of runners
    """
    
    def __init__(self):
        self.igniters: dict[str, SubgraphIgniter] = {}
    
    def create_igniter(
        self,
        container: Container,
        environment: str = "runtime",
    ) -> SubgraphIgniter:
        """Create and register an igniter for a container."""
        igniter = SubgraphIgniter(container, environment)
        self.igniters[container.id] = igniter
        return igniter
    
    def get_igniter(self, container_id: str) -> SubgraphIgniter | None:
        """Get an igniter by container ID."""
        return self.igniters.get(container_id)
    
    def ignite_all(self) -> dict:
        """Ignite all registered igniters."""
        results = {}
        for container_id, igniter in self.igniters.items():
            results[container_id] = igniter.ignite()
        return results
    
    def shutdown_all(self):
        """Shutdown all igniters."""
        for igniter in self.igniters.values():
            igniter.shutdown()
        self.igniters.clear()
    
    def status(self) -> dict:
        """Get status of all igniters."""
        return {
            container_id: igniter.get_status()
            for container_id, igniter in self.igniters.items()
        }
