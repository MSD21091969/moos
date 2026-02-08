"""Document management service."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.core.logging import get_logger
from src.models.documents import Document, DocumentCreate
from src.models.context import UserContext
from src.persistence.firestore_client import FirestoreClient
from src.services.storage_service import StorageService, FirestoreStorageProvider

if TYPE_CHECKING:
    from src.services.session_service import SessionService

logger = get_logger(__name__)


class DocumentService:
    """Service for managing documents within sessions."""

    def __init__(
        self,
        firestore: FirestoreClient,
        session_service: Optional["SessionService"] = None,
        storage_service: Optional[StorageService] = None,
    ):
        self.firestore = firestore
        self.session_service = session_service
        self.storage_service = storage_service or StorageService(
            FirestoreStorageProvider(firestore)
        )
        self.collection = "sessions"
        self.sub_collection = "documents"

    async def upload_document(
        self,
        session_id: str,
        user_ctx: UserContext,
        request: DocumentCreate,
        content_bytes: Optional[bytes] = None,
    ) -> Document:
        """
        Upload a document to a session.

        Args:
            session_id: Parent session ID
            user_ctx: User context (for ownership validation)
            request: Document creation request
            content_bytes: Optional binary content. If provided, stores in blob storage.

        Returns:
            Created document

        Raises:
            NotFoundError: Session not found
            PermissionDeniedError: User doesn't own the session
            ValidationError: Invalid document data
        """
        # ✅ SECURITY: Validate session access (owner or shared users can upload)
        if self.session_service:
            await self.session_service.get(session_id, user_ctx.user_id)

        # Validate content
        if not content_bytes and (not request.content or len(request.content.strip()) == 0):
            raise ValidationError("Document content cannot be empty")

        # Create document
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        storage_path = None
        size_bytes = 0

        if content_bytes:
            # Store binary content
            filename_safe = f"{session_id}_{document_id}_{request.filename}"
            storage_path = await self.storage_service.save_file(
                filename_safe, content_bytes, request.content_type
            )
            size_bytes = len(content_bytes)
            # Clear text content if binary is provided
            request.content = None
        else:
            # Text content
            size_bytes = len(request.content.encode("utf-8"))

        document = Document(
            document_id=document_id,
            session_id=session_id,
            filename=request.filename,
            content_type=request.content_type,
            size_bytes=size_bytes,
            content=request.content,
            storage_path=storage_path,
            created_at=now,
            updated_at=now,
            user_id=user_ctx.user_id,
            tags=request.tags,
            metadata=request.metadata,
        )

        # Store in Firestore
        doc_ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection(self.sub_collection)
            .document(document_id)
        )
        await doc_ref.set(document.model_dump())

        # Update session's document count
        session_ref = self.firestore.collection(self.collection).document(session_id)
        await session_ref.update({"updated_at": now})

        logger.info(
            f"Uploaded document {document_id} to session {session_id} by {user_ctx.user_id}"
        )
        return document

    async def get_document(
        self, session_id: str, document_id: str, user_ctx: UserContext
    ) -> Document:
        """
        Get a document by ID.

        Args:
            session_id: Parent session ID
            document_id: Document ID
            user_ctx: User context (for ownership validation)

        Returns:
            Document

        Raises:
            NotFoundError: Document or session not found
            PermissionDeniedError: User doesn't have access
        """
        # ✅ SECURITY: Validate session access (owner or shared users can read)
        if self.session_service:
            await self.session_service.get(session_id, user_ctx.user_id)

        # Get document
        doc_ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection(self.sub_collection)
            .document(document_id)
        )
        doc = await doc_ref.get()

        if not doc.exists:
            raise NotFoundError(f"Document {document_id} not found in session {session_id}")

        return Document(**doc.to_dict())

    async def list_documents(
        self, session_id: str, user_ctx: UserContext, limit: int = 50, offset: int = 0
    ) -> tuple[list[Document], int]:
        """
        List all documents in a session.

        Args:
            session_id: Parent session ID
            user_ctx: User context (for ownership validation)
            limit: Maximum documents to return
            offset: Pagination offset

        Returns:
            Tuple of (documents list, total count)

        Raises:
            NotFoundError: Session not found
            PermissionDeniedError: User doesn't have access
        """
        # ✅ SECURITY: Validate session access (owner or shared users can list)
        if self.session_service:
            await self.session_service.get(session_id, user_ctx.user_id)

        # Get documents
        query = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection(self.sub_collection)
            .order_by("created_at")
        )

        docs = query.stream()
        all_docs = []
        async for doc in docs:
            try:
                all_docs.append(Document(**doc.to_dict()))
            except Exception as e:
                logger.warning(
                    "Failed to parse document", extra={"document_id": doc.id, "error": str(e)}
                )
                continue

        total = len(all_docs)
        paged_docs = all_docs[offset : offset + limit]

        return paged_docs, total

    async def download_document(
        self, session_id: str, document_id: str, user_ctx: UserContext
    ) -> tuple[bytes, str, str]:
        """
        Download document content.

        Args:
            session_id: Parent session ID
            document_id: Document ID
            user_ctx: User context

        Returns:
            Tuple of (content_bytes, filename, content_type)
        """
        doc = await self.get_document(session_id, document_id, user_ctx)

        if doc.storage_path:
            content = await self.storage_service.get_file(doc.storage_path)
        elif doc.content:
            content = doc.content.encode("utf-8")
        else:
            content = b""

        return content, doc.filename, doc.content_type

    async def delete_document(
        self, session_id: str, document_id: str, user_ctx: UserContext
    ) -> None:
        """
        Delete a document.

        Args:
            session_id: Parent session ID
            document_id: Document ID to delete
            user_ctx: User context (must be session owner)

        Raises:
            NotFoundError: Document or session not found
            PermissionDeniedError: User is not session owner
        """
        # ✅ SECURITY: Only owner can delete (not shared users)
        if self.session_service:
            session = await self.session_service.get(session_id, user_ctx.user_id)
            if session.user_id != user_ctx.user_id:
                raise PermissionDeniedError("Only session owner can delete documents")

        # Get document first to check for storage path
        try:
            doc = await self.get_document(session_id, document_id, user_ctx)
            if doc.storage_path:
                await self.storage_service.delete_file(doc.storage_path)
        except NotFoundError:
            # Document might already be deleted or not found, proceed to delete metadata
            pass

        # Delete document
        doc_ref = (
            self.firestore.collection(self.collection)
            .document(session_id)
            .collection(self.sub_collection)
            .document(document_id)
        )
        await doc_ref.delete()

        logger.info(
            "Deleted document from session",
            extra={"document_id": document_id, "session_id": session_id},
        )
