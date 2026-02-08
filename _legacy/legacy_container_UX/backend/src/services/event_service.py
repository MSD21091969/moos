"""Event service for managing hierarchical session events."""

from datetime import datetime, UTC
from typing import Optional, TYPE_CHECKING
import secrets

from src.models.events import SessionEvent, SessionEventTree, EventType, EventSource, EventStatus
from src.persistence.firestore_client import FirestoreClient
from src.core.exceptions import NotFoundError
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.services.session_service import SessionService

logger = get_logger(__name__)


class EventService:
    """
    Service for managing hierarchical session events.

    Provides:
    - Event creation with automatic hierarchy tracking
    - Event tree retrieval with single query
    - Event status updates
    - Event querying by depth, source, status
    """

    def __init__(
        self, firestore_client: FirestoreClient, session_service: Optional["SessionService"] = None
    ):
        """Initialize event service."""
        self.firestore = firestore_client
        self.session_service = session_service

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"evt_{secrets.token_hex(6)}"

    async def create_event(
        self,
        session_id: str,
        event_type: EventType,
        source: EventSource,
        data: dict,
        parent_event_id: Optional[str] = None,
        status: EventStatus = EventStatus.PENDING,
        metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
    ) -> SessionEvent:
        """
        Create a new session event.

        Args:
            session_id: Parent session ID
            event_type: Type of event
            source: Event source
            data: Event data payload
            parent_event_id: Parent event ID (None for root events)
            status: Initial status
            metadata: Additional metadata
            user_id: User ID for ACL validation (optional, skips check if None)

        Returns:
            Created SessionEvent

        Raises:
            PermissionDeniedError: If user_id provided and doesn't own session
        """
        # ✅ SECURITY: Validate session ownership if user_id provided
        if user_id and self.session_service:
            await self.session_service.get(session_id, user_id)

        event_id = self._generate_event_id()

        # Determine hierarchy
        if parent_event_id:
            # Get parent event to build path
            parent = await self.get_event(session_id, parent_event_id)
            if not parent:
                raise NotFoundError(f"Parent event {parent_event_id} not found")

            event_path = f"{parent.event_path}/{event_id}"
            depth = parent.depth + 1
        else:
            # Root event
            event_path = f"/{event_id}"
            depth = 0

        # Create event
        event = SessionEvent(
            event_id=event_id,
            session_id=session_id,
            parent_event_id=parent_event_id,
            event_path=event_path,
            depth=depth,
            event_type=event_type,
            source=source,
            status=status,
            timestamp=datetime.now(UTC),
            data=data,
            metadata=metadata or {},
        )

        # Save to Firestore: /sessions/{session_id}/events/{event_id}
        event_ref = self.firestore.document(f"sessions/{session_id}/events/{event_id}")
        await event_ref.set(event.model_dump(mode="json"))

        # Auto-increment session counters (only for root events)
        if depth == 0:
            try:
                session_ref = self.firestore.document(f"sessions/{session_id}")
                session_doc = await session_ref.get()

                if session_doc.exists:
                    from google.cloud import firestore as gcp_firestore

                    await session_ref.update(
                        {
                            "event_count": gcp_firestore.Increment(1),
                            "last_event_at": datetime.now(UTC),
                        }
                    )
            except Exception as e:
                logger.warning(
                    "Failed to update event count for session",
                    extra={"session_id": session_id, "error": str(e)},
                )

        logger.info(
            "Created event",
            extra={
                "event_id": event_id,
                "type": event_type.value,
                "source": source.value,
                "depth": depth,
            },
        )
        return event

    async def get_event(
        self, session_id: str, event_id: str, user_id: Optional[str] = None
    ) -> Optional[SessionEvent]:
        """
        Get event by ID.

        Args:
            session_id: Session ID
            event_id: Event ID
            user_id: User ID for ACL validation (optional, skips check if None)

        Returns:
            SessionEvent or None if not found

        Raises:
            PermissionDeniedError: If user_id provided and doesn't own session
        """
        # ✅ SECURITY: Validate session ownership if user_id provided
        if user_id and self.session_service:
            await self.session_service.get(session_id, user_id)

        event_ref = self.firestore.document(f"sessions/{session_id}/events/{event_id}")
        doc = await event_ref.get()

        if not doc.exists:
            return None

        return SessionEvent(**doc.to_dict())

    async def update_event_status(
        self,
        session_id: str,
        event_id: str,
        status: EventStatus,
        result: Optional[any] = None,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SessionEvent:
        """
        Update event status and result.

        Args:
            session_id: Session ID
            event_id: Event ID
            status: New status
            result: Event result (for COMPLETED)
            error: Error message (for FAILED)
            user_id: User ID for ACL validation (optional, skips check if None)

        Returns:
            Updated SessionEvent

        Raises:
            PermissionDeniedError: If user_id provided and doesn't own session
        """
        # ✅ SECURITY: Validate session ownership if user_id provided
        if user_id and self.session_service:
            await self.session_service.get(session_id, user_id)

        event = await self.get_event(session_id, event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found")

        # Update fields
        event.status = status
        event.completed_at = datetime.now(UTC)

        if event.timestamp and event.completed_at:
            delta = event.completed_at - event.timestamp
            event.duration_ms = int(delta.total_seconds() * 1000)

        if result is not None:
            event.result = result

        if error:
            event.error = error

        # Save to Firestore
        event_ref = self.firestore.document(f"sessions/{session_id}/events/{event_id}")
        await event_ref.update(event.model_dump(mode="json"))

        logger.info("Updated event status", extra={"event_id": event_id, "status": status.value})
        return event

    async def get_event_tree(self, session_id: str, event_id: str) -> Optional[SessionEventTree]:
        """
        Get event tree (event + all descendants).

        Uses single query with event_path prefix matching.

        Args:
            session_id: Session ID
            event_id: Root event ID

        Returns:
            SessionEventTree or None if root not found
        """
        # Get root event
        root = await self.get_event(session_id, event_id)
        if not root:
            return None

        # Get all descendants using path prefix query
        # Query: WHERE event_path STARTS WITH root.event_path
        events_collection = self.firestore.collection(f"sessions/{session_id}/events")

        # Get all events that are descendants or the root itself
        docs = (
            await events_collection.where("event_path", ">=", root.event_path)
            .where("event_path", "<", root.event_path + "\uffff")
            .get()
        )

        all_events = [SessionEvent(**doc.to_dict()) for doc in docs]

        # Build tree recursively
        children_map = {}

        # Group events by parent
        for event in all_events:
            if event.event_id == event_id:
                continue  # Skip root

            parent_id = event.parent_event_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(event)

        def build_tree(event: SessionEvent) -> SessionEventTree:
            """Recursively build event tree."""
            children = children_map.get(event.event_id, [])
            child_trees = [build_tree(child) for child in children]
            total_descendants = len(children) + sum(tree.total_descendants for tree in child_trees)
            return SessionEventTree(
                event=event, children=child_trees, total_descendants=total_descendants
            )

        return build_tree(root)

    async def list_events(
        self,
        session_id: str,
        depth: Optional[int] = None,
        source: Optional[EventSource] = None,
        status: Optional[EventStatus] = None,
        event_type_filter: list[EventType] | None = None,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> tuple[list[SessionEvent], int]:
        """
        List session events with filtering.

        OPTIMIZATION STRATEGY (Firestore Index Efficiency):
        - Only depth filter is applied in Firestore (requires composite index: depth + timestamp)
        - Other filters (source, status, event_type) applied in-application to avoid 30+ composite indexes
        - This trades slight memory/CPU for massive reduction in index management burden

        Args:
            session_id: Session ID
            depth: Filter by depth (0=root only, 1=first level children, etc.)
            source: Filter by source (applied in-app)
            status: Filter by status (applied in-app)
            event_type_filter: Filter by event types (applied in-app)
            limit: Max events to return
            offset: Pagination offset
            user_id: User ID for ACL validation (optional, skips check if None)

        Returns:
            (events, total_count) tuple

        Raises:
            PermissionDeniedError: If user_id provided and doesn't own session
        """
        # ✅ SECURITY: Validate session ownership if user_id provided
        if user_id and self.session_service:
            await self.session_service.get(session_id, user_id)

        events_collection = self.firestore.collection(f"sessions/{session_id}/events")

        # STEP 1: Build Firestore query with minimal filters
        # Only use Firestore for depth filter + ordering (requires only 1 composite index)
        if depth is not None:
            query = events_collection.where("depth", "==", depth).order_by("timestamp")
        else:
            # No depth filter: query all events sorted by timestamp
            query = events_collection.order_by("timestamp")

        # STEP 2: Fetch MORE docs than requested to account for app-level filtering
        # If filtering, fetch 5x multiplier to ensure we get enough after filtering
        fetch_multiplier = 5 if (source or status or event_type_filter) else 1
        fetch_limit = limit * fetch_multiplier

        try:
            all_docs = await query.limit(fetch_limit).get()
        except Exception as e:
            logger.error(
                "Failed to query events for session",
                extra={"session_id": session_id, "error": str(e)},
            )
            return [], 0

        # STEP 3: Apply remaining filters in-application (no index needed!)
        filtered_events = []

        for doc in all_docs:
            try:
                event = SessionEvent(**doc.to_dict())
            except Exception as e:
                logger.warning("Failed to parse event", extra={"event_id": doc.id, "error": str(e)})
                continue

            # Apply source filter
            if source and event.source != source:
                continue

            # Apply status filter
            if status and event.status != status:
                continue

            # Apply event_type filter
            if event_type_filter and event.event_type not in event_type_filter:
                continue

            filtered_events.append(event)

            # Stop once we have enough filtered results
            if len(filtered_events) >= limit:
                break

        # STEP 4: Handle pagination on filtered results
        # Extract the requested page from filtered results
        paginated_events = filtered_events[offset : offset + limit]

        # Calculate total count (actual filtered count for this batch)
        # NOTE: This is the count of filtered results up to fetch_limit,
        # not the global count (which would require iterating all docs)
        total = len(filtered_events)

        logger.debug(
            f"List events: fetched {len(all_docs)}, "
            f"filtered {len(filtered_events)}, "
            f"returned {len(paginated_events)}, "
            f"total {total}"
        )

        return paginated_events, total

    async def count_session_events(self, session_id: str) -> int:
        """
        Count total events in session.

        Args:
            session_id: Session ID

        Returns:
            Total event count
        """
        events_collection = self.firestore.collection(f"sessions/{session_id}/events")
        docs = await events_collection.get()
        return len(docs)

    async def delete_event(self, session_id: str, event_id: str) -> None:
        """
        Delete event and all descendants.

        Args:
            session_id: Session ID
            event_id: Event ID to delete
        """
        # Get event to find path
        event = await self.get_event(session_id, event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found")

        # Delete event and all descendants
        events_collection = self.firestore.collection(f"sessions/{session_id}/events")

        # Query all events with matching path prefix
        docs = (
            await events_collection.where("event_path", ">=", event.event_path)
            .where("event_path", "<", event.event_path + "\uffff")
            .get()
        )

        # Delete each event
        for doc in docs:
            event_ref = self.firestore.document(
                f"sessions/{session_id}/events/{doc.get('event_id')}"
            )
            await event_ref.delete()

        logger.info(
            "Deleted event and descendants",
            extra={"event_id": event_id, "descendants_count": len(docs) - 1},
        )
