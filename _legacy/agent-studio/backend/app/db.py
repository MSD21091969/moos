"""
SQLite database for conversation persistence.
"""
import aiosqlite
from datetime import datetime
from typing import Optional
from app.deps import DB_PATH

async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Phase 6: UserObject Auth System
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'ACCOUNTUSER',
                display_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Phase B: Collider Containers & ACL
        await db.execute("""
            CREATE TABLE IF NOT EXISTS containers (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                parent_id TEXT,
                name TEXT NOT NULL,
                definition_id TEXT,
                visual_x REAL DEFAULT 0.0,
                visual_y REAL DEFAULT 0.0,
                visual_color TEXT DEFAULT '#3b82f6',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS container_acl (
                id TEXT PRIMARY KEY,
                container_id TEXT NOT NULL,
                grantee_id TEXT NOT NULL,
                permission TEXT NOT NULL DEFAULT 'read',
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (container_id) REFERENCES containers(id),
                FOREIGN KEY (grantee_id) REFERENCES users(id)
            )
        """)

        # Phase A.5: Canvas storage - stores canvas metadata per user
        await db.execute("""
            CREATE TABLE IF NOT EXISTS canvasses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                container_id TEXT,
                name TEXT NOT NULL DEFAULT 'Lody''s Canvas',
                files TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Add missing columns if they don't exist
        try:
            await db.execute("ALTER TABLE canvasses ADD COLUMN container_id TEXT")
        except Exception:
            pass  # Column already exists
            
        try:
            await db.execute("ALTER TABLE canvasses ADD COLUMN is_draft INTEGER DEFAULT 1")
        except Exception:
            pass  # Column already exists

        try:
            await db.execute("ALTER TABLE canvasses ADD COLUMN rules TEXT DEFAULT '{}'")
        except Exception:
            pass  # Column already exists
        
        await db.commit()
        
        # Seed initial users
        await seed_users(db)


from app.auth import get_password_hash

async def seed_users(db: aiosqlite.Connection):
    """Seed initial users and their containers if they don't exist."""
    # Generate hash dynamically to ensure compatibility with installed library
    test123_hash = get_password_hash("test123")
    
    users = [
        ("superuser@test.com", "ADMIN", "superuser@test.com"),
        ("lola@test.com", "ACCOUNTUSER", "lola@test.com"),
        ("menno@test.com", "ACCOUNTUSER", "menno@test.com"),
    ]
    
    import uuid
    
    # Track user IDs for ACL sharing
    user_ids = {}
    
    # 1. Ensure users exist
    for email, role, name in users:
        cursor = await db.execute("SELECT id, display_name FROM users WHERE email = ?", (email,))
        existing = await cursor.fetchone()
        
        if existing:
            user_ids[email] = existing[0]
            # Optionally update display name to match email if it changed (self-healing)
            # existing[1] is display_name
            if existing[1] != name: 
                 await db.execute("UPDATE users SET display_name = ? WHERE id = ?", (name, existing[0]))
        else:
            user_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO users (id, email, password_hash, role, display_name) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, test123_hash, role, name)
            )
            print(f"Seeded user: {email} ({role})")
            user_ids[email] = user_id
            
    await db.commit()
    
    # 2. Ensure each user has one "Home" container
    container_ids = []
    
    for email, user_id in user_ids.items():
        # check if user has any container
        cursor = await db.execute("SELECT id FROM containers WHERE owner_id = ?", (user_id,))
        existing_container = await cursor.fetchone()
        
        cid = None
        if existing_container:
            cid = existing_container[0]
        else:
            cid = str(uuid.uuid4())
            _, _, display_name = next(u for u in users if u[0] == email)
            # Strict Rule: Container Name = User Name = Email
            cont_name = display_name
            
            # Assign separate colors based on user
            if email == "superuser@test.com":
                color = "#ef4444" # Red
            elif email == "lola@test.com":
                color = "#db2777" # Pink
            else:
                color = "#3b82f6" # Blue (Menno/Default)

            await db.execute(
                """INSERT INTO containers 
                   (id, owner_id, name, visual_color) 
                   VALUES (?, ?, ?, ?)""",
                (cid, user_id, cont_name, color)
            )
            print(f"Seeded container for {email}: {cont_name}")
            
            # Auto-creation of default canvas removed as per user request.
            # User must manually create canvases via the UI (+) button.
        
        if cid:
            container_ids.append(cid)
            
    await db.commit()
    
    # 3. Share ALL containers with ALL users (Mesh ACL)
    # Grant 'editor' permission
    for cid in container_ids:
        for email, uid in user_ids.items():
            # Check if ACL exists
            cursor = await db.execute(
                "SELECT id FROM container_acl WHERE container_id = ? AND grantee_id = ?",
                (cid, uid)
            )
            existing_acl = await cursor.fetchone()
            
            if not existing_acl:
                acl_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO container_acl 
                       (id, container_id, grantee_id, permission) 
                       VALUES (?, ?, ?, ?)""",
                    (acl_id, cid, uid, 'editor')
                )
    
    await db.commit()


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_conversation(title: Optional[str] = None) -> int:
    """Create a new conversation and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title or "New Chat",)
        )
        await db.commit()
        return cursor.lastrowid


async def add_message(conversation_id: int, role: str, content: str) -> int:
    """Add a message to a conversation."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        await db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.now(), conversation_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_conversations() -> list[dict]:
    """Get all conversations."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_messages(conversation_id: int) -> list[dict]:
    """Get all messages for a conversation."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_conversation(conversation_id: int):
    """Delete a conversation and its messages."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await db.commit()


# === Canvas CRUD Operations ===

import json
import uuid as uuid_module

async def get_user_canvasses(user_id: str) -> list[dict]:
    """Get all canvasses visible to a user (owned or in shared containers)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT DISTINCT cv.* 
            FROM canvasses cv
            LEFT JOIN containers ct ON cv.container_id = ct.id
            LEFT JOIN container_acl acl ON ct.id = acl.container_id
            WHERE cv.user_id = ? 
               OR ct.owner_id = ? 
               OR acl.grantee_id = ?
            ORDER BY cv.created_at
            """,
            (user_id, user_id, user_id)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            canvas = dict(row)
            try:
                canvas['files'] = json.loads(canvas['files'])
            except:
                canvas['files'] = []
            result.append(canvas)
        return result


async def get_canvas(canvas_id: str) -> Optional[dict]:
    """Get a single canvas by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM canvasses WHERE id = ?",
            (canvas_id,)
        )
        row = await cursor.fetchone()
        if row:
            canvas = dict(row)
            canvas['files'] = json.loads(canvas['files'])
            return canvas
        return None


async def create_canvas(user_id: str, name: str = "Lody's Canvas", files: list = None, container_id: str = None) -> dict:
    """Create a new canvas for a user. If container_id is set, canvas belongs to a Collider container."""
    canvas_id = str(uuid_module.uuid4())
    files_json = json.dumps(files if files else [])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO canvasses (id, user_id, container_id, name, files) VALUES (?, ?, ?, ?, ?)",
            (canvas_id, user_id, container_id, name, files_json)
        )
        await db.commit()
    return await get_canvas(canvas_id)


async def update_canvas(canvas_id: str, name: Optional[str] = None, files: Optional[list] = None, is_draft: Optional[int] = None, container_id: Optional[str] = None) -> Optional[dict]:
    """Update a canvas."""
    async with aiosqlite.connect(DB_PATH) as db:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if files is not None:
            updates.append("files = ?")
            params.append(json.dumps(files))
        if is_draft is not None:
            updates.append("is_draft = ?")
            params.append(is_draft)
        if container_id is not None:
            updates.append("container_id = ?")
            params.append(container_id)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(canvas_id)
            
            await db.execute(
                f"UPDATE canvasses SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            await db.commit()
    return await get_canvas(canvas_id)


async def delete_canvas(canvas_id: str):
    """Delete a canvas."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM canvasses WHERE id = ?", (canvas_id,))
        await db.commit()


async def ensure_default_canvas(user_id: str, display_name: str = "Lody", discovered_files: list = None) -> dict:
    """Ensure user has at least one canvas, create default if none exist."""
    canvasses = await get_user_canvasses(user_id)
    if not canvasses:
        # Create default canvas with personalized name and optionally discovered cache files
        default_name = f"{display_name}'s Canvas"
        return await create_canvas(user_id, default_name, files=discovered_files)
    return canvasses[0]
