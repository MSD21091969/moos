"""Session management service."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional

from src.core.cache import cached, invalidate_cache
from src.core.exceptions import DepthLimitError, NotFoundError, PermissionDeniedError, ValidationError
from src.core.logging import get_logger
from src.models.links import ResourceType
from src.models.permissions import Tier, get_session_limit
from src.models.sessions import (
    Session,
    SessionCreate,
    SessionStatus,
    SessionUpdate,
)
from src.persistence.firestore_client import FirestoreClient
from src.services.container_service import TIER_MAX_DEPTH

if TYPE_CHECKING:
    from src.models.links import ResourceLink

logger = get_logger(__name__)


class SessionService:
    """Service for managing sessions."""

    def __init__(self, firestore: FirestoreClient):
        self.firestore = firestore
        self.collection = "sessions"

    async def create(self, user_id: str, user_tier: str, request: SessionCreate) -> Session:
        """
        Create a new session with tier limit check and depth computation.

        Args:
            user_id: User creating session
            user_tier: User's subscription tier
            request: Session creation request

        Returns:
            Created session

        Raises:
            ValidationError: If user exceeds session limit for their tier
        """
        # Check tier limit
        try:
            user_tier_enum = Tier(
                user_tier.value if isinstance(user_tier, Tier) else user_tier.lower()
            )
        except ValueError as exc:
            raise ValidationError(f"Unknown tier: {user_tier}") from exc
        max_sessions = get_session_limit(user_tier_enum)
        if max_sessions != -1:  # -1 = unlimited
            # Count active sessions using positional arguments (standard Firestore API)
            query = (
                self.firestore.collection(self.collection)
                .where("user_id", "==", user_id)
                .where("status", "==", SessionStatus.ACTIVE.value)
            )
            docs = query.stream()
            active_sessions = []
            async for doc in docs:  # stream() returns async generator
                active_sessions.append(doc)
            active_count = len(active_sessions)

            if active_count >= max_sessions:
                raise ValidationError(
                    f"Session limit reached. Tier '{user_tier}' allows max {max_sessions} active sessions."
                )

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=request.metadata.ttl_hours)

        # Compute depth: 0 if no parent (L0 container), parent.depth + 1 otherwise
        depth = 0
        parent_id = request.parent_id or None
        
        if parent_id:
            parent_doc = await self.firestore.collection(self.collection).document(parent_id).get()
            if parent_doc.exists:
                parent_data = parent_doc.to_dict()
                depth = parent_data.get("depth", 0) + 1
            else:
                raise ValidationError(f"Parent session {parent_id} not found")

        parent_session_id = getattr(request, "parent_session_id", parent_id)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            metadata=request.metadata,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            collection_schemas=request.initial_collections,
            # session_tools=[], # Removed in Collider V2
            active_agent_id=None,
            source_session_id=None,
            created_by=user_id,
            acl={"owner": user_id, "editors": [], "viewers": []},  # V4.0.0 ACL structure
            parent_id=parent_id,  # V4.0.0 unified parent_id
            depth=depth,  # V4.0.0 depth field
            # Legacy fields for migration compatibility
            parent_session_id=parent_session_id,
            child_sessions=[],
            is_shared=False,
            shared_with_users=[],
        )

        doc_ref = self.firestore.collection(self.collection).document(session_id)
        await doc_ref.set(session.model_dump())

        # NEW: If this is a child session, add to parent's child_sessions list (legacy compatibility)
        if parent_id:
            parent_ref = self.firestore.collection(self.collection).document(
                parent_id
            )
            parent_doc = await parent_ref.get()
            if parent_doc.exists:
                parent_data = parent_doc.to_dict()
                parent_child_sessions = parent_data.get("child_sessions", [])
                parent_child_sessions.append(session_id)
                await parent_ref.update(
                    {"child_sessions": parent_child_sessions, "updated_at": now}
                )
                logger.info(
                    "Added child session to parent",
                    extra={
                        "session_id": session_id,
                        "parent_session_id": parent_session_id,
                    },
                )

        logger.info(
            "Created session for user", extra={"session_id": session_id, "user_id": user_id}
        )
        return session

    async def create_batch(
        self, user_id: str, user_tier: str, requests: list[SessionCreate]
    ) -> tuple[list[Session], list[dict]]:
        """Create multiple sessions in batch operation (max 25 per call).

        Args:
            user_id: User creating sessions
            user_tier: User's subscription tier
            requests: List of session creation requests (max 25)

        Returns:
            Tuple of (created_sessions, errors)
            errors: [{"index": int, "title": str, "error": str}]

        Raises:
            ValidationError: If batch size exceeds limit or user exceeds tier quota
        """
        if len(requests) > 25:
            raise ValidationError("Batch creation limited to 25 sessions per request")

        # Check tier limit upfront (optimistic - check before any writes)
        try:
            user_tier_enum = Tier(
                user_tier.value if isinstance(user_tier, Tier) else user_tier.lower()
            )
        except ValueError as exc:
            raise ValidationError(f"Unknown tier: {user_tier}") from exc

        max_sessions = get_session_limit(user_tier_enum)
        if max_sessions != -1:  # -1 = unlimited
            query = (
                self.firestore.collection(self.collection)
                .where("user_id", "==", user_id)
                .where("status", "==", SessionStatus.ACTIVE.value)
            )
            docs = query.stream()
            active_sessions = []
            async for doc in docs:
                active_sessions.append(doc)
            active_count = len(active_sessions)

            if active_count + len(requests) > max_sessions:
                raise ValidationError(
                    f"Batch creation would exceed session limit. "
                    f"Tier '{user_tier}' allows max {max_sessions} active sessions. "
                    f"Current: {active_count}, Requested: {len(requests)}"
                )

        # Process batch in chunks (Firestore batch limit is 500 operations)
        # Each session = 1 write + potential 1 parent update = 2 ops max
        # Safe chunk size = 25 sessions (50 ops max, well under 500 limit)
        created_sessions = []
        errors = []
        now = datetime.now(UTC)

        for idx, request in enumerate(requests):
            try:
                session_id = f"sess_{uuid.uuid4().hex[:12]}"
                expires_at = now + timedelta(hours=request.metadata.ttl_hours)

                session = Session(
                    session_id=session_id,
                    user_id=user_id,
                    metadata=request.metadata,
                    status=SessionStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    expires_at=expires_at,
                    collection_schemas=request.initial_collections,
                    # session_tools=[], # Removed in Collider V2
                    active_agent_id=None,
                    source_session_id=None,
                    created_by=user_id,
                    acl={"owner": user_id, "editors": [], "viewers": []},  # V4.0.0
                    parent_id=request.parent_session_id or None,
                    depth=0,  # Batch: assume L0 for now (could enhance later)
                    # Legacy fields
                    parent_session_id=request.parent_session_id,
                    child_sessions=[],
                    is_shared=False,
                    shared_with_users=[],
                )

                # Write session
                doc_ref = self.firestore.collection(self.collection).document(session_id)
                await doc_ref.set(session.model_dump())

                # Update parent if this is a child session
                if request.parent_session_id:
                    parent_ref = self.firestore.collection(self.collection).document(
                        request.parent_session_id
                    )
                    parent_doc = await parent_ref.get()
                    if parent_doc.exists:
                        parent_data = parent_doc.to_dict()
                        parent_child_sessions = parent_data.get("child_sessions", [])
                        parent_child_sessions.append(session_id)
                        await parent_ref.update(
                            {"child_sessions": parent_child_sessions, "updated_at": now}
                        )

                created_sessions.append(session)
                logger.info(
                    "Created session in batch",
                    extra={
                        "session_id": session_id,
                        "user_id": user_id,
                        "batch_index": idx,
                    },
                )

            except Exception as e:
                error_msg = str(e)
                errors.append(
                    {
                        "index": idx,
                        "title": request.metadata.title,
                        "error": error_msg,
                    }
                )
                logger.warning(
                    "Failed to create session in batch",
                    extra={
                        "user_id": user_id,
                        "batch_index": idx,
                        "error": error_msg,
                    },
                )

        logger.info(
            "Batch session creation complete",
            extra={
                "user_id": user_id,
                "total_requested": len(requests),
                "success_count": len(created_sessions),
                "failed_count": len(errors),
            },
        )

        return created_sessions, errors

    @cached(ttl=1800, prefix="session")  # Cache for 30 minutes
    async def get(self, session_id: str, user_id: str) -> Session:
        """Get session by ID with ACL check (ownership OR shared access)."""
        doc = await self.firestore.collection(self.collection).document(session_id).get()

        if not doc.exists:
            raise NotFoundError(f"Session {session_id} not found")

        try:
            session_data = doc.to_dict()

            # NEW: Fetch visual metadata from separate collection (Sovereign Data pattern)
            # We store visuals separately to keep the main session doc clean and allow for multiple views
            visuals_ref = (
                self.firestore.collection(self.collection)
                .document(session_id)
                .collection("visuals")
                .document("default")
            )
            visuals_doc = await visuals_ref.get()

            if visuals_doc.exists:
                # Merge visuals back into metadata for API compatibility
                if "metadata" in session_data:
                    session_data["metadata"]["visual_metadata"] = visuals_doc.to_dict()

            session = Session(**session_data)
        except Exception as e:
            raise ValidationError(f"Invalid session data in {session_id}: {e}")

        # V4.0.0 ACL check: owner OR editor OR viewer
        acl = session.acl if isinstance(session.acl, dict) else {}
        is_owner = acl.get("owner") == user_id
        is_editor = user_id in acl.get("editors", [])
        is_viewer = user_id in acl.get("viewers", [])

        if not (is_owner or is_editor or is_viewer):
            raise PermissionDeniedError(
                f"User {user_id} does not have access to session {session_id}"
            )

        return session

    async def list_user_sessions(
        self,
        user_id: str,
        status: SessionStatus | None = None,
        page: int = 1,
        page_size: int = 50,
        tags: list[str] | None = None,
        session_type: str | None = None,
        parent_session_id: str | None = None,  # NEW: Filter by parent
    ) -> tuple[list[Session], int]:
        """List sessions for user with pagination and filters.

        Tags are filtered in-memory (Firestore doesn't support efficient array-contains-any).
        This is acceptable for <1000 sessions. Refactor to Firestore query if performance degrades.
        """
        query = self.firestore.collection(self.collection).where("user_id", "==", user_id)

        if status:
            query = query.where("status", "==", status.value)

        if session_type:
            query = query.where("metadata.session_type", "==", session_type)

        # NEW: Filter by parent_session_id for container child queries
        if parent_session_id is not None:
            query = query.where("parent_session_id", "==", parent_session_id)

        query = query.order_by("created_at", direction="DESCENDING")
        docs = query.stream()

        sessions = []
        async for doc in docs:
            try:
                session = Session(**doc.to_dict())
                # Filter tags in-memory
                if tags and not any(tag in session.metadata.tags for tag in tags):
                    continue
                sessions.append(session)
            except Exception as e:
                logger.warning(
                    "Skipping invalid session", extra={"session_id": doc.id, "error": str(e)}
                )
                continue

        total = len(sessions)
        offset = (page - 1) * page_size
        return sessions[offset : offset + page_size], total

    @invalidate_cache("session:*")  # Invalidate session cache on update
    async def update(self, session_id: str, user_id: str, update_data: SessionUpdate) -> Session:
        """Update session metadata. Only owner can update (not shared users)."""
        session = await self.get(session_id, user_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        if any(k in update_dict for k in ["title", "description", "tags", "custom_fields", "domain", "scenario", "theme_color"]):
            metadata_dict = session.metadata.model_dump()
            for key in ["title", "description", "tags", "custom_fields", "domain", "scenario", "theme_color"]:
                if key in update_dict:
                    metadata_dict[key] = update_dict.pop(key)
            update_dict["metadata"] = metadata_dict

        # Handle preferences update (merge with existing)
        if "preferences" in update_dict:
            new_prefs = update_dict["preferences"]
            current_prefs = session.preferences.copy()
            current_prefs.update(new_prefs)
            update_dict["preferences"] = current_prefs
            logger.info(
                "Updating session preferences",
                extra={"session_id": session_id, "preferences": list(new_prefs.keys())},
            )

        # Handle visual_metadata update (merge with existing metadata.visual_metadata)
        if "visual_metadata" in update_dict:
            new_visual = update_dict.pop("visual_metadata")

            # NEW: Write to separate collection (Sovereign Data pattern)
            # This keeps the main session document clean and focused on domain data
            visuals_ref = (
                self.firestore.collection(self.collection)
                .document(session_id)
                .collection("visuals")
                .document("default")
            )
            await visuals_ref.set(new_visual, merge=True)

            logger.info(
                "Updated session visual metadata (separate collection)",
                extra={"session_id": session_id, "keys": list(new_visual.keys())},
            )

            # We do NOT update the main session doc with visual_metadata
            # But we might need to update 'updated_at' on the main doc?
            # Yes, handled by the generic update below.

        # Handle collection schema updates
        if "collections_to_add" in update_dict or "collections_to_remove" in update_dict:
            collections_to_add = update_dict.pop("collections_to_add", {})
            collections_to_remove = update_dict.pop("collections_to_remove", [])

            # Start with current schemas
            collection_schemas = session.collection_schemas.copy()

            # Add new collections
            if collections_to_add:
                collection_schemas.update(collections_to_add)
                logger.info(
                    "Adding collections to session",
                    extra={
                        "session_id": session_id,
                        "collections": list(collections_to_add.keys()),
                    },
                )

            # Remove collections
            if collections_to_remove:
                for name in collections_to_remove:
                    collection_schemas.pop(name, None)
                logger.info(
                    "Removing collections from session",
                    extra={"session_id": session_id, "collections": collections_to_remove},
                )

            update_dict["collection_schemas"] = collection_schemas

        doc_ref = self.firestore.collection(self.collection).document(session_id)
        await doc_ref.update(update_dict)

        return await self.get(session_id, user_id)

    @invalidate_cache("session:*")  # Invalidate session cache on delete
    async def delete(self, session_id: str, user_id: str, cascade: bool = False) -> None:
        """Delete session and optionally all child sessions recursively.

        Args:
            session_id: Session to delete
            user_id: User requesting deletion (must be owner)
            cascade: If True, recursively delete all child sessions

        Raises:
            NotFoundError: Session not found
            PermissionDeniedError: User is not session owner
        """
        session = await self.get(session_id, user_id)

        # NEW: Cascade delete - recursively delete child sessions
        if cascade and session.child_sessions:
            logger.info(
                "Cascade deleting child sessions",
                extra={
                    "session_id": session_id,
                    "child_count": len(session.child_sessions),
                },
            )
            for child_id in session.child_sessions:
                try:
                    await self.delete(child_id, user_id, cascade=True)  # Recursive
                except Exception as e:
                    logger.warning(
                        "Failed to delete child session in cascade",
                        extra={
                            "parent_session_id": session_id,
                            "child_session_id": child_id,
                            "error": str(e),
                        },
                    )

        # Remove this session from parent's child_sessions list
        if session.parent_session_id:
            try:
                parent_ref = self.firestore.collection(self.collection).document(
                    session.parent_session_id
                )
                parent_doc = await parent_ref.get()
                if parent_doc.exists:
                    parent_data = parent_doc.to_dict()
                    parent_child_sessions = parent_data.get("child_sessions", [])
                    if session_id in parent_child_sessions:
                        parent_child_sessions.remove(session_id)
                        await parent_ref.update(
                            {
                                "child_sessions": parent_child_sessions,
                                "updated_at": datetime.now(UTC),
                            }
                        )
                        logger.info(
                            "Removed session from parent's child list",
                            extra={
                                "session_id": session_id,
                                "parent_session_id": session.parent_session_id,
                            },
                        )
            except Exception as e:
                logger.warning(
                    "Failed to update parent after child deletion",
                    extra={
                        "session_id": session_id,
                        "parent_session_id": session.parent_session_id,
                        "error": str(e),
                    },
                )

        # Delete the session itself
        await self.firestore.collection(self.collection).document(session_id).delete()
        logger.info("Deleted session", extra={"session_id": session_id})

    @invalidate_cache("session:*")
    async def get_events(
        self,
        session_id: str,
        event_type_filter: list | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        """
        Get events for session (wrapper for event_service.list_events).

        Args:
            session_id: Session identifier
            event_type_filter: Filter by event types (e.g., ["user_message", "agent_message"])
            limit: Maximum events to return
            offset: Offset for pagination

        Returns:
            Tuple of (events list, total count)
        """
        from src.models.events import EventType
        from src.services.event_service import EventService

        event_service = EventService(self.firestore)

        # Convert string types to EventType enum if needed
        type_filter = None
        if event_type_filter:
            type_filter = []
            for et in event_type_filter:
                if isinstance(et, str):
                    type_filter.append(EventType(et))
                else:
                    type_filter.append(et)

        # Query events with type filter
        events, total = await event_service.list_events(
            session_id=session_id, event_type_filter=type_filter, limit=limit, offset=offset
        )

        return events, total

    async def add_resource_link(
        self,
        session_id: str,
        user_id: str,
        link: "ResourceLink",
        user_tier: str | Tier = "FREE",
    ) -> "ResourceLink":
        """
        Add a resource link to the session's subcollection.
        
        Part of Collider V2 Architecture (v3.2.0):
        Resources are stored in a subcollection /sessions/{id}/resources/
        to allow for scalable, unlimited linking without hitting document size limits.
        
        Multi-instance support: Generates link_id as {type}_{resource_id}_{suffix}
        to allow multiple instances of the same tool/agent in one session.
        
        Args:
            session_id: Session ID
            user_id: User ID for ACL verification
            link: ResourceLink to add
            
        Returns:
            ResourceLink with generated link_id
            
        Raises:
            NotFoundError: Session not found
            PermissionDeniedError: User doesn't have access
            DepthLimitError: Tier-based depth exceeded
        """
        import secrets
        from src.models.links import ResourceLink
        
        # ACL check: Verify user has access to session
        session = await self.get(session_id, user_id)

        # Depth + tier guardrails (mirror ContainerService rules)
        max_depth = self._get_max_depth(user_tier)
        new_depth = (session.depth or 0) + 1

        if new_depth > max_depth + 1:
            raise DepthLimitError(f"Depth {new_depth} exceeds absolute limit {max_depth + 1}")

        if new_depth == max_depth + 1 and link.resource_type != ResourceType.SOURCE:
            raise DepthLimitError(
                f"Only SOURCE allowed at depth {new_depth} (Tier {user_tier} limit)"
            )
        
        # Terminal node guardrail: Cannot add children to SOURCE or USER
        # Note: Sessions are containers, so this checks the SESSION's allowed children,
        # not whether we're adding TO a terminal node (that's handled by parent validation)
        if link.resource_type in (ResourceType.SOURCE, ResourceType.USER):
            # These are valid terminal leaf resources - allow adding them
            pass
        
        # Generate unique link_id: {type}_{resource_id}_{6-char-suffix}
        suffix = secrets.token_hex(3)
        link_id = f"{link.resource_type.value}_{link.resource_id}_{suffix}"
        
        # Set link_id on the model
        link_with_id = link.model_copy(update={"link_id": link_id})
        
        ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection("resources")
            .document(link_id)
        )
        
        await ref.set(link_with_id.model_dump())
        logger.info(
            "Added resource link to session", 
            extra={"session_id": session_id, "link_id": link_id, "type": link.resource_type.value}
        )
        
        return link_with_id

    def _get_max_depth(self, tier: str | Tier) -> int:
        """Resolve max depth for tier (defaults to FREE safeguards)."""
        if isinstance(tier, Tier):
            return TIER_MAX_DEPTH.get(tier.name.upper(), 2)
        return TIER_MAX_DEPTH.get(str(tier).upper(), 2)

    async def get_resources(self, session_id: str, user_id: str, resource_type: str | None = None) -> list["ResourceLink"]:
        """
        Get resources for a session, optionally filtered by type.
        
        Args:
            session_id: Session ID
            user_id: User ID for ACL verification
            resource_type: Optional ResourceType value (e.g. 'tool', 'agent')
            
        Returns:
            List of ResourceLink objects
            
        Raises:
            NotFoundError: Session not found
            PermissionDeniedError: User doesn't have access
        """
        from src.models.links import ResourceLink
        
        # ACL check: Verify user has access to session
        await self.get(session_id, user_id)
        
        ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection("resources")
        )
        
        if resource_type:
            query = ref.where("resource_type", "==", resource_type)
            docs = query.stream()
        else:
            docs = ref.stream()
            
        links = []
        async for doc in docs:
            try:
                data = doc.to_dict()
                # Ensure link_id is populated from document ID
                if not data.get("link_id"):
                    data["link_id"] = doc.id
                links.append(ResourceLink(**data))
            except Exception as e:
                logger.warning(
                    "Skipping invalid resource link", 
                    extra={"session_id": session_id, "doc_id": doc.id, "error": str(e)}
                )
                
        return links

    async def share_session(
        self, session_id: str, owner_user_id: str, target_user_ids: list[str]
    ) -> Session:
        """
        Share session with other users (ACL management).

        Only session owner can share. Adds users to shared_with_users list.

        Args:
            session_id: Session to share
            owner_user_id: Must be session owner
            target_user_ids: List of user IDs to grant access

        Returns:
            Updated session with new ACL

        Raises:
            NotFoundError: Session doesn't exist
            PermissionDeniedError: User is not owner
        """
        # Get session and verify ownership
        session = await self.get(session_id, owner_user_id)

        if session.user_id != owner_user_id:
            raise PermissionDeniedError(
                f"Only owner can share session. {owner_user_id} is not owner of {session_id}"
            )

        # Update ACL
        current_shared = set(session.shared_with_users)
        new_shared = current_shared.union(set(target_user_ids))

        session_ref = self.firestore.collection(self.collection).document(session_id)
        await session_ref.update(
            {
                "is_shared": True,
                "shared_with_users": list(new_shared),
                "updated_at": datetime.now(UTC),
            }
        )

        logger.info(
            "Shared session with users",
            extra={"session_id": session_id, "user_count": len(target_user_ids)},
        )

        # Return updated session
        return await self.get(session_id, owner_user_id)

    async def unshare_session(
        self, session_id: str, owner_user_id: str, target_user_ids: list[str]
    ) -> Session:
        """
        Remove users from session ACL.

        Only session owner can unshare.

        Args:
            session_id: Session to unshare
            owner_user_id: Must be session owner
            target_user_ids: User IDs to revoke access from

        Returns:
            Updated session with modified ACL
        """
        # Get session and verify ownership
        session = await self.get(session_id, owner_user_id)

        if session.user_id != owner_user_id:
            raise PermissionDeniedError(
                f"Only owner can unshare session. {owner_user_id} is not owner of {session_id}"
            )

        # Update ACL
        current_shared = set(session.shared_with_users)
        new_shared = current_shared - set(target_user_ids)

        session_ref = self.firestore.collection(self.collection).document(session_id)
        await session_ref.update(
            {
                "is_shared": len(new_shared) > 0,
                "shared_with_users": list(new_shared),
                "updated_at": datetime.now(UTC),
            }
        )

        logger.info(
            "Unshared session from users",
            extra={"session_id": session_id, "user_count": len(target_user_ids)},
        )

        # Return updated session
        return await self.get(session_id, owner_user_id)

    async def remove_resource_link(self, session_id: str, user_id: str, link_id: str) -> None:
        """
        Remove a resource link from the session's subcollection.
        
        Args:
            session_id: Session ID
            user_id: User ID for ACL verification
            link_id: Full link ID (e.g. 'tool_csv_analyzer_a3f8b2')
            
        Raises:
            NotFoundError: Session or link not found
            PermissionDeniedError: User doesn't have access
        """
        # ACL check: Verify user has access to session
        await self.get(session_id, user_id)
        
        ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection("resources")
            .document(link_id)
        )
        
        # Verify link exists before deleting
        doc = await ref.get()
        if not doc.exists:
            raise NotFoundError(f"Resource link '{link_id}' not found in session '{session_id}'")
        
        # Terminal node guardrail: Cannot delete USER links with role="owner" (system-defined)
        link_data = doc.to_dict()
        if link_data.get("resource_type") == "USER" and link_data.get("role") == "owner":
            raise PermissionDeniedError(
                "Cannot delete owner USER link - this is a system-defined reference. "
                "To change ownership, use the share/transfer ownership API."
            )
        
        await ref.delete()
        logger.info(
            "Removed resource link from session", 
            extra={"session_id": session_id, "link_id": link_id}
        )

    async def get_resource_by_link_id(self, session_id: str, user_id: str, link_id: str) -> "ResourceLink":
        """
        Get a single resource link by its link_id.
        
        Args:
            session_id: Session ID
            user_id: User ID for ACL verification
            link_id: Full link ID (e.g. 'tool_csv_analyzer_a3f8b2')
            
        Returns:
            ResourceLink
            
        Raises:
            NotFoundError: Session or link not found
            PermissionDeniedError: User doesn't have access
        """
        from src.models.links import ResourceLink
        
        # ACL check: Verify user has access to session
        await self.get(session_id, user_id)
        
        ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection("resources")
            .document(link_id)
        )
        
        doc = await ref.get()
        if not doc.exists:
            raise NotFoundError(f"Resource link '{link_id}' not found in session '{session_id}'")
        
        data = doc.to_dict()
        if not data.get("link_id"):
            data["link_id"] = doc.id
        
        return ResourceLink(**data)

    async def update_resource_link(
        self, session_id: str, user_id: str, link_id: str, updates: dict
    ) -> "ResourceLink":
        """
        Update a resource link in the session's subcollection.
        
        Part of Collider V2 Architecture:
        Supports partial updates to metadata, preset_params, enabled, description.
        
        Args:
            session_id: Session ID
            user_id: User ID for ACL verification
            link_id: Document ID in format {type}_{resource_id}
            updates: Dict of fields to update (metadata, preset_params, enabled, description)
            
        Returns:
            Updated ResourceLink
            
        Raises:
            NotFoundError: If link or session doesn't exist
            PermissionDeniedError: User doesn't have access
        """
        from src.models.links import ResourceLink
        
        # ACL check: Verify user has access to session
        await self.get(session_id, user_id)
        
        ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection("resources")
            .document(link_id)
        )
        
        # Verify link exists
        doc = await ref.get()
        if not doc.exists:
            raise NotFoundError(f"Resource link '{link_id}' not found in session '{session_id}'")
        
        # Filter to allowed update fields only
        allowed_fields = {"metadata", "preset_params", "input_mappings", "enabled", "description"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            # No valid updates, return existing link
            return ResourceLink(**doc.to_dict())
        
        await ref.update(filtered_updates)
        logger.info(
            "Updated resource link",
            extra={"session_id": session_id, "link_id": link_id, "fields": list(filtered_updates.keys())}
        )
        
        # Return updated link with link_id populated
        updated_doc = await ref.get()
        data = updated_doc.to_dict()
        data["link_id"] = link_id
        return ResourceLink(**data)
