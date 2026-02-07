"""Unit tests for src/core/background_tasks.py

TEST: Background job tasks for Cloud Run Jobs
PURPOSE: Validate async task execution, error handling, export formats
VALIDATES: Session exports, cleanup jobs, notifications, pipelines
EXPECTED: All background tasks execute correctly and handle errors
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.background_tasks import BackgroundTasks, TASK_REGISTRY


class TestExportSessionMessages:
    """Test export_session_messages task."""

    @pytest.mark.asyncio
    async def test_export_json_success(self):
        """
        TEST: Export session as JSON
        PURPOSE: Verify JSON export functionality
        VALIDATES: Export result with file URL
        EXPECTED: Completed status with gs:// URL
        """
        mock_session = MagicMock()
        mock_events = [{"role": "user", "content": "test"}]

        with patch("src.core.background_tasks.get_firestore_client"):
            with patch("src.core.background_tasks.SessionService") as mock_service:
                mock_service_instance = mock_service.return_value
                mock_service_instance.get = AsyncMock(return_value=mock_session)
                mock_service_instance.get_events = AsyncMock(return_value=(mock_events, 1))

                result = await BackgroundTasks.export_session_messages("sess_123", "json")

        assert result["status"] == "completed"
        assert result["format"] == "json"
        assert "gs://exports/" in result["file_url"]
        assert result["event_count"] == 1

    @pytest.mark.asyncio
    async def test_export_csv_success(self):
        """
        TEST: Export session as CSV
        PURPOSE: Verify CSV export functionality
        VALIDATES: CSV format handling
        EXPECTED: Completed with .csv URL
        """
        mock_session = MagicMock()

        with patch("src.core.background_tasks.get_firestore_client"):
            with patch("src.core.background_tasks.SessionService") as mock_service:
                mock_service_instance = mock_service.return_value
                mock_service_instance.get = AsyncMock(return_value=mock_session)
                mock_service_instance.get_events = AsyncMock(return_value=([], 0))

                result = await BackgroundTasks.export_session_messages("sess_123", "csv")

        assert result["status"] == "completed"
        assert result["file_url"].endswith(".csv")

    @pytest.mark.asyncio
    async def test_export_unsupported_format_fails(self):
        """
        TEST: Export with unsupported format
        PURPOSE: Verify format validation
        VALIDATES: Error handling for bad format
        EXPECTED: Failed status with error
        """
        mock_session = MagicMock()

        with patch("src.core.background_tasks.get_firestore_client"):
            with patch("src.core.background_tasks.SessionService") as mock_service:
                mock_service_instance = mock_service.return_value
                mock_service_instance.get = AsyncMock(return_value=mock_session)
                mock_service_instance.get_messages = AsyncMock(return_value=([], 0))

                result = await BackgroundTasks.export_session_messages("sess_123", "xml")

        assert result["status"] == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_export_missing_session_fails(self):
        """
        TEST: Export non-existent session
        PURPOSE: Verify session validation
        VALIDATES: Error for missing session
        EXPECTED: Failed status
        """
        with patch("src.core.background_tasks.get_firestore_client"):
            with patch("src.core.background_tasks.SessionService") as mock_service:
                mock_service_instance = mock_service.return_value
                mock_service_instance.get = AsyncMock(return_value=None)

                result = await BackgroundTasks.export_session_messages("sess_missing", "json")

        assert result["status"] == "failed"


class TestCleanupOldSessions:
    """Test cleanup_old_sessions task."""

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_sessions(self):
        """
        TEST: Cleanup old archived sessions
        PURPOSE: Verify cleanup logic
        VALIDATES: Old sessions deleted
        EXPECTED: Deleted count returned
        """
        mock_docs = [MagicMock(id="sess_old1"), MagicMock(id="sess_old2")]

        async def mock_stream():
            for doc in mock_docs:
                yield doc

        with patch("src.core.background_tasks.get_firestore_client") as mock_get_client:
            # Create mock client
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Mock query chain with async stream
            mock_query = MagicMock()
            mock_query.stream = mock_stream
            mock_where_1 = MagicMock()
            mock_where_1.where.return_value = mock_query
            mock_collection = MagicMock()
            mock_collection.where.return_value = mock_where_1
            mock_client.collection.return_value = mock_collection

            with patch("src.core.background_tasks.SessionService") as mock_service:
                mock_service_instance = mock_service.return_value
                mock_service_instance.delete = AsyncMock()

                result = await BackgroundTasks.cleanup_old_sessions(days_old=90)

        assert result["status"] == "completed"
        assert result["deleted_count"] == 2

    @pytest.mark.asyncio
    async def test_cleanup_handles_empty_results(self):
        """
        TEST: Cleanup with no old sessions
        PURPOSE: Verify empty result handling
        VALIDATES: No errors on empty set
        EXPECTED: 0 deleted count
        """

        async def mock_empty_stream():
            return
            yield  # Make it a generator

        with patch("src.core.background_tasks.get_firestore_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Mock empty query chain
            mock_query = MagicMock()
            mock_query.stream = mock_empty_stream
            mock_where_1 = MagicMock()
            mock_where_1.where.return_value = mock_query
            mock_collection = MagicMock()
            mock_collection.where.return_value = mock_where_1
            mock_client.collection.return_value = mock_collection

            result = await BackgroundTasks.cleanup_old_sessions()

        assert result["deleted_count"] == 0
        assert result["status"] == "completed"


class TestSendNotification:
    """Test send_notification task."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """
        TEST: Send notification to user
        PURPOSE: Verify notification task
        VALIDATES: Notification sent
        EXPECTED: Sent status
        """
        result = await BackgroundTasks.send_notification(
            user_id="user_123", notification_type="email", data={"subject": "Test"}
        )

        assert result["status"] == "sent"
        assert result["user_id"] == "user_123"
        assert result["type"] == "email"


class TestProcessDataPipeline:
    """Test process_data_pipeline task."""

    @pytest.mark.asyncio
    async def test_pipeline_execution_success(self):
        """
        TEST: Execute data pipeline
        PURPOSE: Verify pipeline task
        VALIDATES: Pipeline completes
        EXPECTED: Completed status
        """
        result = await BackgroundTasks.process_data_pipeline(
            pipeline_id="pipeline_123", input_data={"key": "value"}
        )

        assert result["status"] == "completed"
        assert result["pipeline_id"] == "pipeline_123"


class TestTaskRegistry:
    """Test TASK_REGISTRY."""

    def test_registry_contains_all_tasks(self):
        """
        TEST: Task registry completeness
        PURPOSE: Verify all tasks registered
        VALIDATES: Registry has all task functions
        EXPECTED: 4 tasks registered
        """
        assert "export_session_messages" in TASK_REGISTRY
        assert "cleanup_old_sessions" in TASK_REGISTRY
        assert "send_notification" in TASK_REGISTRY
        assert "process_data_pipeline" in TASK_REGISTRY
        assert len(TASK_REGISTRY) == 4
