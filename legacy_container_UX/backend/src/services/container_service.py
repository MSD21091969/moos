"""Unified Container Service for all container operations.

Handles CRUD for all container types (UserSession, Session, Agent, Tool, Source)
using the ContainerRegistry as the single source of truth.

Extends BaseContainerService for shared validation logic.
Replaces both the old ContainerService and SessionService.
"""

import uuid
from datetime import datetime, timedelta, UTC

from src.core.exceptions import (
    CircularDependencyError,
    DepthLimitError,
    InvalidContainmentError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.core.logging import get_logger
from src.models.containers import AgentInstance, SourceInstance, ToolInstance, UserSession
from src.models.sessions import Session, SessionCreate, SessionMetadata, SessionStatus
from src.models.permissions import Tier, get_session_limit
from src.models.links import ResourceLink, ResourceType
from src.services.base_container_service import BaseContainerService, TIER_MAX_DEPTH
from src.services.container_registry import (
    ContainerRegistry,
    ContainerType,
    get_container_registry,
)

logger = get_logger(__name__)


class ContainerService(BaseContainerService):
    """Unified service for all container CRUD operations.
    
    Handles:
    - UserSession (L0 workspace root)
    - Session (naked container)
    - Agent, Tool, Source (definition-backed)
    
    All operations go through ContainerRegistry for consistent
    caching, ACL enforcement, and event emission.
    """

    def __init__(self, firestore_client, registry: ContainerRegistry | None = None):
        """Initialize container service.
        
        Args:
            firestore_client: Firestore client instance
            registry: Optional ContainerRegistry (defaults to global)
        """
        # Initialize registry with firestore client if not provided
        if registry is None:
            registry = get_container_registry(firestore_client)
        super().__init__(registry)
        self.firestore = firestore_client

    # ========================================================================
    # Session Operations (replaces SessionService)
    # ========================================================================

    async def create_session(
        self,
        user_id: str,
        user_tier: str,
        request: SessionCreate,
        parent_id: str | None = None
    ) -> Session:
        """Create a new session with tier limit check and depth computation.
        
        Args:
            user_id: User creating session
            user_tier: User's subscription tier
            request: Session creation request
            parent_id: Parent container ID (defaults to usersession_{user_id})
            
        Returns:
            Created session
            
        Raises:
            ValidationError: If user exceeds session limit for tier
            DepthLimitError: If depth limit exceeded
        """
        # Normalize tier
        try:
            tier_enum = Tier(user_tier.lower() if isinstance(user_tier, str) else user_tier.value.lower())
        except ValueError:
            raise ValidationError(f"Unknown tier: {user_tier}")
        
        # Check tier limit on active sessions
        max_sessions = get_session_limit(tier_enum)
        if max_sessions != -1:
            existing = await self.registry.get_by_acl(user_id, ContainerType.SESSION)
            active_count = sum(1 for s in existing if s.get("status") == SessionStatus.ACTIVE.value)
            
            if active_count >= max_sessions:
                raise ValidationError(
                    f"Session limit reached. Tier '{user_tier}' allows max {max_sessions} active sessions."
                )
        
        # Generate session ID
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=request.metadata.ttl_hours)
        
        # Determine parent
        actual_parent_id = parent_id or request.parent_id or f"usersession_{user_id}"
        
        # Build session data
        session_data = {
            "instance_id": session_id,
            "session_id": session_id,
            "definition_id": None,  # Sessions are naked containers
            "metadata": request.metadata.model_dump(),
            "status": SessionStatus.ACTIVE.value,
            "expires_at": expires_at.isoformat(),
            "collection_schemas": {},
            "custom_fields": {},
            "preferences": {},
            "active_agent_id": None,
            "event_count": 0,
            "last_event_at": None,
            "created_by_email": None,
        }
        
        # Use base class validation and creation
        result = await self.create_container(
            container_type=ContainerType.SESSION,
            parent_id=actual_parent_id,
            user_id=user_id,
            user_tier=tier_enum,
            data=session_data
        )
        
        # Also add ResourceLink to parent
        await self.registry.add_resource(
            container_type=self._infer_container_type(actual_parent_id),
            container_id=actual_parent_id,
            resource_link={
                "resource_type": ResourceType.SESSION.value,
                "resource_id": session_id,
                "instance_id": session_id,
                "enabled": True,
                "preset_params": {},
                "input_mappings": {},
                "metadata": request.metadata.visual_metadata or {},
                "description": request.metadata.title,
            },
            user_id=user_id
        )
        
        logger.info(
            "Created session",
            extra={"session_id": session_id, "user_id": user_id, "parent_id": actual_parent_id}
        )
        
        return Session(**result)

    async def get_session(self, session_id: str, user_id: str) -> Session:
        """Get session by ID with ACL check.
        
        Args:
            session_id: Session ID
            user_id: User requesting
            
        Returns:
            Session
            
        Raises:
            NotFoundError: Session doesn't exist
            PermissionDeniedError: User lacks access
        """
        data = await self.registry.get(ContainerType.SESSION, session_id, user_id)
        if not data:
            raise NotFoundError(f"Session {session_id} not found or access denied")
        
        return Session(**data)

    async def update_session(
        self,
        session_id: str,
        user_id: str,
        updates: dict
    ) -> Session:
        """Update session fields.
        
        Args:
            session_id: Session ID
            user_id: User making update
            updates: Fields to update
            
        Returns:
            Updated session
        """
        result = await self.registry.update(
            ContainerType.SESSION,
            session_id,
            updates,
            user_id
        )
        return Session(**result)

    async def delete_session(self, session_id: str, user_id: str) -> None:
        """Delete session (owner only).
        
        Args:
            session_id: Session ID
            user_id: User deleting
        """
        await self.registry.unregister(ContainerType.SESSION, session_id, user_id)
        logger.info("Deleted session", extra={"session_id": session_id, "user_id": user_id})

    # ========================================================================
    # Instance Operations (Agent, Tool, Source)
    # ========================================================================

    async def create_instance(
        self,
        parent_id: str | None,
        definition_id: str,
        container_type: str,
        user_id: str,
        user_tier: str = "FREE",
        **kwargs
    ) -> str:
        """Create container instance with ACL and tier-gated depth validation.
        
        Args:
            parent_id: Parent container ID (None for Orphan)
            definition_id: Definition ID from registry
            container_type: "agent", "tool", or "source"
            user_id: User creating the instance
            user_tier: User tier (FREE, PRO, ENTERPRISE)
            **kwargs: Additional fields (title, etc.)
            
        Returns:
            Created instance_id
        """
        # Map string type to enum
        type_map = {
            "agent": ContainerType.AGENT,
            "tool": ContainerType.TOOL,
            "source": ContainerType.SOURCE,
            "session": ContainerType.SESSION,
        }
        ctype = type_map.get(container_type.lower())
        if not ctype:
            raise ValidationError(f"Unknown container type: {container_type}")
        
        # Generate instance ID
        instance_id = f"{container_type}_{uuid.uuid4().hex[:12]}"
        
        # Build instance data
        instance_data = {
            "instance_id": instance_id,
            "definition_id": definition_id,
            **kwargs
        }
        
        # Normalize tier
        try:
            tier_enum = Tier(user_tier.lower() if isinstance(user_tier, str) else user_tier.value.lower())
        except ValueError:
            tier_enum = Tier.FREE
        
        # Use base class validation and creation
        await self.create_container(
            container_type=ctype,
            parent_id=parent_id,
            user_id=user_id,
            user_tier=tier_enum,
            data=instance_data
        )
        
        # Add ResourceLink to parent if parent_id exists
        if parent_id:
            parent_type = self._infer_container_type(parent_id)
            await self.registry.add_resource(
                container_type=parent_type,
                container_id=parent_id,
                resource_link={
                    "resource_type": container_type.upper(),
                    "resource_id": definition_id,
                    "instance_id": instance_id,
                    "enabled": True,
                    "preset_params": kwargs.get("preset_params", {}),
                    "input_mappings": kwargs.get("input_mappings", {}),
                    "metadata": kwargs.get("metadata", {}),
                    "description": kwargs.get("title"),
                },
                user_id=user_id
            )
        
        logger.info(
            "Created container instance",
            extra={
                "instance_id": instance_id,
                "type": container_type,
                "parent_id": parent_id,
                "user_id": user_id
            }
        )
        return instance_id

    async def get_instance(
        self,
        instance_id: str,
        container_type: str,
        user_id: str
    ) -> dict:
        """Get container instance with ACL check.
        
        Args:
            instance_id: Container instance ID
            container_type: "usersession", "session", "agent", "tool", or "source"
            user_id: User requesting access
            
        Returns:
            Container data
        """
        type_map = {
            "usersession": ContainerType.USERSESSION,
            "session": ContainerType.SESSION,
            "agent": ContainerType.AGENT,
            "tool": ContainerType.TOOL,
            "source": ContainerType.SOURCE,
        }
        ctype = type_map.get(container_type.lower())
        if not ctype:
            raise ValidationError(f"Unknown container type: {container_type}")
        
        data = await self.registry.get(ctype, instance_id, user_id)
        if not data:
            raise NotFoundError(f"{container_type} {instance_id} not found or access denied")
        
        return data

    async def update_instance(
        self,
        instance_id: str,
        container_type: str,
        user_id: str,
        updates: dict
    ) -> None:
        """Update container instance with ACL check.
        
        Args:
            instance_id: Container instance ID
            container_type: Container type
            user_id: User making update
            updates: Fields to update
        """
        type_map = {
            "usersession": ContainerType.USERSESSION,
            "session": ContainerType.SESSION,
            "agent": ContainerType.AGENT,
            "tool": ContainerType.TOOL,
            "source": ContainerType.SOURCE,
        }
        ctype = type_map.get(container_type.lower())
        if not ctype:
            raise ValidationError(f"Unknown container type: {container_type}")
        
        await self.registry.update(ctype, instance_id, updates, user_id)
        
        logger.info(
            "Updated container instance",
            extra={"instance_id": instance_id, "type": container_type, "user_id": user_id}
        )

    async def delete_instance(
        self,
        instance_id: str,
        container_type: str,
        user_id: str
    ) -> None:
        """Delete container instance with ACL check.
        
        Args:
            instance_id: Container instance ID
            container_type: Container type
            user_id: User deleting instance
        """
        type_map = {
            "usersession": ContainerType.USERSESSION,
            "session": ContainerType.SESSION,
            "agent": ContainerType.AGENT,
            "tool": ContainerType.TOOL,
            "source": ContainerType.SOURCE,
        }
        ctype = type_map.get(container_type.lower())
        if not ctype:
            raise ValidationError(f"Unknown container type: {container_type}")
        
        await self.registry.unregister(ctype, instance_id, user_id)
        
        logger.info(
            "Deleted container instance",
            extra={"instance_id": instance_id, "type": container_type, "user_id": user_id}
        )

    # ========================================================================
    # Resource Link Operations
    # ========================================================================

    async def add_resource(
        self,
        parent_id: str,
        link: ResourceLink,
        user_id: str,
        user_tier: str = "FREE"
    ) -> str:
        """Add ResourceLink to parent's /resources/.
        
        Args:
            parent_id: Parent container ID
            link: ResourceLink to add
            user_id: User adding resource
            user_tier: User tier for depth validation
            
        Returns:
            Created link_id
        """
        parent_type = self._infer_container_type(parent_id)
        if not parent_type:
            raise ValidationError(f"Unknown container ID format: {parent_id}")
        
        # Terminal node check
        if parent_type in (ContainerType.SOURCE,):
            raise InvalidContainmentError("Source is a terminal node and cannot contain resources")
        
        # Get parent for depth validation
        parent = await self.registry.get(parent_type, parent_id, user_id=None)
        if not parent:
            raise NotFoundError(f"Parent {parent_id} not found")
        
        # Depth validation
        new_depth = parent.get("depth", 0) + 1
        tier_enum = Tier(user_tier.lower()) if isinstance(user_tier, str) else user_tier
        max_depth = self.get_max_depth(tier_enum)
        
        if new_depth > max_depth + 1:
            raise DepthLimitError(f"Depth {new_depth} exceeds absolute limit {max_depth + 1}")
        
        if new_depth == max_depth + 1 and link.resource_type != ResourceType.SOURCE:
            raise DepthLimitError(f"Only SOURCE allowed at depth {new_depth} (Tier {user_tier} limit)")
        
        # Containment rules
        if parent_type == ContainerType.USERSESSION and link.resource_type != ResourceType.SESSION:
            if link.resource_type != ResourceType.USER:  # USER links are allowed
                raise InvalidContainmentError("UserSession can only contain Sessions")
        
        # Add via registry
        result = await self.registry.add_resource(
            container_type=parent_type,
            container_id=parent_id,
            resource_link=link.model_dump(),
            user_id=user_id
        )
        
        return result.get("link_id")

    async def list_resources(
        self,
        parent_id: str,
        user_id: str,
        resource_type: str | None = None
    ) -> list[ResourceLink]:
        """List ResourceLinks in parent's /resources/.
        
        Args:
            parent_id: Parent container ID
            user_id: User requesting list
            resource_type: Optional filter by type
            
        Returns:
            List of ResourceLinks
        """
        parent_type = self._infer_container_type(parent_id)
        if not parent_type:
            raise ValidationError(f"Unknown container ID format: {parent_id}")
        
        resources = await self.registry.get_resources(parent_type, parent_id, user_id)
        
        # Filter by type if specified
        if resource_type:
            resources = [r for r in resources if r.get("resource_type", "").upper() == resource_type.upper()]
        
        return [ResourceLink(**r) for r in resources]

    async def remove_resource(
        self,
        parent_id: str,
        link_id: str,
        user_id: str
    ) -> None:
        """Remove ResourceLink from parent's /resources/.
        
        Args:
            parent_id: Parent container ID
            link_id: ResourceLink document ID
            user_id: User removing resource
        """
        parent_type = self._infer_container_type(parent_id)
        if not parent_type:
            raise ValidationError(f"Unknown container ID format: {parent_id}")
        
        await self.registry.remove_resource(parent_type, parent_id, link_id, user_id)
        
        logger.info(
            "Removed resource from container",
            extra={"parent_id": parent_id, "link_id": link_id, "user_id": user_id}
        )

    # ========================================================================
    # UserSession Operations
    # ========================================================================

    async def get_or_create_usersession(self, user_id: str) -> UserSession:
        """Get UserSession or create if doesn't exist.
        
        Called on user sign-in to ensure workspace root exists.
        
        Args:
            user_id: User ID
            
        Returns:
            UserSession container
        """
        instance_id = f"usersession_{user_id}"
        
        # Try to get existing
        data = await self.registry.get(ContainerType.USERSESSION, instance_id, user_id=None)
        
        if data:
            logger.info("UserSession exists", extra={"user_id": user_id})
            return UserSession(**data)
        
        # Create new UserSession
        usersession_data = {
            "instance_id": instance_id,
            "user_id": user_id,
            "parent_id": None,
            "depth": 0,
            "acl": {"owner": user_id, "editors": [], "viewers": []},
            "preferences": {},
        }
        
        result = await self.registry.register(
            ContainerType.USERSESSION,
            usersession_data,
            user_id
        )
        
        # Add owner USER ResourceLink
        await self.registry.add_resource(
            container_type=ContainerType.USERSESSION,
            container_id=instance_id,
            resource_link={
                "resource_type": ResourceType.USER.value,
                "resource_id": user_id,
                "role": "owner",
                "enabled": True,
                "preset_params": {},
                "input_mappings": {},
                "metadata": {},
            },
            user_id=user_id
        )
        
        logger.info("Created UserSession", extra={"user_id": user_id})
        return UserSession(**result)

    async def get_workspace_resources(self, user_id: str) -> list[ResourceLink]:
        """Get all resources in user's workspace (UserSession).
        
        Args:
            user_id: User ID
            
        Returns:
            List of ResourceLinks (USER + SESSIONs)
        """
        instance_id = f"usersession_{user_id}"
        return await self.list_resources(instance_id, user_id)

    # ========================================================================
    # Batch Operations
    # ========================================================================

    async def batch_update(
        self,
        operations: list[dict],
        user_id: str
    ) -> list[dict]:
        """Execute multiple container operations in batch.
        
        Args:
            operations: List of operations
            user_id: User executing batch
            
        Returns:
            List of results
        """
        return await self.registry.batch_update(operations, user_id)

