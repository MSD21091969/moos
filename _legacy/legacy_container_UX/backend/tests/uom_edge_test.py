"""
UOM (Universal Object Model) Edge Test Suite
Tests all container types, depths, and tier restrictions per ARCHITECTURE_V5
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Authorization": "Bearer test", "Content-Type": "application/json"}

# Test state tracking
created_ids = {
    "usersession": None,
    "l1_sessions": [],
    "l2_sessions": [],
    "l3_sessions": [],
    "l4_sessions": [],
    "agents": [],
    "tools": [],
    "sources": [],
}
test_results = []

def log(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({"test": test_name, "passed": passed, "details": details})
    print(f"{status}: {test_name}" + (f" - {details}" if details else ""))

async def test_tier_resolution():
    """Test 1: Verify ENTERPRISE tier is correctly resolved"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/workspace", headers=HEADERS)
        data = r.json()
        tier = data.get("user", {}).get("tier", "")
        log("Tier Resolution", tier == "enterprise", f"tier={tier}")
        return tier == "enterprise"

async def test_workspace_init():
    """Test 2: Get/Create UserSession (L0 - root container)"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/api/v5/workspace", headers=HEADERS)
        data = r.json()
        usersession_id = data.get("data", {}).get("usersession", {}).get("instance_id")
        created_ids["usersession"] = usersession_id
        log("Workspace Init (UserSession L0)", bool(usersession_id), f"id={usersession_id}")
        return bool(usersession_id)

async def create_session(parent_id: str, title: str) -> dict:
    """Helper to create a session"""
    async with httpx.AsyncClient() as client:
        body = {
            "parent_id": parent_id,
            "session_metadata": {"title": title, "session_type": "interactive"}
        }
        r = await client.post(f"{BASE_URL}/api/v5/containers/session", headers=HEADERS, json=body)
        if r.status_code == 200:
            return r.json().get("data", {})
        else:
            return {"error": r.text, "status": r.status_code}

async def test_l1_session_creation():
    """Test 3: Create L1 Session (depth=1) inside UserSession"""
    result = await create_session(created_ids["usersession"], "L1 Test Session")
    if "error" not in result:
        created_ids["l1_sessions"].append(result.get("session_id"))
        depth = result.get("depth", -1)
        log("L1 Session Creation", depth == 1, f"id={result.get('session_id')} depth={depth}")
        return True
    log("L1 Session Creation", False, result.get("error", ""))
    return False

async def test_l2_session_creation():
    """Test 4: Create L2 Session (depth=2) inside L1 - FREE tier limit"""
    if not created_ids["l1_sessions"]:
        log("L2 Session Creation", False, "No L1 session to nest in")
        return False
    result = await create_session(created_ids["l1_sessions"][0], "L2 Test Session")
    if "error" not in result:
        created_ids["l2_sessions"].append(result.get("session_id"))
        depth = result.get("depth", -1)
        log("L2 Session Creation (FREE limit)", depth == 2, f"id={result.get('session_id')} depth={depth}")
        return True
    log("L2 Session Creation", False, str(result.get("error", ""))[:100])
    return False

async def test_l3_session_creation():
    """Test 5: Create L3 Session (depth=3) - PRO/ENTERPRISE only"""
    if not created_ids["l2_sessions"]:
        log("L3 Session Creation", False, "No L2 session to nest in")
        return False
    result = await create_session(created_ids["l2_sessions"][0], "L3 Test Session")
    if "error" not in result:
        created_ids["l3_sessions"].append(result.get("session_id"))
        depth = result.get("depth", -1)
        log("L3 Session Creation (PRO+ only)", depth == 3, f"id={result.get('session_id')} depth={depth}")
        return True
    log("L3 Session Creation", False, str(result.get("error", ""))[:100])
    return False

async def test_l4_session_creation():
    """Test 6: Create L4 Session (depth=4) - max for PRO/ENTERPRISE"""
    if not created_ids["l3_sessions"]:
        log("L4 Session Creation", False, "No L3 session to nest in")
        return False
    result = await create_session(created_ids["l3_sessions"][0], "L4 Test Session")
    if "error" not in result:
        created_ids["l4_sessions"].append(result.get("session_id"))
        depth = result.get("depth", -1)
        log("L4 Session Creation (max depth)", depth == 4, f"id={result.get('session_id')} depth={depth}")
        return True
    log("L4 Session Creation", False, str(result.get("error", ""))[:100])
    return False

async def test_l5_session_blocked():
    """Test 7: L5 Session should be BLOCKED (exceeds ENTERPRISE limit)"""
    if not created_ids["l4_sessions"]:
        log("L5 Session Blocked", False, "No L4 session to test with")
        return False
    result = await create_session(created_ids["l4_sessions"][0], "L5 Should Fail")
    # Should fail with depth error
    if "error" in result or result.get("status") == 400:
        log("L5 Session Blocked (expected)", True, "Correctly rejected depth>4")
        return True
    log("L5 Session Blocked", False, f"Should have failed but got: {result}")
    return False

async def add_resource(container_type: str, container_id: str, resource_type: str, resource_id: str, description: str):
    """Helper to add a ResourceLink"""
    async with httpx.AsyncClient() as client:
        body = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "instance_id": resource_id,
            "description": description,
            "metadata": {"x": 100, "y": 100}
        }
        r = await client.post(
            f"{BASE_URL}/api/v5/containers/{container_type}/{container_id}/resources",
            headers=HEADERS, json=body
        )
        if r.status_code == 200:
            return r.json().get("data", {})
        return {"error": r.text, "status": r.status_code}

async def test_add_agent_to_session():
    """Test 8: Add Agent to L1 Session"""
    if not created_ids["l1_sessions"]:
        log("Add Agent to Session", False, "No session")
        return False
    agent_id = f"agent_test_{datetime.now().strftime('%H%M%S')}"
    result = await add_resource("session", created_ids["l1_sessions"][0], "agent", agent_id, "Test Agent")
    if "error" not in result:
        created_ids["agents"].append(agent_id)
        log("Add Agent to Session", True, f"link_id={result.get('link_id')}")
        return True
    log("Add Agent to Session", False, str(result)[:100])
    return False

async def test_add_tool_to_session():
    """Test 9: Add Tool to L1 Session"""
    if not created_ids["l1_sessions"]:
        log("Add Tool to Session", False, "No session")
        return False
    tool_id = f"tool_test_{datetime.now().strftime('%H%M%S')}"
    result = await add_resource("session", created_ids["l1_sessions"][0], "tool", tool_id, "Test Tool")
    if "error" not in result:
        created_ids["tools"].append(tool_id)
        log("Add Tool to Session", True, f"link_id={result.get('link_id')}")
        return True
    log("Add Tool to Session", False, str(result)[:100])
    return False

async def test_add_source_to_session():
    """Test 10: Add Source to L1 Session"""
    if not created_ids["l1_sessions"]:
        log("Add Source to Session", False, "No session")
        return False
    source_id = f"source_test_{datetime.now().strftime('%H%M%S')}"
    result = await add_resource("session", created_ids["l1_sessions"][0], "source", source_id, "Test Source")
    if "error" not in result:
        created_ids["sources"].append(source_id)
        log("Add Source to Session", True, f"link_id={result.get('link_id')}")
        return True
    log("Add Source to Session", False, str(result)[:100])
    return False

async def test_list_resources():
    """Test 11: List resources in L1 Session"""
    if not created_ids["l1_sessions"]:
        log("List Resources", False, "No session")
        return False
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/api/v5/containers/session/{created_ids['l1_sessions'][0]}/resources",
            headers=HEADERS
        )
        if r.status_code == 200:
            resources = r.json().get("data", {}).get("resources", [])
            log("List Resources", len(resources) >= 3, f"count={len(resources)}")
            return True
        log("List Resources", False, r.text[:100])
        return False

async def test_update_resource_position():
    """Test 12: Update resource position (drag simulation)"""
    if not created_ids["l1_sessions"]:
        log("Update Position", False, "No session")
        return False
    async with httpx.AsyncClient() as client:
        # First get resources to find a link_id
        r = await client.get(
            f"{BASE_URL}/api/v5/containers/session/{created_ids['l1_sessions'][0]}/resources",
            headers=HEADERS
        )
        resources = r.json().get("data", {}).get("resources", [])
        if not resources:
            log("Update Position", False, "No resources to update")
            return False
        link_id = resources[0].get("link_id")
        # Update position
        r = await client.patch(
            f"{BASE_URL}/api/v5/containers/session/{created_ids['l1_sessions'][0]}/resources/{link_id}",
            headers=HEADERS,
            json={"metadata": {"x": 200, "y": 300}}
        )
        log("Update Position", r.status_code == 200, f"link_id={link_id}")
        return r.status_code == 200

async def test_terminal_node_source():
    """Test 13: Source is terminal - cannot add children"""
    if not created_ids["sources"]:
        log("Source Terminal Check", False, "No source to test")
        return False
    # Try to add a resource to source - should fail
    result = await add_resource("source", created_ids["sources"][0], "tool", "tool_illegal", "Should Fail")
    # Should fail
    if "error" in result or result.get("status") in [400, 404]:
        log("Source Terminal Check", True, "Correctly rejected adding child to Source")
        return True
    log("Source Terminal Check", False, f"Should have failed: {result}")
    return False

async def test_containment_rules():
    """Test 14: UserSession can only contain Sessions (not agents directly)"""
    if not created_ids["usersession"]:
        log("Containment Rules", False, "No usersession")
        return False
    # Try to add agent directly to UserSession - should fail
    result = await add_resource("usersession", created_ids["usersession"], "agent", "agent_illegal", "Should Fail")
    if "error" in result or result.get("status") in [400]:
        log("Containment Rules", True, "Correctly rejected Agent in UserSession")
        return True
    log("Containment Rules", False, f"Should have failed: {result}")
    return False

async def test_get_container():
    """Test 15: Get specific container"""
    if not created_ids["l1_sessions"]:
        log("Get Container", False, "No session")
        return False
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/api/v5/containers/session/{created_ids['l1_sessions'][0]}",
            headers=HEADERS
        )
        if r.status_code == 200:
            data = r.json().get("data", {})
            log("Get Container", bool(data.get("session_id")), f"title={data.get('metadata', {}).get('title')}")
            return True
        log("Get Container", False, r.text[:100])
        return False

async def test_update_container():
    """Test 16: Update container metadata"""
    if not created_ids["l1_sessions"]:
        log("Update Container", False, "No session")
        return False
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{BASE_URL}/api/v5/containers/session/{created_ids['l1_sessions'][0]}",
            headers=HEADERS,
            json={"metadata": {"title": "Updated L1 Session", "description": "Updated via test"}}
        )
        log("Update Container", r.status_code == 200, "Title updated")
        return r.status_code == 200

async def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("UOM EDGE TEST SUITE - Testing all depths and container types")
    print("=" * 60)
    print()
    
    # Run tests in order (some depend on previous)
    await test_tier_resolution()
    await test_workspace_init()
    await test_l1_session_creation()
    await test_l2_session_creation()
    await test_l3_session_creation()
    await test_l4_session_creation()
    await test_l5_session_blocked()
    await test_add_agent_to_session()
    await test_add_tool_to_session()
    await test_add_source_to_session()
    await test_list_resources()
    await test_update_resource_position()
    await test_terminal_node_source()
    await test_containment_rules()
    await test_get_container()
    await test_update_container()
    
    # Summary
    print()
    print("=" * 60)
    passed = sum(1 for t in test_results if t["passed"])
    total = len(test_results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    # Show failures
    failures = [t for t in test_results if not t["passed"]]
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f['test']}: {f['details']}")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
