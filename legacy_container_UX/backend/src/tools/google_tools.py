"""Google Workspace data tools (Extract and Load)."""

from typing import Any

from googleapiclient.discovery import build
from pydantic_ai import RunContext

from src.core.container import get_container
from src.core.exceptions import AuthenticationError, ValidationError
from src.core.oauth_manager import OAuthManager
from src.core.tool_registry import ToolCategory, get_tool_registry
from src.core.tool_wrapper import enforce_permissions
from src.models.context import SessionContext

registry = get_tool_registry()


@registry.register(
    name="import_google_sheet",
    description="Import data from Google Sheets into session",
    category=ToolCategory.EXTRACT,
    required_tier="PRO",
    quota_cost=5,
    tags=["extract", "google", "sheets", "import", "etl"],
)
@enforce_permissions("import_google_sheet")
async def import_google_sheet(
    ctx: RunContext[SessionContext],
    spreadsheet_url: str,
    sheet_name: str | None = None,
    range_notation: str | None = None,
) -> dict:
    """
    Import data from Google Sheets.

    Args:
        ctx: Session context
        spreadsheet_url: Google Sheets URL or spreadsheet ID
        sheet_name: Optional sheet name (default: first sheet)
        range_notation: Optional range (e.g., "A1:D10", default: all data)

    Returns:
        {
            "rows": [[cell1, cell2, ...], ...],
            "headers": [col1, col2, ...],
            "row_count": int,
            "spreadsheet_id": str,
            "sheet_name": str
        }

    Raises:
        AuthenticationError: If user hasn't authorized Google OAuth
        ValidationError: If spreadsheet not found or invalid
    """

    # Extract spreadsheet ID from URL
    spreadsheet_id = _extract_spreadsheet_id(spreadsheet_url)

    # Get OAuth credentials
    container = get_container()
    oauth_manager = OAuthManager(container.firestore_client)
    credentials = await oauth_manager.get_credentials(
        user_id=ctx.deps.user_id,
        provider="google",
    )

    if not credentials:
        raise AuthenticationError(
            "Google account not connected. Please authorize via /oauth/google"
        )

    # Build Sheets API service
    service = build("sheets", "v4", credentials=credentials)

    # Determine range
    if range_notation:
        full_range = f"{sheet_name}!{range_notation}" if sheet_name else range_notation
    else:
        full_range = sheet_name if sheet_name else ""

    try:
        # Fetch data
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=full_range)
            .execute()
        )

        rows = result.get("values", [])

        if not rows:
            return {
                "rows": [],
                "headers": [],
                "row_count": 0,
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name or "Unknown",
            }

        # First row as headers
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        # Store in session (optional - for session history)
        # TODO: Store in /sessions/{id}/imported_data/{import_id}

        return {
            "rows": data_rows,
            "headers": headers,
            "row_count": len(data_rows),
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name or result.get("range", "").split("!")[0],
        }

    except Exception as e:
        raise ValidationError(f"Failed to import sheet: {str(e)}")


@registry.register(
    name="export_to_sheets",
    description="Export session data to Google Sheets",
    category=ToolCategory.LOAD,
    required_tier="PRO",
    quota_cost=5,
    tags=["load", "google", "sheets", "export", "etl"],
)
@enforce_permissions("export_to_sheets")
async def export_to_sheets(
    ctx: RunContext[SessionContext],
    spreadsheet_url: str,
    data: list[list[Any]],
    sheet_name: str | None = None,
    start_cell: str = "A1",
    include_headers: bool = True,
    headers: list[str] | None = None,
) -> dict:
    """
    Export data to Google Sheets.

    Args:
        ctx: Session context
        spreadsheet_url: Google Sheets URL or spreadsheet ID
        data: 2D array of data to write [[row1], [row2], ...]
        sheet_name: Optional sheet name (default: first sheet)
        start_cell: Starting cell (e.g., "A1")
        include_headers: Whether to prepend headers
        headers: Optional header row (if include_headers=True)

    Returns:
        {
            "updated_cells": int,
            "updated_rows": int,
            "spreadsheet_id": str,
            "sheet_name": str
        }

    Raises:
        UnauthorizedError: If user hasn't authorized Google OAuth
        ValidationError: If export fails
    """

    # Extract spreadsheet ID from URL
    spreadsheet_id = _extract_spreadsheet_id(spreadsheet_url)

    # Get OAuth credentials
    container = get_container()
    oauth_manager = OAuthManager(container.firestore_client)
    credentials = await oauth_manager.get_credentials(
        user_id=ctx.deps.user_id,
        provider="google",
    )

    if not credentials:
        raise AuthenticationError(
            "Google account not connected. Please authorize via /oauth/google"
        )

    # Build Sheets API service
    service = build("sheets", "v4", credentials=credentials)

    # Prepare data
    values_to_write = []
    if include_headers and headers:
        values_to_write.append(headers)
    values_to_write.extend(data)

    # Determine range
    full_range = f"{sheet_name}!{start_cell}" if sheet_name else start_cell

    try:
        # Write data
        body = {"values": values_to_write}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=full_range,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )

        return {
            "updated_cells": result.get("updatedCells", 0),
            "updated_rows": result.get("updatedRows", 0),
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name or "Unknown",
        }

    except Exception as e:
        raise ValidationError(f"Failed to export to sheet: {str(e)}")


def _extract_spreadsheet_id(url_or_id: str) -> str:
    """
    Extract spreadsheet ID from URL or return as-is if already ID.

    Args:
        url_or_id: Google Sheets URL or spreadsheet ID

    Returns:
        Spreadsheet ID

    Examples:
        >>> _extract_spreadsheet_id("https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit")
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        >>> _extract_spreadsheet_id("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    """
    if url_or_id.startswith("http"):
        # Extract from URL: /spreadsheets/d/{id}/
        parts = url_or_id.split("/")
        if "d" in parts:
            idx = parts.index("d")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        raise ValidationError("Invalid Google Sheets URL")
    return url_or_id
