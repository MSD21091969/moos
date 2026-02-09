from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    container: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    admin_account: Mapped[AdminAccount | None] = relationship(
        back_populates="user", uselist=False
    )
    permissions: Mapped[list[AppPermission]] = relationship(back_populates="user")


class AdminAccount(Base):
    __tablename__ = "admin_accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="admin_account")
    owned_applications: Mapped[list[Application]] = relationship(back_populates="owner")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    app_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    owner_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("admin_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    root_node_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("nodes.id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[AdminAccount | None] = relationship(
        back_populates="owned_applications"
    )
    nodes: Mapped[list[Node]] = relationship(
        back_populates="application", foreign_keys="Node.application_id"
    )
    root_node: Mapped[Node | None] = relationship(
        foreign_keys=[root_node_id], post_update=True
    )
    permissions: Mapped[list[AppPermission]] = relationship(
        back_populates="application"
    )


class AppPermission(Base):
    __tablename__ = "app_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "application_id", name="uq_user_application"),
        Index("idx_permissions_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    can_read: Mapped[bool] = mapped_column(Boolean, default=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="permissions")
    application: Mapped[Application] = relationship(back_populates="permissions")


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("application_id", "path", name="uq_application_path"),
        Index("idx_nodes_application", "application_id"),
        Index("idx_nodes_parent", "parent_id"),
        Index("idx_nodes_path", "path"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
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
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
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
