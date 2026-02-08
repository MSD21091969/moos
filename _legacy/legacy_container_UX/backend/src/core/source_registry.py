"""Source registry for data input connectors.

System-only sources with tier gating. Sources are output-only (no inputs).
"""

from src.core.logging import get_logger
from src.models.definitions import OutputSpec, SourceDefinition

logger = get_logger(__name__)


# System sources (read-only, no custom sources in v4.0.0)
_SYSTEM_SOURCES: list[SourceDefinition] = [
    SourceDefinition(
        id="source_file",
        title="File Source",
        description="Read data from local or cloud files (CSV, JSON, Excel, Parquet)",
        source_type="file",
        min_tier="FREE",
        outputs={
            "data": OutputSpec(type="array", description="Loaded file data rows"),
            "metadata": OutputSpec(type="json", description="File metadata (size, modified, etc.)"),
        },
        connection_schema={
            "path": {"type": "string", "required": True, "description": "File path or URL"},
            "format": {"type": "string", "default": "csv", "description": "File format"},
            "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
        },
        created_by="systemadmin",
    ),
    SourceDefinition(
        id="source_api",
        title="API Source",
        description="Fetch data from REST APIs with authentication",
        source_type="api",
        min_tier="FREE",
        outputs={
            "response": OutputSpec(type="json", description="API response data"),
            "status_code": OutputSpec(type="int", description="HTTP status code"),
            "headers": OutputSpec(type="json", description="Response headers"),
        },
        connection_schema={
            "url": {"type": "string", "required": True, "description": "API endpoint URL"},
            "method": {"type": "string", "default": "GET", "description": "HTTP method"},
            "auth_type": {"type": "string", "default": "none", "description": "Authentication type"},
        },
        created_by="systemadmin",
    ),
    SourceDefinition(
        id="source_database",
        title="Database Source",
        description="Query SQL/NoSQL databases (requires PRO tier)",
        source_type="database",
        min_tier="PRO",
        outputs={
            "rows": OutputSpec(type="array", description="Query result rows"),
            "row_count": OutputSpec(type="int", description="Number of rows returned"),
            "columns": OutputSpec(type="array", description="Column names and types"),
        },
        connection_schema={
            "db_type": {"type": "string", "required": True, "description": "Database type"},
            "connection_string": {"type": "string", "required": True, "description": "Connection string"},
            "query": {"type": "string", "required": True, "description": "Query to execute"},
            "timeout": {"type": "int", "default": 30, "description": "Query timeout in seconds"},
        },
        created_by="systemadmin",
    ),
    SourceDefinition(
        id="source_stream",
        title="Stream Source",
        description="Real-time data streams (Kafka, Pub/Sub, WebSocket) — requires ENTERPRISE tier",
        source_type="stream",
        min_tier="ENTERPRISE",
        outputs={
            "messages": OutputSpec(type="array", description="Batch of streamed messages"),
            "offset": OutputSpec(type="int", description="Current stream position"),
            "lag": OutputSpec(type="int", description="Consumer lag (messages behind)"),
        },
        connection_schema={
            "stream_type": {"type": "string", "required": True, "description": "Stream type"},
            "endpoint": {"type": "string", "required": True, "description": "Stream endpoint URL"},
            "topic": {"type": "string", "required": True, "description": "Topic/channel name"},
            "consumer_group": {"type": "string", "default": "default", "description": "Consumer group"},
            "batch_size": {"type": "int", "default": 100, "description": "Messages per batch"},
        },
        created_by="systemadmin",
    ),
]


class SourceRegistry:
    """Registry for source connectors (system-only in v4.0.0)."""

    def __init__(self):
        """Initialize registry with system sources."""
        self._sources = {s.id: s for s in _SYSTEM_SOURCES}
        logger.info("Initialized source registry", extra={"source_count": len(self._sources)})

    def get_source(self, source_id: str) -> SourceDefinition | None:
        """Get source definition by ID.
        
        Args:
            source_id: Source definition ID
            
        Returns:
            SourceDefinition or None if not found
        """
        return self._sources.get(source_id)

    def get_available_sources(self, user_tier: str) -> list[SourceDefinition]:
        """Get sources available to user based on tier.
        
        Args:
            user_tier: User tier (free/pro/enterprise)
            
        Returns:
            List of accessible sources
        """
        tier_order = {"free": 0, "pro": 1, "enterprise": 2}
        user_tier_level = tier_order.get(user_tier.lower(), 0)

        available = []
        for source in self._sources.values():
            min_tier_level = tier_order.get(source.min_tier.lower(), 0)
            if user_tier_level >= min_tier_level:
                available.append(source)

        logger.info(
            "Listed available sources",
            extra={
                "user_tier": user_tier,
                "available_count": len(available),
                "total_count": len(self._sources)
            }
        )
        return available

    def list_all_sources(self) -> list[SourceDefinition]:
        """List all system sources (admin only).
        
        Returns:
            All source definitions
        """
        return list(self._sources.values())


# Global registry instance
_registry: SourceRegistry | None = None


def get_source_registry() -> SourceRegistry:
    """Get global source registry instance.
    
    Returns:
        SourceRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry
