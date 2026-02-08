"""Initialize and register all tools."""

import importlib
from typing import Sequence

from src.core.logging import get_logger
from src.core.tool_registry import get_tool_registry

logger = get_logger(__name__)


def register_all_tools():
    """
    Register all available tools.

    Import all tool modules to trigger @registry.register decorators.
    This populates the global tool registry.
    """
    # Import modules to trigger registration. Load each module individually so
    # a missing optional dependency does not prevent other tools from
    # registering.
    modules: Sequence[str] = (
        "src.tools.export_tools",
        "src.tools.text_tools",
        "src.tools.transform_tools",
        "src.tools.filesystem_tools",
        "src.tools.google_tools",
    )

    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            logger.warning(
                "Tool module not loaded", extra={"module_name": module_name, "error": str(exc)}
            )

    # Registry is populated by decorators
    registry = get_tool_registry()

    return registry


def get_registered_tool_count() -> int:
    """Get count of registered tools."""
    registry = get_tool_registry()
    return len(registry._tools)


def print_tool_summary():
    """Print summary of all registered tools."""
    registry = get_tool_registry()

    logger.info("=" * 60)
    logger.info("REGISTERED TOOLS SUMMARY")
    logger.info("=" * 60)

    categories = registry.get_all_categories()

    for category in categories:
        tools = [t for t in registry._tools.values() if t.category == category]
        logger.info(
            "Tool category", extra={"category": category.value.upper(), "count": len(tools)}
        )

        for tool in tools:
            logger.info(
                "Tool details",
                extra={
                    "name": tool.name,
                    "description": tool.description,
                    "required_tier": tool.required_tier,
                    "quota_cost": tool.quota_cost,
                    "tags": ", ".join(tool.tags) if tool.tags else None,
                },
            )

    logger.info("=" * 60)
    logger.info("Tool registry summary", extra={"total_tools": len(registry._tools)})
    logger.info("=" * 60)


# Auto-register on import
register_all_tools()
