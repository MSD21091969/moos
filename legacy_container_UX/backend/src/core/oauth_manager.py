"""OAuth token management for external API integrations."""

from datetime import datetime, timezone
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from src.core.config import settings
from src.core.exceptions import AuthenticationError
from src.persistence.firestore_client import FirestoreClient


class OAuthManager:
    """
    Manage OAuth tokens for external services.

    Stores tokens in Firestore: /users/{user_id}/oauth_tokens/{provider}
    Supports: Google Workspace, future: Microsoft 365, etc.
    """

    def __init__(self, firestore_client: FirestoreClient):
        """Initialize OAuth manager."""
        self.db = firestore_client

    async def store_token(
        self,
        user_id: str,
        provider: str,
        credentials: Credentials,
    ) -> None:
        """
        Store OAuth credentials for a user.

        Args:
            user_id: User identifier
            provider: OAuth provider (e.g., "google")
            credentials: Google OAuth2 credentials object

        Raises:
            Exception: If storage fails
        """
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        doc_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("oauth_tokens")
            .document(provider)
        )
        await doc_ref.set(token_data)

    async def get_credentials(
        self,
        user_id: str,
        provider: str,
    ) -> Optional[Credentials]:
        """
        Retrieve OAuth credentials for a user.

        Args:
            user_id: User identifier
            provider: OAuth provider (e.g., "google")

        Returns:
            Google Credentials object or None if not found

        Raises:
            AuthenticationError: If token expired and refresh failed
        """
        doc_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("oauth_tokens")
            .document(provider)
        )
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        token_data = doc.to_dict()

        # Reconstruct Credentials object
        credentials = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )

        # Check if expired
        if credentials.expired and credentials.refresh_token:
            try:
                # Refresh token
                from google.auth.transport.requests import Request

                credentials.refresh(Request())

                # Store refreshed token
                await self.store_token(user_id, provider, credentials)
            except Exception as e:
                raise AuthenticationError(f"Failed to refresh OAuth token: {str(e)}")

        return credentials

    async def revoke_token(
        self,
        user_id: str,
        provider: str,
    ) -> None:
        """
        Revoke OAuth token for a user.

        Args:
            user_id: User identifier
            provider: OAuth provider
        """
        doc_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("oauth_tokens")
            .document(provider)
        )
        await doc_ref.delete()

    async def has_valid_token(
        self,
        user_id: str,
        provider: str,
    ) -> bool:
        """
        Check if user has valid OAuth token.

        Args:
            user_id: User identifier
            provider: OAuth provider

        Returns:
            True if valid token exists
        """
        credentials = await self.get_credentials(user_id, provider)
        return credentials is not None and credentials.valid


class GoogleOAuthFlow:
    """
    Google OAuth 2.0 authorization flow.

    Handles user consent and token exchange.
    """

    # Scopes for Google Workspace APIs
    SHEETS_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    DRIVE_SCOPES = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    @staticmethod
    def create_flow(
        scopes: list[str],
        redirect_uri: str,
    ) -> Flow:
        """
        Create OAuth flow.

        Args:
            scopes: OAuth scopes to request
            redirect_uri: Callback URL after authorization

        Returns:
            Flow object

        Raises:
            Exception: If client config not found
        """
        # In production, client_secrets.json should be in secure location
        # For MVP, we'll use environment variables
        client_config = {
            "web": {
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri=redirect_uri,
        )

        return flow

    @staticmethod
    def get_authorization_url(flow: Flow) -> str:
        """
        Get authorization URL for user consent.

        Args:
            flow: OAuth flow

        Returns:
            Authorization URL
        """
        auth_url, _ = flow.authorization_url(
            access_type="offline",  # Request refresh token
            include_granted_scopes="true",
            prompt="consent",  # Force consent screen
        )
        return auth_url

    @staticmethod
    def exchange_code(flow: Flow, code: str) -> Credentials:
        """
        Exchange authorization code for credentials.

        Args:
            flow: OAuth flow
            code: Authorization code from callback

        Returns:
            Credentials object

        Raises:
            Exception: If exchange fails
        """
        flow.fetch_token(code=code)
        return flow.credentials
