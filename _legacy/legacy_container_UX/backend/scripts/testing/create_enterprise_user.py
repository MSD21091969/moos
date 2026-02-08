"""Create enterprise@test.com user in production"""

from datetime import UTC, datetime
import bcrypt
from google.cloud import firestore


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_enterprise_user():
    """Create enterprise@test.com user"""
    db = firestore.Client()
    
    user_data = {
        "email": "enterprise@test.com",
        "user_id": "user_enterprise",
        "tier": "ENTERPRISE",
        "permissions": ["all"],
        "quota_limit": 10000,
        "quota_used": 0,
        "password_hash": get_password_hash("test123"),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "is_active": True,
    }
    
    # Check if exists
    users_ref = db.collection("users")
    existing = list(users_ref.where("email", "==", "enterprise@test.com").limit(1).stream())
    
    if existing:
        print("⚠️  enterprise@test.com already exists")
        return
    
    # Create user
    doc_ref = users_ref.document()
    doc_ref.set(user_data)
    
    print("✅ Created enterprise@test.com / test123")


if __name__ == "__main__":
    create_enterprise_user()
