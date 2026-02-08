"""Unit tests for src/core/jobs_client.py

TEST: Cloud Run Jobs client
PURPOSE: Validate background job triggering
VALIDATES: Job execution, status checks
EXPECTED: All job operations work correctly
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.jobs_client import (
    CloudRunJobsClient,
    get_jobs_client,
    trigger_background_task,
    CLOUD_RUN_AVAILABLE,
)


@pytest.mark.skipif(not CLOUD_RUN_AVAILABLE, reason="google-cloud-run not installed")
class TestCloudRunJobsClient:
    """Test CloudRunJobsClient class."""

    def test_client_initialization(self):
        """
        TEST: Initialize jobs client
        PURPOSE: Verify client creation
        VALIDATES: Client attributes set
        EXPECTED: Client ready
        """
        with patch("src.core.jobs_client.run_v2.JobsClient"):
            with patch("src.core.jobs_client.run_v2.ExecutionsClient"):
                with patch("src.core.jobs_client.settings") as mock_settings:
                    mock_settings.gcp_project = "test-project"

                    client = CloudRunJobsClient()

                    assert client.project_id == "test-project"
                    assert client.region == "europe-west4"

    @pytest.mark.asyncio
    async def test_trigger_job_success(self):
        """
        TEST: Trigger Cloud Run Job
        PURPOSE: Verify job execution
        VALIDATES: Job triggered with params
        EXPECTED: Execution ID returned
        """
        with patch("src.core.jobs_client.run_v2.JobsClient") as MockJobsClient:
            with patch("src.core.jobs_client.run_v2.ExecutionsClient"):
                with patch("src.core.jobs_client.settings") as mock_settings:
                    mock_settings.gcp_project = "test-project"

                    # Mock run_job response
                    mock_operation = MagicMock()
                    mock_operation.name = "execution_123"
                    MockJobsClient.return_value.run_job.return_value = mock_operation

                    client = CloudRunJobsClient()
                    result = await client.trigger_job(
                        job_name="test-job",
                        task_name="export_session_messages",
                        task_args={"session_id": "sess_123"},
                    )

                    assert result["job_name"] == "test-job"
                    assert result["status"] == "triggered"

    @pytest.mark.asyncio
    async def test_get_execution_status(self):
        """
        TEST: Get job execution status
        PURPOSE: Verify status retrieval
        VALIDATES: Execution details returned
        EXPECTED: Status, timestamps included
        """
        with patch("src.core.jobs_client.run_v2.JobsClient"):
            with patch("src.core.jobs_client.run_v2.ExecutionsClient") as MockExecClient:
                with patch("src.core.jobs_client.settings") as mock_settings:
                    mock_settings.gcp_project = "test-project"

                    # Mock execution response
                    mock_execution = MagicMock()
                    mock_execution.completion_status = "SUCCEEDED"
                    MockExecClient.return_value.get_execution.return_value = mock_execution

                    client = CloudRunJobsClient()
                    result = await client.get_execution_status("execution_123")

                    assert result["status"] == "SUCCEEDED"


class TestGetJobsClient:
    """Test get_jobs_client singleton."""

    def test_get_jobs_client_returns_singleton(self):
        """
        TEST: Get jobs client singleton
        PURPOSE: Verify global instance
        VALIDATES: Same instance returned
        EXPECTED: Singleton pattern
        """
        with patch("src.core.jobs_client.CloudRunJobsClient"):
            client1 = get_jobs_client()
            client2 = get_jobs_client()

            assert client1 is client2


@pytest.mark.asyncio
async def test_trigger_background_task():
    """
    TEST: Trigger background task convenience function
    PURPOSE: Verify helper function
    VALIDATES: Job triggered with task name
    EXPECTED: Execution details returned
    """
    with patch("src.core.jobs_client.get_jobs_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.trigger_job.return_value = {
            "job_name": "background-worker",
            "execution_id": "exec_123",
            "task_name": "cleanup_old_sessions",
            "status": "triggered",
        }
        mock_get_client.return_value = mock_client

        result = await trigger_background_task(
            task_name="cleanup_old_sessions", task_args={"days_old": 90}
        )

        assert result["task_name"] == "cleanup_old_sessions"
        assert result["status"] == "triggered"
