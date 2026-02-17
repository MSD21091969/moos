from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class SystemRole(str, enum.Enum):
    """System-level roles for users."""

    SUPERADMIN = "superadmin"
    COLLIDER_ADMIN = "collider_admin"
    APP_ADMIN = "app_admin"
    APP_USER = "app_user"


class AppRole(str, enum.Enum):
    """Application-level permission roles."""

    APP_ADMIN = "app_admin"  # Owner/admin of the app
    APP_USER = "app_user"  # Regular member


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    system_role: Mapped[SystemRole] = mapped_column(
        Enum(SystemRole), nullable=False, default=SystemRole.APP_USER
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    permissions: Mapped[list[AppPermission]] = relationship(back_populates="user")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    owner_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    root_node_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("nodes.id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User | None] = relationship(foreign_keys=[owner_id])
    nodes: Mapped[list[Node]] = relationship(
        back_populates="application", foreign_keys="Node.application_id"
    )
    root_node: Mapped[Node | None] = relationship(
        foreign_keys=[root_node_id], post_update=True
    )
    permissions: Mapped[list[AppPermission]] = relationship(
        back_populates="application"
    )
    access_requests: Mapped[list[AppAccessRequest]] = relationship(
        back_populates="application"
    )


class AppPermission(Base):
    __tablename__ = "app_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "application_id", name="uq_user_application"),
        Index("idx_permissions_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[AppRole] = mapped_column(
        Enum(AppRole), nullable=False, default=AppRole.APP_USER
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="permissions")
    application: Mapped[Application] = relationship(back_populates="permissions")


class AppAccessRequest(Base):
    """Access requests for applications."""

    __tablename__ = "app_access_requests"
    __table_args__ = (
        Index("idx_app_access_requests_user_id", "user_id"),
        Index("idx_app_access_requests_application_id", "application_id"),
        Index("idx_app_access_requests_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    application: Mapped[Application] = relationship(back_populates="access_requests")
    resolver: Mapped[User | None] = relationship(foreign_keys=[resolved_by])


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("application_id", "path", name="uq_application_path"),
        Index("idx_nodes_application", "application_id"),
        Index("idx_nodes_parent", "parent_id"),
        Index("idx_nodes_path", "path"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=True,
    )
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    container: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    application: Mapped[Application] = relationship(
        back_populates="nodes", foreign_keys=[application_id]
    )
    parent: Mapped[Node | None] = relationship(
        remote_side="Node.id", back_populates="children"
    )
    children: Mapped[list[Node]] = relationship(back_populates="parent")
