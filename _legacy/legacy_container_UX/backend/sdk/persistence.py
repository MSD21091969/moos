"""Local session persistence for collider-sdk.

Allows users to work offline and sync sessions to remote server when available.
Supports multiple storage backends: SQLite, JSON files, in-memory.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sdk.models import Session

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """Abstract base class for session storage backends."""

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Store a new session."""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Session]:
        """List sessions with optional filters."""
        pass

    @abstractmethod
    async def update(self, session_id: str, **kwargs) -> Optional[Session]:
        """Update session metadata."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    async def export(self, filepath: str) -> None:
        """Export all sessions to file."""
        pass

    @abstractmethod
    async def import_sessions(self, filepath: str) -> int:
        """Import sessions from file. Returns count imported."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all sessions from storage."""
        pass


class SQLiteSessionStore(SessionStore):
    """SQLite-based persistent storage for sessions.

    Production-grade local storage with indexing and query optimization.

    Usage:
    ```python
    store = SQLiteSessionStore("~/.collider/sessions.db")
    await store.initialize()

    session = Session(
        session_id="sess_123",
        title="My Analysis",
        user_id="user_456",
        ...
    )
    await store.create(session)

    # Later, retrieve
    retrieved = await store.get("sess_123")
    ```
    """

    def __init__(self, db_path: str = "~/.collider/sessions.db"):
        """Initialize SQLite store.

        Args:
            db_path: Path to SQLite database file. Supports ~ expansion.
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized SQLiteSessionStore at {self.db_path}")

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                session_type TEXT DEFAULT 'analysis',
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ttl_hours INTEGER,
                metadata TEXT,
                local_only BOOLEAN DEFAULT 0,
                synced_to_server BOOLEAN DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                UNIQUE(session_id, tag)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
            """
        )

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON sessions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON sessions(created_at)")

        conn.commit()
        conn.close()
        logger.info("Session tables initialized")

    async def create(self, session: Session) -> Session:
        """Store a new session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        metadata = json.dumps(session.metadata or {})

        cursor.execute(
            """
            INSERT INTO sessions 
            (session_id, user_id, title, session_type, status, created_at, updated_at, ttl_hours, metadata, local_only)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.session_id,
                session.user_id,
                session.title,
                session.session_type,
                session.status,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.ttl_hours,
                metadata,
                1,  # Mark as local-only initially
            ),
        )

        # Insert tags
        if session.tags:
            for tag in session.tags:
                cursor.execute(
                    "INSERT INTO session_tags (session_id, tag) VALUES (?, ?)",
                    (session.session_id, tag),
                )

        conn.commit()
        conn.close()
        logger.info(f"Created session {session.session_id} in local store")
        return session

    async def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID with full metadata."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Get tags
        cursor.execute("SELECT tag FROM session_tags WHERE session_id = ?", (session_id,))
        tags = [t[0] for t in cursor.fetchall()]

        conn.close()

        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            title=row["title"],
            session_type=row["session_type"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            ttl_hours=row["ttl_hours"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            tags=tags,
        )

    async def list(
        self,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Session]:
        """List sessions with optional filtering."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT DISTINCT s.* FROM sessions s"
        params = []

        if tags:
            query += " JOIN session_tags st ON s.session_id = st.session_id"

        query += " WHERE 1=1"

        if status:
            query += " AND s.status = ?"
            params.append(status)

        if session_type:
            query += " AND s.session_type = ?"
            params.append(session_type)

        if tags:
            placeholders = ",".join("?" * len(tags))
            query += f" AND st.tag IN ({placeholders})"
            params.extend(tags)

        query += " ORDER BY s.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            cursor.execute(
                "SELECT tag FROM session_tags WHERE session_id = ?",
                (row["session_id"],),
            )
            row_tags = [t[0] for t in cursor.fetchall()]

            sessions.append(
                Session(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    session_type=row["session_type"],
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    ttl_hours=row["ttl_hours"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    tags=row_tags,
                )
            )

        conn.close()
        return sessions

    async def update(self, session_id: str, **kwargs) -> Optional[Session]:
        """Update session metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current session
        session = await self.get(session_id)
        if not session:
            conn.close()
            return None

        # Update allowed fields
        update_fields = []
        params = []

        for field in ["title", "status", "session_type", "metadata"]:
            if field in kwargs:
                if field == "metadata":
                    update_fields.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    update_fields.append(f"{field} = ?")
                    params.append(kwargs[field])

        if not update_fields:
            conn.close()
            return session

        # Always update updated_at
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE session_id = ?"
        params.append(session_id)

        cursor.execute(query, params)
        conn.commit()
        conn.close()

        logger.info(f"Updated session {session_id}")
        return await self.get(session_id)

    async def delete(self, session_id: str) -> bool:
        """Delete a session and all related data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted session {session_id}")

        return deleted

    async def export(self, filepath: str) -> None:
        """Export all sessions to JSON file for backup/sharing."""
        sessions = await self.list(limit=10000)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "session_count": len(sessions),
            "sessions": [
                {
                    **session.model_dump(),
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                }
                for session in sessions
            ],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(sessions)} sessions to {filepath}")

    async def import_sessions(self, filepath: str) -> int:
        """Import sessions from exported JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported_count = 0

        for session_data in data.get("sessions", []):
            try:
                session = Session(
                    session_id=session_data["session_id"],
                    user_id=session_data["user_id"],
                    title=session_data["title"],
                    session_type=session_data.get("session_type", "analysis"),
                    status=session_data.get("status", "active"),
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    updated_at=datetime.fromisoformat(session_data["updated_at"]),
                    ttl_hours=session_data.get("ttl_hours"),
                    metadata=session_data.get("metadata"),
                    tags=session_data.get("tags", []),
                )

                # Check if already exists
                existing = await self.get(session.session_id)
                if existing:
                    await self.update(
                        session.session_id,
                        title=session.title,
                        status=session.status,
                        metadata=session.metadata,
                    )
                else:
                    await self.create(session)

                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import session: {e}")

        logger.info(f"Imported {imported_count} sessions from {filepath}")
        return imported_count

    async def clear(self) -> None:
        """Delete all sessions from local storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM session_tags")
        cursor.execute("DELETE FROM session_messages")
        cursor.execute("DELETE FROM sessions")

        conn.commit()
        conn.close()

        logger.info("Cleared all local sessions")


class InMemorySessionStore(SessionStore):
    """In-memory session storage for testing and ephemeral use.

    Fast but data is lost when process exits.
    """

    def __init__(self):
        """Initialize in-memory store."""
        self.sessions: Dict[str, Session] = {}
        logger.info("Initialized InMemorySessionStore")

    async def create(self, session: Session) -> Session:
        """Store session in memory."""
        self.sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> Optional[Session]:
        """Retrieve session from memory."""
        return self.sessions.get(session_id)

    async def list(
        self,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Session]:
        """List sessions with filtering."""
        result = list(self.sessions.values())

        if status:
            result = [s for s in result if s.status == status]

        if session_type:
            result = [s for s in result if s.session_type == session_type]

        if tags:
            result = [s for s in result if any(t in s.tags for t in tags)]

        return result[:limit]

    async def update(self, session_id: str, **kwargs) -> Optional[Session]:
        """Update session in memory."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.now()
        return session

    async def delete(self, session_id: str) -> bool:
        """Delete session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def export(self, filepath: str) -> None:
        """Export to JSON file."""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "session_count": len(self.sessions),
            "sessions": [
                {
                    **s.model_dump(),
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in self.sessions.values()
            ],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

    async def import_sessions(self, filepath: str) -> int:
        """Import from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported_count = 0

        for session_data in data.get("sessions", []):
            session = Session(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                title=session_data["title"],
                session_type=session_data.get("session_type", "analysis"),
                status=session_data.get("status", "active"),
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"]),
                ttl_hours=session_data.get("ttl_hours"),
                metadata=session_data.get("metadata"),
                tags=session_data.get("tags", []),
            )
            self.sessions[session.session_id] = session
            imported_count += 1

        return imported_count

    async def clear(self) -> None:
        """Clear all sessions."""
        self.sessions.clear()
