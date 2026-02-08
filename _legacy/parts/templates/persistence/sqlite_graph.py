"""
SQLite Graph Persistence Template
Source: My Tiny Data Collider (Legacy)
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text, select, delete

Base = declarative_base()

# --- SQL Models ---
class DBUser(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    json_data = Column(Text, nullable=False)

class DBContainer(Base):
    __tablename__ = "containers"
    id = Column(String, primary_key=True)
    owner_id = Column(String, index=True)
    parent_id = Column(String, index=True, nullable=True)
    json_data = Column(Text, nullable=False)

class DBLink(Base):
    __tablename__ = "links"
    id = Column(String, primary_key=True)
    owner_id = Column(String, index=True) # Successor
    json_data = Column(Text, nullable=False)

class DBDefinition(Base):
    __tablename__ = "definitions"
    id = Column(String, primary_key=True)
    kind = Column(String, index=True)
    json_data = Column(Text, nullable=False)

class DBRunRecord(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    job_id = Column(String, index=True, unique=True)
    container_id = Column(String, index=True)
    json_data = Column(Text, nullable=False)


class SqlAlchemyPersistence:
    """
    Durable SQL Persistence.
    Defaults to SQLite for local dev.
    Compatible with PostgreSQL for Prod.
    """
    def __init__(self, connection_string: str = "sqlite+aiosqlite:///./collider.db"):
        self.engine = create_async_engine(connection_string, echo=False)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print(f"Initialized SqlAlchemyPersistence: {connection_string}")

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # --- Helper ---
    async def _save_obj(self, db_cls, model: Any, index_fields: dict):
        async with self.async_session() as session:
            async with session.begin():
                instance = await session.get(db_cls, str(model.id))
                if instance:
                    # Update fields
                    instance.json_data = model.model_dump_json()
                    for k, v in index_fields.items():
                        setattr(instance, k, str(v) if v else None)
                else:
                    # Create
                    instance = db_cls(
                        id=str(model.id),
                        json_data=model.model_dump_json(),
                        **{k: str(v) if v else None for k, v in index_fields.items()}
                    )
                    session.add(instance)
                await session.commit()

    async def _get_obj(self, db_cls, model_cls, obj_id: UUID):
        async with self.async_session() as session:
            stmt = select(db_cls).where(db_cls.id == str(obj_id))
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            if instance:
                return model_cls.model_validate_json(instance.json_data)
            return None
