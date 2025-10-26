"""
Member Service

Provides business logic and database operations for managing users stored in the
`members` collection (legacy naming).
"""

from typing import Any, List, Optional
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.member import User, UserCreate, UserUpdate, UserPreferences
from app.utils.firebase_config import get_firestore_client


class MemberService:
    """Service class for user-related database operations."""

    COLLECTION_NAME = "members"

    def __init__(self):
        """Initialize the member service with Firestore client."""
        self.db: Any = get_firestore_client()

    def fetch_user_by_id(self, member_id: str) -> Optional[User]:
        """
        Fetch a user from the members collection by member ID.

        Args:
            member_id (str): The unique identifier of the user document in Firestore

        Returns:
            Optional[User]: User object if found, None otherwise

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            doc = self.db.collection(self.COLLECTION_NAME).document(member_id).get()

            if doc.exists:
                return self._document_to_user(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching user with ID {member_id}: {str(e)}")

    def fetch_user_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user from the members collection by email address.

        Args:
            email (str): The email address of the user

        Returns:
            Optional[User]: User object if found, None otherwise

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = (
                self.db.collection(self.COLLECTION_NAME)
                .where("email", "==", email)
                .limit(1)
                .stream()
            )

            for doc in docs:
                return self._document_to_user(doc)
            return None
        except Exception as e:
            raise Exception(f"Error fetching user with email {email}: {str(e)}")

    def fetch_all_users(self) -> List[User]:
        """
        Fetch all users from the members collection.

        Returns:
            List[User]: List of all user objects

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = self.db.collection(self.COLLECTION_NAME).stream()
            users = [self._document_to_user(doc) for doc in docs]
            return users
        except Exception as e:
            raise Exception(f"Error fetching all users: {str(e)}")

    def fetch_users_by_criteria(self, field: str, value: any, operator: str = "==") -> List[User]:
        """
        Fetch users from the members collection based on custom criteria.

        Args:
            field (str): The field name to filter by
            value (any): The value to match
            operator (str): The comparison operator (==, <, >, <=, >=, !=)

        Returns:
            List[User]: List of user objects matching the criteria

        Raises:
            Exception: If there's an error accessing the database
            ValueError: If an invalid operator is provided
        """
        valid_operators = ["==", "<", ">", "<=", ">=", "!="]
        if operator not in valid_operators:
            raise ValueError(
                f"Invalid operator '{operator}'. Must be one of: {', '.join(valid_operators)}"
            )

        try:
            storage_field = self._map_storage_field(field)
            query = self.db.collection(self.COLLECTION_NAME).where(storage_field, operator, value)
            docs = query.stream()
            users = [self._document_to_user(doc) for doc in docs]
            return users
        except Exception as e:
            raise Exception(
                f"Error fetching users with criteria {field} {operator} {value}: {str(e)}"
            )

    @staticmethod
    def _map_storage_field(field: str) -> str:
        """
        Map internal snake_case field names to stored Firestore field names (camelCase).
        """
        field_mapping = {
            "display_name": "displayName",
            "displayName": "displayName",
            "photo_url": "photoURL",
            "photoURL": "photoURL",
            "is_email_verified": "isEmailVerified",
            "isEmailVerified": "isEmailVerified",
            "created_at": "createdAt",
            "createdAt": "createdAt",
            "lastSignInAt": "lastSignInAt",
            "last_sign_in_at": "lastSignInAt",
        }
        return field_mapping.get(field, field)

    def create_user(self, member_data: UserCreate) -> User:
        """
        Create a new user in the members collection.

        Args:
            member_data (UserCreate): The user data to create

        Returns:
            User: The created user object with ID

        Raises:
            Exception: If there's an error creating the user
        """
        try:
            now = datetime.now()
            data = member_data.model_dump(by_alias=True, exclude_none=True)
            data.setdefault("createdAt", now)
            data.setdefault("lastSignInAt", now)
            data.setdefault("isEmailVerified", False)
            data.setdefault("role", "user")
            if data.get("preferences") is None:
                data["preferences"] = {
                    "emailNotifications": True,
                    "marketingEmails": False,
                }
            data["updatedAt"] = now

            doc_ref = self.db.collection(self.COLLECTION_NAME).document()
            doc_ref.set(data)

            return User(
                id=doc_ref.id,
                email=data["email"],
                display_name=data.get("displayName"),
                photo_url=data.get("photoURL"),
                role=data.get("role", "user"),
                is_email_verified=data.get("isEmailVerified", False),
                phone=data.get("phone"),
                address=data.get("address"),
                preferences=data.get("preferences"),
                created_at=data["createdAt"],
                last_sign_in_at=data.get("lastSignInAt"),
            )
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")

    def update_user(self, member_id: str, update_data: UserUpdate) -> Optional[User]:
        """
        Update an existing user in the members collection.

        Args:
            member_id (str): The ID of the member to update
            update_data (UserUpdate): The data to update

        Returns:
            Optional[User]: The updated user object, or None if member doesn't exist

        Raises:
            Exception: If there's an error updating the user
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(member_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = update_data.model_dump(by_alias=True, exclude_none=True)
            update_fields["updatedAt"] = datetime.now()

            doc_ref.update(update_fields)

            # Fetch and return the updated user
            return self.fetch_user_by_id(member_id)
        except Exception as e:
            raise Exception(f"Error updating user with ID {member_id}: {str(e)}")

    def delete_user(self, member_id: str) -> bool:
        """
        Delete a user from the members collection.

        Args:
            member_id (str): The ID of the user to delete

        Returns:
            bool: True if the user was deleted, False if the user doesn't exist

        Raises:
            Exception: If there's an error deleting the user
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(member_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting user with ID {member_id}: {str(e)}")

    @staticmethod
    def _document_to_user(doc: DocumentSnapshot) -> User:
        """
        Convert a Firestore document snapshot to a User object.

        Args:
            doc (DocumentSnapshot): The Firestore document snapshot

        Returns:
            User: The converted User object
        """
        data = doc.to_dict() or {}

        # Handle preferences with backward compatibility for casing
        preferences_data = data.get("preferences")
        preferences = UserPreferences(**preferences_data) if preferences_data else None

        display_name = data.get("displayName") or data.get("display_name")
        photo_url = data.get("photoURL") or data.get("photo_url")
        created_at = data.get("createdAt") or data.get("created_at") or datetime.now()
        last_sign_in_at = data.get("lastSignInAt") or data.get("last_sign_in_at")
        is_email_verified = data.get("isEmailVerified", data.get("is_email_verified", False))
        role = data.get("role", "user")

        return User(
            id=doc.id,
            email=data.get("email"),
            display_name=display_name,
            photo_url=photo_url,
            role=role,
            is_email_verified=is_email_verified,
            phone=data.get("phone"),
            address=data.get("address"),
            preferences=preferences,
            created_at=created_at,
            last_sign_in_at=last_sign_in_at,
        )


# Convenience function to create a service instance
def get_member_service() -> MemberService:
    """Create and return a user service instance."""
    return MemberService()
