"""
Experiment 5: Streaming Responses

Goal: Understand real-time output streaming for long-running tasks
"""

import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 5: Streaming Responses ===\n")
    
    agent = create_deep_agent(
        model="ollama:codellama:13b",
        instructions="You are a creative writing assistant. Write detailed, engaging content.",
    )
    
    deps = DeepAgentDeps(backend=StateBackend())
    
    # Test 1: Stream a long response
    print("Test 1: Streaming a story (watch it appear in real-time)")
    print("-" * 50)
    
    full_response = ""
    async for chunk in agent.run_stream(
        "Write a short story (3-4 paragraphs) about a robot learning to paint",
        deps=deps
    ):
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n" + "=" * 50)
    print(f"Total characters: {len(full_response)}\n")
    
    # Test 2: Stream with longer content
    print("\nTest 2: Streaming a tutorial")
    print("-" * 50)
    
    tokens_received = 0
    async for chunk in agent.run_stream(
        "Explain how neural networks work, covering: structure, forward pass, backpropagation, and training",
        deps=deps
    ):
        print(chunk, end="", flush=True)
        tokens_received += 1
    
    print("\n" + "=" * 50)
    print(f"Chunks received: {tokens_received}\n")
    
    # Test 3: Compare streaming vs non-streaming timing
    print("\nTest 3: Timing comparison")
    print("-" * 50)
    
    import time
    
    # Non-streaming
    start = time.time()
    result = await agent.run(
        "List and briefly explain 10 programming concepts",
        deps=deps
    )
    non_stream_time = time.time() - start
    print(f"Non-streaming: {non_stream_time:.2f}s (response appears all at once)")
    
    # Streaming
    start = time.time()
    first_chunk_time = None
    async for chunk in agent.run_stream(
        "List and briefly explain 10 programming concepts",
        deps=deps
    ):
        if first_chunk_time is None:
            first_chunk_time = time.time() - start
        print(".", end="", flush=True)
    total_stream_time = time.time() - start
    
    print(f"\nStreaming: {total_stream_time:.2f}s total, first chunk at {first_chunk_time:.2f}s")
    print(f"Time to first byte advantage: {non_stream_time - first_chunk_time:.2f}s\n")
    
    print("\n=== Key Learnings ===")
    print("1. Streaming: Use run_stream() instead of run()")
    print("2. Real-time: Chunks arrive as generated, not batched")
    print("3. UX benefit: User sees progress immediately")
    print("4. Same API: Both methods use same agent/deps")
    print("5. Tool calls: Can stream text around tool invocations")


if __name__ == "__main__":
    asyncio.run(main())
