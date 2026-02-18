from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_creates_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"username": "newuser", "password": "newpass"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"
    assert data["user"]["system_role"] == "app_user"


@pytest.mark.asyncio
async def test_signup_duplicate_username(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"username": "dupeuser", "password": "pass1"},
    )
    response = await client.post(
        "/api/v1/auth/signup",
        json={"username": "dupeuser", "password": "pass2"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_signup_restricted_role(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "sneaky",
            "password": "pass",
            "system_role": "superadmin",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"username": "loginuser", "password": "loginpass"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "loginpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "loginuser"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"username": "wrongpw", "password": "correct"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpw", "password": "incorrect"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "ghost", "password": "ghost"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"username": "meuser", "password": "mepass"},
    )
    token = signup.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "meuser"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
