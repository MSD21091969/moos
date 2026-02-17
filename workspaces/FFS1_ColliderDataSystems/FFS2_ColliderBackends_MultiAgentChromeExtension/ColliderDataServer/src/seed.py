"""Database seeder — loads FFS4-10 .agent contexts into the database.

Usage:
    cd ColliderDataServer
    uv run python -m src.seed
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from sqlalchemy import select

from src.core.auth import hash_password
from src.core.database import Base, async_session, engine
from src.db.models import Application, AppPermission, AppRole, Node, SystemRole, User

# FFS6 application definition
APPLICATIONS = [
    {
        "display_name": "Application 1XZ",
    },
]


def _read_text_files(directory: Path) -> list[str]:
    """Read all .md files from a directory and return their contents."""
    if not directory.exists():
        return []
    contents = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix in (".md", ".txt"):
            contents.append(f.read_text(encoding="utf-8"))
    return contents


def _read_yaml_files(directory: Path) -> list[dict]:
    """Read all .yaml/.yml files from a directory."""
    if not directory.exists():
        return []
    items = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data:
                items.append(data)
    return items


def _read_config_files(directory: Path) -> dict:
    """Read all config files into a merged dict, keyed by stem."""
    if not directory.exists():
        return {}
    merged = {}
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data:
                merged[f.stem] = data
    return merged


def load_agent_container(agent_dir: Path) -> dict:
    """Load a .agent directory into a NodeContainer-compatible dict."""
    manifest_path = agent_dir / "manifest.yaml"
    manifest = {}
    if manifest_path.exists():
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}

    return {
        "manifest": manifest,
        "instructions": _read_text_files(agent_dir / "instructions"),
        "rules": _read_text_files(agent_dir / "rules"),
        "skills": _read_text_files(agent_dir / "skills"),
        "tools": _read_yaml_files(agent_dir / "tools"),
        "knowledge": _read_text_files(agent_dir / "knowledge"),
        "workflows": _read_yaml_files(agent_dir / "workflows"),
        "configs": _read_config_files(agent_dir / "configs"),
    }


async def seed():
    """Create seed users, FFS6 application, and permissions."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        print("\n== Seeding Collider Database ==\n")

        # 1. Create seed users
        seed_users = [
            {
                "username": "Sam",
                "password": "Sam",
                "system_role": SystemRole.SUPERADMIN,
            },
            {
                "username": "Lola",
                "password": "Lola",
                "system_role": SystemRole.COLLIDER_ADMIN,
            },
            {
                "username": "Menno",
                "password": "Menno",
                "system_role": SystemRole.COLLIDER_ADMIN,
            },
        ]

        created_users = []
        for user_data in seed_users:
            result = await session.execute(
                select(User).where(User.username == user_data["username"])
            )
            user = result.scalar_one_or_none()

            if user is None:
                password = user_data.pop("password")
                user = User(
                    **user_data,
                    password_hash=hash_password(password),
                )
                session.add(user)
                await session.flush()
                print(f"[+] Created user: {user.username} ({user.system_role.value})")
            else:
                print(f"[-] User already exists: {user.username}")

            created_users.append(user)

        # Get Lola as default app owner
        lola = next(u for u in created_users if u.username == "Lola")

        # 2. Create FFS6 application with empty root node
        for app_def in APPLICATIONS:
            result = await session.execute(
                select(Application).where(
                    Application.display_name == app_def["display_name"]
                )
            )
            app = result.scalar_one_or_none()

            if app is not None:
                print(f"[-] App already exists: {app_def['display_name']}")
                continue

            # Create application
            app = Application(
                owner_id=lola.id,
                display_name=app_def["display_name"],
                config={},
            )
            session.add(app)
            await session.flush()

            # Create root node
            root_node = Node(
                application_id=app.id,
                parent_id=None,
                path="/",
                container={
                    "manifest": {"title": "x1z Root", "version": "1.0"},
                    "instructions": [
                        "Root container for Collider x1z application tree"
                    ],
                    "rules": [],
                    "skills": [],
                    "tools": [],
                    "knowledge": [],
                    "workflows": [],
                    "configs": {},
                },
                metadata_={"frontend_app": "ffs6", "frontend_route": "/"},
            )
            session.add(root_node)
            await session.flush()

            # Create /admin node
            admin_node = Node(
                application_id=app.id,
                parent_id=root_node.id,
                path="/admin",
                container={
                    "manifest": {
                        "title": "Administration",
                        "rbac": ["superadmin", "collider_admin"],
                    },
                    "instructions": ["Admin section for system management"],
                    "rules": [],
                    "skills": [],
                    "tools": [],
                    "knowledge": [],
                    "workflows": [],
                    "configs": {},
                },
                metadata_={"frontend_app": "ffs6", "frontend_route": "/admin"},
            )
            session.add(admin_node)
            await session.flush()

            # Create /admin/assign-roles node
            assign_roles_node = Node(
                application_id=app.id,
                parent_id=admin_node.id,
                path="/admin/assign-roles",
                container={
                    "manifest": {
                        "title": "Assign System Roles",
                        "rbac": ["superadmin", "collider_admin"],
                    },
                    "instructions": [
                        "Only SUPERADMIN and COLLIDER_ADMIN can assign system roles",
                        "COLLIDER_ADMIN can only assign APP_ADMIN or APP_USER roles",
                    ],
                    "rules": [],
                    "skills": [],
                    "tools": [],
                    "knowledge": [],
                    "workflows": [],
                    "configs": {},
                },
                metadata_={
                    "frontend_app": "ffs6",
                    "frontend_route": "/admin/assign-roles",
                },
            )
            session.add(assign_roles_node)
            await session.flush()

            # Create /admin/grant-permission node
            grant_permission_node = Node(
                application_id=app.id,
                parent_id=admin_node.id,
                path="/admin/grant-permission",
                container={
                    "manifest": {
                        "title": "Grant App Permissions",
                        "rbac": ["superadmin", "collider_admin", "app_admin"],
                    },
                    "instructions": [
                        "View and approve pending access requests",
                        "Grant app_admin or app_user permissions",
                    ],
                    "rules": [],
                    "skills": [],
                    "tools": [],
                    "knowledge": [],
                    "workflows": [],
                    "configs": {},
                },
                metadata_={
                    "frontend_app": "ffs6",
                    "frontend_route": "/admin/grant-permission",
                },
            )
            session.add(grant_permission_node)
            await session.flush()

            # Link root node
            app.root_node_id = root_node.id
            await session.flush()

            # Grant all seed users app_admin role on the app
            for user in created_users:
                perm = AppPermission(
                    user_id=user.id,
                    application_id=app.id,
                    role=AppRole.APP_ADMIN,
                )
                session.add(perm)

            await session.flush()
            print(
                f"[+] Created app: {app_def['display_name']} (owner: {lola.username})"
            )

        await session.commit()
        print("\n== Seeding Complete ==\n")
        print("Login credentials:")
        print("  Sam/Sam (superadmin)")
        print("  Lola/Lola (collider_admin)")
        print("  Menno/Menno (collider_admin)")
        print()


if __name__ == "__main__":
    print("Seeding Collider database...")
    asyncio.run(seed())
