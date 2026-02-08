"""Workspace API - User's global view of all tables, workers, and activity.

Provides dashboard-level operations and cross-table insights.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from src.api.dependencies import get_user_context, get_session_service
from src.core.logging import get_logger
from src.models.context import UserContext
from src.services.session_service import SessionService

logger = get_logger(__name__)
router = APIRouter(prefix="/workspace", tags=["Workspace"])


@router.get("")
async def get_workspace_overview(
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Get workspace dashboard overview.

    **Visual Metaphor:** Bird's eye view of all your tables and activity.

    **Returns:**
    - Total tables by status
    - Recent activity across all tables
    - Quota usage summary
    - Quick actions
    """
    try:
        # Get all user sessions for stats
        sessions, total = await session_service.list_user_sessions(
            user_id=user_ctx.user_id,
            page=1,
            page_size=100,
        )

        # Aggregate stats
        stats = {
            "total_tables": total,
            "active_tables": len([s for s in sessions if s.status.value == "active"]),
            "completed_tables": len([s for s in sessions if s.status.value == "completed"]),
            "archived_tables": len([s for s in sessions if s.status.value == "archived"]),
        }

        # User info with implicit context
        user_info = {
            "user_id": user_ctx.user_id,
            "email": user_ctx.email,
            "tier": user_ctx.tier.value,
            "quota_remaining": user_ctx.quota_remaining,
            "permissions": list(user_ctx.permissions),
        }

        # Recent tables (last 5)
        recent_tables = [
            {
                "table_id": s.session_id,
                "title": s.metadata.title,
                "type": s.metadata.session_type.value,
                "last_activity": s.updated_at.isoformat(),
            }
            for s in sorted(sessions, key=lambda x: x.updated_at, reverse=True)[:5]
        ]

        # Available actions based on tier
        actions = ["create_table", "view_tables", "search_tables"]
        if user_ctx.tier.value != "free":
            actions.extend(["share_table", "clone_table", "export_data"])
        if "manage_users" in user_ctx.permissions:
            actions.append("admin_dashboard")

        return {
            "user": user_info,
            "stats": stats,
            "recent_tables": recent_tables,
            "actions": actions,
        }

    except Exception as e:
        logger.error("Failed to load workspace", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load workspace")


@router.get("/tables")
async def list_workspace_tables(
    filter: Optional[str] = None,  # all, active, shared, archived
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    List all tables with workspace-level filtering.

    **Filters:**
    - `all`: All tables
    - `active`: Currently active tables
    - `shared`: Tables shared with me
    - `archived`: Archived tables

    **Visual Metaphor:** Different views of your workspace.
    """
    try:
        # TODO: Implement shared filter when ACL fully implemented
        status_filter = None
        if filter == "active":
            from src.models.sessions import SessionStatus

            status_filter = SessionStatus.ACTIVE
        elif filter == "archived":
            from src.models.sessions import SessionStatus

            status_filter = SessionStatus.ARCHIVED

        sessions, total = await session_service.list_user_sessions(
            user_id=user_ctx.user_id,
            page=1,
            page_size=100,
            status=status_filter,
        )

        tables = [
            {
                "table_id": s.session_id,
                "title": s.metadata.title,
                "type": s.metadata.session_type.value,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "is_shared": len(s.acl) > 1 if s.acl else False,
            }
            for s in sessions
        ]

        return {
            "filter": filter or "all",
            "total": total,
            "tables": tables,
        }

    except Exception as e:
        logger.error("Failed to list tables", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tables")


@router.get("/activity")
async def get_workspace_activity(
    limit: int = 20,
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Get recent activity across all tables.

    **Visual Metaphor:** Activity feed showing what happened at all your tables.

    **Returns:** Chronological list of recent events across all sessions.
    """
    try:
        # Get recent sessions
        sessions, _ = await session_service.list_user_sessions(
            user_id=user_ctx.user_id,
            page=1,
            page_size=50,
        )

        # Collect activity (simplified - in production, query events collection)
        activity = [
            {
                "type": "table_created",
                "table_id": s.session_id,
                "table_title": s.metadata.title,
                "timestamp": s.created_at.isoformat(),
            }
            for s in sorted(sessions, key=lambda x: x.created_at, reverse=True)[:limit]
        ]

        return {
            "activity": activity,
            "count": len(activity),
        }

    except Exception as e:
        logger.error("Failed to load activity", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load activity")


@router.get("/usage")
async def get_workspace_usage(
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Get quota usage and statistics.

    **Visual Metaphor:** See how much capacity you're using.

    **Returns:**
    - Quota remaining
    - Usage trends
    - Tier limits
    - Upgrade options (if applicable)
    """
    try:
        from src.models.permissions import get_quota_limit, get_session_limit

        tier = user_ctx.tier
        daily_limit = get_quota_limit(tier)
        session_limit = get_session_limit(tier)

        usage = {
            "quota": {
                "remaining": user_ctx.quota_remaining,
                "daily_limit": daily_limit,
                "percentage_used": round(
                    ((daily_limit - user_ctx.quota_remaining) / daily_limit * 100), 1
                )
                if daily_limit > 0
                else 0,
            },
            "tier": {
                "current": tier.value,
                "session_limit": session_limit if session_limit != -1 else "unlimited",
            },
            "upgrade_available": tier.value == "free",
        }

        return usage

    except Exception as e:
        logger.error("Failed to load usage", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load usage")
