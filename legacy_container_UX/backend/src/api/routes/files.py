"""File management routes for GCS and external data sources."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.core.logging import get_logger
from src.models.users import User
from src.services.gcs_storage import GCSStorageProvider

logger = get_logger(__name__)
router = APIRouter(prefix="/files", tags=["Files"])


class SignedUrlRequest(BaseModel):
    """Request model for signed URL generation."""

    file_path: str
    expiration_minutes: int = 60
    method: str = "GET"  # GET or PUT
    content_type: str | None = None


class SignedUrlResponse(BaseModel):
    """Response model for signed URL."""

    signed_url: str
    expires_in: int  # seconds


class UploadResponse(BaseModel):
    """Response model for file upload."""

    gcs_path: str
    size: int
    content_type: str


@router.post("/gcs-signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    request: SignedUrlRequest,
    current_user: User = Depends(get_current_user),
) -> SignedUrlResponse:
    """Generate signed URL for GCS file access.

    Args:
        request: Signed URL parameters
        current_user: Authenticated user

    Returns:
        Signed URL and expiration time

    Raises:
        HTTPException: If URL generation fails
    """
    try:
        gcs = GCSStorageProvider()

        # Validate file path (prevent directory traversal)
        if ".." in request.file_path or request.file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path")

        # Generate signed URL
        url = gcs.generate_signed_url(
            blob_name=request.file_path,
            expiration_minutes=request.expiration_minutes,
            method=request.method,
            content_type=request.content_type,
        )

        logger.info(f"User {current_user.id} generated signed URL for {request.file_path}")

        return SignedUrlResponse(
            signed_url=url,
            expires_in=request.expiration_minutes * 60,
        )

    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-to-gcs", response_model=UploadResponse)
async def upload_to_gcs(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Upload file to GCS bucket.

    Args:
        file: Uploaded file
        current_user: Authenticated user

    Returns:
        GCS path and file metadata

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Read file content
        content = await file.read()

        # Generate unique blob name
        # Format: uploads/{user_id}/{filename}
        blob_name = f"uploads/{current_user.id}/{file.filename}"

        # Upload to GCS
        gcs = GCSStorageProvider()
        await gcs.upload_file(
            blob_name=blob_name,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )

        logger.info(
            f"User {current_user.id} uploaded {file.filename} ({len(content)} bytes) to {blob_name}"
        )

        return UploadResponse(
            gcs_path=blob_name,
            size=len(content),
            content_type=file.content_type or "application/octet-stream",
        )

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/gcs/{file_path:path}")
async def delete_from_gcs(
    file_path: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete file from GCS bucket.

    Args:
        file_path: Path to file in GCS
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If deletion fails or unauthorized
    """
    try:
        # Validate ownership (file must be under user's upload path)
        expected_prefix = f"uploads/{current_user.id}/"
        if not file_path.startswith(expected_prefix):
            raise HTTPException(
                status_code=403,
                detail="Unauthorized to delete this file",
            )

        gcs = GCSStorageProvider()

        # Check if file exists
        if not gcs.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file
        await gcs.delete_file(file_path)

        logger.info(f"User {current_user.id} deleted {file_path}")

        return {"message": "File deleted successfully", "path": file_path}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-gcs")
async def list_gcs_files(
    prefix: str | None = None,
    current_user: User = Depends(get_current_user),
) -> dict:
    """List files in GCS bucket for current user.

    Args:
        prefix: Optional path prefix to filter files
        current_user: Authenticated user

    Returns:
        List of files with metadata
    """
    try:
        # Scope to user's upload directory
        user_prefix = f"uploads/{current_user.id}/"
        if prefix:
            # Ensure prefix is within user's directory
            if not prefix.startswith(user_prefix):
                prefix = user_prefix + prefix
        else:
            prefix = user_prefix

        gcs = GCSStorageProvider()
        files = await gcs.list_files(prefix=prefix)

        logger.info(f"User {current_user.id} listed {len(files)} files")

        return {"files": files, "count": len(files)}

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
