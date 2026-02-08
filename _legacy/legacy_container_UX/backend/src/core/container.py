"""Dependency Injection container with singleton pattern for expensive resources."""

from typing import Optional
from src.persistence.firestore_client import FirestoreClient


class AppContainer:
    """
    Singleton container for application-wide dependencies.

    Manages expensive resources:
    - Firestore client (connection pooling)

    Usage:
        container = AppContainer()
        db = container.firestore_client
    """

    _instance: Optional["AppContainer"] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize container (only once)."""
        if not AppContainer._initialized:
            self._firestore_client: Optional[FirestoreClient] = None
            AppContainer._initialized = True

    @property
    def firestore_client(self) -> FirestoreClient:
        """
        Get Firestore client (lazy initialization).

        Uses mock client in development, real client in production.
        Controlled by settings.use_firestore_mocks.
        """
        if self._firestore_client is None:
            self._firestore_client = FirestoreClient()
        return self._firestore_client

    async def reset(self):
        """
        Reset all singletons (for testing).

        Closes connections and clears cached instances.
        """
        if self._firestore_client:
            await self._firestore_client.close()
            self._firestore_client = None

        AppContainer._initialized = False
        AppContainer._instance = None


# Convenience function for getting container
def get_container() -> AppContainer:
    """Get AppContainer singleton instance."""
    return AppContainer()
