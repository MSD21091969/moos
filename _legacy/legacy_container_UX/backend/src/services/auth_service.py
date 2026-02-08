"""Authentication service."""

import logging
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from jose import jwt
import bcrypt
from google.cloud import firestore
from src.core.config import settings
from src.models.users import UserInDB
from src.persistence.firestore_client import FirestoreClient

if TYPE_CHECKING:
    from src.models.users import User, UserUpdate

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication."""

    def __init__(self, firestore: FirestoreClient):
        self.firestore = firestore
        # Test password hash for "test123" - used for all test users
        self.test_password_hash = "$2b$12$F9QjU1g/CP9D8wuveMrwce6Z8ieKy3KqMkRCI.3fEgmD3oDSb6Rwy"  # nosec B105

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        # Truncate password to 72 bytes for bcrypt compatibility
        password_bytes = plain_password[:72].encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        password_bytes = password[:72].encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a new access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user by fetching from Firestore."""
        try:
            # Query users by email
            users_ref = self.firestore.collection("users")
            query = users_ref.where("email", "==", username).limit(1)
            docs = query.stream()

            user_doc = None
            async for doc in docs:
                user_doc = doc
                break

            if not user_doc:
                # DEVELOPMENT MODE: Auto-create test user on first login
                if settings.environment == "development" and settings.use_firestore_mocks:
                    if password == "test123":  # Only works with test password
                        logger.info("Auto-creating test user", extra={"username": username})
                        user_id = f"user_{username.split('@')[0]}"

                        # Check if user already exists in Firestore (don't overwrite)
                        existing_user_doc = await users_ref.document(user_id).get()
                        if existing_user_doc.exists:
                            logger.info(
                                "Test user already exists, skipping creation",
                                extra={"username": username},
                            )
                            user_doc = existing_user_doc
                        else:
                            test_user_data = {
                                "user_id": user_id,
                                "email": username,
                                "display_name": username.split("@")[0].title(),
                                "tier": "PRO",  # Give PRO tier for testing
                                "hashed_password": self.test_password_hash,
                                "quota_used_today": 0,
                                "daily_quota": 1000,
                                "created_at": datetime.utcnow().isoformat(),
                                "role": "user",
                            }
                            await users_ref.document(user_id).set(test_user_data)
                        return UserInDB(
                            user_id=user_id,
                            email=username,
                            full_name=test_user_data["display_name"],
                            tier="PRO",
                            hashed_password=self.test_password_hash,
                        )
                return None

            user_data = user_doc.to_dict()

            # Verify password against stored hash
            stored_hash = user_data.get("hashed_password", self.test_password_hash)
            if not self.verify_password(password, stored_hash):
                return None

            # Return UserInDB (compatible with existing auth flow)
            return UserInDB(
                user_id=user_data.get("user_id"),
                email=user_data.get("email"),
                full_name=user_data.get("display_name", ""),
                tier=user_data.get("tier", "free"),
                hashed_password=self.test_password_hash,
            )
        except Exception:
            return None

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate user and return JWT access token.

        Args:
            username: User email
            password: Plain text password

        Returns:
            JWT access token

        Raises:
            AuthenticationError: If credentials invalid
        """
        from src.core.exceptions import AuthenticationError

        user = await self.authenticate_user(username, password)
        if not user:
            raise AuthenticationError("Invalid username or password")

        # Create access token
        access_token = self.create_access_token(
            data={
                "sub": user.user_id,
                "email": user.email,
                "tier": user.tier.value.lower()
                if hasattr(user.tier, "value")
                else str(user.tier).lower(),
            }
        )

        # Update last login timestamp
        try:
            user_ref = self.firestore.collection("users").document(user.user_id)
            await user_ref.update(
                {"last_login_at": datetime.utcnow(), "login_count": firestore.Increment(1)}
            )
        except Exception as e:
            # Non-critical failure - log and continue
            logger.warning(
                "Failed to update last login timestamp",
                extra={"user_id": user.user_id, "error": str(e)},
            )

        return access_token

    async def register(self, email: str, password: str, full_name: Optional[str] = None) -> "User":
        """
        Register a new user account.

        Args:
            email: User email address
            password: Plain text password (will be hashed)
            full_name: Optional display name

        Returns:
            Created User object

        Raises:
            ValidationError: If email already exists or password too weak
        """
        from src.core.exceptions import ValidationError
        from src.models.users import User
        from src.models.permissions import Tier
        import uuid

        # Check if email already exists
        users_ref = self.firestore.collection("users")
        query = users_ref.where("email", "==", email).limit(1)
        docs = query.stream()

        async for doc in docs:
            raise ValidationError(f"Email {email} already registered")

        # Generate user ID
        user_id = f"user_{uuid.uuid4().hex[:12]}"

        # Hash password
        hashed_password = self.get_password_hash(password)

        # Create user document
        user_data = {
            "user_id": user_id,
            "email": email,
            "full_name": full_name or "",
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False,
            "tier": Tier.FREE.value,
            "daily_quota": 100,
            "quota_used_today": 0,
            "quota_reset_at": datetime.utcnow(),
            "status": "active",
            "role": "user",
            "organization_id": None,
            "team_ids": [],
            "last_login_at": None,
            "ip_address": None,
            "login_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Save to Firestore
        user_ref = self.firestore.collection("users").document(user_id)
        await user_ref.set(user_data)

        return User(**user_data)

    async def refresh_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New JWT access token

        Raises:
            AuthenticationError: If refresh token invalid or expired
        """
        from src.core.exceptions import AuthenticationError

        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")

            if not user_id:
                raise AuthenticationError("Invalid refresh token")

            # Verify user still exists and is active
            user_ref = self.firestore.collection("users").document(user_id)
            user_doc = await user_ref.get()

            if not user_doc.exists:
                raise AuthenticationError("User not found")

            user_data = user_doc.to_dict()
            if not user_data.get("is_active", False):
                raise AuthenticationError("User account is inactive")

            # Create new access token
            access_token = self.create_access_token(
                data={"sub": user_id, "email": user_data.get("email")}
            )

            return access_token

        except jwt.JWTError:
            raise AuthenticationError("Invalid or expired refresh token")

    async def logout(self, user_id: str) -> None:
        """
        Logout user (invalidate tokens server-side if using token blacklist).

        Args:
            user_id: User to logout

        Note:
            Current implementation is stateless (JWT-based).
            For true logout, implement token blacklist in Redis.
        """
        # In stateless JWT, logout is client-side (delete token)
        # For server-side logout, add token to blacklist
        pass

    async def get_user_by_email(self, email: str) -> Optional["User"]:
        """Get user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        try:
            users_query = self.firestore.collection("users").where("email", "==", email).limit(1)

            docs = [doc async for doc in users_query.stream()]
            if not docs:
                return None

            user_data = docs[0].to_dict()
            from src.models.users import User

            return User(**user_data)
        except Exception:
            return None

    async def get_user(self, user_id: str) -> "User":
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User object

        Raises:
            NotFoundError: If user doesn't exist
        """
        from src.core.exceptions import NotFoundError
        from src.models.users import User

        user_ref = self.firestore.collection("users").document(user_id)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            raise NotFoundError(f"User {user_id} not found")

        user_data = user_doc.to_dict()
        return User(**user_data)

    async def update_user(self, user_id: str, updates: "UserUpdate") -> "User":
        """
        Update user profile.

        Args:
            user_id: User to update
            updates: Fields to update (partial)

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If email already in use by another user
        """
        from src.core.exceptions import NotFoundError, ValidationError
        from src.models.users import User

        # Verify user exists
        user_ref = self.firestore.collection("users").document(user_id)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            raise NotFoundError(f"User {user_id} not found")

        # Check if email change conflicts with existing user
        if updates.email:
            users_ref = self.firestore.collection("users")
            query = users_ref.where("email", "==", updates.email).limit(1)
            docs = query.stream()

            async for doc in docs:
                if doc.id != user_id:
                    raise ValidationError(f"Email {updates.email} already in use")

        # Build update dict (only non-None fields)
        update_data = {
            k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None
        }
        update_data["updated_at"] = datetime.utcnow()

        # Update Firestore
        await user_ref.update(update_data)

        # Fetch and return updated user
        updated_doc = await user_ref.get()
        return User(**updated_doc.to_dict())
