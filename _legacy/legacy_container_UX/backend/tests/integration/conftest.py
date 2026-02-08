"""Integration test fixtures."""

import os
import pytest
from datetime import datetime, timezone
from typing import Generator
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-min-32-characters-long-for-security")
os.environ.setdefault("USE_FIRESTORE_MOCKS", "true")
os.environ.setdefault("LOGFIRE_TOKEN", "")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from src.main import app
from src.persistence.mock_firestore import MockFirestoreClient
from src.core.container import AppContainer, get_container
from src.api.dependencies import get_app_container
from src.models.context import UserContext


@pytest.fixture
def mock_firestore():
    """MockFirestore instance for integration tests."""
    return MockFirestoreClient()


@pytest.fixture
def mock_container(mock_firestore):
    """Mock AppContainer with MockFirestore."""
    container = AppContainer()
    # Set the private attribute directly to bypass the property
    container._firestore_client = mock_firestore
    return container


@pytest.fixture
def integration_app(mock_container):
    """FastAPI app with MockFirestore (real services, no mocks)."""
    # Override the container dependency to use our mock container
    app.dependency_overrides[get_app_container] = lambda: mock_container

    yield app

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def integration_client(integration_app):
    """Test client for integration tests."""
    return TestClient(integration_app)


@pytest.fixture
async def test_user(mock_firestore):
    """Create test user with PRO tier in MockFirestore."""
    now = datetime.now(timezone.utc)
    user_data = {
        "user_id": "test_user_integration",
        "email": "integration@test.com",
        "display_name": "Integration Test User",
        "tier": "pro",
        "permissions": [
            "create_session",
            "read_session",
            "update_session",
            "delete_session",
            "share_session",
            "run_agent",
            "upload_document",
            "read_data",
            "write_data",
        ],
        "quota_remaining": 1000,
        "quota_limit": 1000,
        "created_at": now,
        "updated_at": now,
    }

    # Store user in Firestore
    await mock_firestore.collection("users").document(user_data["user_id"]).set(user_data)

    # Return as UserContext for test usage
    return UserContext(
        user_id=user_data["user_id"],
        email=user_data["email"],
        display_name=user_data.get("display_name"),
        tier=user_data["tier"],
        permissions=user_data["permissions"],
        quota_remaining=user_data["quota_remaining"],
    )


@pytest.fixture
async def test_user_free(mock_firestore):
    """Create FREE tier test user."""
    now = datetime.now(timezone.utc)
    user_data = {
        "user_id": "test_user_free",
        "email": "free@test.com",
        "display_name": "Free User",
        "tier": "free",
        "permissions": ["create_session", "read_session"],
        "quota_remaining": 100,
        "quota_limit": 100,
        "created_at": now,
        "updated_at": now,
    }

    await mock_firestore.collection("users").document(user_data["user_id"]).set(user_data)

    return UserContext(
        user_id=user_data["user_id"],
        email=user_data["email"],
        display_name=user_data.get("display_name"),
        tier=user_data["tier"],
        permissions=user_data["permissions"],
        quota_remaining=user_data["quota_remaining"],
    )


@pytest.fixture(autouse=True)
async def cleanup_firestore(mock_firestore):
    """Clear MockFirestore after each test to prevent pollution."""
    yield

    # Clear all collections
    collections_to_clear = ["sessions", "users", "documents", "quota_usage", "events"]

    for collection_name in collections_to_clear:
        # MockFirestore doesn't have a clear method, but the instance is recreated per test
        # This is more for documentation/future real Firestore emulator support
        _ = mock_firestore.collection(collection_name)
        pass


# ============================================================================
# Real Firestore Integration Test Fixtures
# ============================================================================


@pytest.fixture
def use_real_firestore() -> bool:
    """
    Check if tests should use real Firestore.

    Returns True if USE_FIRESTORE_MOCKS=false and FIRESTORE_PROJECT_ID is set.
    """
    use_mocks = os.environ.get("USE_FIRESTORE_MOCKS", "true").lower()
    project_id = os.environ.get("FIRESTORE_PROJECT_ID", "")
    return use_mocks == "false" and bool(project_id)


@pytest.fixture
def enterprise_client(use_real_firestore) -> Generator[TestClient, None, None]:
    """
    Test client for full integration tests with real or mock Firestore.

    When USE_FIRESTORE_MOCKS=false, connects to real Firestore instance.
    Otherwise uses MockFirestore.
    """
    if use_real_firestore:
        # Use real Firestore from container
        container = get_container()
        app.dependency_overrides[get_app_container] = lambda: container
    else:
        # Use mock Firestore
        mock_fs = MockFirestoreClient()
        mock_container = AppContainer()
        mock_container._firestore_client = mock_fs
        app.dependency_overrides[get_app_container] = lambda: mock_container

    with TestClient(app) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def enterprise_token(enterprise_client: TestClient, use_real_firestore) -> str:
    """
    Get JWT token for enterprise@test.com user.

    For real Firestore: Authenticates with enterprise@test.com/test123
    For mock Firestore: Creates mock user and generates token
    """
    if use_real_firestore:
        # Login with real credentials
        from tests.integration.helpers.auth_helper import login_user

        return login_user(enterprise_client, "enterprise@test.com", "test123")
    else:
        # For mock tests, we need to create a user in mock Firestore first
        # and then generate a valid JWT token
        from src.services.auth_service import AuthService
        from src.core.container import get_container

        container = get_container()
        auth_service = AuthService(container.firestore_client)

        # Create the enterprise user in mock Firestore
        import asyncio
        from src.models.users import User
        from src.models.permissions import Tier
        from datetime import UTC

        async def create_mock_user():
            user = User(
                user_id="enterprise@test.com",
                email="enterprise@test.com",
                display_name="Enterprise Test User",
                tier=Tier.ENTERPRISE,
                daily_quota=10000,
                quota_used_today=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                hashed_password="$2b$12$F9QjU1g/CP9D8wuveMrwce6Z8ieKy3KqMkRCI.3fEgmD3oDSb6Rwy",  # test123
            )
            await (
                container.firestore_client.collection("users")
                .document(user.user_id)
                .set(user.model_dump())
            )

        # Create user if it doesn't exist
        try:
            asyncio.get_event_loop().run_until_complete(create_mock_user())
        except RuntimeError:
            # Loop already running - use new loop
            loop = asyncio.new_event_loop()
            loop.run_until_complete(create_mock_user())
            loop.close()

        # Generate JWT token
        return auth_service.create_access_token(
            data={"sub": "enterprise@test.com", "tier": "enterprise"}
        )


@pytest.fixture
def enterprise_headers(enterprise_token: str) -> dict[str, str]:
    """Authorization headers for enterprise user."""
    return {"Authorization": f"Bearer {enterprise_token}"}


@pytest.fixture
def created_session_ids() -> list[str]:
    """Track session IDs created during test for cleanup."""
    return []


@pytest.fixture
async def auto_cleanup_sessions(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    use_real_firestore: bool,
):
    """
    Auto-cleanup fixture that deletes created sessions after test.

    Usage in test:
        created_session_ids.append(session_id)  # Track for cleanup
    """
    yield

    # Cleanup: Delete all tracked sessions
    if use_real_firestore and created_session_ids:
        for session_id in created_session_ids:
            try:
                response = enterprise_client.delete(
                    f"/sessions/{session_id}",
                    headers=enterprise_headers,
                )
                # 204 (deleted) or 404 (already gone) are both acceptable
                assert response.status_code in [
                    204,
                    404,
                ], f"Failed to cleanup session {session_id}: {response.status_code}"
            except Exception as e:
                # Log but don't fail the test on cleanup errors
                print(f"Warning: Failed to cleanup session {session_id}: {e}")
