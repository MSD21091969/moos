from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import (
    app_permissions,
    apps,
    auth,
    context,
    health,
    nodes,
    agent_bootstrap,
    permissions,
    roles,
    rtc,
    sse,
    templates,
    users,
    execution,
)
from src.core.config import settings
from src.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load templates
    from src.core.templates import registry

    registry.load_all()

    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="Collider Data Server",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(apps.router)
app.include_router(app_permissions.router)
app.include_router(nodes.router)
app.include_router(context.router)
app.include_router(sse.router)
app.include_router(permissions.router)
app.include_router(rtc.router)
app.include_router(templates.router)
app.include_router(execution.router)
app.include_router(agent_bootstrap.router)
