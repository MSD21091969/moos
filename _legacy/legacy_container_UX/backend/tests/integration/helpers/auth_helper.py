"""Authentication helper for integration tests.

Provides utilities for obtaining JWT tokens for test users.
"""

from fastapi.testclient import TestClient


def login_user(client: TestClient, email: str, password: str = "test123") -> str:
    """
    Login user and return JWT access token.

    Args:
        client: FastAPI TestClient instance
        email: User email (test@test.com, pro@test.com, enterprise@test.com)
        password: User password (default: test123)

    Returns:
        JWT access token string

    Raises:
        AssertionError: If login fails
    """
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token_data = response.json()
    assert "access_token" in token_data, "No access token in response"
    return token_data["access_token"]


def get_auth_headers(token: str) -> dict[str, str]:
    """
    Create authorization headers from JWT token.

    Args:
        token: JWT access token

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {token}"}


def login_and_get_headers(
    client: TestClient, email: str, password: str = "test123"
) -> dict[str, str]:
    """
    Login user and return authorization headers.

    Convenience method combining login_user and get_auth_headers.

    Args:
        client: FastAPI TestClient instance
        email: User email
        password: User password (default: test123)

    Returns:
        Dictionary with Authorization header
    """
    token = login_user(client, email, password)
    return get_auth_headers(token)
