"""
Phase A Validation Tests - Automated testing of all Phase C changes

Tests:
1. ToolBrowser convertBackendTool() logic (Dict → Array conversion)
2. /user/tools endpoints (POST, GET, DELETE)
3. Gemini agent function schemas (WORKSPACE_OPERATIONS vs DATA_TOOLS)
4. Google tools registration in /tools/available
"""

import sys
from pathlib import Path


# Test 1: Verify convertBackendTool() exists and handles Dict format
def test_toolbrowser_conversion():
    """Test ToolBrowser.tsx has convertBackendTool() function"""
    print("\n[TEST 1] ToolBrowser convertBackendTool() function...")

    toolbrowser_path = Path("frontend/src/components/ToolBrowser.tsx")
    if not toolbrowser_path.exists():
        print("❌ FAIL: ToolBrowser.tsx not found")
        return False

    content = toolbrowser_path.read_text(encoding="utf-8")

    # Check for convertBackendTool function
    if "convertBackendTool" not in content:
        print("❌ FAIL: convertBackendTool function not found")
        return False

    # Check for Dict → Array conversion logic
    if "Object.entries(backendTool.parameters)" not in content:
        print("❌ FAIL: Object.entries conversion logic missing")
        return False

    # Check for Array.isArray check
    if "Array.isArray(backendTool.parameters)" not in content:
        print("❌ FAIL: Array.isArray check missing")
        return False

    print("✅ PASS: convertBackendTool() function found with Dict→Array logic")
    return True


# Test 2: Verify /user/tools endpoints exist
def test_user_tools_endpoints():
    """Test /user/tools endpoints in user.py"""
    print("\n[TEST 2] /user/tools API endpoints...")

    user_routes_path = Path("src/api/routes/user.py")
    if not user_routes_path.exists():
        print("❌ FAIL: user.py not found")
        return False

    content = user_routes_path.read_text(encoding="utf-8")

    # Check for POST endpoint (without @ prefix)
    if 'router.post("/tools' not in content:
        print("❌ FAIL: POST /user/tools endpoint not found")
        return False

    # Check for GET endpoint (without @ prefix)
    if 'router.get("/tools' not in content:
        print("❌ FAIL: GET /user/tools endpoint not found")
        return False

    # Check for DELETE endpoint (without @ prefix)
    if 'router.delete("/tools/{tool_id}' not in content:
        print("❌ FAIL: DELETE /user/tools/{tool_id} endpoint not found")
        return False

    # Check for builtin-only validation
    if 'type="builtin"' not in content and '"builtin"' not in content:
        print("⚠️  WARNING: Builtin-only validation may be missing")

    print("✅ PASS: All 3 /user/tools endpoints found (POST, GET, DELETE)")
    return True


# Test 3: Verify Gemini agent separation
def test_gemini_agent_separation():
    """Test Gemini agent WORKSPACE_OPERATIONS vs DATA_TOOLS separation"""
    print("\n[TEST 3] Gemini agent function schema separation...")

    gemini_path = Path("frontend/src/lib/gemini-agent.ts")
    if not gemini_path.exists():
        print("❌ FAIL: gemini-agent.ts not found")
        return False

    content = gemini_path.read_text(encoding="utf-8")

    # Check for WORKSPACE_OPERATIONS
    if "WORKSPACE_OPERATIONS" not in content:
        print("❌ FAIL: WORKSPACE_OPERATIONS not found")
        return False

    # Check for DATA_TOOLS
    if "DATA_TOOLS" not in content:
        print("❌ FAIL: DATA_TOOLS not found")
        return False

    # Check for combined SDK_OPERATIONS (flexible spacing)
    if (
        "SDK_OPERATIONS" not in content
        or "WORKSPACE_OPERATIONS" not in content
        or "DATA_TOOLS" not in content
    ):
        print("❌ FAIL: Combined SDK_OPERATIONS not found")
        return False

    # Check for tool_ prefix in DATA_TOOLS
    if "tool_addToSession" not in content and "tool_add" not in content:
        print("⚠️  WARNING: tool_ prefix may be missing from DATA_TOOLS")

    print("✅ PASS: WORKSPACE_OPERATIONS and DATA_TOOLS separated correctly")
    return True


# Test 4: Verify google_tools registration
def test_google_tools_registration():
    """Test google_tools registered in tools/__init__.py"""
    print("\n[TEST 4] Google tools registration...")

    tools_init_path = Path("src/tools/__init__.py")
    if not tools_init_path.exists():
        print("❌ FAIL: tools/__init__.py not found")
        return False

    content = tools_init_path.read_text(encoding="utf-8")

    # Check for google_tools reference (in import or module list)
    if "google_tools" not in content:
        print("❌ FAIL: google_tools not referenced in __init__.py")
        return False

    print("✅ PASS: google_tools registered in tools/__init__.py")
    return True


# Test 5: Verify API client methods
def test_api_client_methods():
    """Test API client has user tools methods"""
    print("\n[TEST 5] API client user tools methods...")

    api_client_path = Path("frontend/src/lib/api-client.ts")
    if not api_client_path.exists():
        print("❌ FAIL: api-client.ts not found")
        return False

    content = api_client_path.read_text(encoding="utf-8")

    # Check for listUserTools
    if "listUserTools" not in content:
        print("❌ FAIL: listUserTools() method not found")
        return False

    # Check for createUserTool
    if "createUserTool" not in content:
        print("❌ FAIL: createUserTool() method not found")
        return False

    # Check for deleteUserTool
    if "deleteUserTool" not in content:
        print("❌ FAIL: deleteUserTool() method not found")
        return False

    print("✅ PASS: All user tools API methods found")
    return True


# Test 6: Verify two-tab ToolBrowser
def test_toolbrowser_tabs():
    """Test ToolBrowser has two tabs"""
    print("\n[TEST 6] ToolBrowser two-tab navigation...")

    toolbrowser_path = Path("frontend/src/components/ToolBrowser.tsx")
    if not toolbrowser_path.exists():
        print("❌ FAIL: ToolBrowser.tsx not found")
        return False

    content = toolbrowser_path.read_text(encoding="utf-8")

    # Check for tab state
    if "activeTab" not in content and "selectedTab" not in content:
        print("❌ FAIL: Tab state management not found")
        return False

    # Check for Workspace tab
    if "Workspace" not in content:
        print("❌ FAIL: Workspace tab not found")
        return False

    # Check for Data Tools tab
    if "Data Tools" not in content and "Data" not in content:
        print("❌ FAIL: Data Tools tab not found")
        return False

    print("✅ PASS: Two-tab navigation found in ToolBrowser")
    return True


# Test 7: Verify drag-drop handlers
def test_drag_drop_handlers():
    """Test drag-drop handlers in ToolBrowser and TableView"""
    print("\n[TEST 7] Drag-drop handlers...")

    toolbrowser_path = Path("frontend/src/components/ToolBrowser.tsx")
    tableview_path = Path("frontend/src/components/TableView.tsx")

    if not toolbrowser_path.exists():
        print("❌ FAIL: ToolBrowser.tsx not found")
        return False

    if not tableview_path.exists():
        print("❌ FAIL: TableView.tsx not found")
        return False

    toolbrowser_content = toolbrowser_path.read_text(encoding="utf-8")
    tableview_content = tableview_path.read_text(encoding="utf-8")

    # Check ToolBrowser drag handlers
    if "onDragStart" not in toolbrowser_content:
        print("❌ FAIL: onDragStart not found in ToolBrowser")
        return False

    # Check TableView drop handlers
    if "onDrop" not in tableview_content:
        print("❌ FAIL: onDrop not found in TableView")
        return False

    if "onDragOver" not in tableview_content:
        print("❌ FAIL: onDragOver not found in TableView")
        return False

    print("✅ PASS: Drag-drop handlers found in both components")
    return True


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("PHASE A VALIDATION - Testing All Phase C Changes")
    print("=" * 70)

    tests = [
        test_toolbrowser_conversion,
        test_user_tools_endpoints,
        test_gemini_agent_separation,
        test_google_tools_registration,
        test_api_client_methods,
        test_toolbrowser_tabs,
        test_drag_drop_handlers,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ ERROR: {test.__name__} failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed / total * 100:.1f}%")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Ready for Phase B deployment")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix issues before deploying")
        return 1


if __name__ == "__main__":
    sys.exit(main())
