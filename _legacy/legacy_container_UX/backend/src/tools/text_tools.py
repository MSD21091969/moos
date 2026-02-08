"""Text processing and manipulation tools."""

import re
from typing import Optional

from pydantic_ai import RunContext

from src.core.tool_registry import ToolCategory, get_tool_registry
from src.core.tool_wrapper import enforce_permissions
from src.models.context import SessionContext

registry = get_tool_registry()


@registry.register(
    name="search_text",
    description="Search for patterns in text using regex",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=1,
    tags=["text", "search", "regex", "find"],
)
@enforce_permissions("search_text")
async def search_text(
    ctx: RunContext[SessionContext],
    text: str,
    pattern: str,
    case_sensitive: bool = True,
) -> dict:
    """
    Search text using regex pattern.

    Args:
        ctx: Session context
        text: Text to search
        pattern: Regex pattern
        case_sensitive: Case sensitive search (default: True)

    Returns:
        {"matches": [list of matches], "count": int}
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    matches = re.findall(pattern, text, flags)
    return {"matches": matches, "count": len(matches), "pattern": pattern}


@registry.register(
    name="replace_text",
    description="Replace text patterns using regex",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="PRO",
    quota_cost=2,
    tags=["text", "replace", "regex", "edit"],
)
@enforce_permissions("replace_text")
async def replace_text(
    ctx: RunContext[SessionContext],
    text: str,
    pattern: str,
    replacement: str,
    count: int = 0,
) -> dict:
    """
    Replace text using regex pattern.

    Args:
        ctx: Session context
        text: Original text
        pattern: Regex pattern to find
        replacement: Replacement text
        count: Max replacements (0 = all)

    Returns:
        {"result": modified_text, "replacements": int}
    """
    result = re.sub(pattern, replacement, text, count=count)
    replacements = len(re.findall(pattern, text))
    if count > 0:
        replacements = min(replacements, count)
    return {"result": result, "replacements": replacements}


@registry.register(
    name="extract_text",
    description="Extract structured data from text",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=2,
    tags=["text", "extract", "parse", "regex"],
)
@enforce_permissions("extract_text")
async def extract_text(
    ctx: RunContext[SessionContext],
    text: str,
    pattern: str,
    group_names: Optional[list[str]] = None,
) -> dict:
    """
    Extract structured data using named groups.

    Args:
        ctx: Session context
        text: Text to parse
        pattern: Regex with named groups
        group_names: Expected group names

    Returns:
        {"matches": [{"group": value}], "count": int}
    """
    matches = []
    for match in re.finditer(pattern, text):
        matches.append(match.groupdict())
    return {"matches": matches, "count": len(matches)}


@registry.register(
    name="count_words",
    description="Count words and characters in text",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=1,
    tags=["text", "count", "statistics"],
)
@enforce_permissions("count_words")
async def count_words(ctx: RunContext[SessionContext], text: str) -> dict:
    """
    Count words, characters, lines in text.

    Args:
        ctx: Session context
        text: Text to analyze

    Returns:
        {"words": int, "chars": int, "lines": int}
    """
    words = len(text.split())
    chars = len(text)
    lines = text.count("\n") + 1
    return {"words": words, "characters": chars, "lines": lines}
