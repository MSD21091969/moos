"""Definition service for agent/tool/source registry management.

Handles CRUD for definition templates with tier gating and ACL filtering.
"""

from datetime import datetime

from src.core.logging import get_logger
from src.models.definitions import AgentDefinition, SourceDefinition, ToolDefinition  # noqa: F401

logger = get_logger(__name__)


class DefinitionService:
    """Service for definition registry CRUD and tier-gated access."""

    def __init__(self, firestore_client):
        """Initialize definition service.
        
        Args:
            firestore_client: Firestore client instance
        """
        self.firestore = firestore_client

    async def create_definition(
        self,
        definition_type: str,
        definition_data: dict,
        user_id: str,
        user_tier: str
    ) -> str:
        """Create custom definition (PRO/ENT only).
        
        Args:
            definition_type: "agent", "tool", or "source"
            definition_data: Definition fields
            user_id: User creating definition
            user_tier: User tier (free/pro/enterprise)
            
        Returns:
            Created definition_id
            
        Raises:
            PermissionDeniedError: Tier too low
        """
        # Tier gate: only PRO+ can create custom definitions
        if user_tier.lower() not in ["pro", "enterprise"]:
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Custom definitions require PRO or ENT tier")

        # Generate ID
        definition_id = self._generate_definition_id(definition_type)

        # Add metadata
        definition_data["id"] = definition_id
        definition_data["created_at"] = datetime.utcnow()
        definition_data["updated_at"] = datetime.utcnow()
        definition_data["created_by"] = user_id
        definition_data["min_tier"] = user_tier.lower()  # Inherit from creator
        definition_data["acl"] = {"owner": user_id, "editors": [], "viewers": []}

        # Validate and save
        if definition_type == "agent":
            definition = AgentDefinition(**definition_data)
        elif definition_type == "tool":
            definition = ToolDefinition(**definition_data)
        elif definition_type == "source":
            definition = SourceDefinition(**definition_data)
        else:
            raise ValueError(f"Invalid definition type: {definition_type}")

        await self.firestore.collection(f"{definition_type}_definitions").document(definition_id).set(
            definition.model_dump()
        )

        logger.info(
            "Created custom definition",
            extra={
                "definition_id": definition_id,
                "type": definition_type,
                "user_id": user_id,
                "tier": user_tier
            }
        )
        return definition_id

    async def get_definition(
        self,
        definition_id: str,
        definition_type: str,
        user_id: str
    ) -> dict:
        """Get definition with ACL check.
        
        Args:
            definition_id: Definition ID
            definition_type: "agent", "tool", or "source"
            user_id: User requesting access
            
        Returns:
            Definition data
            
        Raises:
            NotFoundError: Definition doesn't exist
            PermissionDeniedError: User lacks access
        """
        doc_ref = self.firestore.collection(f"{definition_type}_definitions").document(definition_id)
        doc = await doc_ref.get()

        if not doc.exists:
            from src.core.exceptions import NotFoundError
            raise NotFoundError(f"{definition_type} definition {definition_id} not found")

        data = doc.to_dict()

        # System definitions (no created_by) are public
        if not data.get("created_by"):
            return data

        # Custom definitions require ACL check
        acl = data.get("acl", {})
        if not self._user_can_access(user_id, acl):
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError(f"User {user_id} cannot access {definition_id}")

        return data

    async def list_available_definitions(
        self,
        definition_type: str,
        user_id: str,
        user_tier: str
    ) -> list[dict]:
        """List definitions available to user (system + custom with ACL + tier).
        
        Args:
            definition_type: "agent", "tool", or "source"
            user_id: User requesting list
            user_tier: User tier (free/pro/enterprise)
            
        Returns:
            List of definitions (system + accessible custom)
        """
        definitions = []

        # Query all definitions
        docs = await self.firestore.collection(f"{definition_type}_definitions").get()

        for doc in docs:
            data = doc.to_dict()

            # Check tier gate
            min_tier = data.get("min_tier", "free")
            if not self._tier_meets_minimum(user_tier, min_tier):
                continue

            # System definitions (no created_by) are public
            if not data.get("created_by"):
                definitions.append(data)
                continue

            # Custom definitions require ACL check
            acl = data.get("acl", {})
            if self._user_can_access(user_id, acl):
                definitions.append(data)

        logger.info(
            "Listed available definitions",
            extra={
                "type": definition_type,
                "count": len(definitions),
                "user_id": user_id,
                "tier": user_tier
            }
        )
        return definitions

    async def update_definition(
        self,
        definition_id: str,
        definition_type: str,
        updates: dict,
        user_id: str
    ) -> None:
        """Update custom definition (custom only, owner/editor).
        
        Args:
            definition_id: Definition ID
            definition_type: Definition type
            updates: Fields to update
            user_id: User making update
            
        Raises:
            NotFoundError: Definition doesn't exist
            PermissionDeniedError: Not owner/editor or system definition
        """
        doc_ref = self.firestore.collection(f"{definition_type}_definitions").document(definition_id)
        doc = await doc_ref.get()

        if not doc.exists:
            from src.core.exceptions import NotFoundError
            raise NotFoundError(f"{definition_type} definition {definition_id} not found")

        data = doc.to_dict()

        # Cannot update system definitions
        if not data.get("created_by"):
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Cannot update system definitions")

        # Requires owner or editor
        acl = data.get("acl", {})
        if not self._user_can_edit(user_id, acl):
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError(f"User {user_id} cannot edit {definition_id}")

        updates["updated_at"] = datetime.utcnow()
        await doc_ref.update(updates)

        logger.info(
            "Updated custom definition",
            extra={"definition_id": definition_id, "type": definition_type, "user_id": user_id}
        )

    async def delete_definition(
        self,
        definition_id: str,
        definition_type: str,
        user_id: str
    ) -> None:
        """Delete custom definition (owner only).
        
        Args:
            definition_id: Definition ID
            definition_type: Definition type
            user_id: User deleting definition
            
        Raises:
            NotFoundError: Definition doesn't exist
            PermissionDeniedError: Not owner or system definition
        """
        doc_ref = self.firestore.collection(f"{definition_type}_definitions").document(definition_id)
        doc = await doc_ref.get()

        if not doc.exists:
            from src.core.exceptions import NotFoundError
            raise NotFoundError(f"{definition_type} definition {definition_id} not found")

        data = doc.to_dict()

        # Cannot delete system definitions
        if not data.get("created_by"):
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Cannot delete system definitions")

        # Requires owner only
        acl = data.get("acl", {})
        if acl.get("owner") != user_id:
            from src.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError(f"Only owner can delete {definition_id}")

        await doc_ref.delete()

        logger.info(
            "Deleted custom definition",
            extra={"definition_id": definition_id, "type": definition_type, "user_id": user_id}
        )

    # Helper methods

    def _generate_definition_id(self, definition_type: str) -> str:
        """Generate unique definition ID."""
        import uuid
        suffix = uuid.uuid4().hex[:12]
        return f"{definition_type}_{suffix}"

    def _user_can_access(self, user_id: str, acl: dict) -> bool:
        """Check if user has any access (owner, editor, or viewer)."""
        return (
            acl.get("owner") == user_id or
            user_id in acl.get("editors", []) or
            user_id in acl.get("viewers", [])
        )

    def _user_can_edit(self, user_id: str, acl: dict) -> bool:
        """Check if user can edit (owner or editor)."""
        return (
            acl.get("owner") == user_id or
            user_id in acl.get("editors", [])
        )

    def _tier_meets_minimum(self, user_tier: str, min_tier: str) -> bool:
        """Check if user tier meets minimum requirement."""
        tier_order = {"free": 0, "pro": 1, "enterprise": 2}
        return tier_order.get(user_tier.lower(), 0) >= tier_order.get(min_tier.lower(), 0)
