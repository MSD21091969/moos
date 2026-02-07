"""
Create test users in production Firestore

Usage:
    python scripts/create_test_user.py
"""

from datetime import UTC, datetime

import bcrypt
from google.cloud import firestore


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt directly (avoid passlib compatibility issues)"""
    # bcrypt has 72-byte password limit
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError(f"Password too long: {len(password_bytes)} bytes (max 72)")

    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_test_users():
    """Create test users in Firestore"""
    # Initialize Firestore client
    db = firestore.Client()

    # Test user data
    test_users = [
        {
            "email": "test@example.com",
            "user_id": "user_test",
            "tier": "ENTERPRISE",
            "permissions": ["all"],
            "quota_limit": 10000,
            "quota_used": 0,
            "password_hash": get_password_hash("test123"),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "is_active": True,
        }
    ]

    print("Creating test users in production Firestore...")

    for user_data in test_users:
        email = user_data["email"]

        # Check if user already exists
        users_ref = db.collection("users")
        existing = list(users_ref.where("email", "==", email).limit(1).stream())

        if existing:
            print(f"⚠️  User {email} already exists, skipping...")
            continue

        # Create user document
        doc_ref = users_ref.document()
        doc_ref.set(user_data)

        print(f"✅ Created user: {email} (tier: {user_data['tier']})")

    print("\n✅ Test users created successfully!")
    print("You can now run: python test_production_chatagent.py")


if __name__ == "__main__":
    create_test_users()
