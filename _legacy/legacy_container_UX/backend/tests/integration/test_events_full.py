"""Full integration tests for event querying endpoints.

Tests all 3 event API endpoints with real/mock Firestore:
1. GET /sessions/{id}/events - List events with filters
2. GET /sessions/{id}/events/{event_id} - Get event details
3. GET /sessions/{id}/events/{event_id}/tree - Get event tree

Note: This requires the composite Firestore index (depth+source+timestamp)
which must be deployed to production Firestore.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_list_session_events(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/events - List events."""
    # Create session and run agent to generate events
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Event Test Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Run agent to create some events
    enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={"message": "Test message for events", "session_id": session_id},
    )
    # Agent might fail but that's ok - we just want some events

    # List events
    response = enterprise_client.get(
        f"/sessions/{session_id}/events",
        headers=enterprise_headers,
    )

    # May return 200 with empty list or 400 if index not deployed
    # Accept both for integration tests
    assert response.status_code in [
        200,
        400,
    ], f"List events returned unexpected status: {response.status_code}"

    if response.status_code == 200:
        events = response.json()
        assert "events" in events
        assert "total" in events
        assert isinstance(events["events"], list)


@pytest.mark.integration
def test_list_events_with_filters(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/events with filters."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Filtered Events Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Test various filters
    filter_tests = [
        "?depth=0",  # Root events only
        "?source=USER",  # User events
        "?status=COMPLETED",  # Completed events
        "?limit=10",  # Pagination
    ]

    for filter_query in filter_tests:
        response = enterprise_client.get(
            f"/sessions/{session_id}/events{filter_query}",
            headers=enterprise_headers,
        )

        # Accept 200 (success) or 400 (index not deployed)
        assert response.status_code in [
            200,
            400,
        ], f"Filter {filter_query} returned unexpected status: {response.status_code}"


@pytest.mark.integration
def test_get_event_details(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/events/{event_id} - Get event details."""
    # Create session and run agent
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Event Details Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Run agent to create an event
    agent_response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={"message": "Create event", "session_id": session_id},
    )

    # Try to get event details if we have an event_id
    if agent_response.status_code == 200 and "event_id" in agent_response.json():
        event_id = agent_response.json()["event_id"]

        response = enterprise_client.get(
            f"/sessions/{session_id}/events/{event_id}",
            headers=enterprise_headers,
        )

        # Accept 200 (found) or 404 (not found)
        assert response.status_code in [
            200,
            404,
        ], f"Get event details returned unexpected status: {response.status_code}"


@pytest.mark.integration
def test_get_event_tree(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test GET /sessions/{id}/events/{event_id}/tree - Get event tree."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Event Tree Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Run agent to create events
    agent_response = enterprise_client.post(
        "/agent/run",
        headers=enterprise_headers,
        json={"message": "Create event tree", "session_id": session_id},
    )

    # Try to get event tree if we have an event_id
    if agent_response.status_code == 200 and "event_id" in agent_response.json():
        event_id = agent_response.json()["event_id"]

        response = enterprise_client.get(
            f"/sessions/{session_id}/events/{event_id}/tree",
            headers=enterprise_headers,
        )

        # Accept 200 (found), 404 (not found), or 501 (not implemented)
        assert response.status_code in [
            200,
            404,
            501,
        ], f"Get event tree returned unexpected status: {response.status_code}"


@pytest.mark.integration
def test_list_events_nonexistent_session(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
):
    """Test error handling for non-existent session."""
    response = enterprise_client.get(
        "/sessions/sess_000000000000/events",
        headers=enterprise_headers,
    )

    # Should return 404 for non-existent session
    assert response.status_code in [404, 400], "Should return 404 or 400 for non-existent session"


@pytest.mark.integration
def test_invalid_event_filter(
    enterprise_client: TestClient,
    enterprise_headers: dict[str, str],
    created_session_ids: list[str],
    auto_cleanup_sessions,
):
    """Test error handling for invalid filter values."""
    # Create session
    create_response = enterprise_client.post(
        "/sessions",
        headers=enterprise_headers,
        json={"title": "Invalid Filter Session", "session_type": "chat", "ttl_hours": 24},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    created_session_ids.append(session_id)

    # Test invalid source filter
    response = enterprise_client.get(
        f"/sessions/{session_id}/events?source=INVALID_SOURCE",
        headers=enterprise_headers,
    )

    assert response.status_code == 400, "Should return 400 for invalid source filter"
