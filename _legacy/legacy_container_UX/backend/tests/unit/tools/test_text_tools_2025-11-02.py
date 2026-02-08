"""Unit tests for text_tools.py"""

import pytest
from pydantic_ai import RunContext

from src.models.context import SessionContext
from src.tools.text_tools import count_words, extract_text, replace_text, search_text


@pytest.fixture
def session_ctx():
    """Create test session context."""
    return SessionContext(
        user_id="user_test",
        session_id="sess_test",
        user_email="test@test.com",
        tier="PRO",
        permissions=["search_text", "replace_text", "extract_text", "count_words"],
        quota_remaining=100.0,
    )


@pytest.fixture
def run_ctx(session_ctx):
    """Create RunContext for tools."""
    from unittest.mock import MagicMock

    # Create a mock RunContext that has deps attribute
    ctx = MagicMock(spec=RunContext)
    ctx.deps = session_ctx
    ctx.retry = 0
    return ctx


class TestSearchText:
    """Test search_text tool."""

    @pytest.mark.asyncio
    async def test_search_finds_matches(self, run_ctx):
        """Test basic text search."""
        text = "The quick brown fox jumps over the lazy dog"
        pattern = r"\bthe\b"

        result = await search_text(run_ctx, text, pattern, case_sensitive=False)

        assert result["count"] == 2
        assert len(result["matches"]) == 2
        assert result["pattern"] == pattern

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, run_ctx):
        """Test case-insensitive search."""
        text = "Python PYTHON python PyThOn"
        pattern = r"python"

        result = await search_text(run_ctx, text, pattern, case_sensitive=False)

        assert result["count"] == 4

    @pytest.mark.asyncio
    async def test_search_no_matches(self, run_ctx):
        """Test search with no matches."""
        text = "Hello world"
        pattern = r"xyz"

        result = await search_text(run_ctx, text, pattern)

        assert result["count"] == 0
        assert result["matches"] == []

    @pytest.mark.asyncio
    async def test_search_complex_pattern(self, run_ctx):
        """Test search with complex regex."""
        text = "Email: test@example.com and admin@test.org"
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        result = await search_text(run_ctx, text, pattern)

        assert result["count"] == 2
        assert "test@example.com" in result["matches"]
        assert "admin@test.org" in result["matches"]


class TestReplaceText:
    """Test replace_text tool."""

    @pytest.mark.asyncio
    async def test_replace_all_occurrences(self, run_ctx):
        """Test replacing all occurrences."""
        text = "foo bar foo baz foo"
        pattern = r"foo"
        replacement = "qux"

        result = await replace_text(run_ctx, text, pattern, replacement)

        assert result["replacements"] == 3
        assert result["result"] == "qux bar qux baz qux"

    @pytest.mark.asyncio
    async def test_replace_limited_count(self, run_ctx):
        """Test limited replacement count."""
        text = "foo foo foo foo"
        pattern = r"foo"
        replacement = "bar"

        result = await replace_text(run_ctx, text, pattern, replacement, count=2)

        assert result["replacements"] == 2
        assert result["result"] == "bar bar foo foo"

    @pytest.mark.asyncio
    async def test_replace_with_regex_groups(self, run_ctx):
        """Test replacement with capture groups."""
        text = "2025-11-02"
        pattern = r"(\d{4})-(\d{2})-(\d{2})"
        replacement = r"\3/\2/\1"

        result = await replace_text(run_ctx, text, pattern, replacement)

        assert result["result"] == "02/11/2025"

    @pytest.mark.asyncio
    async def test_replace_no_matches(self, run_ctx):
        """Test replacement with no matches."""
        text = "Hello world"
        pattern = r"xyz"
        replacement = "abc"

        result = await replace_text(run_ctx, text, pattern, replacement)

        assert result["replacements"] == 0
        assert result["result"] == text


class TestExtractText:
    """Test extract_text tool."""

    @pytest.mark.asyncio
    async def test_extract_named_groups(self, run_ctx):
        """Test extraction with named groups."""
        text = "User: alice (age: 30), User: bob (age: 25)"
        pattern = r"User: (?P<name>\w+) \(age: (?P<age>\d+)\)"

        result = await extract_text(run_ctx, text, pattern)

        assert result["count"] == 2
        assert len(result["matches"]) == 2
        assert result["matches"][0] == {"name": "alice", "age": "30"}
        assert result["matches"][1] == {"name": "bob", "age": "25"}

    @pytest.mark.asyncio
    async def test_extract_multiple_matches(self, run_ctx):
        """Test extracting multiple matches."""
        text = "Price: $10, Price: $20, Price: $30"
        pattern = r"Price: \$(?P<amount>\d+)"

        result = await extract_text(run_ctx, text, pattern)

        assert result["count"] == 3
        amounts = [m["amount"] for m in result["matches"]]
        assert amounts == ["10", "20", "30"]

    @pytest.mark.asyncio
    async def test_extract_no_matches(self, run_ctx):
        """Test extraction with no matches."""
        text = "No prices here"
        pattern = r"Price: \$(?P<amount>\d+)"

        result = await extract_text(run_ctx, text, pattern)

        assert result["count"] == 0
        assert result["matches"] == []

    @pytest.mark.asyncio
    async def test_extract_email_components(self, run_ctx):
        """Test extracting email components."""
        text = "Email: alice@example.com"
        # Pattern captures just the email parts, not the prefix
        pattern = r"(?P<user>[a-z]+)@(?P<domain>[a-z]+)\.(?P<tld>[a-z]+)"

        result = await extract_text(run_ctx, text, pattern)

        assert result["count"] == 1
        assert result["matches"][0]["user"] == "alice"
        assert result["matches"][0]["domain"] == "example"
        assert result["matches"][0]["tld"] == "com"


class TestCountWords:
    """Test count_words tool."""

    @pytest.mark.asyncio
    async def test_count_basic(self, run_ctx):
        """Test basic word counting."""
        text = "The quick brown fox"

        result = await count_words(run_ctx, text)

        assert result["words"] == 4
        assert result["characters"] == 19
        assert result["lines"] == 1

    @pytest.mark.asyncio
    async def test_count_multiline(self, run_ctx):
        """Test counting in multiline text."""
        text = "Line 1\nLine 2\nLine 3"

        result = await count_words(run_ctx, text)

        assert result["words"] == 6
        assert result["lines"] == 3

    @pytest.mark.asyncio
    async def test_count_empty_text(self, run_ctx):
        """Test counting empty text."""
        text = ""

        result = await count_words(run_ctx, text)

        assert result["words"] == 0
        assert result["characters"] == 0
        assert result["lines"] == 1

    @pytest.mark.asyncio
    async def test_count_whitespace(self, run_ctx):
        """Test counting with extra whitespace."""
        text = "word1   word2\n\nword3"

        result = await count_words(run_ctx, text)

        assert result["words"] == 3
        assert result["lines"] == 3
