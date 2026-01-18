
import asyncio
import logging
from app.db import get_user_by_email, init_db
from app.auth import verify_password, get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_auth():
    print("--- Starting Auth Debug ---")
    
    # 1. Initialize DB (to ensure tables exist)
    await init_db()
    
    # 2. Check if user exists
    email = "lola@test.com"
    password = "test123"
    
    print(f"Checking user: {email}")
    user = await get_user_by_email(email)
    
    if not user:
        print("[FAIL] User NOT FOUND in database!")
    else:
        print(f"[OK] User found: {user['email']} (ID: {user['id']})")
        print(f"Stored Hash: {user['password_hash']}")
        
        # 3. Verify Password
        try:
            is_valid = verify_password(password, user["password_hash"])
            if is_valid:
                print("[OK] Password verification SUCCESS")
            else:
                print("[FAIL] Password verification FAILED")
        except Exception as e:
            print(f"[ERROR] Error verifying password: {e}")

    # 4. Test Hashing (to see if library works)
    try:
        test_hash = get_password_hash("test")
        print(f"[OK] Hashing test: {test_hash}")
    except Exception as e:
        print(f"[ERROR] Hashing library error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth())
