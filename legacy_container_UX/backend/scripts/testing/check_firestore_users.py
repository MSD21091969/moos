"""
Check Firestore for existing users

Usage:
    python scripts/check_firestore_users.py
"""

from google.cloud import firestore


def check_users():
    """List all users in Firestore"""
    try:
        # Initialize Firestore client
        db = firestore.Client(project="mailmind-ai-djbuw", database="my-tiny-data-collider")

        print("🔍 Checking Firestore for users...")
        print("Project: mailmind-ai-djbuw")
        print("Database: my-tiny-data-collider")
        print()

        # Get all users
        users_ref = db.collection("users")
        users = list(users_ref.limit(20).stream())

        if not users:
            print("❌ No users found in Firestore")
            print("\n💡 You need to create a test user:")
            print(
                "   Option 1: Set GOOGLE_APPLICATION_CREDENTIALS and run scripts/create_test_user.py"
            )
            print("   Option 2: Use Swagger UI to create user via API")
            return

        print(f"✅ Found {len(users)} user(s):\n")

        for user_doc in users:
            user = user_doc.to_dict()
            email = user.get("email", "no-email")
            tier = user.get("tier", "unknown")
            quota_limit = user.get("quota_limit", 0)
            quota_used = user.get("quota_used", 0)
            is_active = user.get("is_active", False)

            status = "✅ active" if is_active else "❌ inactive"
            print(f"  {status}")
            print(f"    Email: {email}")
            print(f"    Tier: {tier}")
            print(f"    Quota: {quota_used}/{quota_limit}")
            print(f"    Doc ID: {user_doc.id}")
            print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure GOOGLE_APPLICATION_CREDENTIALS is set:")
        print("   set GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json")


if __name__ == "__main__":
    check_users()
