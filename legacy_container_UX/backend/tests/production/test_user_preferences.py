"""Production tests for user preferences (workspace/session state sync)."""

import asyncio
import sys
from pathlib import Path

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Backend URL
BASE_URL = "https://my-tiny-data-collider-ng2rb7mwyq-ez.a.run.app"

# Test credentials
TEST_USER = "enterprise@test.com"
TEST_PASSWORD = "test123"


async def get_token() -> str:
    """Login and get JWT token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_USER,
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["access_token"]


async def test_get_preferences(token: str):
    """Test GET /user/preferences."""
    print("\n[1/5] Testing GET /user/preferences...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/user/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"GET failed: {response.text}"
        data = response.json()

        # Verify response structure
        assert "user_id" in data
        assert "draft_messages" in data
        assert "active_tabs" in data
        assert "ui_preferences" in data

        print(f"   ✅ GET /user/preferences: {response.status_code}")
        print(f"   - user_id: {data['user_id']}")
        print(f"   - draft_messages: {len(data['draft_messages'])} items")
        print(f"   - active_tabs: {len(data['active_tabs'])} items")
        return data


async def test_update_preferences(token: str):
    """Test PATCH /user/preferences."""
    print("\n[2/5] Testing PATCH /user/preferences...")

    update_data = {
        "active_session_id": "sess_test_123",
        "draft_messages": {"sess_test_123": "This is a test draft message"},
        "ui_preferences": {"theme": "dark", "sidebarCollapsed": True},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{BASE_URL}/user/preferences",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=update_data,
        )
        assert response.status_code == 200, f"PATCH failed: {response.text}"
        data = response.json()

        # Verify updates applied
        assert data["active_session_id"] == "sess_test_123"
        assert "sess_test_123" in data["draft_messages"]
        assert data["ui_preferences"]["theme"] == "dark"

        print(f"   ✅ PATCH /user/preferences: {response.status_code}")
        print(f"   - active_session_id: {data['active_session_id']}")
        print(f"   - draft saved: '{data['draft_messages']['sess_test_123'][:30]}...'")
        print(f"   - theme: {data['ui_preferences']['theme']}")
        return data


async def test_verify_persistence(token: str):
    """Test that preferences persist across requests."""
    print("\n[3/5] Testing persistence (GET after PATCH)...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/user/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify previously saved data still exists
        assert data["active_session_id"] == "sess_test_123"
        assert "sess_test_123" in data["draft_messages"]
        assert data["ui_preferences"]["theme"] == "dark"

        print("   ✅ Persistence verified: Data survived across requests")
        return data


async def test_merge_updates(token: str):
    """Test that PATCH merges instead of replacing."""
    print("\n[4/5] Testing merge behavior...")

    # Add another draft without removing the first
    merge_data = {
        "draft_messages": {"sess_test_456": "Another draft message"},
        "ui_preferences": {
            "fontSize": 14  # Add new field without removing theme
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{BASE_URL}/user/preferences",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=merge_data,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify both drafts exist
        assert "sess_test_123" in data["draft_messages"]  # Old draft still there
        assert "sess_test_456" in data["draft_messages"]  # New draft added

        # Verify UI prefs merged
        assert data["ui_preferences"]["theme"] == "dark"  # Old field still there
        assert data["ui_preferences"]["fontSize"] == 14  # New field added

        print("   ✅ Merge verified: Both drafts exist, UI prefs merged")
        print(f"   - draft_messages: {list(data['draft_messages'].keys())}")
        print(f"   - ui_preferences: {list(data['ui_preferences'].keys())}")
        return data


async def test_cleanup(token: str):
    """Reset preferences to clean state."""
    print("\n[5/5] Cleanup: Resetting preferences...")

    reset_data = {"active_session_id": None, "draft_messages": {}, "ui_preferences": {}}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{BASE_URL}/user/preferences",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=reset_data,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["active_session_id"] is None
        assert len(data["draft_messages"]) == 0

        print("   ✅ Cleanup complete: Preferences reset")


async def main():
    """Run all production tests."""
    print("=" * 70)
    print("PRODUCTION TEST: User Preferences (Workspace/Session State Sync)")
    print("=" * 70)
    print(f"Backend: {BASE_URL}")
    print(f"User: {TEST_USER}")

    try:
        # Get auth token
        print("\n[0/5] Authenticating...")
        token = await get_token()
        print("   ✅ Authentication successful")

        # Run tests
        await test_get_preferences(token)
        await test_update_preferences(token)
        await test_verify_persistence(token)
        await test_merge_updates(token)
        await test_cleanup(token)

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED (5/5)")
        print("=" * 70)
        print("\n✨ Workspace/Session State Sync is production-ready!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
