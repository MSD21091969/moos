"""UserSession service for workspace root management.

UserSession is the L0 container created once per user on sign-in.
It contains USER (owner) + SESSION (ACL-permitted) ResourceLinks.

Redis ACL Cache Integration:
- Cache key: acl:user:{user_id}:sessions
- TTL: 24h (aligned with JWT lifetime)
- Invalidation: On sync_session_links() changes
"""

import secrets
from datetime import datetime, UTC

from src.core.logging import get_logger
from src.core.acl_cache import get_acl_cache
from src.models.containers import UserSession
from src.models.links import ResourceLink, ResourceType

logger = get_logger(__name__)


class UserSessionService:
    """Service for UserSession lifecycle and workspace population."""

    def __init__(self, firestore_client):
        """Initialize UserSession service.
        
        Args:
            firestore_client: Firestore client instance
        """
        self.firestore = firestore_client

    async def get_or_create(self, user_id: str) -> UserSession:
        """Get UserSession or create if doesn't exist.
        
        Called on user sign-in to ensure workspace root exists.
        
        Args:
            user_id: User ID
            
        Returns:
            UserSession container
        """
        instance_id = f"usersession_{user_id}"
        doc_ref = self.firestore.collection("usersessions").document(instance_id)
        doc = await doc_ref.get()

        if doc.exists:
            logger.info("UserSession exists", extra={"user_id": user_id})
            return UserSession(**doc.to_dict())

        # Create new UserSession
        usersession = UserSession(
            instance_id=instance_id,
            user_id=user_id,
            parent_id=None,
            depth=0,
            acl={"owner": user_id, "editors": [], "viewers": []},
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await doc_ref.set(usersession.model_dump())

        # Add owner USER ResourceLink
        await self.firestore.collection(f"usersessions/{instance_id}/resources").add({
            "resource_type": ResourceType.USER.value,
            "resource_id": user_id,
            "role": "owner",
            "added_at": datetime.utcnow(),
            "added_by": user_id,
            "enabled": True,
            "preset_params": {},
            "input_mappings": {},
            "metadata": {},
        })

        logger.info("Created UserSession", extra={"user_id": user_id})
        return usersession

    async def populate_sessions(self, user_id: str) -> list[str]:
        """Query ACL-permitted sessions for user.
        
        Returns session IDs where user is owner, editor, or viewer.
        Uses Redis cache with Firestore fallback.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session IDs
        """
        acl_cache = get_acl_cache()
        
        # Try cache first
        cached_ids = await acl_cache.get_permitted_sessions(user_id)
        if cached_ids is not None:
            logger.debug(
                "Using cached session IDs",
                extra={"user_id": user_id, "count": len(cached_ids)}
            )
            return list(cached_ids)
        
        # Cache miss - query Firestore
        session_ids = set()

        # Query sessions where user is owner
        owner_query = self.firestore.collection("sessions").where("acl.owner", "==", user_id)
        owner_docs = await owner_query.get()
        session_ids.update(doc.id for doc in owner_docs)

        # Query sessions where user is editor
        editor_query = self.firestore.collection("sessions").where("acl.editors", "array_contains", user_id)
        editor_docs = await editor_query.get()
        session_ids.update(doc.id for doc in editor_docs)

        # Query sessions where user is viewer
        viewer_query = self.firestore.collection("sessions").where("acl.viewers", "array_contains", user_id)
        viewer_docs = await viewer_query.get()
        session_ids.update(doc.id for doc in viewer_docs)

        logger.info(
            "Populated ACL-permitted sessions from Firestore",
            extra={"user_id": user_id, "session_count": len(session_ids)}
        )
        
        # Cache for future requests
        await acl_cache.refresh_from_firestore(user_id, session_ids)
        
        return list(session_ids)

    async def get_resources(self, user_id: str) -> list[ResourceLink]:
        """Get ResourceLinks in UserSession (USER + SESSIONs).
        
        Args:
            user_id: User ID
            
        Returns:
            List of ResourceLinks
        """
        instance_id = f"usersession_{user_id}"
        resources_ref = self.firestore.collection(f"usersessions/{instance_id}/resources")
        docs = await resources_ref.get()

        links = []
        for doc in docs:
            data = doc.to_dict()
            data["link_id"] = doc.id
            links.append(ResourceLink(**data))

        logger.info(
            "Retrieved UserSession resources",
            extra={"user_id": user_id, "resource_count": len(links)}
        )
        return links

    async def sync_session_links(self, user_id: str) -> int:
        """Sync SESSION ResourceLinks with ACL-permitted sessions.
        
        Adds missing sessions, removes revoked access.
        Invalidates Redis cache on changes.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of changes made
        """
        instance_id = f"usersession_{user_id}"
        acl_cache = get_acl_cache()
        
        # Get current SESSION links
        current_links = await self.get_resources(user_id)
        current_session_ids = {
            link.resource_id for link in current_links
            if link.resource_type == ResourceType.SESSION
        }

        # Get ACL-permitted sessions (will use cache if available)
        permitted_session_ids = set(await self.populate_sessions(user_id))

        # Add missing sessions
        to_add = permitted_session_ids - current_session_ids
        for session_id in to_add:
            await self.firestore.collection(f"usersessions/{instance_id}/resources").add({
                "resource_type": ResourceType.SESSION.value,
                "resource_id": session_id,
                "instance_id": session_id,  # Session IS the instance
                "added_at": datetime.utcnow(),
                "added_by": "system",  # Auto-sync
                "enabled": True,
                "preset_params": {},
                "input_mappings": {},
                "metadata": {},  # Default position, will be set by frontend
            })

        # Remove revoked sessions
        to_remove = current_session_ids - permitted_session_ids
        for session_id in to_remove:
            # Find and delete ResourceLink
            query = self.firestore.collection(f"usersessions/{instance_id}/resources") \
                .where("resource_type", "==", ResourceType.SESSION.value) \
                .where("resource_id", "==", session_id)
            docs = await query.get()
            for doc in docs:
                await doc.reference.delete()

        changes = len(to_add) + len(to_remove)
        
        # Invalidate cache if changes occurred
        if changes > 0:
            await acl_cache.invalidate_user(user_id)
            logger.info(
                "Invalidated ACL cache due to session link changes",
                extra={"user_id": user_id}
            )
        
        logger.info(
            "Synced UserSession session links",
            extra={
                "user_id": user_id,
                "added": len(to_add),
                "removed": len(to_remove),
                "total_changes": changes
            }
        )
        return changes

    async def add_resource(self, user_id: str, link: ResourceLink) -> ResourceLink:
        """Add a ResourceLink to UserSession.
        
        Only SESSION and USER types are allowed at workspace level.
        
        Args:
            user_id: User ID
            link: ResourceLink to add (link_id will be generated)
            
        Returns:
            Created ResourceLink with link_id
        """
        instance_id = f"usersession_{user_id}"
        
        # Generate link_id: {type}_{resource_id}_{random_hex}
        random_suffix = secrets.token_hex(3)
        link_id = f"{link.resource_type.value}_{link.resource_id}_{random_suffix}"
        
        # Prepare document data
        link_data = link.model_dump()
        link_data["link_id"] = link_id
        link_data["added_at"] = datetime.now(UTC)
        
        # Store in Firestore subcollection
        await self.firestore.collection(f"usersessions/{instance_id}/resources").document(link_id).set(link_data)
        
        logger.info(
            "Added resource to UserSession",
            extra={
                "user_id": user_id,
                "link_id": link_id,
                "resource_type": link.resource_type.value,
                "resource_id": link.resource_id,
            }
        )
        
        # Return complete link
        link_data["link_id"] = link_id
        return ResourceLink(**link_data)

    async def get_resource(self, user_id: str, link_id: str) -> ResourceLink | None:
        """Get a single ResourceLink by link_id.
        
        Args:
            user_id: User ID
            link_id: ResourceLink ID
            
        Returns:
            ResourceLink or None if not found
        """
        instance_id = f"usersession_{user_id}"
        doc_ref = self.firestore.collection(f"usersessions/{instance_id}/resources").document(link_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        data["link_id"] = doc.id
        return ResourceLink(**data)

    async def update_resource(self, user_id: str, link_id: str, updates: dict) -> ResourceLink | None:
        """Update a ResourceLink in UserSession.
        
        Args:
            user_id: User ID
            link_id: ResourceLink ID
            updates: Fields to update
            
        Returns:
            Updated ResourceLink or None if not found
        """
        instance_id = f"usersession_{user_id}"
        doc_ref = self.firestore.collection(f"usersessions/{instance_id}/resources").document(link_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        # Add updated_at timestamp
        updates["updated_at"] = datetime.now(UTC)
        
        await doc_ref.update(updates)
        
        # Return updated document
        updated_doc = await doc_ref.get()
        data = updated_doc.to_dict()
        data["link_id"] = updated_doc.id
        
        logger.info(
            "Updated resource in UserSession",
            extra={"user_id": user_id, "link_id": link_id, "fields": list(updates.keys())}
        )
        
        return ResourceLink(**data)

    async def remove_resource(self, user_id: str, link_id: str) -> bool:
        """Remove a ResourceLink from UserSession.
        
        Owner USER links cannot be deleted (system-defined).
        
        Args:
            user_id: User ID
            link_id: ResourceLink ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If trying to delete owner USER link
        """
        instance_id = f"usersession_{user_id}"
        doc_ref = self.firestore.collection(f"usersessions/{instance_id}/resources").document(link_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return False
        
        data = doc.to_dict()
        
        # Owner protection: Cannot delete owner USER link
        if data.get("resource_type") == ResourceType.USER.value and data.get("role") == "owner":
            raise ValueError("Cannot delete owner USER link (system-defined)")
        
        await doc_ref.delete()
        
        logger.info(
            "Removed resource from UserSession",
            extra={"user_id": user_id, "link_id": link_id}
        )
        
        return True
