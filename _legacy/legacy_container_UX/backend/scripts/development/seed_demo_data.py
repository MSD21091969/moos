import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.persistence.mock_firestore import MockFirestoreClient


def generate_session_id() -> str:
    """Generate session ID using same logic as SessionService."""
    return f"sess_{uuid.uuid4().hex[:12]}"


def generate_link_id(resource_type: str, resource_id: str) -> str:
    """Generate link ID using same logic as SessionService."""
    import secrets
    suffix = secrets.token_hex(3)
    return f"{resource_type}_{resource_id}_{suffix}"


def seed():
    # Path relative to workspace root
    persist_path = "backend/.firestore_mock_data.json"
    
    print(f"Seeding data to {persist_path}...")
    
    db = MockFirestoreClient(persist_path=persist_path)
    
    # User ID matches what AuthService creates: user_{email_prefix}
    # enterprise@test.com -> user_enterprise
    user_id = "user_enterprise"
    
    # 1. Create UserSession (Workspace Root)
    # Uses same pattern as UserSessionService.get_or_create()
    usersession_id = f"usersession_{user_id}"
    usersession_data = {
        "instance_id": usersession_id,
        "user_id": user_id,
        "created_by": user_id,
        "depth": 0,
        "parent_id": None,
        "acl": {"owner": user_id, "editors": [], "viewers": []},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "preferences": {
            "display_name": "Enterprise User",
            "agent_name": "Navigator",
            "ux_vocabulary": {
                "session": "sticky note",
                "session_plural": "sticky notes"
            }
        }
    }
    db.seed_data("usersessions", usersession_id, usersession_data)
    print(f"Created UserSession: {usersession_id}")
    
    # 2. Create Demo Sessions (IDs generated using same logic as SessionService)
    session_titles = [
        ("Trip to Santorini", 100, 100),
        ("Q4 Marketing Plan", 400, 100),
        ("Product Roadmap", 100, 400),
    ]
    
    for title, x, y in session_titles:
        # Generate ID using same pattern as backend
        session_id = generate_session_id()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_by": user_id,
            "parent_id": usersession_id,
            "depth": 1,
            "status": "active",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "acl": {"owner": user_id, "editors": [], "viewers": []},
            "metadata": {
                "title": title,
                "session_type": "interactive",
                "ttl_hours": 24,
                "is_container": True,
                "visual_state": {
                    "x": x, "y": y, 
                    "width": 250, "height": 200,
                    "color": "#ffffff",
                    "is_minimized": False
                }
            }
        }
        db.seed_data("sessions", session_id, session_data)
        print(f"Created Session: {title} ({session_id})")
        
        # 3. Create ResourceLink for Session (using same pattern as services)
        link_id = generate_link_id("session", session_id)
        link_data = {
            "link_id": link_id,
            "resource_type": "session",
            "resource_id": session_id,
            "instance_id": None,
            "description": title,  # Session title for display
            "added_at": datetime.now(timezone.utc).isoformat(),
            "added_by": "system",
            "enabled": True,
            "preset_params": {},
            "input_mappings": {},
            "metadata": {"x": x, "y": y}
        }
        db.seed_data(f"usersessions/{usersession_id}/resources", link_id, link_data)
        print(f"Created ResourceLink: {link_id}")
        
    # 4. Create ResourceLink for User (Owner)
    user_link_id = generate_link_id("user", user_id)
    user_link_data = {
        "resource_type": "user",
        "resource_id": user_id,
        "role": "owner",
        "added_at": datetime.now(timezone.utc).isoformat(),
        "added_by": user_id,
        "enabled": True,
        "preset_params": {},
        "input_mappings": {},
        "metadata": {}
    }
    db.seed_data(f"usersessions/{usersession_id}/resources", user_link_id, user_link_data)
    print(f"Created ResourceLink: {user_link_id}")

    print("✅ Seeded demo data successfully")

if __name__ == "__main__":
    seed()
