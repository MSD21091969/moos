"""Test that integration test fixtures work correctly."""

import pytest


def test_integration_client_initialized(integration_client):
    """
    TEST: Integration test client initialization
    PURPOSE: Verify TestClient works with integration app
    VALIDATES: Fixture setup correct
    EXPECTED: Client responds to health check
    """
    response = integration_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_test_user_created(test_user, mock_firestore):
    """
    TEST: Test user fixture creates user in Firestore
    PURPOSE: Verify user fixture setup
    VALIDATES: User exists in MockFirestore
    EXPECTED: User document retrievable
    """
    # Verify user was created in Firestore
    user_ref = mock_firestore.collection("users").document(test_user.user_id)
    user_doc = await user_ref.get()

    assert user_doc.exists
    user_data = user_doc.to_dict()
    assert user_data["user_id"] == test_user.user_id
    assert user_data["email"] == test_user.email
    assert user_data["tier"] == "pro"
    assert user_data["quota_remaining"] == 1000
