"""
Experiment 1: Basic Agent with Toolsets

Goal: Understand how to register tools and toolsets with pydantic-deep
"""

import asyncio
import os
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai.toolsets import FunctionToolset
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 1: Basic Toolsets ===\n")
    
    # Configure Ollama
    os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
    os.environ["OPENAI_API_KEY"] = "ollama"
    
    # Create math toolset
    math_tools = FunctionToolset()
    
    @math_tools.tool
    async def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
    
    @math_tools.tool
    async def multiply(a: int, b: int) -> int:
        """Multiply two numbers together."""
        return a * b
    
    @math_tools.tool
    async def power(base: int, exponent: int) -> int:
        """Raise base to the power of exponent."""
        return base ** exponent
    
    # Create standalone tool (not in toolset)
    async def get_user_name(ctx) -> str:
        """Get the current user's name from context."""
        return "Test User"
    
    agent = create_deep_agent(
        model="openai:qwen3:14b",  # Using qwen3 (verified working)
        instructions="You are a helpful coding assistant. Use the available tools to solve problems.",
        toolsets=[math_tools],
        tools=[get_user_name],
    )
    
    deps = DeepAgentDeps(backend=StateBackend())
    
    # Test 1: Simple addition
    print("Test 1: Simple addition")
    print("-" * 50)
    result1 = await agent.run("What is 15 + 7?", deps=deps)
    print(f"Result: {result1.output}\n")
    
    # Test 2: Chained operations
    print("\nTest 2: Chained operations")
    print("-" * 50)
    result2 = await agent.run(
        "Calculate (5 + 3) multiplied by 2, then raise to the power of 2",
        deps=deps
    )
    print(f"Result: {result2.output}\n")
    
    # Test 3: Using context tool
    print("\nTest 3: Using context-aware tool")
    print("-" * 50)
    result3 = await agent.run("What's the user's name?", deps=deps)
    print(f"Result: {result3.output}\n")
    
    print("\n=== Key Learnings ===")
    print("1. Toolsets: Group related tools together via FunctionToolset")
    print("2. Standalone tools: Can pass individual functions via tools=[]")
    print("3. Tool decoration: Use @toolset.tool to register functions")
    print("4. Context access: Tools can access RunContext for shared state")
    print("5. Local models: Set OPENAI_BASE_URL env var for Ollama")


if __name__ == "__main__":
    asyncio.run(main())
