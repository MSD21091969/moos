from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.auth import create_access_token, hash_password
from src.core.database import Base, get_db
from src.db.models import SystemRole, User
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_collider.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user() -> User:
    """Create a COLLIDER_ADMIN user in the test DB."""
    async with test_session() as session:
        user = User(
            username="test_admin",
            password_hash=hash_password("testpass"),
            system_role=SystemRole.COLLIDER_ADMIN,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict[str, str]:
    """Return auth headers for a COLLIDER_ADMIN user."""
    token = create_access_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def superadmin_user() -> User:
    """Create a SUPERADMIN user in the test DB."""
    async with test_session() as session:
        user = User(
            username="test_superadmin",
            password_hash=hash_password("testpass"),
            system_role=SystemRole.SUPERADMIN,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def superadmin_headers(superadmin_user: User) -> dict[str, str]:
    """Return auth headers for a SUPERADMIN user."""
    token = create_access_token(superadmin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def app_user() -> User:
    """Create an APP_USER user in the test DB."""
    async with test_session() as session:
        user = User(
            username="test_app_user",
            password_hash=hash_password("testpass"),
            system_role=SystemRole.APP_USER,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def app_user_headers(app_user: User) -> dict[str, str]:
    """Return auth headers for an APP_USER user."""
    token = create_access_token(app_user)
    return {"Authorization": f"Bearer {token}"}
