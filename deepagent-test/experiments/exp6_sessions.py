"""
Experiment 6: Session Management and Isolation

Goal: Understand session isolation, cleanup, and multi-user scenarios
"""

import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, SessionManager
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 6: Session Management ===\n")
    
    # Create session manager
    manager = SessionManager(
        default_runtime="local",
        default_idle_timeout=3600,  # 1 hour
    )
    
    # Start cleanup loop (runs in background)
    manager.start_cleanup_loop(interval=300)  # Check every 5 minutes
    
    agent = create_deep_agent(
        model="ollama:qwen3:14b",
        instructions="You are a helpful assistant. Remember context from previous messages.",
    )
    
    # Test 1: Multiple isolated sessions
    print("Test 1: Session isolation")
    print("-" * 50)
    
    # User 1's session
    session1 = await manager.get_or_create("user-1")
    result1a = await agent.run(
        "My name is Alice and I like pizza",
        deps=session1.deps
    )
    print(f"User 1 (first): {result1a.output}\n")
    
    # User 2's session
    session2 = await manager.get_or_create("user-2")
    result2a = await agent.run(
        "My name is Bob and I like sushi",
        deps=session2.deps
    )
    print(f"User 2 (first): {result2a.output}\n")
    
    # Test memory isolation
    result1b = await agent.run(
        "What's my name and what do I like?",
        deps=session1.deps
    )
    print(f"User 1 (recall): {result1b.output}\n")
    
    result2b = await agent.run(
        "What's my name and what do I like?",
        deps=session2.deps
    )
    print(f"User 2 (recall): {result2b.output}\n")
    
    # Test 2: Session reuse
    print("\nTest 2: Session persistence (reusing session ID)")
    print("-" * 50)
    
    # Get same session again
    session1_again = await manager.get_or_create("user-1")
    result1c = await agent.run(
        "Do you remember what I told you earlier?",
        deps=session1_again.deps
    )
    print(f"User 1 (persistence check): {result1c.output}\n")
    
    # Test 3: Session info
    print("\nTest 3: Session information")
    print("-" * 50)
    print(f"Active sessions: {len(manager._sessions)}")
    print(f"Session 1 ID: {session1.session_id}")
    print(f"Session 2 ID: {session2.session_id}")
    print(f"Session 1 backend type: {type(session1.deps.backend).__name__}")
    
    # Test 4: Manual backend (no session manager)
    print("\n\nTest 4: Manual deps (no session manager)")
    print("-" * 50)
    
    manual_deps = DeepAgentDeps(backend=StateBackend())
    result_manual = await agent.run(
        "My name is Charlie",
        deps=manual_deps
    )
    print(f"Manual (first): {result_manual.output}\n")
    
    result_manual2 = await agent.run(
        "What's my name?",
        deps=manual_deps
    )
    print(f"Manual (recall): {result_manual2.output}\n")
    
    # Stop cleanup loop
    await manager.stop_cleanup_loop()
    
    print("\n=== Key Learnings ===")
    print("1. SessionManager: Multi-user isolation and lifecycle management")
    print("2. get_or_create(): Reuses existing session or creates new one")
    print("3. Isolation: Each session has independent context/history")
    print("4. Cleanup: Automatic timeout-based cleanup loop")
    print("5. Manual mode: Can use DeepAgentDeps directly without sessions")
    print("6. Backend per session: Each session gets its own backend instance")


if __name__ == "__main__":
    asyncio.run(main())
