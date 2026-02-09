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

from src.core.database import Base, async_session, engine
from src.db.models import AdminAccount, Application, AppPermission, Node, User

# FFS application definitions. Each maps an app_id to its FFS .agent directory.
FFS3_ROOT = Path(__file__).resolve().parent.parent.parent.parent / (
    "FFS3_ColliderApplicationsFrontendServer"
)

APPLICATIONS = [
    {
        "app_id": "application00",
        "display_name": "Collider Sidepanel Browser",
        "domain": "SIDEPANEL",
        "agent_dir": FFS3_ROOT
        / "FFS4_application00_ColliderSidepanelAppnodeBrowser"
        / ".agent",
    },
    {
        "app_id": "application01",
        "display_name": "Collider PiP Agent Seat",
        "domain": "AGENT_SEAT",
        "agent_dir": FFS3_ROOT
        / "FFS5_application01_ColliderPictureInPictureMainAgentSeat"
        / ".agent",
    },
    {
        "app_id": "applicationx",
        "display_name": "Collider IDE",
        "domain": "FILESYST",
        "agent_dir": FFS3_ROOT
        / "FFS6_applicationx_FILESYST_ColliderIDE_appnodes"
        / ".agent",
    },
    {
        "app_id": "applicationz",
        "display_name": "Collider Account Manager",
        "domain": "ADMIN",
        "agent_dir": FFS3_ROOT
        / "FFS7_applicationz_ADMIN_ColliderAccount_appnodes"
        / ".agent",
    },
    {
        "app_id": "application1",
        "display_name": "My Tiny Data Collider",
        "domain": "CLOUD",
        "agent_dir": FFS3_ROOT
        / "FFS8_application1_CLOUD_my-tiny-data-collider_appnodes"
        / ".agent",
    },
    {
        "app_id": "application2",
        "display_name": "Future External Website 1",
        "domain": "CLOUD",
        "agent_dir": FFS3_ROOT
        / "FFS9_application2_CLOUD_future-external-website1_appnodes"
        / ".agent",
    },
    {
        "app_id": "application3",
        "display_name": "Future External Website 2",
        "domain": "CLOUD",
        "agent_dir": FFS3_ROOT
        / "FFS10_application3_CLOUD_future-external-website2_appnodes"
        / ".agent",
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
    """Create dev user, applications, root nodes, and permissions."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. Create dev user
        result = await session.execute(
            select(User).where(User.firebase_uid == "dev-firebase-uid-000")
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email="dev@collider.local",
                firebase_uid="dev-firebase-uid-000",
                profile={"name": "Dev User", "role": "admin"},
            )
            session.add(user)
            await session.flush()
            print(f"  Created dev user: {user.email} ({user.id})")

        # 2. Create admin account
        result = await session.execute(
            select(AdminAccount).where(AdminAccount.user_id == user.id)
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            admin = AdminAccount(user_id=user.id)
            session.add(admin)
            await session.flush()
            print(f"  Created admin account: {admin.id}")

        # 3. Create applications + root nodes
        for app_def in APPLICATIONS:
            result = await session.execute(
                select(Application).where(Application.app_id == app_def["app_id"])
            )
            app = result.scalar_one_or_none()

            if app is not None:
                print(f"  Skipping existing app: {app_def['app_id']}")
                continue

            # Load .agent context
            agent_dir = app_def["agent_dir"]
            if agent_dir.exists():
                container = load_agent_container(agent_dir)
                print(f"  Loaded .agent from {agent_dir}")
            else:
                container = {}
                print(f"  WARNING: .agent dir not found: {agent_dir}")

            # Create application
            app = Application(
                app_id=app_def["app_id"],
                owner_id=admin.id,
                display_name=app_def["display_name"],
                config={"domain": app_def["domain"]},
            )
            session.add(app)
            await session.flush()

            # Create root node
            root_node = Node(
                application_id=app.id,
                path="/",
                container=container,
                metadata_={"domain": app_def["domain"], "is_root": True},
            )
            session.add(root_node)
            await session.flush()

            # Link root node
            app.root_node_id = root_node.id
            await session.flush()

            # Create permissions for dev user
            perm = AppPermission(
                user_id=user.id,
                application_id=app.id,
                can_read=True,
                can_write=True,
                is_admin=True,
            )
            session.add(perm)
            await session.flush()

            print(
                f"  Created app: {app_def['app_id']} "
                f"({app_def['display_name']}) "
                f"root_node={root_node.id}"
            )

        await session.commit()
        print("\nSeeding complete.")


if __name__ == "__main__":
    print("Seeding Collider database...")
    asyncio.run(seed())
