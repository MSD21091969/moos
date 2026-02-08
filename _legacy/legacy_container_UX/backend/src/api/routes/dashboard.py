"""Dashboard statistics API endpoints.

Handles:
- Get dashboard overview statistics
- Get session activity feed
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_user_context
from src.api.models import DashboardStatsResponse, SessionActivityResponse, ActivityItem
from src.models.context import UserContext
from src.core.container import get_container
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _parse_timestamp(ts_value) -> datetime:
    """Parse timestamp from various formats to datetime object."""
    if isinstance(ts_value, datetime):
        return ts_value
    if isinstance(ts_value, str):
        return datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(user_ctx: UserContext = Depends(get_user_context)):
    """
    Get dashboard overview statistics for visualization.

    **Authentication Required**: Yes

    **Returns**:
    - Total sessions, messages, tool calls
    - Most used tools/agents
    - Quota usage trends (7-day chart data)
    - Recent activity timeline
    - Session distribution by status

    **Use Cases**:
    - Main dashboard visualization
    - Analytics overview
    - Quick insights into usage patterns

    **Frontend Integration**:
    ```typescript
    const stats = await fetch('/dashboard/stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Display in dashboard cards
    <DashboardCard title="Sessions" value={stats.total_sessions} />
    <DashboardCard title="Messages" value={stats.total_messages} />

    // Usage trend chart
    <LineChart data={stats.quota_usage_trend} />

    // Top tools list
    <ToolsList tools={stats.most_used_tools} />
    ```
    """
    try:
        container = get_container()
        firestore = container.firestore_client

        # Get user's sessions
        sessions_ref = firestore.collection("sessions").where("user_id", "==", user_ctx.user_id)
        sessions = []
        async for session in sessions_ref.stream():
            sessions.append(session)

        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.to_dict().get("status") == "active")

        # Session distribution
        session_distribution: Dict[str, int] = {}
        for session in sessions:
            status = session.to_dict().get("status", "unknown")
            session_distribution[status] = session_distribution.get(status, 0) + 1

        # Count messages across all sessions
        total_messages = 0
        total_tool_calls = 0
        tool_usage: Dict[str, int] = {}

        for session in sessions:
            session_id = session.id
            # Count messages in this session
            # NOTE: For large sessions, this could be memory-intensive
            # TODO: Consider using Firestore count() aggregation when available
            messages_ref = firestore.collection(f"sessions/{session_id}/messages")
            messages = []
            async for msg in messages_ref.stream():
                messages.append(msg)
            total_messages += len(messages)

            # Count tool calls
            events_ref = firestore.collection(f"sessions/{session_id}/events")
            events = []
            async for event in events_ref.stream():
                events.append(event)
            for event in events:
                event_data = event.to_dict()
                if event_data.get("event_type") == "tool_execution":
                    total_tool_calls += 1
                    tool_name = event_data.get("tool_name", "unknown")
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        # Most used tools (top 5)
        most_used_tools = [
            {"name": tool_name, "count": count, "last_used": datetime.now(timezone.utc).isoformat()}
            for tool_name, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Quota usage trend (7 days)
        # TODO: Implement actual quota calculation from quota_usage collection
        # For now, returns default structure with zero usage
        quota_usage_trend = []
        for i in range(7):
            date = (datetime.now(timezone.utc) - timedelta(days=6 - i)).date().isoformat()
            quota_usage_trend.append(
                {
                    "date": date,
                    "used": 0,  # Will be calculated from quota_usage collection
                    "limit": 100 if user_ctx.tier.value == "free" else 1000,
                }
            )

        # Recent activity (last 10 items)
        recent_activity = []
        for session in sessions[:10]:
            session_data = session.to_dict()
            created_at = session_data.get("created_at", datetime.now(timezone.utc))
            timestamp_iso = (
                created_at.isoformat()
                if isinstance(created_at, datetime)
                else created_at
                if isinstance(created_at, str)
                else datetime.now(timezone.utc).isoformat()
            )
            recent_activity.append(
                {
                    "type": "session",
                    "timestamp": timestamp_iso,
                    "session_id": session.id,
                    "preview": session_data.get("title", "Untitled Session")[:50],
                }
            )

        return DashboardStatsResponse(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            total_messages=total_messages,
            total_tool_calls=total_tool_calls,
            most_used_tools=most_used_tools,
            most_used_agents=[],  # Would fetch from agent usage tracking
            quota_usage_trend=quota_usage_trend,
            recent_activity=recent_activity,
            session_distribution=session_distribution,
        )

    except Exception as e:
        logger.error(
            "Failed to get dashboard stats",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        # Return fallback with empty data
        return DashboardStatsResponse(
            total_sessions=0,
            active_sessions=0,
            total_messages=0,
            total_tool_calls=0,
            most_used_tools=[],
            most_used_agents=[],
            quota_usage_trend=[],
            recent_activity=[],
            session_distribution={},
        )


@router.get("/sessions/{session_id}/activity", response_model=SessionActivityResponse)
async def get_session_activity(
    session_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum activities to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Get chronological activity feed for a specific session.

    **Authentication Required**: Yes

    **Returns**:
    - Messages (user/assistant)
    - Tool calls with results
    - Document uploads
    - Agent switches
    - Formatted for timeline UI component

    **Use Cases**:
    - Session detail view
    - Activity timeline
    - Audit log

    **Frontend Integration**:
    ```typescript
    const activity = await fetch(`/dashboard/sessions/${sessionId}/activity`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Display in timeline
    <Timeline>
      {activity.activities.map(item => (
        <TimelineItem
          key={item.activity_id}
          timestamp={item.timestamp}
          type={item.activity_type}
          content={item.message_content || item.tool_name}
        />
      ))}
    </Timeline>
    ```
    """
    try:
        container = get_container()
        firestore = container.firestore_client

        # Verify session exists and user has access
        session_ref = firestore.collection("sessions").document(session_id)
        session_doc = await session_ref.get()

        if not session_doc.exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        session_data = session_doc.to_dict()
        if session_data.get("user_id") != user_ctx.user_id:
            raise HTTPException(status_code=403, detail="Access denied to this session")

        # Collect activities from messages and events
        activities: List[ActivityItem] = []

        # Get messages
        messages_ref = (
            firestore.collection(f"sessions/{session_id}/messages")
            .order_by("timestamp")
            .limit(limit)
        )
        messages = []
        async for msg in messages_ref.stream():
            messages.append(msg)

        for msg in messages:
            msg_data = msg.to_dict()
            timestamp = _parse_timestamp(msg_data.get("timestamp"))

            activities.append(
                ActivityItem(
                    activity_id=msg.id,
                    activity_type="message",
                    timestamp=timestamp,
                    user_id=session_data.get("user_id", user_ctx.user_id),
                    session_id=session_id,
                    message_content=msg_data.get("content", "")[:200],  # Truncate
                    message_role=msg_data.get("role", "user"),
                    metadata={},
                )
            )

        # Get tool execution events
        events_ref = (
            firestore.collection(f"sessions/{session_id}/events")
            .where("event_type", "==", "tool_execution")
            .limit(limit)
        )
        events = []
        async for event in events_ref.stream():
            events.append(event)

        for event in events:
            event_data = event.to_dict()
            timestamp = _parse_timestamp(event_data.get("timestamp"))

            activities.append(
                ActivityItem(
                    activity_id=event.id,
                    activity_type="tool_call",
                    timestamp=timestamp,
                    user_id=session_data.get("user_id", user_ctx.user_id),
                    session_id=session_id,
                    message_role=None,  # Not applicable for tool_call
                    document_name=None,  # Not applicable for tool_call
                    agent_id=None,  # Not applicable for tool_call
                    tool_name=event_data.get("tool_name", "unknown"),
                    tool_result=str(event_data.get("output", ""))[:200],  # Truncate
                    metadata={
                        "duration_ms": event_data.get("duration_ms", 0),
                        "status": event_data.get("status", "unknown"),
                    },
                )
            )

        # Sort activities by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total_count = len(activities)
        activities = activities[offset : offset + limit]
        has_more = (offset + limit) < total_count

        return SessionActivityResponse(
            session_id=session_id, activities=activities, total_count=total_count, has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get session activity",
            extra={"session_id": session_id, "user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get session activity: {str(e)}")
