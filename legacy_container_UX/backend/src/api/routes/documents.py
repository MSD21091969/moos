"""Document management API endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, Response

from src.api.dependencies import get_user_context, get_document_service
from src.core.exceptions import NotFoundError, PermissionDeniedError
from src.core.logging import get_logger
from src.models.context import UserContext
from src.models.documents import DocumentCreate, DocumentListResponse, DocumentResponse
from src.services.document_service import DocumentService

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions/{session_id}/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    session_id: str,
    filename: str = Form(..., min_length=1, max_length=255),
    file: UploadFile = File(...),
    user_ctx: UserContext = Depends(get_user_context),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Upload a document to a session.
    Supports both text and binary files.
    """
    try:
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        text_content = None
        content_bytes = None

        # Try to decode as text
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            # If not UTF-8, treat as binary
            content_bytes = content

        # Create document request
        request = DocumentCreate(
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            content=text_content,
            tags=[],
            metadata={"original_name": filename},
        )

        # Upload document
        document = await document_service.upload_document(
            session_id, user_ctx, request, content_bytes=content_bytes
        )

        return DocumentResponse(
            document_id=document.document_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            user_id=document.user_id,
            tags=document.tags,
            metadata=document.metadata,
        )

    except HTTPException:
        raise
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to upload document", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(
    session_id: str,
    document_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    document_service: DocumentService = Depends(get_document_service),
):
    """Download a document."""
    try:
        content, filename, content_type = await document_service.download_document(
            session_id, document_id, user_ctx
        )

        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to download document", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    session_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_ctx: UserContext = Depends(get_user_context),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    List all documents in a session.

    **Authentication Required**: Yes

    **Authorization**: User must own the session or have shared access

    **Use Case**: Frontend loads document list for session
    """
    try:
        offset = (page - 1) * page_size
        documents, total = await document_service.list_documents(
            session_id, user_ctx, limit=page_size, offset=offset
        )

        doc_responses = [
            DocumentResponse(
                document_id=doc.document_id,
                filename=doc.filename,
                content_type=doc.content_type,
                size_bytes=doc.size_bytes,
                created_at=doc.created_at,
                user_id=doc.user_id,
                tags=doc.tags,
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        has_more = (page * page_size) < total

        return DocumentListResponse(
            session_id=session_id,
            documents=doc_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to list documents", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    session_id: str,
    document_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get a specific document by ID.

    **Authentication Required**: Yes

    **Authorization**: User must own the session or have shared access

    **Use Case**: Load document details and content
    """
    try:
        document = await document_service.get_document(session_id, document_id, user_ctx)

        return DocumentResponse(
            document_id=document.document_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            user_id=document.user_id,
            tags=document.tags,
            metadata=document.metadata,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get document",
            extra={"document_id": document_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    session_id: str,
    document_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Delete a document.

    **Authentication Required**: Yes (must be session owner)

    **Authorization**: Only session owner can delete documents

    **Use Case**: User removes a document from session
    """
    try:
        await document_service.delete_document(session_id, document_id, user_ctx)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to delete document",
            extra={"document_id": document_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
