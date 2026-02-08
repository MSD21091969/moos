"""Storage service for handling file operations."""

import base64
from typing import Protocol

from src.core.logging import get_logger
from src.core.exceptions import NotFoundError

logger = get_logger(__name__)


class StorageProvider(Protocol):
    """Protocol for storage providers."""

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        """Upload content and return a reference/URL."""
        ...

    async def download(self, path: str) -> bytes:
        """Download content."""
        ...

    async def delete(self, path: str) -> None:
        """Delete content."""
        ...


class FirestoreStorageProvider:
    """
    Simple storage provider that stores small files in Firestore documents.
    Suitable for the "Tiny" version of the project.
    """

    def __init__(self, firestore_client):
        self.firestore = firestore_client
        self.collection = "storage_blobs"

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        """Store binary content as Base64 in a Firestore document."""
        # Encode binary to base64 string for JSON compatibility
        b64_content = base64.b64encode(content).decode("utf-8")

        doc_ref = self.firestore.collection(self.collection).document(path)
        await doc_ref.set(
            {"content": b64_content, "content_type": content_type, "size_bytes": len(content)}
        )

        logger.info(f"Stored blob at {path} ({len(content)} bytes)")
        return path

    async def download(self, path: str) -> bytes:
        """Retrieve binary content from Firestore."""
        doc_ref = self.firestore.collection(self.collection).document(path)
        doc = await doc_ref.get()

        if not doc.exists:
            raise NotFoundError(f"Blob {path} not found")

        data = doc.to_dict()
        # Decode base64 string back to bytes
        return base64.b64decode(data["content"])

    async def delete(self, path: str) -> None:
        """Delete the blob document."""
        doc_ref = self.firestore.collection(self.collection).document(path)
        await doc_ref.delete()


class StorageService:
    """Service for managing file storage."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider

    async def save_file(self, filename: str, content: bytes, content_type: str) -> str:
        """Save a file and return its storage path."""
        # Sanitize filename to be a valid document ID if needed
        safe_path = filename.replace("/", "_").replace("\\", "_")
        return await self.provider.upload(safe_path, content, content_type)

    async def get_file(self, path: str) -> bytes:
        """Retrieve a file's content."""
        return await self.provider.download(path)

    async def delete_file(self, path: str) -> None:
        """Delete a file."""
        await self.provider.delete(path)
