"""
Authentication Service

Provides authentication and session management functions including:
- User sign-up
- User sign-out
- Session management
- Token invalidation
- KakaoTalk OAuth sign-up/sign-in
"""

from datetime import datetime
from typing import Optional, Any, Tuple
from app.utils.firebase_config import get_firestore_client
from app.models.member import User
from app.services.kakao_oauth_service import get_kakao_oauth_service


class AuthService:
    """Service class for authentication-related operations."""

    USERS_COLLECTION = "members"
    SESSIONS_COLLECTION = "sessions"

    def __init__(self):
        """Initialize the auth service with Firestore client."""
        self.db: Any = get_firestore_client()

    async def sign_up_user(self, email: str, display_name: str) -> User:
        """
        Sign up a new user by creating a member record.

        This function:
        1. Checks if email already exists
        2. Creates a new member document with email and username
        3. Initializes member with default values

        Args:
            email (str): User's email address
            display_name (str): User's display name/username

        Returns:
            User: The created user object

        Raises:
            ValueError: If email already exists
            Exception: If there's an error during sign-up
        """
        try:
            # Check if email already exists
            existing_users = (
                self.db.collection(self.USERS_COLLECTION)
                .where("email", "==", email)
                .limit(1)
                .stream()
            )

            if any(existing_users):
                raise ValueError(f"User with email '{email}' already exists")

            # Create new member document
            now = datetime.now()
            member_data = {
                "email": email,
                "displayName": display_name,
                "photoURL": None,
                "role": "user",
                "phone": None,
                "address": None,
                "isEmailVerified": False,
                "createdAt": now,
                "lastSignInAt": now,
                "isSignedIn": True,
                "preferences": {
                    "emailNotifications": True,
                    "marketingEmails": False,
                },
            }

            # Add member to Firestore
            doc_ref = self.db.collection(self.USERS_COLLECTION).document()
            doc_ref.set(member_data)

            print(f"User {email} signed up successfully with ID: {doc_ref.id}")

            # Create and return User object
            return User(
                id=doc_ref.id,
                email=email,
                display_name=display_name,
                photo_url=None,
                role="user",
                phone=None,
                address=None,
                is_email_verified=False,
                created_at=now,
                last_sign_in_at=now,
                preferences=member_data["preferences"],
            )

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error signing up user: {str(e)}")

    async def sign_out_user(self, user_id: str) -> bool:
        """
        Sign out a user by invalidating their session and updating their status.

        This function:
        1. Updates the user's last sign-out timestamp
        2. Invalidates any active sessions
        3. Clears authentication tokens/sessions

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if sign-out was successful, False otherwise

        Raises:
            Exception: If there's an error during sign-out
        """
        try:
            # Update user's last sign-out timestamp
            user_ref = self.db.collection(self.USERS_COLLECTION).document(user_id)

            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"User {user_id} not found for sign-out")
                return False

            # Update user document with sign-out info
            user_ref.update(
                {
                    "lastSignOutAt": datetime.now(),
                    "isSignedIn": False,
                    "updatedAt": datetime.now(),
                }
            )

            print(f"User {user_id} signed out successfully")

            # Optional: Invalidate sessions
            await self._invalidate_sessions(user_id)

            return True

        except Exception as e:
            print(f" Error signing out user {user_id}: {str(e)}")
            return False

    async def _invalidate_sessions(self, user_id: str) -> bool:
        """
        Invalidate all active sessions for a user.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if sessions were invalidated, False otherwise
        """
        try:
            # Query and delete all active sessions for the user
            sessions_ref = self.db.collection(self.SESSIONS_COLLECTION)
            query = sessions_ref.where("user_id", "==", user_id).where("is_active", "==", True)

            docs = query.stream()
            deleted_count = 0

            for doc in docs:
                doc.reference.update({"is_active": False, "signed_out_at": datetime.now()})
                deleted_count += 1

            if deleted_count > 0:
                print(f"Invalidated {deleted_count} session(s) for user {user_id}")

            return True

        except Exception as e:
            print(f"Error invalidating sessions for user {user_id}: {str(e)}")
            return False

    async def verify_user_session(self, user_id: str) -> bool:
        """
        Verify if a user has an active session.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if user has an active session, False otherwise
        """
        try:
            user_ref = self.db.collection(self.USERS_COLLECTION).document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return False

            user_data = user_doc.to_dict()
            # Check if user is signed in
            is_signed_in = user_data.get("isSignedIn", user_data.get("is_signed_in", False))

            return is_signed_in

        except Exception as e:
            print(f"Error verifying session for user {user_id}: {str(e)}")
            return False

    async def get_user_session_info(self, user_id: str) -> Optional[dict]:
        """
        Get information about a user's current session.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            Optional[dict]: Session information if user is signed in, None otherwise
        """
        try:
            user_ref = self.db.collection(self.USERS_COLLECTION).document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return None

            user_data = user_doc.to_dict()

            return {
                "userId": user_id,
                "isSignedIn": user_data.get("isSignedIn", user_data.get("is_signed_in", False)),
                "createdAt": user_data.get("createdAt", user_data.get("created_at")),
                "lastSignInAt": user_data.get("lastSignInAt", user_data.get("last_sign_in_at")),
                "lastSignOutAt": user_data.get("lastSignOutAt", user_data.get("last_sign_out_at")),
            }

        except Exception as e:
            print(f"Error getting session info for user {user_id}: {str(e)}")
            return None

    # ==================== KAKAO OAUTH METHODS ====================

    async def sign_up_with_kakao(
        self,
        kakao_code: str,
        display_name: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        Sign up a new user using KakaoTalk OAuth.

        This function:
        1. Exchanges KakaoTalk authorization code for access token
        2. Retrieves user information from KakaoTalk
        3. Creates a new user if email doesn't exist
        4. Links KakaoTalk account to the user

        Args:
            kakao_code: KakaoTalk authorization code from OAuth callback
            display_name: Optional custom display name (defaults to KakaoTalk nickname)
            redirect_uri: Optional override of default redirect URI

        Returns:
            Tuple[User, bool]: Created user object and whether it's a new user

        Raises:
            ValueError: If KakaoTalk authentication fails or email already exists
            Exception: If there's an error during sign-up
        """
        try:
            # Get Kakao OAuth service
            kakao_service = get_kakao_oauth_service()

            # Authenticate with KakaoTalk
            kakao_auth = await kakao_service.authenticate_with_kakao(
                kakao_code, redirect_uri
            )

            kakao_id = kakao_auth.get("kakao_id")
            email = kakao_auth.get("email")
            nickname = kakao_auth.get("nickname")
            profile_image = kakao_auth.get("profile_image")

            if not email:
                raise ValueError(
                    "KakaoTalk account does not have a verified email address. "
                    "Please verify your email in KakaoTalk settings."
                )

            # Check if user with this email already exists
            existing_users = (
                self.db.collection(self.USERS_COLLECTION)
                .where("email", "==", email)
                .limit(1)
                .stream()
            )

            existing_user_list = list(existing_users)
            if existing_user_list:
                # User already exists, update Kakao info if not set
                user_doc = existing_user_list[0]
                user_data = user_doc.to_dict()

                if not user_data.get("kakaoId"):
                    user_doc.reference.update({
                        "kakaoId": kakao_id,
                        "kakaoConnectedAt": datetime.now(),
                    })

                return User(
                    id=user_doc.id,
                    email=user_data.get("email"),
                    display_name=user_data.get("displayName"),
                    photo_url=user_data.get("photoURL"),
                    role=user_data.get("role", "user"),
                    phone=user_data.get("phone"),
                    address=user_data.get("address"),
                    is_email_verified=user_data.get("isEmailVerified", False),
                    created_at=user_data.get("createdAt"),
                    last_sign_in_at=datetime.now(),
                    kakao_id=kakao_id,
                    kakao_connected_at=datetime.now(),
                    preferences=user_data.get("preferences"),
                ), False

            # Create new user
            now = datetime.now()
            final_display_name = display_name or nickname or email.split("@")[0]

            member_data = {
                "email": email,
                "displayName": final_display_name,
                "photoURL": profile_image,
                "role": "user",
                "phone": None,
                "address": None,
                "isEmailVerified": True,  # KakaoTalk emails are verified
                "kakaoId": kakao_id,
                "kakaoConnectedAt": now,
                "createdAt": now,
                "lastSignInAt": now,
                "isSignedIn": True,
                "preferences": {
                    "emailNotifications": True,
                    "marketingEmails": False,
                },
            }

            # Add member to Firestore
            doc_ref = self.db.collection(self.USERS_COLLECTION).document()
            doc_ref.set(member_data)

            print(f"User {email} signed up with KakaoTalk (Kakao ID: {kakao_id})")

            # Create and return User object
            return User(
                id=doc_ref.id,
                email=email,
                display_name=final_display_name,
                photo_url=profile_image,
                role="user",
                phone=None,
                address=None,
                is_email_verified=True,
                created_at=now,
                last_sign_in_at=now,
                kakao_id=kakao_id,
                kakao_connected_at=now,
                preferences=member_data["preferences"],
            ), True

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error signing up with KakaoTalk: {str(e)}")

    async def sign_in_with_kakao(
        self,
        kakao_code: str,
        redirect_uri: Optional[str] = None,
    ) -> User:
        """
        Sign in an existing user using KakaoTalk OAuth.

        This function:
        1. Exchanges KakaoTalk authorization code for access token
        2. Retrieves user information from KakaoTalk
        3. Looks up user by email or KakaoTalk ID
        4. Updates last sign-in timestamp

        Args:
            kakao_code: KakaoTalk authorization code from OAuth callback
            redirect_uri: Optional override of default redirect URI

        Returns:
            User: The authenticated user object

        Raises:
            ValueError: If KakaoTalk authentication fails or user not found
            Exception: If there's an error during sign-in
        """
        try:
            # Get Kakao OAuth service
            kakao_service = get_kakao_oauth_service()

            # Authenticate with KakaoTalk
            kakao_auth = await kakao_service.authenticate_with_kakao(
                kakao_code, redirect_uri
            )

            kakao_id = kakao_auth.get("kakao_id")
            email = kakao_auth.get("email")

            if not email:
                raise ValueError(
                    "KakaoTalk account does not have a verified email address. "
                    "Please verify your email in KakaoTalk settings."
                )

            # Try to find user by email first
            users = (
                self.db.collection(self.USERS_COLLECTION)
                .where("email", "==", email)
                .limit(1)
                .stream()
            )

            user_list = list(users)

            if not user_list:
                # Try to find by KakaoTalk ID as fallback
                users = (
                    self.db.collection(self.USERS_COLLECTION)
                    .where("kakaoId", "==", kakao_id)
                    .limit(1)
                    .stream()
                )

                user_list = list(users)

                if not user_list:
                    raise ValueError(
                        f"User with email '{email}' not found. "
                        "Please sign up first."
                    )

            user_doc = user_list[0]
            user_data = user_doc.to_dict()

            # Update last sign-in timestamp and ensure Kakao ID is linked
            user_doc.reference.update({
                "lastSignInAt": datetime.now(),
                "isSignedIn": True,
                "updatedAt": datetime.now(),
                "kakaoId": kakao_id,
                "kakaoConnectedAt": kakao_auth.get("connected_at", datetime.now()),
            })

            print(f"User {email} signed in with KakaoTalk")

            # Return updated User object
            return User(
                id=user_doc.id,
                email=user_data.get("email"),
                display_name=user_data.get("displayName"),
                photo_url=user_data.get("photoURL"),
                role=user_data.get("role", "user"),
                phone=user_data.get("phone"),
                address=user_data.get("address"),
                is_email_verified=user_data.get("isEmailVerified", False),
                created_at=user_data.get("createdAt"),
                last_sign_in_at=datetime.now(),
                kakao_id=kakao_id,
                kakao_connected_at=kakao_auth.get("connected_at"),
                preferences=user_data.get("preferences"),
            )

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error signing in with KakaoTalk: {str(e)}")


# Global auth service instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create the auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


async def sign_out_user(user_id: str) -> bool:
    """
    Convenience function to sign out a user.

    Args:
        user_id (str): The unique identifier of the user

    Returns:
        bool: True if sign-out was successful, False otherwise
    """
    auth_service = get_auth_service()
    return await auth_service.sign_out_user(user_id)
