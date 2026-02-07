"""
Test suite for data export tools.

Tests cover:
- export_json: JSON file export
- export_csv: CSV file export
- format_output: Display formatting
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pydantic_ai import RunContext

from src.models.context import SessionContext
from src.models.permissions import Tier
from src.tools.export_tools import (
    export_json,
    export_csv,
    format_output,
)


@pytest.fixture
def session_ctx():
    """Create SessionContext for tool testing."""
    return SessionContext(
        session_id="sess_test123456",
        user_id="user_test",
        user_email="test@example.com",
        tier=Tier.PRO,
        permissions=["export_json", "export_csv", "format_output"],
        quota_remaining=100,
    )


@pytest.fixture
def run_ctx(session_ctx):
    """Create RunContext with SessionContext."""
    ctx = MagicMock(spec=RunContext)
    ctx.deps = session_ctx
    return ctx


@pytest.fixture
def temp_export_dir(tmp_path):
    """Create temporary directory for export tests."""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir


class TestExportJson:
    """Test export_json tool."""

    @pytest.mark.asyncio
    async def test_export_json_basic(self, run_ctx, temp_export_dir):
        """
        TEST: Export data to JSON file
        PURPOSE: Validate basic JSON export
        EXPECTED: File created with correct content
        """
        data = {"name": "Alice", "age": 30, "items": [1, 2, 3]}
        file_path = str(temp_export_dir / "output.json")

        result = await export_json(run_ctx, data, file_path)

        assert result["file"] == file_path
        assert result["size"] > 0

        # Verify file content
        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data

    @pytest.mark.asyncio
    async def test_export_json_creates_directories(self, run_ctx, temp_export_dir):
        """
        TEST: Create parent directories if missing
        PURPOSE: Validate directory creation
        EXPECTED: Nested directories created
        """
        data = {"test": "value"}
        file_path = str(temp_export_dir / "nested" / "dir" / "output.json")

        result = await export_json(run_ctx, data, file_path)

        assert Path(result["file"]).exists()
        assert Path(result["file"]).parent.exists()

    @pytest.mark.asyncio
    async def test_export_json_custom_indent(self, run_ctx, temp_export_dir):
        """
        TEST: Custom indentation
        PURPOSE: Validate indent parameter
        EXPECTED: JSON formatted with specified indent
        """
        data = {"a": 1, "b": 2}
        file_path = str(temp_export_dir / "indented.json")

        await export_json(run_ctx, data, file_path, indent=4)

        # Check file content has correct indentation
        with open(file_path, "r") as f:
            content = f.read()
        assert "    " in content  # 4-space indent


class TestExportCsv:
    """Test export_csv tool."""

    @pytest.mark.asyncio
    async def test_export_csv_basic(self, run_ctx, temp_export_dir):
        """
        TEST: Export list of dicts to CSV
        PURPOSE: Validate basic CSV export
        EXPECTED: CSV file with headers and rows
        """
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        file_path = str(temp_export_dir / "output.csv")

        result = await export_csv(run_ctx, data, file_path)

        assert result["file"] == file_path
        assert result["rows"] == 2

        # Verify CSV content
        with open(file_path, "r") as f:
            lines = f.readlines()
        assert "name,age" in lines[0]
        assert "Alice,30" in lines[1]

    @pytest.mark.asyncio
    async def test_export_csv_empty_data(self, run_ctx, temp_export_dir):
        """
        TEST: Export empty list
        PURPOSE: Validate error handling
        EXPECTED: Error returned
        """
        data = []
        file_path = str(temp_export_dir / "empty.csv")

        result = await export_csv(run_ctx, data, file_path)

        assert "error" in result
        assert "No data" in result["error"]

    @pytest.mark.asyncio
    async def test_export_csv_missing_keys(self, run_ctx, temp_export_dir):
        """
        TEST: Objects with missing keys
        PURPOSE: Validate handling of incomplete data
        EXPECTED: Empty strings for missing values
        """
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob"},  # Missing age
        ]
        file_path = str(temp_export_dir / "partial.csv")

        result = await export_csv(run_ctx, data, file_path)

        assert result["rows"] == 2

        with open(file_path, "r") as f:
            lines = f.readlines()
        assert "Bob," in lines[2]  # Empty age field


class TestFormatOutput:
    """Test format_output tool."""

    @pytest.mark.asyncio
    async def test_format_as_json(self, run_ctx):
        """
        TEST: Format as JSON string
        PURPOSE: Validate JSON formatting
        EXPECTED: Pretty-printed JSON
        """
        data = [{"name": "Alice", "age": 30}]

        result = await format_output(run_ctx, data, style="json")

        assert result["style"] == "json"
        assert "Alice" in result["formatted"]
        # Verify it's valid JSON
        parsed = json.loads(result["formatted"])
        assert parsed == data

    @pytest.mark.asyncio
    async def test_format_as_table(self, run_ctx):
        """
        TEST: Format as ASCII table
        PURPOSE: Validate table formatting
        EXPECTED: Table with headers and rows
        """
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        result = await format_output(run_ctx, data, style="table")

        assert result["style"] == "table"
        formatted = result["formatted"]
        assert "name" in formatted
        assert "age" in formatted
        assert "Alice" in formatted
        assert "Bob" in formatted
        assert "|" in formatted  # Table separator

    @pytest.mark.asyncio
    async def test_format_as_list(self, run_ctx):
        """
        TEST: Format as bulleted list
        PURPOSE: Validate list formatting
        EXPECTED: Each item on new line with bullet
        """
        data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

        result = await format_output(run_ctx, data, style="list")

        assert result["style"] == "list"
        formatted = result["formatted"]
        assert formatted.count("- ") == 2  # Two bullets
        assert "Item 1" in formatted
        assert "Item 2" in formatted

    @pytest.mark.asyncio
    async def test_format_empty_data(self, run_ctx):
        """
        TEST: Format empty dataset
        PURPOSE: Validate edge case
        EXPECTED: Graceful handling
        """
        data = []

        result = await format_output(run_ctx, data, style="table")

        assert result["style"] == "table"
        assert "No data" in result["formatted"]

    @pytest.mark.asyncio
    async def test_format_unsupported_style(self, run_ctx):
        """
        TEST: Unsupported format style
        PURPOSE: Validate error handling
        EXPECTED: Error message
        """
        data = [{"test": "value"}]

        result = await format_output(run_ctx, data, style="xml")

        assert "error" in result
        assert "not supported" in result["error"]
