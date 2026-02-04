"""Seed database with test data for MVP."""
import asyncio
from src.db import async_session, User, AdminAccount, Application, AppPermission, Node


async def seed():
    """Create test user, admin, application, and nodes."""
    async with async_session() as session:
        # Check if already seeded
        from sqlalchemy import select
        existing = await session.execute(select(User).where(User.email == "superuser@test.com"))
        if existing.scalar_one_or_none():
            print("Database already seeded")
            return

        # Create test user
        user = User(
            email="superuser@test.com",
            firebase_uid="test_superuser",
            profile={"display_name": "Super User"},
            container={"permissions": ["*"], "secrets": {}, "settings": {"theme": "dark"}},
        )
        session.add(user)
        await session.flush()

        # Create admin account
        admin = AdminAccount(user_id=user.id)
        session.add(admin)
        await session.flush()

        # Create application1
        app = Application(
            app_id="application1",
            display_name="My Test App",
            owner_id=admin.id,
            config={"api_rules": {}, "rate_limits": {"default": 100}},
        )
        session.add(app)
        await session.flush()

        # Create permission
        perm = AppPermission(
            user_id=user.id,
            application_id=app.id,
            can_read=True,
            can_write=True,
            is_admin=True,
        )
        session.add(perm)

        # Create nodes
        root = Node(
            application_id=app.id,
            path="/",
            container={
                "manifest": {"version": "1.0"},
                "instructions": ["Root node of the application"],
                "rules": [],
                "skills": [],
                "tools": [],
                "knowledge": [],
                "workflows": [],
                "configs": {},
            },
            metadata={"type": "root"},
        )
        session.add(root)
        await session.flush()

        dashboard = Node(
            application_id=app.id,
            parent_id=root.id,
            path="/dashboard",
            container={
                "manifest": {},
                "instructions": ["Dashboard view - show metrics and quick actions"],
                "rules": ["Always provide helpful summaries"],
                "skills": ["data_analysis"],
                "tools": [{"name": "chart_tool", "description": "Generate charts"}],
                "knowledge": [],
                "workflows": [],
                "configs": {},
            },
            metadata={"type": "page", "icon": "📊"},
        )
        session.add(dashboard)

        settings = Node(
            application_id=app.id,
            parent_id=root.id,
            path="/settings",
            container={
                "manifest": {},
                "instructions": ["Settings panel - manage user preferences"],
                "rules": [],
                "skills": [],
                "tools": [],
                "knowledge": [],
                "workflows": [],
                "configs": {},
            },
            metadata={"type": "page", "icon": "⚙️"},
        )
        session.add(settings)

        # Update root_node_id
        app.root_node_id = root.id

        await session.commit()
        print("✅ Database seeded with test data:")
        print(f"   User: superuser@test.com")
        print(f"   App: application1")
        print(f"   Nodes: /, /dashboard, /settings")


if __name__ == "__main__":
    asyncio.run(seed())
