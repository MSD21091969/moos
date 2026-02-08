"""Context enrichment helpers - add implicit context to responses.

Philosophy: "Collider emerges complexity out of simplicity"

Simple principle: Every object knows its context and relationships.
No fancy magic, just smart defaults and eager loading where it matters.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from src.models.sessions import Session
from src.persistence.firestore_client import FirestoreClient


async def enrich_session_context(
    session: Session,
    firestore: Optional[FirestoreClient] = None,
) -> Dict[str, Any]:
    """
    Add implicit context to session (table) response.

    Enriches with:
    - contents summary (objects, workers, messages)
    - available actions based on state
    - quick stats

    Simple but powerful: Users see what's on the table without asking.
    """
    session_dict = session.model_dump()

    # Add table_id alias for frontend clarity
    session_dict["table_id"] = session_dict["session_id"]

    # Add contents summary (what's on the table)
    contents = {
        "objects": 0,
        "workers": 0,
        "messages": 0,
    }

    # If firestore provided, do eager counts (optional performance optimization)
    if firestore:
        try:
            # Count documents in this session
            docs_query = firestore.collection("documents").where(
                "session_id", "==", session.session_id
            )
            docs = []
            async for doc in docs_query.stream():
                docs.append(doc)
            contents["objects"] = len(docs)

            # Count workers (resources)
            resources_query = firestore.collection("sessions").document(session.session_id).collection("resources")
            resources = []
            async for res in resources_query.stream():
                resources.append(res)
            contents["workers"] = len(resources)

            # Count events/messages
            events_query = firestore.collection("events").where(
                "session_id", "==", session.session_id
            )
            events = []
            async for event in events_query.stream():
                events.append(event)
            contents["messages"] = len(events)

        except Exception:
            # Silent fail - enrichment is nice-to-have, not critical
            pass

    session_dict["contents"] = contents

    # Add available actions based on status
    actions = []
    if session.status.value == "active":
        actions = [
            "add_object",
            "invite_worker",
            "ask_agent",
            "share",
            "clone",
            "export",
            "archive",
        ]
    elif session.status.value == "completed":
        actions = ["view", "export", "clone", "archive"]
    elif session.status.value == "archived":
        actions = ["view", "restore", "delete_permanently"]

    session_dict["actions"] = actions

    # Add visual hints
    session_dict["color"] = _get_session_color(session)
    session_dict["icon"] = _get_session_icon(session)

    return session_dict


def _get_session_color(session: Session) -> str:
    """Get visual color for session type."""
    colors = {
        "chat": "#3b82f6",  # Blue
        "analysis": "#10b981",  # Green
        "workflow": "#8b5cf6",  # Purple
        "simulation": "#f59e0b",  # Amber
    }
    return colors.get(session.metadata.session_type.value, "#6b7280")


def _get_session_icon(session: Session) -> str:
    """Get visual icon for session type."""
    icons = {
        "chat": "💬",
        "analysis": "📊",
        "workflow": "🔄",
        "simulation": "🎮",
    }
    return icons.get(session.metadata.session_type.value, "📋")


def add_workspace_context(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add implicit workspace context to user data.

    Simple enrichment: Tell users what they can do based on their tier.
    """
    tier = user_data.get("tier", "free")

    # Available actions based on tier
    actions = ["create_table", "view_tables", "search_tables"]

    if tier != "free":
        actions.extend(["share_table", "clone_table", "export_data"])

    if "admin" in user_data.get("permissions", []):
        actions.append("admin_dashboard")

    user_data["actions"] = actions

    # Add upgrade prompt if free tier
    if tier == "free":
        user_data["upgrade_available"] = True
        user_data["upgrade_benefits"] = [
            "More quota",
            "Unlimited tables",
            "Collaboration features",
            "Advanced tools",
        ]

    return user_data


def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time.

    Simple, human-readable timestamps: "5m ago", "2h ago", "3d ago"
    """
    now = datetime.now(dt.tzinfo or None)
    diff = now - dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds / 86400)}d ago"
    else:
        return dt.strftime("%Y-%m-%d")
