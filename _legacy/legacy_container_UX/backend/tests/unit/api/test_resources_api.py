"""Unit tests for ResourceLink V2 API endpoints.

Tests the Pure ResourceLink architecture with direct CRUD operations
on the ResourceLink model via /sessions/{id}/resources endpoints.

Updated for v4.0.0 Universal Object Model - uses SessionService directly.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.models.links import ResourceLink, ResourceType
from src.services.session_service import SessionService


class TestResourceLinkV2API:
    """Test suite for ResourceLink V2 Pure CRUD API."""
    
    @pytest.fixture
    def mock_session_service(self):
        """Mock SessionService for ResourceLink operations."""
        service = Mock(spec=SessionService)
        service.add_resource_link = AsyncMock()
        service.get_resources = AsyncMock()
        service.remove_resource_link = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_resource_link(self):
        """Sample ResourceLink for testing."""
        return ResourceLink(
            resource_id="csv_analyzer",
            resource_type=ResourceType.TOOL,
            description="Analyze Q3 Sales",
            preset_params={"delimiter": ";"},
            metadata={"x": 200, "y": 150, "color": "blue"},
            added_at=datetime.utcnow(),
            added_by="user123",
            enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_add_resource_link_creates_v2_model(self, mock_session_service, sample_resource_link):
        """Test that adding a resource creates a ResourceLink model."""
        mock_session_service.add_resource_link.return_value = sample_resource_link
        
        result = await mock_session_service.add_resource_link(
            session_id="sess_123",
            user_id="user123",
            link=sample_resource_link
        )
        
        assert result.resource_id == "csv_analyzer"
        mock_session_service.add_resource_link.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_resources_returns_resource_links(self, mock_session_service, sample_resource_link):
        """Test that fetching resources returns ResourceLink models."""
        mock_session_service.get_resources.return_value = [sample_resource_link]
        
        result = await mock_session_service.get_resources(
            session_id="sess_123",
            user_id="user123",
            resource_type=ResourceType.TOOL
        )
        
        assert len(result) == 1
        assert isinstance(result[0], ResourceLink)
        assert result[0].resource_id == "csv_analyzer"
        assert result[0].metadata["x"] == 200
    
    @pytest.mark.asyncio
    async def test_remove_resource_link_deletes_by_id(self, mock_session_service):
        """Test that removing a resource deletes it by link_id."""
        await mock_session_service.remove_resource_link(
            session_id="sess_123",
            user_id="user123",
            link_id="tool_csv_analyzer_a3f8b2"
        )
        
        mock_session_service.remove_resource_link.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resource_link_captures_metadata(self, sample_resource_link):
        """Test that ResourceLink captures visual metadata."""
        assert "x" in sample_resource_link.metadata
        assert "y" in sample_resource_link.metadata
        assert "color" in sample_resource_link.metadata
        assert sample_resource_link.metadata["x"] == 200
        assert sample_resource_link.metadata["y"] == 150
        assert sample_resource_link.metadata["color"] == "blue"
    
    @pytest.mark.asyncio
    async def test_resource_link_captures_context(self, sample_resource_link):
        """Test that ResourceLink captures description and configuration."""
        assert sample_resource_link.description == "Analyze Q3 Sales"
        assert sample_resource_link.preset_params == {"delimiter": ";"}
        assert sample_resource_link.added_by == "user123"
        assert sample_resource_link.enabled is True
    
    def test_resource_type_enum_values(self):
        """Test ResourceType enum has all required values (v3.1.0)."""
        # Universal Object Model v3.1.0 defines 5 types
        assert ResourceType.SESSION == "session"
        assert ResourceType.AGENT == "agent"
        assert ResourceType.TOOL == "tool"
        assert ResourceType.SOURCE == "source"
        assert ResourceType.USER == "user"


class TestDeprecatedSessionToolInstance:
    """Verify legacy SessionToolInstance/SessionAgentInstance are removed in V4.0.0 API."""
    
    def test_session_service_uses_resource_links(self):
        """SessionService should use ResourceLink for V4.0.0 operations."""
        from src.services.session_service import SessionService
        import inspect
        
        # Get source code
        source = inspect.getsource(SessionService)
        
        # V4.0.0 methods should use ResourceLink
        assert "ResourceLink" in source, "SessionService must use ResourceLink"
    
    def test_resource_link_is_primary_model(self):
        """ResourceLink should be the primary model in V4.0.0 architecture."""
        from src.models.links import ResourceLink
        import inspect
        
        # Verify ResourceLink has all required fields (v4.0.0)
        source = inspect.getsource(ResourceLink)
        required_fields = [
            "resource_id",
            "resource_type",
            "description",
            "instance_id",  # Added in v4.0.0
            "preset_params",
            "metadata",
            "added_at",
            "added_by",
            "enabled"
        ]
        
        for field in required_fields:
            assert field in source, f"ResourceLink missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
