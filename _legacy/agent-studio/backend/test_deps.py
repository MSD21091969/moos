import asyncio
import os
import sys

# Mock paths
sys.path.append(r"D:\agent-factory\agent-studio\backend")

from app.deps import get_deps_for_session

async def test_deps():
    print("Testing get_deps_for_session...")
    try:
        deps = await get_deps_for_session("test_session_id", "testuser@example.com")
        print(f"Success! Backend type: {type(deps.backend)}")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deps())
