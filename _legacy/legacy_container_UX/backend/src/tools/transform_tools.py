"""Data transformation and conversion tools."""

import json
from typing import Any

from pydantic_ai import RunContext

from src.core.tool_registry import ToolCategory, get_tool_registry
from src.core.tool_wrapper import enforce_permissions
from src.models.context import SessionContext

registry = get_tool_registry()


@registry.register(
    name="convert_format",
    description="Convert data between JSON, CSV, XML formats",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="PRO",
    quota_cost=3,
    tags=["convert", "format", "json", "csv"],
)
@enforce_permissions("convert_format")
async def convert_format(
    ctx: RunContext[SessionContext],
    data: str,
    from_format: str,
    to_format: str,
) -> dict:
    """
    Convert data between formats.

    Args:
        ctx: Session context
        data: Input data as string
        from_format: Source format (json, csv)
        to_format: Target format (json, csv)

    Returns:
        {"result": converted_data, "from": format, "to": format}
    """
    # Simple JSON conversions only for now
    if from_format == "json" and to_format == "csv":
        parsed = json.loads(data)
        if isinstance(parsed, list) and len(parsed) > 0:
            keys = parsed[0].keys()
            csv = ",".join(keys) + "\n"
            for item in parsed:
                csv += ",".join(str(item.get(k, "")) for k in keys) + "\n"
            return {"result": csv, "from": from_format, "to": to_format}

    return {"error": f"Conversion {from_format} → {to_format} not supported"}


@registry.register(
    name="merge_data",
    description="Merge multiple JSON objects or arrays",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="PRO",
    quota_cost=2,
    tags=["merge", "combine", "json"],
)
@enforce_permissions("merge_data")
async def merge_data(
    ctx: RunContext[SessionContext],
    data_list: list[str],
    strategy: str = "concat",
) -> dict:
    """
    Merge multiple data sources.

    Args:
        ctx: Session context
        data_list: List of JSON strings
        strategy: Merge strategy (concat, deep_merge)

    Returns:
        {"result": merged_data}
    """
    parsed = [json.loads(d) for d in data_list]

    if strategy == "concat":
        # Concatenate arrays
        result: list[Any] = []
        for item in parsed:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return {"result": result, "strategy": strategy}

    elif strategy == "deep_merge":
        # Merge objects
        merged: dict[str, Any] = {}
        for item in parsed:
            if isinstance(item, dict):
                merged.update(item)
        return {"result": merged, "strategy": strategy}

    return {"error": f"Strategy {strategy} not supported"}


@registry.register(
    name="clean_data",
    description="Clean and normalize data (trim, dedupe, normalize)",
    category=ToolCategory.DATA_ANALYSIS,
    required_tier="FREE",
    quota_cost=2,
    tags=["clean", "normalize", "dedupe"],
)
@enforce_permissions("clean_data")
async def clean_data(
    ctx: RunContext[SessionContext],
    data: list[dict[str, Any]],
    operations: list[str],
) -> dict:
    """
    Clean and normalize data.

    Args:
        ctx: Session context
        data: List of objects
        operations: Operations to apply (trim, dedupe, lowercase)

    Returns:
        {"result": cleaned_data, "operations": list}
    """
    result = data.copy()

    if "dedupe" in operations:
        # Remove duplicates (convert to JSON for comparison)
        seen = set()
        deduped = []
        for item in result:
            key = json.dumps(item, sort_keys=True)
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        result = deduped

    if "trim" in operations:
        # Trim string values
        for item in result:
            for key, value in item.items():
                if isinstance(value, str):
                    item[key] = value.strip()

    if "lowercase" in operations:
        # Lowercase string values
        for item in result:
            for key, value in item.items():
                if isinstance(value, str):
                    item[key] = value.lower()

    return {"result": result, "operations": operations, "count": len(result)}
