import sys
sys.path.append(r"D:\agent-factory\agent-studio\backend")

# Need to set up env for imports to work if they rely on it
# But main.py sets up env via deps? No, deps has configure_gcp but it's called inside `get_deps_for_session`.
# However, module level imports in coordinator.py execute immediately. 
# `deps` is imported in `coordinator.py`, but `configure_gcp` is not called at module level there.
# This could be the issue! If `create_deep_agent` needs GCP creds at import time, it will fail because `configure_gcp` hasn't run yet.

from app.deps import configure_gcp
configure_gcp() # Ensure env is set before importing coordinator

try:
    print("Importing coordinator...")
    from app.agents.coordinator import get_coordinator_with_registered_subagents
    print("Coordinator imported successfully.")
    
    # Mock deps
    class MockDeps:
        pass
    
    deps = MockDeps()
    deps.subagents = {}
    
    print("Getting coordinator instance...")
    c = get_coordinator_with_registered_subagents(deps)
    print(f"Success! Agent model: {c.model}")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
