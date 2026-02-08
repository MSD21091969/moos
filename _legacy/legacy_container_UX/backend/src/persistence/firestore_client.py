"""Async Firestore client wrapper."""

from google.cloud import firestore
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class FirestoreClient:
    """Async Firestore wrapper with mock support."""

    def __init__(self):
        logger.info(
            f"Initializing FirestoreClient with use_firestore_mocks={settings.use_firestore_mocks}, gcp_project={settings.gcp_project}"
        )
        if settings.use_firestore_mocks:
            from src.persistence.mock_firestore import MockFirestoreClient

            self._client = MockFirestoreClient()
            logger.info("✓ Using mock Firestore client")
        else:
            self._client = firestore.AsyncClient(
                project=settings.gcp_project, database=settings.firestore_database
            )
            logger.info(
                f"✓ Connected to Firestore: {settings.gcp_project}/{settings.firestore_database}"
            )

    def collection(self, path: str):
        return self._client.collection(path)

    def document(self, path: str):
        return self._client.document(path)

    async def close(self) -> None:
        if self._client is not None and hasattr(self._client, "close"):
            close_result = self._client.close()
            if close_result is not None:
                await close_result
            logger.info("Firestore client closed")


_firestore_client: FirestoreClient | None = None


async def get_firestore_client() -> FirestoreClient:
    """Get or create Firestore client singleton."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = FirestoreClient()
    return _firestore_client


async def close_firestore_client() -> None:
    """Close Firestore client."""
    global _firestore_client
    if _firestore_client:
        await _firestore_client.close()
        _firestore_client = None
