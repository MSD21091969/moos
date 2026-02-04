"""Application API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db import get_db, Application
from src.schemas import ApplicationCreate, ApplicationResponse

router = APIRouter(prefix="/apps", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    db: AsyncSession = Depends(get_db)
):
    """List all applications (MVP: no permission filtering)."""
    result = await db.execute(select(Application))
    apps = result.scalars().all()
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get application by app_id."""
    result = await db.execute(
        select(Application).where(Application.app_id == app_id)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return ApplicationResponse.model_validate(app)


@router.post("", response_model=ApplicationResponse)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new application."""
    # Check if app_id already exists
    existing = await db.execute(
        select(Application).where(Application.app_id == data.app_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application ID already exists")
    
    app = Application(
        app_id=data.app_id,
        display_name=data.display_name,
        config={},
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    
    return ApplicationResponse.model_validate(app)
