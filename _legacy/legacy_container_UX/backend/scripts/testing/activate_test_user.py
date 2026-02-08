"""
Activate existing test user in Firestore

Usage:
    python scripts/activate_test_user.py
"""

from datetime import datetime

from google.cloud import firestore


def activate_user():
    """Activate test@test.com user with proper settings"""
    try:
        # Initialize Firestore client
        db = firestore.Client(project="mailmind-ai-djbuw", database="my-tiny-data-collider")

        email = "test@test.com"
        print(f"🔧 Activating user: {email}")

        # Get user document
        user_ref = db.collection("users").document(email)
        user_doc = user_ref.get()

        if not user_doc.exists:
            print(f"❌ User {email} not found")
            return

        # Update user to active with quota
        updates = {
            "is_active": True,
            "tier": "ENTERPRISE",
            "quota_limit": 10000,
            "quota_used": 0,
            "updated_at": datetime.utcnow(),
        }

        user_ref.update(updates)
        print("✅ User activated successfully!")
        print(f"   Email: {email}")
        print("   Tier: ENTERPRISE")
        print("   Quota: 0/10000")
        print("   Status: active")
        print("\n💡 You can now test with:")
        print(f"   Username: {email}")
        print("   Password: test123")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    activate_user()
