import asyncio
import sys
from sqlalchemy import select
from src.core.database import async_session
from src.db.models import User, SystemRole, Application, AppAccessRequest
from src.core.auth import hash_password

async def seed_data():
    async with async_session() as db:
        print("Seeding data...")

        # 1. Ensure 'Sam' exists and is SUPERADMIN
        print("Checking 'Sam' user...")
        result = await db.execute(select(User).where(User.username == "Sam"))
        sam = result.scalar_one_or_none()
        
        valid_password_hash = hash_password("Sam")
        
        if sam:
            print(f"Updating 'Sam' role to SUPERADMIN (current: {sam.system_role})")
            sam.system_role = SystemRole.SUPERADMIN
            sam.password_hash = valid_password_hash # Ensure password is 'Sam'
        else:
            print("Creating 'Sam' as SUPERADMIN")
            sam = User(
                username="Sam",
                password_hash=valid_password_hash,
                system_role=SystemRole.SUPERADMIN
            )
            db.add(sam)
        
        await db.flush()

        # 2. Create other Users idempotently
        users_data = [
            ("super_admin", SystemRole.SUPERADMIN),
            ("collider_admin", SystemRole.COLLIDER_ADMIN),
            ("app_owner", SystemRole.APP_ADMIN),
            ("regular_joe", SystemRole.APP_USER),
        ]

        user_map = {}
        msg_hash = hash_password("password")
        for username, role in users_data:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if not user:
                print(f"Creating user {username}")
                user = User(
                    username=username,
                    password_hash=msg_hash,
                    system_role=role
                )
                db.add(user)
            # Update password for existing too, just in case
            user.password_hash = msg_hash
            user_map[username] = user
        
        await db.flush() # get IDs

        # 3. Create Applications idempotently
        # We need owners to exist
        if "app_owner" in user_map:
            owner = user_map["app_owner"]
        else:
            # fetch if it was existing
            result = await db.execute(select(User).where(User.username == "app_owner"))
            owner = result.scalar_one_or_none()

        apps_data = [
            ("Finance Dashboard", "ADMIN", owner.id if owner else sam.id),
            ("Cloud Resources", "CLOUD", sam.id),
            ("Local Files", "FILESYST", sam.id),
        ]

        app_map = {}
        for name, domain, owner_id in apps_data:
            result = await db.execute(select(Application).where(Application.display_name == name))
            app = result.scalar_one_or_none()
            if not app:
                print(f"Creating app {name}")
                app = Application(
                    display_name=name,
                    owner_id=owner_id,
                    config={"domain": domain}
                )
                db.add(app)
            app_map[name] = app

        await db.flush()

        # 4. Create Access Requests
        # ... logic for requests (simplified for now to avoid complexity with existing checks)
        
        await db.commit()
        print("Seeding complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
