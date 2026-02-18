from __future__ import annotations

import pytest
from httpx import AsyncClient
from src.db.models import User


@pytest.mark.asyncio
async def test_admin_can_list_users(client: AsyncClient, admin_headers: dict):
    response = await client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_regular_user_cannot_list_users(
    client: AsyncClient, app_user_headers: dict
):
    response = await client.get("/api/v1/users/", headers=app_user_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_can_delete_user(
    client: AsyncClient,
    superadmin_headers: dict,
    app_user: User,
):
    response = await client.delete(
        f"/api/v1/users/{app_user.id}",
        headers=superadmin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_cannot_delete_user(
    client: AsyncClient,
    admin_headers: dict,
    app_user: User,
):
    response = await client.delete(
        f"/api/v1/users/{app_user.id}",
        headers=admin_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_assign_role(
    client: AsyncClient,
    admin_headers: dict,
    app_user: User,
):
    response = await client.post(
        f"/api/v1/users/{app_user.id}/assign-role",
        json={"system_role": "app_admin"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "assigned role" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_collider_admin_cannot_assign_superadmin(
    client: AsyncClient,
    admin_headers: dict,
    app_user: User,
):
    response = await client.post(
        f"/api/v1/users/{app_user.id}/assign-role",
        json={"system_role": "superadmin"},
        headers=admin_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_access_request_flow(
    client: AsyncClient,
    admin_headers: dict,
    admin_user: User,
):
    # Create an app
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Access Test App"},
        headers=admin_headers,
    )
    app_id = app_resp.json()["id"]

    # Signup a new user
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"username": "requester", "password": "reqpass"},
    )
    user_token = signup.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # User requests access
    req_resp = await client.post(
        f"/api/v1/apps/{app_id}/request-access",
        json={"application_id": app_id, "message": "Please let me in"},
        headers=user_headers,
    )
    assert req_resp.status_code == 200
    request_id = req_resp.json()["id"]

    # Admin sees pending requests
    pending = await client.get(
        f"/api/v1/apps/{app_id}/pending-requests",
        headers=admin_headers,
    )
    assert pending.status_code == 200
    assert len(pending.json()) >= 1

    # Admin approves
    approve = await client.post(
        f"/api/v1/apps/{app_id}/requests/{request_id}/approve",
        json={"role": "app_user"},
        headers=admin_headers,
    )
    assert approve.status_code == 200

    # Verify permission was created
    perms = await client.get(
        f"/api/v1/permissions/?application_id={app_id}",
        headers=admin_headers,
    )
    assert perms.status_code == 200
    user_id = signup.json()["user"]["id"]
    perm_list = perms.json()
    assert any(p["user_id"] == user_id for p in perm_list)


@pytest.mark.asyncio
async def test_access_request_rejection(
    client: AsyncClient,
    admin_headers: dict,
):
    # Create an app
    app_resp = await client.post(
        "/api/v1/apps/",
        json={"display_name": "Reject Test App"},
        headers=admin_headers,
    )
    app_id = app_resp.json()["id"]

    # Signup a new user
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"username": "rejected_user", "password": "pass"},
    )
    user_headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    # User requests access
    req_resp = await client.post(
        f"/api/v1/apps/{app_id}/request-access",
        json={"application_id": app_id, "message": "Please"},
        headers=user_headers,
    )
    request_id = req_resp.json()["id"]

    # Admin rejects
    reject = await client.post(
        f"/api/v1/apps/{app_id}/requests/{request_id}/reject",
        headers=admin_headers,
    )
    assert reject.status_code == 200
    assert "denied" in reject.json()["message"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_user_list(client: AsyncClient):
    response = await client.get("/api/v1/users/")
    assert response.status_code in (401, 403)
