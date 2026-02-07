"""
Firebase Authentication Module
Handles Firebase JWT verification with fallback for local development.
"""

import logging
from typing import Optional
from functools import lru_cache

from src.config import get_settings

logger = logging.getLogger(__name__)

# Firebase Admin SDK (optional - only loaded when enabled)
_firebase_app = None


def _init_firebase() -> bool:
    """Initialize Firebase Admin SDK if configured."""
    global _firebase_app

    if _firebase_app is not None:
        return True

    settings = get_settings()

    if not settings.firebase_auth_enabled:
        logger.info("Firebase auth disabled, using dev mode")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with credentials file")
        elif settings.firebase_project_id:
            # Use Application Default Credentials
            _firebase_app = firebase_admin.initialize_app(
                options={"projectId": settings.firebase_project_id}
            )
            logger.info(
                f"Firebase initialized with project: {settings.firebase_project_id}"
            )
        else:
            logger.warning("Firebase enabled but no credentials configured")
            return False

        return True
    except ImportError:
        logger.error("firebase-admin not installed")
        return False
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return False


class FirebaseUser:
    """Decoded Firebase user from JWT."""

    def __init__(
        self,
        uid: str,
        email: Optional[str] = None,
        email_verified: bool = False,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        claims: Optional[dict] = None,
    ):
        self.uid = uid
        self.email = email
        self.email_verified = email_verified
        self.name = name
        self.picture = picture
        self.claims = claims or {}

    @classmethod
    def from_decoded_token(cls, decoded: dict) -> "FirebaseUser":
        """Create FirebaseUser from decoded Firebase token."""
        return cls(
            uid=decoded["uid"],
            email=decoded.get("email"),
            email_verified=decoded.get("email_verified", False),
            name=decoded.get("name"),
            picture=decoded.get("picture"),
            claims=decoded,
        )

    @classmethod
    def from_dev_token(cls, token: str) -> "FirebaseUser":
        """Create a mock FirebaseUser for development (token = email)."""
        # In dev mode, token is treated as email
        return cls(
            uid=f"dev_{token.replace('@', '_').replace('.', '_')}",
            email=token,
            email_verified=True,
            name=token.split("@")[0] if "@" in token else token,
        )


class AuthError(Exception):
    """Authentication error."""

    def __init__(self, message: str, code: str = "auth_error"):
        self.message = message
        self.code = code
        super().__init__(message)


async def verify_firebase_token(id_token: str) -> FirebaseUser:
    """
    Verify a Firebase ID token and return user info.

    In production (firebase_auth_enabled=True):
      - Validates JWT signature with Firebase public keys
      - Checks expiration and audience
      - Returns decoded user claims

    In development (firebase_auth_enabled=False):
      - Treats token as email address
      - Returns mock FirebaseUser for testing

    Raises:
        AuthError: If token is invalid or verification fails
    """
    settings = get_settings()

    if not settings.firebase_auth_enabled:
        # Dev mode: treat token as email
        if not id_token or len(id_token) < 3:
            raise AuthError("Invalid dev token", "invalid_token")

        logger.debug(f"Dev mode auth: {id_token}")
        return FirebaseUser.from_dev_token(id_token)

    # Production mode: verify with Firebase
    if not _init_firebase():
        raise AuthError("Firebase not configured", "config_error")

    try:
        from firebase_admin import auth

        # Verify the ID token
        decoded = auth.verify_id_token(id_token)

        logger.debug(f"Firebase verified: {decoded.get('email', decoded['uid'])}")
        return FirebaseUser.from_decoded_token(decoded)

    except ImportError:
        raise AuthError("firebase-admin not installed", "config_error")
    except auth.ExpiredIdTokenError:
        raise AuthError("Token expired", "expired_token")
    except auth.RevokedIdTokenError:
        raise AuthError("Token revoked", "revoked_token")
    except auth.InvalidIdTokenError as e:
        raise AuthError(f"Invalid token: {e}", "invalid_token")
    except auth.CertificateFetchError:
        raise AuthError("Could not fetch Firebase certificates", "config_error")
    except Exception as e:
        logger.exception("Firebase token verification failed")
        raise AuthError(f"Verification failed: {e}", "verification_failed")


def is_firebase_enabled() -> bool:
    """Check if Firebase auth is enabled."""
    return get_settings().firebase_auth_enabled and _init_firebase()
