"""Collider Pilot - Graph-Context Aware Agent.

This agent is designed to be instantiated with a specific 'Graph Context' (a CompositeDefinition).
It uses the `DefinitionObject` pattern to dynamically treat that Graph as a Tool.
"""
from typing import Optional, List
from pydantic_ai import Agent
from pydantic_deep import create_deep_agent
from models_v2 import DefinitionObject, CompositeDefinition

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
    graph_definition: CompositeDefinition,
    model: str = "google-vertex:gemini-2.5-flash"
) -> Agent:
    """
    Creates a new Collider Pilot instance bound to the given Graph Definition.
    
    The Graph Definition is converted into a Dynamic Tool via DefinitionObject
    and injected into the agent's toolset.
    """
    
    # 1. Create the Dynamic Tool from the Graph
    def_obj = DefinitionObject(graph_definition)
    dynamic_tool = def_obj.to_tool()
    
    # 2. Create the Agent with this tool
    agent = create_deep_agent(
        model=model,
        instructions=COLLIDER_PILOT_INSTRUCTIONS,
        tools=[dynamic_tool],
        name=f"pilot_{graph_definition.name}",
    )
    
    return agent
