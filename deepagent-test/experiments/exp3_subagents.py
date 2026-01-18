"""
Experiment 3: Subagent Delegation

Goal: Understand hierarchical agent patterns and context passing
"""

import asyncio
import os
from pydantic_deep import create_deep_agent, DeepAgentDeps, SubAgentConfig
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 3: Subagent Delegation (GCP) ===\n")

    # Configure GCP Vertex AI
    key_path = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    os.environ["GOOGLE_CLOUD_PROJECT"] = "mailmind-ai-djbuw"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"
    os.environ["LOCATION"] = "us-central1"

    flash_model = "google-vertex:gemini-2.5-flash"
    pro_model = "google-vertex:gemini-2.5-flash"  # Downgrading to Flash for stability
    
    # Create specialist agents with specialized models
    researcher = create_deep_agent(
        model=flash_model,  # Efficient for research
        instructions=(
            "You are a research specialist. When given a topic, "
            "provide thorough, well-cited research findings. "
            "Be comprehensive and academic in your approach."
        ),
        retries=3,
    )
    
    coder = create_deep_agent(
        model=flash_model,  # Code specialist
        instructions=(
            "You are a coding specialist. When asked to implement something, "
            "write clean, well-documented code with error handling. "
            "Follow best practices and explain your design decisions."
        ),
        retries=3,
    )
    
    analyst = create_deep_agent(
        model=flash_model,  # Reasoning specialist
        instructions=(
            "You are a data analyst. Analyze data, identify patterns, "
            "and provide insights with statistical reasoning. "
            "Present findings clearly with examples."
        ),
        retries=3,
    )
    
    # Create coordinator agent with subagents
    coordinator = create_deep_agent(
        model=pro_model,  # General orchestrator (Stronger model)
        instructions=(
            "You are a project coordinator. You delegate tasks to specialist agents. "
            "When you see keywords that match a specialist's domain, delegate to them. "
            "Synthesize their responses into a cohesive answer."
        ),
        retries=3,
        subagents=[
            SubAgentConfig(
                name="researcher",
                description="Specializes in research and information gathering.",
                agent=researcher,
                triggers=["research", "investigate", "study", "analyze topic"],
            ),
            SubAgentConfig(
                name="coder",
                description="Specializes in writing and reviewing Python code.",
                agent=coder,
                triggers=["code", "implement", "write function", "program"],
            ),
            SubAgentConfig(
                name="analyst",
                description="Specializes in data analysis and statistics.",
                agent=analyst,
                triggers=["analyze data", "statistics", "pattern", "insights"],
            ),
        ],
    )
    
    deps = DeepAgentDeps(backend=StateBackend())

    # Register subagents in context (Required because create_deep_agent doesn't automatically register them in deps)
    deps.subagents["researcher"] = researcher
    deps.subagents["coder"] = coder
    deps.subagents["analyst"] = analyst

    # Register subagents in context (Required because create_deep_agent doesn't automatically register them in deps)
    deps.subagents["researcher"] = researcher
    deps.subagents["coder"] = coder
    deps.subagents["analyst"] = analyst
    
    # Test 1: Research delegation
    print("Test 1: Research delegation (trigger: 'research')")
    result1 = await coordinator.run(
        "I need you to research the benefits of microservices architecture",
        deps=deps
    )
    print(f"Result: {result1.output}\n")
    
    # Test 2: Coding delegation
    print("Test 2: Coding delegation (trigger: 'implement')")
    result2 = await coordinator.run(
        "Please implement a Python function to calculate fibonacci numbers using memoization",
        deps=deps
    )
    print(f"Result: {result2.output}\n")
    
    # Test 3: Multiple delegations
    print("Test 3: Multi-step task requiring multiple specialists")
    result3 = await coordinator.run(
        "Research the best sorting algorithms, then implement quicksort in Python",
        deps=deps
    )
    print(f"Result: {result3.output}\n")
    
    # Test 4: No delegation (coordinator handles directly)
    print("Test 4: Task without specialist triggers")
    result4 = await coordinator.run(
        "What's the weather like today?",
        deps=deps
    )
    print(f"Result: {result4.output}\n")
    
    print("\n=== Key Learnings ===")
    print("1. Delegation: Triggered by keywords in SubAgentConfig")
    print("2. Isolation: Each subagent has its own context/instructions")
    print("3. Coordination: Main agent synthesizes subagent responses")
    print("4. Fallback: Coordinator handles tasks that don't match triggers")


if __name__ == "__main__":
    asyncio.run(main())
