"""Tests for Google Workspace tools (import_google_sheet, export_to_sheets)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic_ai import RunContext

from src.tools.google_tools import (
    import_google_sheet,
    export_to_sheets,
    _extract_spreadsheet_id,
)
from src.core.exceptions import AuthenticationError, ValidationError
from src.models.context import SessionContext
from src.models.permissions import Tier


class TestExtractSpreadsheetId:
    """Test spreadsheet ID extraction from URLs."""

    def test_extract_from_full_url(self):
        """Test extracting ID from full Google Sheets URL."""
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        result = _extract_spreadsheet_id(url)
        assert result == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_extract_from_url_with_gid(self):
        """Test extracting ID from URL with gid parameter."""
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
        result = _extract_spreadsheet_id(url)
        assert result == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_passthrough_raw_id(self):
        """Test that raw spreadsheet ID is returned as-is."""
        spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = _extract_spreadsheet_id(spreadsheet_id)
        assert result == spreadsheet_id

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid Google Sheets URL"):
            _extract_spreadsheet_id("https://invalid.url.com/not-a-sheet")


class TestImportGoogleSheet:
    """Test import_google_sheet tool."""

    @pytest.fixture
    def mock_context(self):
        """Create mock RunContext with SessionContext."""
        session_ctx = SessionContext(
            user_id="test_user_123",
            user_email="test@example.com",
            session_id="test_session_123",
            tier=Tier.PRO,
            permissions=[],
            quota_remaining=100,
        )
        ctx = MagicMock(spec=RunContext)
        ctx.deps = session_ctx
        return ctx

    @pytest.fixture
    def mock_credentials(self):
        """Create mock Google credentials."""
        mock_creds = MagicMock()
        mock_creds.valid = True
        return mock_creds

    @pytest.mark.asyncio
    async def test_import_sheet_no_oauth_token(self, mock_context):
        """Test that AuthenticationError is raised when no OAuth token exists."""
        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=None)

                with pytest.raises(AuthenticationError, match="Google account not connected"):
                    await import_google_sheet(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    )

    @pytest.mark.asyncio
    async def test_import_sheet_success(self, mock_context, mock_credentials):
        """Test successful sheet import."""
        mock_values = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]

        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=mock_credentials)

                with patch("src.tools.google_tools.build") as mock_build:
                    mock_service = MagicMock()
                    mock_build.return_value = mock_service

                    # Mock Sheets API response
                    mock_service.spreadsheets().values().get().execute.return_value = {
                        "values": mock_values,
                        "range": "Sheet1!A1:C3",
                    }

                    result = await import_google_sheet(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    )

                    assert result["headers"] == ["Name", "Age", "City"]
                    assert result["row_count"] == 2
                    assert len(result["rows"]) == 2
                    assert result["rows"][0] == ["Alice", "30", "NYC"]

    @pytest.mark.asyncio
    async def test_import_sheet_empty(self, mock_context, mock_credentials):
        """Test importing empty sheet."""
        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=mock_credentials)

                with patch("src.tools.google_tools.build") as mock_build:
                    mock_service = MagicMock()
                    mock_build.return_value = mock_service

                    mock_service.spreadsheets().values().get().execute.return_value = {
                        "values": [],
                    }

                    result = await import_google_sheet(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    )

                    assert result["row_count"] == 0
                    assert result["headers"] == []
                    assert result["rows"] == []


class TestExportToSheets:
    """Test export_to_sheets tool."""

    @pytest.fixture
    def mock_context(self):
        """Create mock RunContext with SessionContext."""
        session_ctx = SessionContext(
            user_id="test_user_123",
            user_email="test@example.com",
            session_id="test_session_123",
            tier=Tier.PRO,
            permissions=[],
            quota_remaining=100,
        )
        ctx = MagicMock(spec=RunContext)
        ctx.deps = session_ctx
        return ctx

    @pytest.fixture
    def mock_credentials(self):
        """Create mock Google credentials."""
        mock_creds = MagicMock()
        mock_creds.valid = True
        return mock_creds

    @pytest.mark.asyncio
    async def test_export_sheets_no_oauth_token(self, mock_context):
        """Test that AuthenticationError is raised when no OAuth token exists."""
        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=None)

                with pytest.raises(AuthenticationError, match="Google account not connected"):
                    await export_to_sheets(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                        data=[["Alice", "30"], ["Bob", "25"]],
                    )

    @pytest.mark.asyncio
    async def test_export_sheet_success(self, mock_context, mock_credentials):
        """Test successful sheet export."""
        data = [["Alice", "30"], ["Bob", "25"]]
        headers = ["Name", "Age"]

        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=mock_credentials)

                with patch("src.tools.google_tools.build") as mock_build:
                    mock_service = MagicMock()
                    mock_build.return_value = mock_service

                    # Mock Sheets API response
                    mock_service.spreadsheets().values().update().execute.return_value = {
                        "updatedCells": 6,
                        "updatedRows": 3,
                    }

                    result = await export_to_sheets(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                        data=data,
                        headers=headers,
                        include_headers=True,
                    )

                    assert result["updated_cells"] == 6
                    assert result["updated_rows"] == 3

    @pytest.mark.asyncio
    async def test_export_sheet_no_headers(self, mock_context, mock_credentials):
        """Test export without headers."""
        data = [["Alice", "30"], ["Bob", "25"]]

        with patch("src.core.container.get_container"):
            with patch("src.tools.google_tools.OAuthManager") as MockOAuthManager:
                mock_oauth = MockOAuthManager.return_value
                mock_oauth.get_credentials = AsyncMock(return_value=mock_credentials)

                with patch("src.tools.google_tools.build") as mock_build:
                    mock_service = MagicMock()
                    mock_build.return_value = mock_service

                    mock_service.spreadsheets().values().update().execute.return_value = {
                        "updatedCells": 4,
                        "updatedRows": 2,
                    }

                    result = await export_to_sheets(
                        mock_context,
                        spreadsheet_url="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                        data=data,
                        include_headers=False,
                    )

                    assert result["updated_rows"] == 2
