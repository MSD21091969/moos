"""Seed database with test data for MVP."""

import asyncio
import os
from src.db import (
    async_session,
    init_db,
    User,
    AdminAccount,
    Application,
    AppPermission,
    Node,
)


async def seed():
    """Create test user, admin, application, and nodes."""
    await init_db()

    async with async_session() as session:
        # Check if already seeded
        from sqlalchemy import select

        existing = await session.execute(
            select(User).where(User.email == "superuser@test.com")
        )
        if existing.scalar_one_or_none():
            print("Database already seeded")
            return

        # Get API key from environment
        google_api_key = os.environ.get("GOOGLE_API_KEY", "")

        # Create test user
        user = User(
            email="superuser@test.com",
            firebase_uid="test_superuser",
            profile={"display_name": "Super User"},
            container={
                "permissions": ["*"],
                "secrets": {"GOOGLE_API_KEY": google_api_key},
                "settings": {"theme": "dark"},
            },
        )
        session.add(user)
        await session.flush()

        # Create admin account
        admin = AdminAccount(user_id=user.id)
        session.add(admin)
        await session.flush()

        # Create application1 (CLOUD domain - primary data app)
        app = Application(
            app_id="my-tiny-data-collider",
            display_name="My Tiny Data Collider",
            domain="CLOUD",
            owner_id=admin.id,
            config={
                "features": ["visual_analytics", "data_connectors", "collaboration"]
            },
        )
        session.add(app)
        await session.flush()

        # Create ADMIN domain application
        admin_app = Application(
            app_id="collider-account",
            display_name="Collider Account",
            domain="ADMIN",
            owner_id=admin.id,
            config={"features": ["user_management", "billing", "system_settings"]},
        )
        session.add(admin_app)
        await session.flush()

        # Create FILESYST domain application (IDE integration)
        filesyst_app = Application(
            app_id="collider-ide",
            display_name="Collider IDE",
            domain="FILESYST",
            owner_id=admin.id,
            config={"features": ["code_assist", "native_messaging", "project_tree"]},
        )
        session.add(filesyst_app)
        await session.flush()

        # Create permission for main app
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
            node_metadata={"type": "root"},
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
            node_metadata={"type": "page", "icon": "📊"},
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
            node_metadata={"type": "page", "icon": "⚙️"},
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
