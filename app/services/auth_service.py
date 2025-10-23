"""
Authentication Service

Provides authentication and session management functions including:
- User sign-out
- Session management
- Token invalidation
"""

from datetime import datetime
from typing import Optional, Any
from app.utils.firebase_config import get_firestore_client


class AuthService:
    """Service class for authentication-related operations."""

    USERS_COLLECTION = "members"
    SESSIONS_COLLECTION = "sessions"

    def __init__(self):
        """Initialize the auth service with Firestore client."""
        self.db: Any = get_firestore_client()

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
                print(f"� User {user_id} not found for sign-out")
                return False

            # Update user document with sign-out info
            user_ref.update(
                {
                    "last_sign_out_at": datetime.now(),
                    "is_signed_in": False,
                    "updated_at": datetime.now(),
                }
            )

            print(f" User {user_id} signed out successfully")

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
                print(f" Invalidated {deleted_count} session(s) for user {user_id}")

            return True

        except Exception as e:
            print(f" Error invalidating sessions for user {user_id}: {str(e)}")
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
            is_signed_in = user_data.get("is_signed_in", False)

            return is_signed_in

        except Exception as e:
            print(f" Error verifying session for user {user_id}: {str(e)}")
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
                "user_id": user_id,
                "is_signed_in": user_data.get("is_signed_in", False),
                "created_at": user_data.get("created_at"),
                "last_sign_in_at": user_data.get("last_sign_in_at"),
                "last_sign_out_at": user_data.get("last_sign_out_at"),
            }

        except Exception as e:
            print(f" Error getting session info for user {user_id}: {str(e)}")
            return None


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
