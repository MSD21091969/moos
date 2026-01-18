"""
Minimal test to verify Ollama connectivity with pydantic-ai
"""

import asyncio
import os
from pydantic_ai import Agent


async def main():
    print("=== Testing Ollama Connectivity ===\n")
    
    # Set Ollama environment variables
    os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
    os.environ["OPENAI_API_KEY"] = "ollama"  # Required but not validated
    
    print("Environment configured:")
    print(f"  BASE_URL: {os.environ['OPENAI_BASE_URL']}")
    print(f"  API_KEY: {os.environ['OPENAI_API_KEY']}\n")
    
    # Test with qwen3:14b (should be most compatible)
    print("Creating agent with qwen3:14b...")
    agent = Agent("openai:qwen3:14b")
    
    print("Sending test prompt...\n")
    result = await agent.run("Say hello and confirm you're running locally via Ollama")
    
    print(f"✅ SUCCESS!")
    print(f"Response: {result.output}\n")
    
    print("Ollama connection verified!")


if __name__ == "__main__":
    asyncio.run(main())
