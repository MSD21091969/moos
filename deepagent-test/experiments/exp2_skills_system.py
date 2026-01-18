"""
Experiment 2: Skills System

Goal: Test how SKILL.md files inject capabilities into agents
"""

import asyncio
import os
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 2: Skills System ===\n")
    
    # Configure GCP Vertex AI
    key_path = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    os.environ["GOOGLE_CLOUD_PROJECT"] = "mailmind-ai-djbuw"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"
    os.environ["LOCATION"] = "us-central1"
    
    model_name = "google-vertex:gemini-2.5-flash"
    
    # Math agent with math skill
    math_agent = create_deep_agent(
        model=model_name,
        instructions="You are a helpful math assistant.",
        skill_directories=[{"path": "../skills/math-helper", "recursive": False}],
        retries=3,
    )
    
    # Code agent with code skill
    code_agent = create_deep_agent(
        model=model_name,
        instructions="You are a helpful code reviewer. Please be concise.",
        skill_directories=[{"path": "../skills/code-reviewer", "recursive": False}],
        retries=3,
    )
    
    deps = DeepAgentDeps(backend=StateBackend())
    
    # Test 1: Use math skill
    print(f"Test 1: Using math-helper skill ({model_name})")
    print("-" * 50)
    result1 = await math_agent.run(
        "I need help with a complex math problem: calculate the derivative of x^2 + 3x + 5",
        deps=deps
    )
    print(f"Result: {result1.output}\n")
    
    # Test 2: Use code review skill
    print(f"\nTest 2: Using code-reviewer skill ({model_name})")
    print("-" * 50)
    code = """
def calculate(x):
    return x*2+3
"""
    result2 = await code_agent.run(
        f"Please review this Python code:\n{code}",
        deps=deps
    )
    print(f"Result: {result2.output}\n")
    
    # Test 3: Test both agents
    print("\nTest 3: Compare both specialized agents")
    print("-" * 50)
    result3a = await math_agent.run("What are your capabilities?", deps=deps)
    print(f"Math agent: {result3a.output}\n")
    result3b = await code_agent.run("What are your capabilities?", deps=deps)
    print(f"Code agent: {result3b.output}\n")
    
    print("\n=== Key Learnings ===")
    print("1. Skills: Markdown files that extend agent capabilities")
    print("2. No code needed: Skills are pure instructions/context")
    print("3. Skill discovery: Auto-loaded from skill_directories")
    print("4. Specialized agents: Each agent gets its own skill set")
    print("5. Skills vs Tools: Skills = prompts, Tools = functions")


if __name__ == "__main__":
    asyncio.run(main())
