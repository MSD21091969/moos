"""Background jobs API endpoints."""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.jobs_client import trigger_background_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobTriggerRequest(BaseModel):
    """Request to trigger a background job."""

    task_name: str = Field(..., description="Task name from background_tasks.py")
    task_args: Optional[dict[str, Any]] = Field(default=None, description="Task arguments as JSON")


class JobTriggerResponse(BaseModel):
    """Response from triggering a job."""

    job_name: str
    execution_id: str
    task_name: str
    status: str


class ExportSessionRequest(BaseModel):
    """Request to export session messages."""

    session_id: str = Field(..., description="Session ID to export")
    export_format: str = Field(default="json", description="Export format (json, csv, pdf)")


@router.post("/trigger", response_model=JobTriggerResponse)
async def trigger_job(request: JobTriggerRequest):
    """Trigger a background job execution.

    This endpoint queues a Cloud Run Job for execution.
    The job runs asynchronously and returns immediately.

    Example:
        POST /jobs/trigger
        {
            "task_name": "export_session_messages",
            "task_args": {"session_id": "123", "export_format": "pdf"}
        }
    """
    try:
        result = await trigger_background_task(
            task_name=request.task_name,
            task_args=request.task_args,
        )
        return JobTriggerResponse(**result)

    except Exception as e:
        logger.error("Failed to trigger job", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")


@router.post("/export-session", response_model=JobTriggerResponse)
async def export_session(request: ExportSessionRequest):
    """Export session messages as a background job.

    Convenience endpoint for session exports.
    Returns immediately while export runs in background.

    Example:
        POST /jobs/export-session
        {
            "session_id": "abc123",
            "export_format": "pdf"
        }
    """
    try:
        result = await trigger_background_task(
            task_name="export_session_messages",
            task_args={
                "session_id": request.session_id,
                "export_format": request.export_format,
            },
        )
        return JobTriggerResponse(**result)

    except Exception as e:
        logger.error("Failed to trigger export", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to trigger export: {str(e)}")
