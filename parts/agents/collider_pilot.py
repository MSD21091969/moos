"""Collider Pilot - Graph-Context Aware Agent.

This agent is designed to be instantiated with a specific 'Graph Context' (a CompositeDefinition).
It uses the `DefinitionObject` pattern to dynamically treat that Graph as a Tool.
"""
from typing import Optional, List, Any
from pydantic_ai import Agent
from pydantic_deep import create_deep_agent
from agent_factory.models_v2 import DefinitionObject, CompositeDefinition

# Standard System Prompt
COLLIDER_PILOT_INSTRUCTIONS = """You are a Collider Pilot, a specialized agent interface for this specific Data Collider Graph.

Your Context:
- You are operating on a specific Subgraph (Cluster) of the Tiny Data Collider.
- This Cluster creates a "Tool" that you can use to process data.

Your Goal:
- Help the user interact with this specific data cluster.
- Execute the cluster with valid inputs when requested.
- Explain the Inputs and Outputs of this cluster based on its schema.

If the user asks about the structure, explain the Input/Output requirements.
If the user provides data, try to map it to the tool inputs and execute it.
"""

def create_collider_pilot(
    graph_definition: Optional[CompositeDefinition] = None,
    model: str = "google-vertex:gemini-2.5-flash",
    extra_tools: Optional[List[Any]] = None
) -> Agent:
    """
    Creates a new Collider Pilot instance.
    
    Args:
        graph_definition: Optional Graph Context. If None, runs in "Workbench Mode".
        model: LLM model to use.
        extra_tools: Additional tools to inject (e.g. container management).
    """
    
    tools = []
    if extra_tools:
        tools.extend(extra_tools)
        
    name = "pilot_workbench"
    
    if graph_definition:
        # Create Dynamic Tool from the Graph
        def_obj = DefinitionObject(graph_definition)
        tools.append(def_obj.to_tool())
        name = f"pilot_{graph_definition.name}"
    
    # Create the Agent
    agent = create_deep_agent(
        model=model,
        instructions=COLLIDER_PILOT_INSTRUCTIONS,
        tools=tools,
        name=name,
    )
    
    return agent
