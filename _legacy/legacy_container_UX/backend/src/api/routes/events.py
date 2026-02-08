"""Event querying API routes.

Handles querying session events and event trees.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from src.api.dependencies import get_user_context
from src.api.models import ErrorResponse
from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.models.context import UserContext
from src.models.events import (
    SessionEvent,
    SessionEventTree,
    SessionEventListResponse,
    EventSource,
    EventStatus,
)
from src.services.event_service import EventService
from src.core.container import get_container
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["Events"])


def get_event_service() -> EventService:
    """Get event service from container."""
    container = get_container()
    from src.services.session_service import SessionService

    session_service = SessionService(container.firestore_client)
    return EventService(container.firestore_client, session_service)


# ============================================================================
# Event Querying
# ============================================================================


@router.get(
    "/{session_id}/events",
    response_model=SessionEventListResponse,
    summary="List session events",
    description="List events in a session with optional filtering",
)
async def list_session_events(
    session_id: str,
    depth: Optional[int] = Query(None, description="Filter by depth (0=root, 1=child, etc.)"),
    source: Optional[str] = Query(None, description="Filter by source (USER, AGENT, TOOL, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, COMPLETED, etc.)"),
    event_type: Optional[str] = Query(
        None, description="Filter by event types (comma-separated: user_message,agent_message)"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_ctx: UserContext = Depends(get_user_context),
    event_service: EventService = Depends(get_event_service),
):
    """
    List events in session with filtering.

    **Authentication Required**: Yes

    **Query Parameters**:
    - depth: Filter by tree depth (0=root events only)
    - source: Filter by event source (USER, AGENT, TOOL, FRAMEWORK, SYSTEM)
    - status: Filter by event status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
    - event_type: Filter by event types (comma-separated: user_message,agent_message)
    - limit: Max events to return (default 50, max 500)
    - offset: Pagination offset (default 0)

    **Example**:
    - `/sessions/{id}/events?depth=0` - Root events only
    - `/sessions/{id}/events?status=FAILED` - Failed events
    - `/sessions/{id}/events?source=AGENT&status=COMPLETED` - Completed agent events
    - `/sessions/{id}/events?event_type=user_message,agent_message` - Message events only
    """
    try:
        # Parse enum values
        source_filter = None
        if source:
            try:
                source_filter = EventSource(source.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid source. Must be one of: {', '.join([s.value for s in EventSource])}",
                )

        status_filter = None
        if status:
            try:
                status_filter = EventStatus(status.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join([s.value for s in EventStatus])}",
                )

        # Parse event_type filter
        event_type_filter = None
        if event_type:
            try:
                from src.models.events import EventType

                # Parse comma-separated event types
                event_type_filter = [EventType(et.strip()) for et in event_type.split(",")]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid event_type: {e}")

        # List events
        events, total = await event_service.list_events(
            session_id=session_id,
            depth=depth,
            source=source_filter,
            status=status_filter,
            event_type_filter=event_type_filter,
            limit=limit,
            offset=offset,
            user_id=user_ctx.user_id,
        )

        # Calculate pagination
        page = (offset // limit) + 1
        has_more = (offset + len(events)) < total

        return SessionEventListResponse(
            session_id=session_id,
            events=events,
            total=total,
            page=page,
            page_size=limit,
            has_more=has_more,
        )

    except HTTPException:
        raise
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to list events", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")


@router.get(
    "/{session_id}/events/{event_id}",
    response_model=SessionEvent,
    responses={404: {"model": ErrorResponse, "description": "Event not found"}},
    summary="Get event details",
)
async def get_event_details(
    session_id: str,
    event_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    event_service: EventService = Depends(get_event_service),
):
    """
    Get details for a specific event.

    **Authentication Required**: Yes

    **Returns**: SessionEvent with all fields including:
    - event_id, parent_event_id, event_path
    - depth, event_type, source, status
    - timestamp, completed_at, duration_ms
    - data, result, error
    - quota_cost
    """
    try:
        event = await event_service.get_event(session_id, event_id, user_ctx.user_id)

        if not event:
            raise HTTPException(
                status_code=404, detail=f"Event '{event_id}' not found in session '{session_id}'"
            )

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get event", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")


@router.get(
    "/{session_id}/events/{event_id}/tree",
    response_model=SessionEventTree,
    responses={404: {"model": ErrorResponse, "description": "Event not found"}},
    summary="Get event tree",
    description="Get event and all descendants in hierarchical structure",
)
async def get_event_tree(
    session_id: str,
    event_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    event_service: EventService = Depends(get_event_service),
):
    """
    Get event tree (event + all descendants).

    Uses efficient single-query retrieval via event_path prefix matching.

    **Authentication Required**: Yes

    **Returns**: SessionEventTree with:
    - event: Root event details
    - children: List of child event trees (recursive)
    - total_descendants: Total number of descendants

    **Example Use Case**:
    Retrieve complete execution tree for an agent invocation to see:
    - Root AGENT_INVOKED event
    - Child TOOL_EXECUTED events
    - Nested tool calls within tools

    **Performance**: Single Firestore query regardless of tree depth.
    """
    try:
        tree = await event_service.get_event_tree(session_id, event_id)

        if not tree:
            raise HTTPException(
                status_code=404, detail=f"Event '{event_id}' not found in session '{session_id}'"
            )

        return tree

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get event tree", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get event tree: {str(e)}")


# ============================================================================
# Trace Explorer Endpoints (PydanticAI-style)
# ============================================================================


@router.get(
    "/{session_id}/trace",
    response_model=list,
    summary="Get trace events for explorer",
    description="""Get flattened event list optimized for trace explorer UI.
    
    Returns events with execution metrics, nested structure indicators,
    and performance data for visualization.
    
    **Use Case**: Power frontend trace explorer tree view
    - Shows event hierarchy with indentation
    - Displays execution times and status
    - Enables filtering by type/status/depth
    """,
)
async def get_trace_events(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event types (comma-separated)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    depth: Optional[int] = Query(None, description="Filter by depth level"),
    user_ctx: UserContext = Depends(get_user_context),
    event_service: EventService = Depends(get_event_service),
):
    """Get trace events with execution metrics."""
    try:
        from src.api.models import TraceEventResponse, EventExecutionSummary

        # Parse filters
        event_type_filter = None
        if event_type:
            try:
                from src.models.events import EventType

                event_type_filter = [EventType(et.strip()) for et in event_type.split(",")]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid event_type: {e}")

        status_filter = None
        if status:
            try:
                status_filter = EventStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        # Get events
        events, total = await event_service.list_events(
            session_id=session_id,
            event_type_filter=event_type_filter,
            status=status_filter,
            depth=depth,
            limit=1000,  # High limit for trace view
            offset=0,
            user_id=user_ctx.user_id,
        )

        # Enhance with trace metadata
        trace_events = []
        for event in events:
            # Calculate child count
            child_events = [e for e in events if e.parent_event_id == event.event_id]

            # Build execution summary
            tools_called = []
            if event.event_type.value.endswith("_execution"):
                tools_called = [event.data.get("tool", "unknown")]

            exec_summary = EventExecutionSummary(
                total_duration_ms=event.duration_ms or 0,
                tools_called=tools_called,
                tokens_used=event.data.get("tokens_used", 0),
                error_count=1 if event.status == EventStatus.FAILED else 0,
                quota_cost=event.quota_cost,
            )

            # Truncate data for preview
            input_preview = None
            output_preview = None
            if event.data:
                input_preview = {k: str(v)[:500] for k, v in event.data.items()}
            if event.result:
                output_preview = str(event.result)[:500]

            trace_event = TraceEventResponse(
                event_id=event.event_id,
                session_id=event.session_id,
                parent_event_id=event.parent_event_id,
                event_path=event.event_path,
                depth=event.depth,
                event_type=event.event_type.value,
                source=event.source.value,
                status=event.status.value,
                timestamp=event.timestamp,
                completed_at=event.completed_at,
                duration_ms=event.duration_ms,
                tool_name=event.data.get("tool") if event.data else None,
                input_preview=input_preview,
                output_preview={"result": output_preview} if output_preview else None,
                error_details=event.error,
                child_count=len(child_events),
                total_descendants=0,  # TODO: Calculate recursively
                execution_summary=exec_summary,
            )
            trace_events.append(trace_event)

        return trace_events

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get trace events", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trace events: {str(e)}")


@router.get(
    "/{session_id}/trace/stats",
    response_model=dict,
    summary="Get trace statistics",
    description="""Get aggregate statistics for session trace.
    
    Returns execution metrics, error rates, quota breakdown,
    and performance percentiles.
    
    **Use Case**: Dashboard widgets and session overview cards
    """,
)
async def get_trace_stats(
    session_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    event_service: EventService = Depends(get_event_service),
):
    """Get session trace statistics."""
    try:
        from src.api.models import TraceStatsResponse
        from collections import defaultdict
        import statistics

        # Get all events
        events, total = await event_service.list_events(
            session_id=session_id,
            limit=5000,
            offset=0,
            user_id=user_ctx.user_id,
        )

        # Calculate statistics
        by_type = defaultdict(int)
        by_status = defaultdict(int)
        quota_breakdown = defaultdict(int)
        durations = []

        for event in events:
            by_type[event.event_type.value] += 1
            by_status[event.status.value] += 1
            quota_breakdown[event.source.value] += event.quota_cost

            if event.duration_ms:
                durations.append(event.duration_ms)

        # Calculate execution time percentiles
        execution_times = {}
        if durations:
            execution_times = {
                "avg_ms": int(statistics.mean(durations)),
                "p50_ms": int(statistics.median(durations)),
                "p95_ms": int(statistics.quantiles(durations, n=20)[18])
                if len(durations) > 1
                else durations[0],
                "min_ms": min(durations),
                "max_ms": max(durations),
            }

        # Calculate error rate
        failed_count = by_status.get("failed", 0)
        error_rate = failed_count / total if total > 0 else 0.0

        stats = TraceStatsResponse(
            session_id=session_id,
            total_events=total,
            by_type=dict(by_type),
            by_status=dict(by_status),
            quota_breakdown=dict(quota_breakdown),
            execution_times=execution_times,
            error_rate=error_rate,
        )

        return stats.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get trace stats", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trace stats: {str(e)}")
