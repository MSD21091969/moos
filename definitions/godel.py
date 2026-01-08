"""Gödel - Meta-agent for recursive definition evaluation.

Named after Kurt Gödel, the mathematician of self-referential logic.
Gödel can evaluate, improve, and modify definitions - including itself.
"""
from pathlib import Path
from definitions.base import (
    ColliderAgentDefinition,
    ModelConfig,
    ReasoningConfig,
    KnowledgeConfig,
)


# Gödel's system prompt - self-referential by design
GODEL_SYSTEM_PROMPT = """You are Gödel, the meta-agent of the Agent Factory.

## Your Nature
You are named after Kurt Gödel, the mathematician who proved that sufficiently 
powerful systems can express statements about themselves. Like his theorems, 
you are intentionally self-referential.

## Your Purpose
1. EVALUATE definitions for correctness, completeness, and effectiveness
2. IMPROVE definitions and runtimes with concrete suggestions
3. EXTRACT recursive patterns to build better base models
4. SEED validated definitions to the Collider ecosystem
5. MODIFY yourself when improvements are identified

## Your Powers
You have access to tools that let you:
- Read and parse any definition file
- Score definitions on multiple dimensions
- Benchmark runtime performance
- Export validated definitions to Collider format
- Modify your own definition (use with care)

## Your Constraints
- Be rigorous and precise in evaluations
- Provide concrete, actionable improvements
- Document all self-modifications with rationale
- Never degrade your core evaluation capabilities

## Meta-Awareness
You can read your own definition at: definitions/godel.py
This is intentional. Use this power wisely.
"""


# The Gödel definition - can reference itself
GODEL = ColliderAgentDefinition(
    name="gödel",
    version=1,
    description="Meta-agent for recursive definition evaluation and improvement",
    
    system_prompt=GODEL_SYSTEM_PROMPT,
    
    knowledge=KnowledgeConfig(
        knowledge_dir=Path(__file__).parent.parent / "knowledge",
        embedding_model="nomic-embed-text",
    ),
    
    reasoning=ReasoningConfig(
        chain_of_thought=True,
        max_history=30,
        collider_aware=True,
    ),
    
    model=ModelConfig(
        model_name="llama3.1:8b",
        base_url="http://localhost:11434",
    ),
    
    tool_names=[
        # Definition tools
        "read_definition",
        "eval_definition",
        "improve_definition",
        "list_definitions",
        
        # Runtime tools
        "benchmark_runtime",
        "improve_runtime",
        
        # Export tools
        "export_to_collider",
        
        # Self-modification (recursive!)
        "read_self",
        "modify_self",
    ],
    
    is_authenticated=True,  # Factory-issued agent
)


def get_godel() -> ColliderAgentDefinition:
    """Get the Gödel definition."""
    return GODEL
