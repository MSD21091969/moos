"""Unit tests for src/api/routes/jobs.py - FIXED VERSION

TEST: Background jobs endpoints with proper dependency overrides
PURPOSE: Validate job triggering and export endpoints
VALIDATES: Async job execution, task arguments
PATTERN: Use app.dependency_overrides instead of direct patching

NOTE: These tests mock the jobs_client module since GCP Cloud Run Jobs
require GCP credentials and project setup.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.main import app as main_app
from src.api.dependencies import get_app_container


# Fixtures


@pytest.fixture
def client():
    """TestClient with overridden dependencies."""
    test_app = FastAPI()
    test_app.include_router(main_app.router)

    # Override dependencies
    async def override_app_container():
        mock_container = MagicMock()
        mock_container.firestore_client = MagicMock()
        return mock_container

    test_app.dependency_overrides[get_app_container] = override_app_container

    return TestClient(test_app)


# Tests


class TestTriggerJob:
    """Test POST /jobs/trigger endpoint."""

    @patch("src.api.routes.jobs.trigger_background_task")
    def test_trigger_job_success(self, mock_trigger, client):
        """
        TEST: Trigger background job
        PURPOSE: Verify job triggering
        VALIDATES: Task arguments, execution response
        EXPECTED: 200 with job info
        """
        mock_trigger.return_value = {
            "job_name": "export-job",
            "execution_id": "exec_abc123",
            "task_name": "export_session_messages",
            "status": "queued",
        }

        response = client.post(
            "/jobs/trigger",
            json={
                "task_name": "export_session_messages",
                "task_args": {"session_id": "sess_123", "export_format": "json"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec_abc123"
        assert data["status"] == "queued"

    @patch("src.api.routes.jobs.trigger_background_task")
    def test_trigger_job_error(self, mock_trigger, client):
        """
        TEST: Job trigger fails
        PURPOSE: Verify error handling
        VALIDATES: Exception → 500
        EXPECTED: 500 internal error
        """
        mock_trigger.side_effect = Exception("GCP credentials not configured")

        response = client.post(
            "/jobs/trigger",
            json={
                "task_name": "cleanup_old_sessions",
                "task_args": {"days": 30},
            },
        )

        assert response.status_code == 500
        assert "Failed to trigger job" in response.json()["detail"]


class TestExportSession:
    """Test POST /jobs/export-session endpoint."""

    @patch("src.api.routes.jobs.trigger_background_task")
    def test_export_session_success(self, mock_trigger, client):
        """
        TEST: Export session as background job
        PURPOSE: Verify export job creation
        VALIDATES: Convenience endpoint wrapping
        EXPECTED: 200 with job info
        """
        mock_trigger.return_value = {
            "job_name": "export-session",
            "execution_id": "exec_export789",
            "task_name": "export_session_messages",
            "status": "queued",
        }

        response = client.post(
            "/jobs/export-session",
            json={
                "session_id": "sess_abc123",
                "export_format": "pdf",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec_export789"
        assert data["task_name"] == "export_session_messages"

        # Verify mock called with correct args
        mock_trigger.assert_called_once()
        call_args = mock_trigger.call_args[1]
        assert call_args["task_name"] == "export_session_messages"
        assert call_args["task_args"]["session_id"] == "sess_abc123"
        assert call_args["task_args"]["export_format"] == "pdf"
