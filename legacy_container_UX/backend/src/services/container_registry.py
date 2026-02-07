"""Container Registry - Single source of truth for all container operations.

The ContainerRegistry is the unified access layer for all container types:
- UserSession (L0 root)
- Session (naked container)
- Agent, Tool, Source (definition-backed)

It wraps Firestore operations with:
1. Redis caching (fast reads)
2. ACL verification
3. Event emission (ContainerChanged)

All mutations go through the registry, ensuring:
- Consistent cache invalidation
- Real-time event propagation to SSE subscribers
- Unified ACL enforcement
"""

import asyncio
import json
import secrets
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.core.redis_client import redis_client

logger = get_logger(__name__)


# ============================================================================
# Event Models
# ============================================================================

class ContainerAction(str, Enum):
    """Actions that trigger ContainerChanged events."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESOURCE_ADDED = "resource_added"
    RESOURCE_REMOVED = "resource_removed"
    ACL_CHANGED = "acl_changed"


class ContainerChanged(BaseModel):
    """Event emitted on any container mutation."""
    
    event_id: str = Field(..., description="Unique event ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    container_type: str = Field(..., description="usersession, session, agent, tool, source")
    container_id: str = Field(..., description="Instance ID")
    action: ContainerAction
    user_id: str = Field(..., description="User who triggered the change")
    parent_id: str | None = Field(None, description="Parent container ID")
    data: dict = Field(default_factory=dict, description="Changed data (partial for updates)")


# ============================================================================
# Container Type Enum
# ============================================================================

class ContainerType(str, Enum):
    """Supported container types."""
    USERSESSION = "usersession"
    SESSION = "session"
    AGENT = "agent"
    TOOL = "tool"
    SOURCE = "source"


# Type to Firestore collection mapping
CONTAINER_COLLECTIONS = {
    ContainerType.USERSESSION: "usersessions",
    ContainerType.SESSION: "sessions",
    ContainerType.AGENT: "agents",
    ContainerType.TOOL: "tools",
    ContainerType.SOURCE: "sources",
}


# ============================================================================
# Container Registry
# ============================================================================

class ContainerRegistry:
    """Single source of truth for container CRUD.
    
    Provides:
    - Unified CRUD for all container types
    - Redis caching with auto-invalidation
    - Event emission for real-time sync
    - ACL verification
    
    All services should use the registry, not direct Firestore access.
    """

    def __init__(self, firestore_client):
        """Initialize registry with Firestore client.
        
        Args:
            firestore_client: Firestore client instance
        """
        self.firestore = firestore_client
        self._event_subscribers: list[asyncio.Queue] = []
        
    # ========================================================================
    # Cache Keys
    # ========================================================================
    
    def _cache_key(self, container_type: ContainerType, container_id: str) -> str:
        """Build Redis cache key for container."""
        return f"container:{container_type.value}:{container_id}"
    
    def _children_cache_key(self, container_id: str) -> str:
        """Build Redis cache key for container's children list."""
        return f"children:{container_id}"
    
    def _acl_cache_key(self, user_id: str, container_type: ContainerType) -> str:
        """Build Redis cache key for user's accessible containers of a type."""
        return f"containers:{user_id}:{container_type.value}"
    
    def _event_stream_key(self, user_id: str) -> str:
        """Build Redis key for user's event stream."""
        return f"events:{user_id}"

    # ========================================================================
    # Event Emission
    # ========================================================================
    
    async def _emit_event(self, event: ContainerChanged) -> None:
        """Emit ContainerChanged event to all subscribers and event store.
        
        Args:
            event: Event to emit
        """
        # Notify in-memory subscribers (for SSE connections) - this always works
        for queue in self._event_subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Event queue full, dropping event")
        
        # Try to store in Redis for catch-up (optional - degrades gracefully)
        try:
            if redis_client._client is not None:
                event_json = event.model_dump_json()
                score = event.timestamp.timestamp()
                await redis_client._client.zadd("events:global", {event_json: score})
                await redis_client._client.zremrangebyrank("events:global", 0, -1001)
        except Exception as e:
            # Redis unavailable - SSE still works via in-memory queue
            logger.debug(f"Redis event storage unavailable: {e}")
        
        logger.info(
            "Emitted ContainerChanged event",
            extra={
                "event_id": event.event_id,
                "container_type": event.container_type,
                "container_id": event.container_id,
                "action": event.action.value
            }
        )
    
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to container events.
        
        Returns:
            Queue that will receive ContainerChanged events
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._event_subscribers.append(queue)
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from container events."""
        if queue in self._event_subscribers:
            self._event_subscribers.remove(queue)
    
    async def get_events_since(self, since_timestamp: float) -> list[ContainerChanged]:
        """Get events since timestamp for catch-up.
        
        Args:
            since_timestamp: Unix timestamp to start from
            
        Returns:
            List of events after timestamp (empty if Redis unavailable)
        """
        # Redis unavailable - no catch-up events (SSE still works for live events)
        if redis_client._client is None:
            return []
        
        try:
            event_jsons = await redis_client._client.zrangebyscore(
                "events:global",
                min=since_timestamp,
                max="+inf"
            )
        except Exception as e:
            logger.debug(f"Redis event fetch unavailable: {e}")
            return []
        
        events = []
        for event_json in event_jsons:
            try:
                event = ContainerChanged.model_validate_json(event_json)
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")
        
        return events

    # ========================================================================
    # Core CRUD Operations
    # ========================================================================
    
    async def register(
        self,
        container_type: ContainerType,
        data: dict,
        user_id: str
    ) -> dict:
        """Register (create) a new container.
        
        Args:
            container_type: Type of container
            data: Container data (must include instance_id)
            user_id: User creating the container
            
        Returns:
            Created container data
        """
        collection = CONTAINER_COLLECTIONS[container_type]
        instance_id = data.get("instance_id")
        
        if not instance_id:
            raise ValueError("instance_id required in data")
        
        # Ensure timestamps and audit fields
        now = datetime.now(UTC)
        data["created_at"] = now
        data["updated_at"] = now
        data["created_by"] = user_id
        
        # Write to Firestore
        doc_ref = self.firestore.collection(collection).document(instance_id)
        await doc_ref.set(data)
        logger.info(f"DEBUG: Wrote to Firestore: {collection}/{instance_id}")
        
        # Cache the container
        cache_key = self._cache_key(container_type, instance_id)
        await redis_client.set(cache_key, json.dumps(data, default=str), ttl=3600)
        
        # Invalidate parent's children cache
        parent_id = data.get("parent_id")
        if parent_id:
            await redis_client.delete(self._children_cache_key(parent_id))
        
        # Emit event
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=instance_id,
            action=ContainerAction.CREATED,
            user_id=user_id,
            parent_id=parent_id,
            data=data
        ))
        
        logger.info(
            "Registered container",
            extra={"type": container_type.value, "instance_id": instance_id}
        )
        return data
    
    async def get(
        self,
        container_type: ContainerType,
        container_id: str,
        user_id: str | None = None
    ) -> dict | None:
        """Get container by ID.
        
        Args:
            container_type: Type of container
            container_id: Instance ID
            user_id: Optional user for ACL check (None = skip ACL)
            
        Returns:
            Container data or None if not found
        """
        cache_key = self._cache_key(container_type, container_id)
        
        # Try cache first
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            if user_id and not self._user_can_access(user_id, data.get("acl", {})):
                return None
            return data
        
        # Cache miss - read from Firestore
        collection = CONTAINER_COLLECTIONS[container_type]
        doc = await self.firestore.collection(collection).document(container_id).get()
        
        if not doc.exists:
            logger.info(f"DEBUG: Firestore doc not found: {collection}/{container_id}")
            return None
        
        data = doc.to_dict()
        
        # ACL check
        if user_id and not self._user_can_access(user_id, data.get("acl", {})):
            return None
        
        # Cache for future reads
        await redis_client.set(cache_key, json.dumps(data, default=str), ttl=3600)
        
        return data
    
    async def update(
        self,
        container_type: ContainerType,
        container_id: str,
        updates: dict,
        user_id: str
    ) -> dict:
        """Update container.
        
        Args:
            container_type: Type of container
            container_id: Instance ID
            updates: Fields to update
            user_id: User making the update
            
        Returns:
            Updated container data
            
        Raises:
            PermissionDeniedError: User can't edit
        """
        from src.core.exceptions import PermissionDeniedError, NotFoundError
        
        # Get current data for ACL check
        current = await self.get(container_type, container_id, user_id=None)
        if not current:
            raise NotFoundError(f"{container_type.value} {container_id} not found")
        
        # Require editor+ permission
        if not self._user_can_edit(user_id, current.get("acl", {})):
            raise PermissionDeniedError(f"User {user_id} cannot edit {container_id}")
        
        # Track if ACL changed
        acl_changed = "acl" in updates and updates["acl"] != current.get("acl")
        old_acl = current.get("acl", {}) if acl_changed else None
        
        # Apply updates
        updates["updated_at"] = datetime.now(UTC)
        collection = CONTAINER_COLLECTIONS[container_type]
        await self.firestore.collection(collection).document(container_id).update(updates)
        
        # Update cache
        current.update(updates)
        cache_key = self._cache_key(container_type, container_id)
        await redis_client.set(cache_key, json.dumps(current, default=str), ttl=3600)
        
        # Invalidate ACL caches if permissions changed
        if acl_changed:
            await self._invalidate_acl_caches(old_acl, updates["acl"])
        
        # Emit event
        action = ContainerAction.ACL_CHANGED if acl_changed else ContainerAction.UPDATED
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=container_id,
            action=action,
            user_id=user_id,
            parent_id=current.get("parent_id"),
            data=updates
        ))
        
        return current
    
    async def unregister(
        self,
        container_type: ContainerType,
        container_id: str,
        user_id: str
    ) -> None:
        """Unregister (delete) a container.
        
        Args:
            container_type: Type of container
            container_id: Instance ID
            user_id: User deleting
            
        Raises:
            PermissionDeniedError: User not owner
        """
        from src.core.exceptions import PermissionDeniedError, NotFoundError
        
        current = await self.get(container_type, container_id, user_id=None)
        if not current:
            raise NotFoundError(f"{container_type.value} {container_id} not found")
        
        # Only owner can delete
        if current.get("acl", {}).get("owner") != user_id:
            raise PermissionDeniedError(f"Only owner can delete {container_id}")
        
        parent_id = current.get("parent_id")
        
        # Delete from Firestore
        collection = CONTAINER_COLLECTIONS[container_type]
        doc_ref = self.firestore.collection(collection).document(container_id)
        
        # Delete /resources/ subcollection first
        resources = await self.firestore.collection(f"{collection}/{container_id}/resources").get()
        for resource_doc in resources:
            await resource_doc.reference.delete()
        
        await doc_ref.delete()
        
        # Invalidate caches
        cache_key = self._cache_key(container_type, container_id)
        await redis_client.delete(cache_key)
        
        if parent_id:
            # Remove from parent's resources
            parent_type = None
            if parent_id.startswith("usersession_"):
                parent_type = ContainerType.USERSESSION
            elif parent_id.startswith("sess_"):
                parent_type = ContainerType.SESSION
            elif parent_id.startswith("agent_"):
                parent_type = ContainerType.AGENT
            elif parent_id.startswith("tool_"):
                parent_type = ContainerType.TOOL
            
            if parent_type:
                parent_collection = CONTAINER_COLLECTIONS[parent_type]
                # Note: Firestore where() requires an index for some queries, but equality on a field should be fine
                parent_resources = await self.firestore.collection(f"{parent_collection}/{parent_id}/resources") \
                    .where("instance_id", "==", container_id).get()
                
                for res_doc in parent_resources:
                    await res_doc.reference.delete()
                    logger.info(f"Removed resource link {res_doc.id} from parent {parent_id}")

            await redis_client.delete(self._children_cache_key(parent_id))
        
        # Emit event
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=container_id,
            action=ContainerAction.DELETED,
            user_id=user_id,
            parent_id=parent_id,
            data={}
        ))
        
        logger.info(
            "Unregistered container",
            extra={"type": container_type.value, "instance_id": container_id}
        )

    # ========================================================================
    # Query Operations
    # ========================================================================
    
    async def get_children(
        self,
        parent_id: str,
        user_id: str
    ) -> list[dict]:
        """Get all children of a container.
        
        Args:
            parent_id: Parent container ID
            user_id: User for ACL filtering
            
        Returns:
            List of child container data
        """
        # Try cache first
        cache_key = self._children_cache_key(parent_id)
        cached = await redis_client.get(cache_key)
        
        if cached:
            children = json.loads(cached)
            # Filter by ACL
            return [c for c in children if self._user_can_access(user_id, c.get("acl", {}))]
        
        # Query all container collections for children
        children = []
        
        for container_type in ContainerType:
            collection = CONTAINER_COLLECTIONS[container_type]
            query = self.firestore.collection(collection).where("parent_id", "==", parent_id)
            docs = await query.get()
            
            for doc in docs:
                data = doc.to_dict()
                data["_type"] = container_type.value
                children.append(data)
        
        # Cache (before ACL filter - filter on read)
        if children:
            await redis_client.set(cache_key, json.dumps(children, default=str), ttl=3600)
        
        # Filter by ACL
        return [c for c in children if self._user_can_access(user_id, c.get("acl", {}))]
    
    async def get_by_acl(
        self,
        user_id: str,
        container_type: ContainerType | None = None
    ) -> list[dict]:
        """Get all containers user has access to.
        
        Args:
            user_id: User ID
            container_type: Optional filter by type (None = all types)
            
        Returns:
            List of accessible containers
        """
        types_to_query = [container_type] if container_type else list(ContainerType)
        results = []
        
        for ctype in types_to_query:
            # Check cache
            cache_key = self._acl_cache_key(user_id, ctype)
            cached = await redis_client.get(cache_key)
            
            if cached:
                results.extend(json.loads(cached))
                continue
            
            # Query Firestore for containers where user is owner/editor/viewer
            collection = CONTAINER_COLLECTIONS[ctype]
            type_results = []
            
            # Owner query
            owner_query = self.firestore.collection(collection).where("acl.owner", "==", user_id)
            owner_docs = await owner_query.get()
            for doc in owner_docs:
                data = doc.to_dict()
                data["_type"] = ctype.value
                type_results.append(data)
            
            # Editor query
            editor_query = self.firestore.collection(collection).where("acl.editors", "array_contains", user_id)
            editor_docs = await editor_query.get()
            for doc in editor_docs:
                data = doc.to_dict()
                if data not in type_results:
                    data["_type"] = ctype.value
                    type_results.append(data)
            
            # Viewer query
            viewer_query = self.firestore.collection(collection).where("acl.viewers", "array_contains", user_id)
            viewer_docs = await viewer_query.get()
            for doc in viewer_docs:
                data = doc.to_dict()
                if data not in type_results:
                    data["_type"] = ctype.value
                    type_results.append(data)
            
            # Cache results
            if type_results:
                await redis_client.set(cache_key, json.dumps(type_results, default=str), ttl=3600)
            
            results.extend(type_results)
        
        return results

    # ========================================================================
    # Resource Link Operations
    # ========================================================================
    
    async def add_resource(
        self,
        container_type: ContainerType,
        container_id: str,
        resource_link: dict,
        user_id: str
    ) -> dict:
        """Add ResourceLink to container's /resources/ subcollection.
        
        If resource_link has an 'instance_id', this adopts an ORPHAN container:
        - Container must have parent_id=None (be in the Library)
        - Updates the instance's parent_id to this container
        - Updates the instance's depth
        
        Args:
            container_type: Parent container type
            container_id: Parent container ID
            resource_link: ResourceLink data
            user_id: User adding the resource
            
        Returns:
            Created ResourceLink with link_id
            
        Raises:
            ValidationError: If instance already has a parent (not orphaned)
        """
        from src.core.exceptions import PermissionDeniedError, NotFoundError, ValidationError
        
        # ACL check
        container = await self.get(container_type, container_id, user_id=None)
        if not container or not self._user_can_edit(user_id, container.get("acl", {})):
            raise PermissionDeniedError(f"User {user_id} cannot edit {container_id}")
        
        # Generate link_id
        # Format: {type}_{resource_id}_{suffix}
        resource_id = resource_link.get("resource_id", "unknown")
        link_id = f"{resource_link.get('resource_type', 'unknown').lower()}_{resource_id}_{secrets.token_hex(3)}"
        resource_link["link_id"] = link_id
        resource_link["added_at"] = datetime.now(UTC)
        resource_link["added_by"] = user_id
        
        # Handle "Adopt Orphan" Logic if instance_id is present
        instance_id = resource_link.get("instance_id")
        if instance_id:
            # Infer child type
            child_type = None
            if instance_id.startswith("sess_"): child_type = ContainerType.SESSION
            elif instance_id.startswith("agent_"): child_type = ContainerType.AGENT
            elif instance_id.startswith("tool_"): child_type = ContainerType.TOOL
            elif instance_id.startswith("source_"): child_type = ContainerType.SOURCE
            
            if child_type:
                # Get child to check current parent
                child = await self.get(child_type, instance_id, user_id=None)
                if not child:
                    raise NotFoundError(f"Instance {instance_id} not found")
                
                # Check if user can edit the child (required to adopt it)
                if not self._user_can_edit(user_id, child.get("acl", {})):
                    raise PermissionDeniedError(f"User {user_id} cannot adopt {instance_id}")

                # ENFORCE: Only orphans can be adopted (parent_id must be None)
                current_parent = child.get("parent_id")
                if current_parent is not None:
                    raise ValidationError(
                        f"Cannot adopt {instance_id}: already has parent '{current_parent}'. "
                        "Unlink it first to make it available in the Library."
                    )

                # Update child with new parent and depth
                parent_depth = container.get("depth", 0)
                child_updates = {
                    "parent_id": container_id,
                    "depth": parent_depth + 1,
                    "updated_at": datetime.now(UTC)
                }
                
                child_collection = CONTAINER_COLLECTIONS[child_type]
                await self.firestore.collection(child_collection).document(instance_id).update(child_updates)
                
                # Invalidate child cache
                await redis_client.delete(self._cache_key(child_type, instance_id))
                
                # Emit update event for child (signals adoption to SSE subscribers)
                await self._emit_event(ContainerChanged(
                    event_id=secrets.token_hex(8),
                    container_type=child_type.value,
                    container_id=instance_id,
                    action=ContainerAction.UPDATED,
                    user_id=user_id,
                    parent_id=container_id,
                    data=child_updates
                ))

        # Write to subcollection
        collection = CONTAINER_COLLECTIONS[container_type]
        await self.firestore.collection(f"{collection}/{container_id}/resources").document(link_id).set(resource_link)
        
        # Invalidate children cache
        await redis_client.delete(self._children_cache_key(container_id))
        
        # Emit event
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=container_id,
            action=ContainerAction.RESOURCE_ADDED,
            user_id=user_id,
            parent_id=container.get("parent_id"),
            data={"link_id": link_id, "resource": resource_link}
        ))
        
        return resource_link
    
    async def get_resources(
        self,
        container_type: ContainerType,
        container_id: str,
        user_id: str
    ) -> list[dict]:
        """Get ResourceLinks from container's /resources/ subcollection.
        
        Args:
            container_type: Container type
            container_id: Container ID
            user_id: User for ACL check
            
        Returns:
            List of ResourceLinks
        """
        # ACL check (need viewer+ access)
        container = await self.get(container_type, container_id, user_id=None)
        if not container or not self._user_can_access(user_id, container.get("acl", {})):
            return []
        
        collection = CONTAINER_COLLECTIONS[container_type]
        resources_ref = self.firestore.collection(f"{collection}/{container_id}/resources")
        docs = await resources_ref.get()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["link_id"] = doc.id
            results.append(data)
        
        return results
    
    async def remove_resource(
        self,
        container_type: ContainerType,
        container_id: str,
        link_id: str,
        user_id: str
    ) -> bool:
        """Remove ResourceLink from container (Unlink/Orphan).
        
        If the resource is a container instance, this operation "orphans" it:
        - Removes the link from the parent
        - Resets the child's parent_id to None
        - Resets the child's depth to 1 (Root Context)
        
        Args:
            container_type: Container type
            container_id: Container ID
            link_id: ResourceLink ID to remove
            user_id: User removing
            
        Returns:
            True if removed, False if not found
        """
        from src.core.exceptions import PermissionDeniedError
        
        # ACL check
        container = await self.get(container_type, container_id, user_id=None)
        if not container or not self._user_can_edit(user_id, container.get("acl", {})):
            raise PermissionDeniedError(f"User {user_id} cannot edit {container_id}")
        
        collection = CONTAINER_COLLECTIONS[container_type]
        doc_ref = self.firestore.collection(f"{collection}/{container_id}/resources").document(link_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return False
            
        link_data = doc.to_dict()
        instance_id = link_data.get("instance_id")
        
        # 1. Delete the link
        await doc_ref.delete()
        
        # 2. If it's a container instance, orphan it (Reset Instance)
        if instance_id:
            # Determine child type from ID prefix or query? 
            # We can try to find it in all collections or infer from ID.
            # Inferring is faster.
            child_type = None
            if instance_id.startswith("sess_"): child_type = ContainerType.SESSION
            elif instance_id.startswith("agent_"): child_type = ContainerType.AGENT
            elif instance_id.startswith("tool_"): child_type = ContainerType.TOOL
            elif instance_id.startswith("source_"): child_type = ContainerType.SOURCE
            
            if child_type:
                child_collection = CONTAINER_COLLECTIONS[child_type]
                child_ref = self.firestore.collection(child_collection).document(instance_id)
                
                # Update child to be an orphan
                updates = {
                    "parent_id": None,
                    "depth": 1, # Reset to root level
                    "updated_at": datetime.now(UTC)
                }
                await child_ref.update(updates)
                
                # Invalidate child cache
                child_cache_key = self._cache_key(child_type, instance_id)
                await redis_client.delete(child_cache_key)
                
                # Emit update event for child
                await self._emit_event(ContainerChanged(
                    event_id=secrets.token_hex(8),
                    container_type=child_type.value,
                    container_id=instance_id,
                    action=ContainerAction.UPDATED,
                    user_id=user_id,
                    parent_id=None,
                    data=updates
                ))

        # Invalidate parent's children cache
        await redis_client.delete(self._children_cache_key(container_id))
        
        # Emit event for parent
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=container_id,
            action=ContainerAction.RESOURCE_REMOVED,
            user_id=user_id,
            parent_id=container.get("parent_id"),
            data={"link_id": link_id}
        ))
        
        return True

    async def update_resource(
        self,
        container_type: ContainerType,
        container_id: str,
        link_id: str,
        updates: dict,
        user_id: str
    ) -> dict:
        """Update ResourceLink in container's /resources/ subcollection.
        
        Args:
            container_type: Container type
            container_id: Container ID
            link_id: ResourceLink ID to update
            updates: Fields to update (description, preset_params, metadata, enabled, etc.)
            user_id: User updating
            
        Returns:
            Updated ResourceLink data
            
        Raises:
            NotFoundError: ResourceLink not found
            PermissionDeniedError: User can't edit
        """
        from src.core.exceptions import PermissionDeniedError, NotFoundError
        
        # ACL check
        container = await self.get(container_type, container_id, user_id=None)
        if not container or not self._user_can_edit(user_id, container.get("acl", {})):
            raise PermissionDeniedError(f"User {user_id} cannot edit {container_id}")
        
        collection = CONTAINER_COLLECTIONS[container_type]
        doc_ref = self.firestore.collection(f"{collection}/{container_id}/resources").document(link_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            raise NotFoundError(f"ResourceLink {link_id} not found in {container_id}")
        
        # Get current data
        current = doc.to_dict()
        
        # Apply updates
        # Merge metadata if present (don't overwrite)
        if "metadata" in updates and isinstance(updates["metadata"], dict):
            current_metadata = current.get("metadata", {}) or {}
            current_metadata.update(updates["metadata"])
            updates["metadata"] = current_metadata

        updates["updated_at"] = datetime.now(UTC)
        await doc_ref.update(updates)
        
        # Merge for return
        current.update(updates)
        current["link_id"] = link_id
        
        # Invalidate children cache
        await redis_client.delete(self._children_cache_key(container_id))
        
        # Emit event (use UPDATED action - could be more specific later)
        await self._emit_event(ContainerChanged(
            event_id=secrets.token_hex(8),
            container_type=container_type.value,
            container_id=container_id,
            action=ContainerAction.UPDATED,
            user_id=user_id,
            parent_id=container.get("parent_id"),
            data={"link_id": link_id, "updates": updates}
        ))
        
        logger.info(
            "Updated resource link",
            extra={"container_id": container_id, "link_id": link_id}
        )
        
        return current

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
            operations: List of operations, each with:
                - action: "create" | "update" | "delete"
                - container_type: ContainerType value
                - container_id: Instance ID
                - data: Operation data
            user_id: User executing batch
            
        Returns:
            List of results for each operation
        """
        results = []
        
        for op in operations:
            action = op.get("action")
            container_type = ContainerType(op.get("container_type"))
            container_id = op.get("container_id")
            data = op.get("data", {})
            
            try:
                if action == "create":
                    data["instance_id"] = container_id
                    result = await self.register(container_type, data, user_id)
                    results.append({"success": True, "data": result})
                elif action == "update":
                    result = await self.update(container_type, container_id, data, user_id)
                    results.append({"success": True, "data": result})
                elif action == "delete":
                    await self.unregister(container_type, container_id, user_id)
                    results.append({"success": True})
                else:
                    results.append({"success": False, "error": f"Unknown action: {action}"})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results

    # ========================================================================
    # ACL Helpers
    # ========================================================================
    
    def _user_can_access(self, user_id: str, acl: dict) -> bool:
        """Check if user has any access (viewer+)."""
        if acl.get("owner") == user_id:
            return True
        if user_id in acl.get("editors", []):
            return True
        if user_id in acl.get("viewers", []):
            return True
        return False
    
    def _user_can_edit(self, user_id: str, acl: dict) -> bool:
        """Check if user has edit access (editor+)."""
        if acl.get("owner") == user_id:
            return True
        if user_id in acl.get("editors", []):
            return True
        return False
    
    async def _invalidate_acl_caches(self, old_acl: dict, new_acl: dict) -> None:
        """Invalidate ACL caches for affected users."""
        affected_users = set()
        
        # Old users
        if old_acl:
            if old_acl.get("owner"):
                affected_users.add(old_acl["owner"])
            affected_users.update(old_acl.get("editors", []))
            affected_users.update(old_acl.get("viewers", []))
        
        # New users
        if new_acl:
            if new_acl.get("owner"):
                affected_users.add(new_acl["owner"])
            affected_users.update(new_acl.get("editors", []))
            affected_users.update(new_acl.get("viewers", []))
        
        # Invalidate caches for all affected users
        for user_id in affected_users:
            for container_type in ContainerType:
                cache_key = self._acl_cache_key(user_id, container_type)
                await redis_client.delete(cache_key)
        
        logger.info(
            "Invalidated ACL caches",
            extra={"affected_users": list(affected_users)}
        )


# ============================================================================
# Global Registry Instance
# ============================================================================

_registry: ContainerRegistry | None = None


def get_container_registry(firestore_client=None) -> ContainerRegistry:
    """Get global ContainerRegistry instance.
    
    Args:
        firestore_client: Optional Firestore client (required on first call)
        
    Returns:
        ContainerRegistry singleton
    """
    global _registry
    
    if _registry is None:
        if firestore_client is None:
            raise ValueError("firestore_client required on first call")
        _registry = ContainerRegistry(firestore_client)
    
    return _registry
