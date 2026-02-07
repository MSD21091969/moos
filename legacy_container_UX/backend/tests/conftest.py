"""
Shared test fixtures for My Tiny Data Collider test suite.

This conftest provides reusable test data, mocks, and utilities across all test categories.
Fixtures are organized by scope and dependency to optimize test performance.
"""

# ============================================================================
# Environment Setup (MUST BE FIRST - before any app imports)
# ============================================================================
# Per pytest best practices: Set environment variables at module import time
# to ensure they're available during FastAPI app startup and lifespan events
import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing_only")
os.environ.setdefault("USE_FIRESTORE_MOCKS", "true")
os.environ.setdefault("LOGFIRE_TOKEN", "")
os.environ.setdefault("REDIS_ENABLED", "false")
os.environ.setdefault("PROJECT_ID", "test-project")
os.environ.setdefault("FIRESTORE_DATABASE", "test-db")

# ============================================================================
# Standard Library & Third-Party Imports
# ============================================================================
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi.testclient import TestClient

from src.core.config import Settings
from src.models.context import SessionContext, UserContext
from src.models.permissions import Tier
from src.models.sessions import Session, SessionCreate, SessionMetadata, SessionStatus, SessionType
from src.models.users import User
from src.persistence.mock_firestore import MockFirestoreClient

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Fast unit tests with no external dependencies")
    config.addinivalue_line("markers", "integration: Tests with mocked services")
    config.addinivalue_line("markers", "e2e: End-to-end tests with real dependencies")
    config.addinivalue_line("markers", "slow: Slow-running tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration & Environment
# ============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Test-specific settings with safe defaults."""
    return Settings(
        ENVIRONMENT="test",
        PROJECT_ID="test-project",
        FIRESTORE_EMULATOR_HOST="localhost:8080",
        JWT_SECRET_KEY="test_secret_key_for_testing_only",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        LOGFIRE_TOKEN="",  # Disable Logfire in tests
        REDIS_URL="",  # Disable Redis in tests
    )


# ============================================================================
# Persistence Layer (Firestore)
# ============================================================================


@pytest.fixture
def mock_firestore() -> MockFirestoreClient:
    """
    Fresh MockFirestoreClient for each test.

    Provides in-memory document storage without GCP dependencies.
    Automatically cleaned up after each test.
    """
    client = MockFirestoreClient()
    yield client
    # Clear storage to prevent test data leakage
    client._storage.clear()
    # Don't persist test data to disk
    if os.path.exists(client._persist_path):
        os.remove(client._persist_path)


@pytest.fixture
async def firestore_with_test_data(mock_firestore: MockFirestoreClient) -> MockFirestoreClient:
    """
    MockFirestore pre-populated with standard test data.

    Useful for integration tests that need existing sessions/users.
    """
    # Create test user
    await (
        mock_firestore.collection("users")
        .document("test_user_123")
        .set(
            {
                "user_id": "test_user_123",
                "email": "test@example.com",
                "tier": "FREE",
                "quota_used_today": 10,
                "daily_quota": 100,
                "hashed_password": "$2b$12$F9QjU1g/CP9D8wuveMrwce6Z8ieKy3KqMkRCI.3fEgmD3oDSb6Rwy",  # test123
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    # Create test session
    await (
        mock_firestore.collection("sessions")
        .document("sess_abc123def456")
        .set(
            {
                "session_id": "sess_abc123def456",
                "user_id": "test_user_123",
                "title": "Existing Test Session",
                "description": "Pre-existing session for tests",
                "status": "active",
                "session_type": "chat",
                "event_count": 5,
                "quota_used": 5,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    return mock_firestore


# ============================================================================
# Domain Models - Users
# ============================================================================


@pytest.fixture
def free_tier_user() -> User:
    """Standard FREE tier user for testing."""
    return User(
        user_id="test_user_free",
        email="free@example.com",
        tier=Tier.FREE,
        quota_used_today=0,
        daily_quota=100,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        organization_id=None,
        last_login_at=None,
        ip_address=None,
    )


@pytest.fixture
def pro_tier_user() -> User:
    """PRO tier user with elevated limits."""
    return User(
        user_id="test_user_pro",
        email="pro@example.com",
        tier=Tier.PRO,
        quota_used_today=50,
        daily_quota=1000,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        organization_id=None,
        last_login_at=None,
        ip_address=None,
    )


@pytest.fixture
def enterprise_tier_user() -> User:
    """ENTERPRISE tier user with maximum limits."""
    return User(
        user_id="test_user_enterprise",
        email="enterprise@example.com",
        tier=Tier.ENTERPRISE,
        quota_used_today=100,
        daily_quota=10000,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        organization_id=None,
        last_login_at=None,
        ip_address=None,
    )


# ============================================================================
# Context Objects
# ============================================================================


@pytest.fixture
def user_context(free_tier_user: User) -> UserContext:
    """UserContext for FREE tier user (most common test case)."""
    return UserContext(
        user_id=free_tier_user.user_id,
        email=free_tier_user.email,
        tier=free_tier_user.tier,
        permissions=["basic"],
        quota_remaining=free_tier_user.daily_quota - free_tier_user.quota_used_today,
    )


@pytest.fixture
def pro_user_context(pro_tier_user: User) -> UserContext:
    """UserContext for PRO tier user."""
    return UserContext(
        user_id=pro_tier_user.user_id,
        email=pro_tier_user.email,
        tier=pro_tier_user.tier,
        permissions=["basic", "advanced"],
        quota_remaining=pro_tier_user.daily_quota - pro_tier_user.quota_used_today,
    )


@pytest.fixture
def session_context(user_context: UserContext) -> SessionContext:
    """SessionContext with standard user context."""
    return SessionContext(
        user_id=user_context.user_id,
        user_email=user_context.email,
        tier=user_context.tier,  # Will be 'free' from UserContext
        permissions=user_context.permissions,
        quota_remaining=user_context.quota_remaining,
        session_id="sess_abc123def456",
    )


# ============================================================================
# Domain Models - Sessions
# ============================================================================


@pytest.fixture
def session_create_payload() -> dict:
    """Valid session creation payload (dict for API tests)."""
    return {
        "title": "Test Session",
        "description": "Session created during testing",
        "session_type": "chat",
        "tags": ["test", "automation"],
        "ttl_hours": 24,
    }


@pytest.fixture
def session_create_model() -> SessionCreate:
    """Valid SessionCreate Pydantic model."""
    return SessionCreate(
        metadata=SessionMetadata(
            title="Test Session",
            description="Session created during testing",
            session_type=SessionType.CHAT,
            tags=["test", "automation"],
            ttl_hours=24,
        )
    )


@pytest.fixture
def active_session() -> Session:
    """Active session for testing updates/reads."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    return Session(
        session_id="sess_abc123def456",
        user_id="test_user_123",
        metadata=SessionMetadata(
            title="Active Test Session",
            description="A session in active state",
            session_type=SessionType.CHAT,
            tags=["test"],
            ttl_hours=24,
        ),
        status=SessionStatus.ACTIVE,
        event_count=5,
        quota_used=5,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(hours=24),  # 24 hours from now
        created_by="test_user_123",
        acl={"test_user_123": "owner"},
    )


@pytest.fixture
def completed_session() -> Session:
    """Completed session for testing state transitions."""
    return Session(
        session_id="sess_completed1234",
        user_id="test_user_123",
        metadata=SessionMetadata(
            title="Completed Test Session",
            description="A completed session",
            session_type=SessionType.ANALYSIS,
            tags=["test", "completed"],
            ttl_hours=168,
        ),
        status=SessionStatus.COMPLETED,
        event_count=25,
        quota_used=30,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by="test_user_123",  # Added missing field
        acl={"test_user_123": "owner"},  # Added ACL
    )


# ============================================================================
# Test Data Builders
# ============================================================================


class SessionBuilder:
    """Fluent builder for Session test data."""

    def __init__(self):
        self.data = {
            "session_id": "sess_builder12345",
            "user_id": "test_user_123",
            "title": "Builder Session",
            "description": "Session from builder",
            "status": SessionStatus.ACTIVE,
            "session_type": SessionType.CHAT,
            "tags": [],
            "event_count": 0,
            "quota_used": 0,
            "ttl_hours": 24,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    def with_id(self, session_id: str):
        self.data["session_id"] = session_id
        return self

    def with_user(self, user_id: str):
        self.data["user_id"] = user_id
        return self

    def with_title(self, title: str):
        self.data["title"] = title
        return self

    def with_status(self, status: SessionStatus):
        self.data["status"] = status
        return self

    def with_type(self, session_type: SessionType):
        self.data["session_type"] = session_type
        return self

    def with_events(self, count: int):
        """Set event count (replaces with_messages)."""
        self.data["event_count"] = count
        return self

    def with_messages(self, count: int):
        """Deprecated: Use with_events() instead. Kept for backward compatibility."""
        self.data["event_count"] = count
        return self

    def with_quota(self, quota: int):
        self.data["quota_used"] = quota
        return self

    def with_ttl(self, hours: int):
        self.data["ttl_hours"] = hours
        return self

    def archived(self):
        self.data["status"] = SessionStatus.ARCHIVED
        return self

    def completed(self):
        self.data["status"] = SessionStatus.COMPLETED
        return self

    def build(self) -> Session:
        return Session(**self.data)


@pytest.fixture
def session_builder() -> SessionBuilder:
    """Session builder fixture for custom test data."""
    return SessionBuilder()


# ============================================================================
# Mock Services
# ============================================================================


@pytest.fixture
def mock_auth_service():
    """Mocked AuthService for testing without JWT dependencies."""
    mock = Mock()
    mock.decode_token.return_value = {
        "sub": "test@example.com",
        "tier": "FREE",
        "permissions": ["basic"],
    }
    mock.verify_token.return_value = True
    return mock


@pytest.fixture
def mock_quota_service():
    """Mocked QuotaService for testing without Firestore."""
    mock = AsyncMock()
    mock.get_remaining.return_value = 95
    mock.check_sufficient.return_value = True
    mock.deduct.return_value = None
    return mock


# ============================================================================
# JWT Token Generation
# ============================================================================


def generate_test_jwt(
    user_id: str = "test_user_123",
    email: str = "test@example.com",
    tier: str = "free",
    permissions: list = None,
    expire_minutes: int = 60,
) -> str:
    """
    Generate valid JWT token for testing.

    Args:
        user_id: User identifier
        email: User email address
        tier: User tier (free, pro, enterprise)
        permissions: List of permission strings
        expire_minutes: Token expiration in minutes

    Returns:
        Valid JWT token string
    """
    if permissions is None:
        permissions = ["basic"]

    payload = {
        "sub": user_id,
        "email": email,
        "tier": tier,
        "permissions": permissions,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, "test_secret_key_for_testing_only", algorithm="HS256")


@pytest.fixture
def valid_jwt_token() -> str:
    """Valid JWT token for FREE tier user."""
    return generate_test_jwt(
        user_id="test_user_123", email="test@example.com", tier="free", permissions=["basic"]
    )


@pytest.fixture
def pro_jwt_token() -> str:
    """Valid JWT token for PRO tier user."""
    return generate_test_jwt(
        user_id="test_user_pro",
        email="pro@example.com",
        tier="pro",
        permissions=["basic", "advanced"],
    )


@pytest.fixture
def enterprise_jwt_token() -> str:
    """Valid JWT token for ENTERPRISE tier user."""
    return generate_test_jwt(
        user_id="test_user_enterprise",
        email="enterprise@example.com",
        tier="enterprise",
        permissions=["basic", "advanced", "premium"],
    )


# ============================================================================
# HTTP Client (API Testing)
# ============================================================================


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient for API route testing.

    Note: For true E2E tests, use test_api.py with real HTTP.
    This is for route unit tests with mocked dependencies.
    """
    from src.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(valid_jwt_token: str) -> dict:
    """Valid authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def pro_auth_headers(pro_jwt_token: str) -> dict:
    """Authorization headers for PRO tier user."""
    return {"Authorization": f"Bearer {pro_jwt_token}"}


# ============================================================================
# Timing & Performance
# ============================================================================


@pytest.fixture
def benchmark_threshold():
    """Performance thresholds for slow test detection."""
    return {
        "unit": 0.1,  # 100ms max for unit tests
        "integration": 1.0,  # 1s max for integration tests
        "e2e": 5.0,  # 5s max for E2E tests
    }


# ============================================================================
# Cleanup Helpers
# ============================================================================


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Auto-reset singleton state between tests.

    Prevents test pollution from cached data.
    """
    from src.models.context import clear_user_cache

    yield

    # Cleanup after test
    clear_user_cache()


# ============================================================================
# Parametrized Test Data
# ============================================================================


@pytest.fixture(params=[Tier.FREE, Tier.PRO, Tier.ENTERPRISE])
def all_tiers(request) -> Tier:
    """Parametrized fixture for testing across all tier levels."""
    return request.param


@pytest.fixture(params=[SessionType.CHAT, SessionType.ANALYSIS, SessionType.INTERACTIVE])
def all_session_types(request) -> SessionType:
    """Parametrized fixture for testing all session types."""
    return request.param


@pytest.fixture(params=[SessionStatus.ACTIVE, SessionStatus.COMPLETED, SessionStatus.ARCHIVED])
def all_session_statuses(request) -> SessionStatus:
    """Parametrized fixture for testing all session statuses."""
    return request.param
