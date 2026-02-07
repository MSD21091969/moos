"""Depth guardrail tests for ContainerService.add_resource."""

from datetime import datetime

import pytest

from src.core.exceptions import DepthLimitError, InvalidContainmentError
from src.models.links import ResourceLink, ResourceType
from src.services.container_service import ContainerService


@pytest.fixture
def container_service(mock_firestore):
    """ContainerService with mock Firestore."""
    return ContainerService(mock_firestore)


async def _create_parent(mock_firestore, collection: str, parent_id: str, depth: int, owner: str = "user_1"):
    await (
        mock_firestore.collection(collection)
        .document(parent_id)
        .set(
            {
                "instance_id": parent_id,
                "definition_id": f"{collection}_def",
                "parent_id": "usersession_root",
                "depth": depth,
                "acl": {"owner": owner, "editors": [], "viewers": []},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": owner,
            }
        )
    )


class TestContainerServiceDepth:
    @pytest.mark.asyncio
    async def test_add_resource_blocks_depth_overflow(self, container_service, mock_firestore):
        """FREE tier cannot add non-source child when new_depth exceeds tier limit."""

        parent_id = "sess_parent"
        await _create_parent(mock_firestore, "sessions", parent_id, depth=2, owner="user_123")

        link = ResourceLink(
            resource_id="agent_def_deep",
            resource_type=ResourceType.AGENT,
            added_at=datetime.utcnow(),
            added_by="user_123",
            enabled=True,
        )

        with pytest.raises(DepthLimitError):
            await container_service.add_resource(
                parent_id=parent_id,
                link=link,
                user_id="user_123",
                user_tier="FREE",
            )

    @pytest.mark.asyncio
    async def test_add_resource_allows_source_at_boundary(self, container_service, mock_firestore):
        """FREE tier allows SOURCE when new_depth hits boundary (max_depth + 1)."""

        parent_id = "sess_mid"
        await _create_parent(mock_firestore, "sessions", parent_id, depth=1, owner="user_123")

        link = ResourceLink(
            resource_id="source_def_boundary",
            resource_type=ResourceType.SOURCE,
            added_at=datetime.utcnow(),
            added_by="user_123",
            enabled=True,
        )

        link_id = await container_service.add_resource(
            parent_id=parent_id,
            link=link,
            user_id="user_123",
            user_tier="FREE",
        )

        assert isinstance(link_id, str)

    @pytest.mark.asyncio
    async def test_add_resource_blocks_source_parent(self, container_service, mock_firestore):
        """Source is terminal: cannot attach resources."""

        parent_id = "source_terminal"
        await _create_parent(mock_firestore, "sources", parent_id, depth=2, owner="user_999")

        link = ResourceLink(
            resource_id="agent_def",
            resource_type=ResourceType.AGENT,
            added_at=datetime.utcnow(),
            added_by="user_999",
            enabled=True,
        )

        with pytest.raises(InvalidContainmentError):
            await container_service.add_resource(
                parent_id=parent_id,
                link=link,
                user_id="user_999",
                user_tier="ENTERPRISE",
            )

    @pytest.mark.asyncio
    async def test_add_resource_blocks_usersession_non_session(self, container_service, mock_firestore):
        """UserSession may only contain Session links."""

        parent_id = "usersession_root"
        await _create_parent(mock_firestore, "usersessions", parent_id, depth=0, owner="user_root")

        link = ResourceLink(
            resource_id="tool_def",
            resource_type=ResourceType.TOOL,
            added_at=datetime.utcnow(),
            added_by="user_root",
            enabled=True,
        )

        with pytest.raises(InvalidContainmentError):
            await container_service.add_resource(
                parent_id=parent_id,
                link=link,
                user_id="user_root",
                user_tier="ENTERPRISE",
            )

    @pytest.mark.asyncio
    async def test_add_resource_enterprise_depth_boundary_disallows_non_source(self, container_service, mock_firestore):
        """ENT/PRO share rule: at max_depth+1 only SOURCE permitted."""

        parent_id = "sess_ent"
        # ENTERPRISE max_depth=3 (L4), so depth=4 (new_depth=4) must be SOURCE-only
        await _create_parent(mock_firestore, "sessions", parent_id, depth=3, owner="user_ent")

        link = ResourceLink(
            resource_id="agent_def",
            resource_type=ResourceType.AGENT,
            added_at=datetime.utcnow(),
            added_by="user_ent",
            enabled=True,
        )

        with pytest.raises(DepthLimitError):
            await container_service.add_resource(
                parent_id=parent_id,
                link=link,
                user_id="user_ent",
                user_tier="ENTERPRISE",
            )
