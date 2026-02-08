"""Data export and serialization tools."""

import json
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext

from src.core.tool_registry import ToolCategory, get_tool_registry
from src.core.tool_wrapper import enforce_permissions
from src.models.context import SessionContext

registry = get_tool_registry()


@registry.register(
    name="export_json",
    description="Export data to JSON file",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=3,
    tags=["export", "json", "save"],
)
@enforce_permissions("export_json")
async def export_json(
    ctx: RunContext[SessionContext],
    data: Any,
    file_path: str,
    indent: int = 2,
) -> dict:
    """
    Export data to JSON file.

    Args:
        ctx: Session context
        data: Data to export
        file_path: Output file path
        indent: JSON indentation (default: 2)

    Returns:
        {"file": path, "size": bytes}
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

    size = path.stat().st_size
    return {"file": str(path), "size": size}


@registry.register(
    name="export_csv",
    description="Export data to CSV file",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="PRO",
    quota_cost=3,
    tags=["export", "csv", "save"],
)
@enforce_permissions("export_csv")
async def export_csv(
    ctx: RunContext[SessionContext],
    data: list[dict[str, Any]],
    file_path: str,
) -> dict:
    """
    Export data to CSV file.

    Args:
        ctx: Session context
        data: List of objects (rows)
        file_path: Output file path

    Returns:
        {"file": path, "rows": count}
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        return {"error": "No data to export"}

    keys = data[0].keys()

    with open(path, "w", encoding="utf-8") as f:
        # Header
        f.write(",".join(keys) + "\n")
        # Rows
        for item in data:
            f.write(",".join(str(item.get(k, "")) for k in keys) + "\n")

    return {"file": str(path), "rows": len(data)}


@registry.register(
    name="format_output",
    description="Format data for display (table, list, tree)",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=1,
    tags=["format", "display", "table"],
)
@enforce_permissions("format_output")
async def format_output(
    ctx: RunContext[SessionContext],
    data: list[dict[str, Any]],
    style: str = "table",
) -> dict:
    """
    Format data for display.

    Args:
        ctx: Session context
        data: Data to format
        style: Display style (table, list, json)

    Returns:
        {"formatted": string, "style": style}
    """
    if style == "json":
        return {"formatted": json.dumps(data, indent=2), "style": style}

    elif style == "table":
        if not data:
            return {"formatted": "No data", "style": style}

        keys = data[0].keys()
        # Simple table format
        header = " | ".join(keys)
        separator = "-" * len(header)
        rows = [" | ".join(str(item.get(k, "")) for k in keys) for item in data]
        table = "\n".join([header, separator] + rows)
        return {"formatted": table, "style": style}

    elif style == "list":
        formatted = "\n".join(f"- {json.dumps(item)}" for item in data)
        return {"formatted": formatted, "style": style}

    return {"error": f"Style {style} not supported"}
