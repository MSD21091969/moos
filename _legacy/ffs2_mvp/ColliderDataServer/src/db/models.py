"""SQLAlchemy ORM models."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.db.connection import Base


class User(Base):
    """User account - synced with Firebase Auth."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    container: Mapped[dict] = mapped_column(JSONB, default=dict)  # ADMIN .agent context
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    admin_accounts: Mapped[list["AdminAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    permissions: Mapped[list["AppPermission"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AdminAccount(Base):
    """Admin account - can own applications."""

    __tablename__ = "admin_accounts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="admin_accounts")
    applications: Mapped[list["Application"]] = relationship(back_populates="owner")


class Application(Base):
    """Application - owns a tree of nodes."""

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    app_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    owner_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("admin_accounts.id", ondelete="SET NULL")
    )
    display_name: Mapped[str | None] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(
        String(16), default="CLOUD"
    )  # FILESYST, CLOUD, ADMIN
    config: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )  # ApplicationConfig (backend-only)
    root_node_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("nodes.id", use_alter=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner: Mapped["AdminAccount"] = relationship(back_populates="applications")
    nodes: Mapped[list["Node"]] = relationship(
        back_populates="application", foreign_keys="Node.application_id"
    )
    permissions: Mapped[list["AppPermission"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class AppPermission(Base):
    """Application permission - app-level only."""

    __tablename__ = "app_permissions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE")
    )
    application_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE")
    )
    can_read: Mapped[bool] = mapped_column(Boolean, default=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="permissions")
    application: Mapped["Application"] = relationship(back_populates="permissions")


class Node(Base):
    """Container node - holds .agent context."""

    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE")
    )
    parent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("nodes.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    container: Mapped[dict] = mapped_column(JSONB, default=dict)  # .agent context
    node_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        back_populates="nodes", foreign_keys=[application_id]
    )
    parent: Mapped["Node | None"] = relationship(
        remote_side=[id], foreign_keys=[parent_id]
    )
